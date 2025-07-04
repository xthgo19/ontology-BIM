import ifcopenshell
from rdflib import Graph, Namespace, Literal, RDF, RDFS
import requests
from flask import current_app
from SPARQLWrapper import SPARQLWrapper, JSON

BASE_URI = "http://exemplo.org/bim#"
inst = Namespace(BASE_URI)

def convert_ifc_to_rdf(ifc_file_path):
    """
    Converte um ficheiro IFC para um grafo RDF, processando uma gama abrangente de
    entidades e relacionamentos para criar um grafo de conhecimento conectado e detalhado.
    """
    try:
        ifc_file = ifcopenshell.open(ifc_file_path)
    except Exception as e:
        current_app.logger.error(f"ERRO ao abrir IFC: {e}")
        return None
        
    graph = Graph()
    graph.bind("inst", inst)
    graph.bind("rdfs", RDFS)

    # 1. Adiciona todos os objetos e suas classes como nós
    for element in ifc_file.by_type('IfcObjectDefinition'):
        if not getattr(element, 'GlobalId', None): continue
        uri = inst[element.GlobalId]
        if element.Name:
            graph.add((uri, RDFS.label, Literal(element.Name)))
        class_uri = inst[element.is_a()]
        graph.add((uri, RDF.type, class_uri))
        graph.add((class_uri, RDFS.label, Literal(element.is_a())))

    # 2. Processa uma variedade de tipos de relacionamentos
    for rel in ifc_file.by_type('IfcRelationship'):
        if not getattr(rel, 'GlobalId', None): continue

        # Relações de Agregação (ex: Projeto -> Edifício -> Andar)
        if rel.is_a('IfcRelAggregates'):
            if not getattr(rel, 'RelatingObject', None) or not getattr(rel, 'RelatedObjects', None): continue
            relating_object_uri = inst[rel.RelatingObject.GlobalId]
            for related_obj in rel.RelatedObjects:
                if getattr(related_obj, 'GlobalId', None):
                    related_object_uri = inst[related_obj.GlobalId]
                    graph.add((relating_object_uri, inst.aggregates, related_object_uri))

        # Relações de Conteúdo Espacial (ex: Andar -> Parede)
        elif rel.is_a('IfcRelContainedInSpatialStructure'):
            if not getattr(rel, 'RelatingStructure', None) or not getattr(rel, 'RelatedElements', None): continue
            spatial_structure_uri = inst[rel.RelatingStructure.GlobalId]
            for contained_elem in rel.RelatedElements:
                if getattr(contained_elem, 'GlobalId', None):
                    contained_elem_uri = inst[contained_elem.GlobalId]
                    graph.add((spatial_structure_uri, inst.contains, contained_elem_uri))
                    graph.add((contained_elem_uri, inst.isContainedIn, spatial_structure_uri))

        # Relações de Material (lógica generalizada)
        elif rel.is_a('IfcRelAssociatesMaterial'):
            mat = None
            # Tenta obter material de um LayerSet
            if hasattr(rel.RelatingMaterial, 'ForLayerSet') and rel.RelatingMaterial.ForLayerSet:
                if rel.RelatingMaterial.ForLayerSet.MaterialLayers:
                    mat = rel.RelatingMaterial.ForLayerSet.MaterialLayers[0].Material
            # Tenta obter material diretamente (caso mais simples)
            elif hasattr(rel.RelatingMaterial, 'Name'):
                mat = rel.RelatingMaterial
            
            if mat and getattr(mat, 'Name', None):
                mat_uri = inst[f"Mat_{mat.Name.replace(' ', '_')}"]
                graph.add((mat_uri, RDFS.label, Literal(mat.Name)))
                graph.add((mat_uri, RDF.type, inst.Material))
                for obj in rel.RelatedObjects:
                    if getattr(obj, 'GlobalId', None):
                        graph.add((inst[obj.GlobalId], inst.hasMaterial, mat_uri))

        # Relações de Tipo (ex: IfcWall -> IfcWallType)
        elif rel.is_a('IfcRelDefinesByType'):
            if not getattr(rel, 'RelatingType', None) or not getattr(rel.RelatingType, 'GlobalId', None): continue
            type_uri = inst[rel.RelatingType.GlobalId]
            for obj in rel.RelatedObjects:
                if getattr(obj, 'GlobalId', None):
                    graph.add((inst[obj.GlobalId], inst.isDefinedBy, type_uri))

        # Relações de Propriedades e Quantidades
        elif rel.is_a('IfcRelDefinesByProperties'):
            if not getattr(rel, 'RelatingPropertyDefinition', None): continue
            prop_set = rel.RelatingPropertyDefinition
            
            # Extrai Quantidades (Volume, Área, etc.)
            if prop_set.is_a('IfcElementQuantity'):
                for quantity in prop_set.Quantities:
                    if not getattr(quantity, 'Name', None) or not hasattr(quantity, 'Value'): continue
                    prop_name = inst[str(quantity.Name).replace(' ', '_')]
                    value_literal = Literal(quantity.Value)
                    for obj in rel.RelatedObjects:
                        if getattr(obj, 'GlobalId', None):
                             graph.add((inst[obj.GlobalId], prop_name, value_literal))

            # Extrai Propriedades de texto/numéricas
            elif prop_set.is_a('IfcPropertySet'):
                 if not hasattr(prop_set, 'HasProperties'): continue
                 for prop in prop_set.HasProperties:
                     if prop.is_a('IfcPropertySingleValue') and getattr(prop, 'NominalValue', None):
                        prop_name = inst[str(prop.Name).replace(' ', '_')]
                        value_literal = Literal(prop.NominalValue.wrappedValue)
                        for obj in rel.RelatedObjects:
                            if getattr(obj, 'GlobalId', None):
                                 graph.add((inst[obj.GlobalId], prop_name, value_literal))

    current_app.logger.info(f"Conversão para RDF (Fuseki) concluída: {len(graph)} triplos.")
    return graph

def upload_to_fuseki(graph):
    endpoint = current_app.config['FUSEKI_GSP_ENDPOINT']
    auth = (current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    try:
        requests.delete(endpoint, params={'default': ''}, auth=auth).raise_for_status()
    except requests.exceptions.RequestException as e:
        current_app.logger.warning(f"Não foi possível limpar o grafo no Fuseki: {e}")
    try:
        response = requests.post(
            endpoint, params={'default': ''}, data=graph.serialize(format='turtle'),
            headers={'Content-Type': 'text/turtle'}, auth=auth
        )
        response.raise_for_status()
        current_app.logger.info("Novos dados carregados no Fuseki.")
        return True
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"ERRO ao carregar para o Fuseki: {e}")
        return False

def get_ontology_summary():
    sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
    sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    sparql.setReturnFormat(JSON)

    # Consulta 1: Busca os tipos de objetos e exemplos de nomes
    types_query = f"""
        PREFIX rdfs: <{RDFS}>
        PREFIX inst: <{BASE_URI}>
        SELECT ?type_label (GROUP_CONCAT(DISTINCT ?ex; SEPARATOR=", ") AS ?examples)
        WHERE {{
            ?s a ?type ; rdfs:label ?ex .
            ?type rdfs:label ?type_label .
            FILTER(STRSTARTS(STR(?type), STR(inst:)))
        }} GROUP BY ?type_label ORDER BY ?type_label
    """
    sparql.setQuery(types_query)
    types_res = sparql.query().convert().get("results", {}).get("bindings", [])
    types = [{"type": r['type_label']['value'], "examples": r['examples']['value'].split(', ')} for r in types_res]

    # Consulta 2: Busca dinamicamente todos os tipos de relações (predicados)
    relations_query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX inst: <{BASE_URI}>
        SELECT DISTINCT ?p_name
        WHERE {{
            ?s ?p ?o .
            FILTER(?p != rdfs:label)
            BIND(
                IF(STRSTARTS(STR(?p), STR(inst:)),
                  REPLACE(STR(?p), STR(inst:), ""),
                  REPLACE(STR(?p), "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdf:")
                )
             AS ?p_name)
        }} ORDER BY ?p_name
    """
    sparql.setQuery(relations_query)
    relations_res = sparql.query().convert().get("results", {}).get("bindings", [])
    relations = sorted([r['p_name']['value'].replace('rdf:type', 'type') for r in relations_res])
    
    return {"types": types, "relations": relations}