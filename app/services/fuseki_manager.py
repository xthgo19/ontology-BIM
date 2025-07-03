import ifcopenshell
from rdflib import Graph, Namespace, Literal, RDF, RDFS
import requests
from flask import current_app
from SPARQLWrapper import SPARQLWrapper, JSON

BASE_URI = "http://exemplo.org/bim#"
inst = Namespace(BASE_URI)

def convert_ifc_to_rdf(ifc_file_path):
    try:
        ifc_file = ifcopenshell.open(ifc_file_path)
    except Exception as e:
        current_app.logger.error(f"ERRO ao abrir IFC: {e}")
        return None
    graph = Graph()
    graph.bind("inst", inst)
    graph.bind("rdfs", RDFS)
    for element in ifc_file.by_type('IfcObjectDefinition'):
        uri = inst[element.GlobalId]
        if element.Name: graph.add((uri, RDFS.label, Literal(element.Name)))
        class_uri = inst[element.is_a()]
        graph.add((uri, RDF.type, class_uri))
        graph.add((class_uri, RDFS.label, Literal(element.is_a())))
    for rel in ifc_file.by_type('IfcRelationship'):
        if rel.is_a('IfcRelAssociatesMaterial') and hasattr(rel, 'RelatedObjects'):
            for obj in rel.RelatedObjects:
                if getattr(obj, 'GlobalId', None):
                    mat = rel.RelatingMaterial
                    if mat and mat.is_a('IfcMaterial'):
                        mat_uri = inst[f"Mat_{mat.Name.replace(' ', '_')}"]
                        graph.add((mat_uri, RDFS.label, Literal(mat.Name)))
                        graph.add((inst[obj.GlobalId], inst.hasMaterial, mat_uri))
    current_app.logger.info(f"Conversão para RDF (Fuseki) concluída: {len(graph)} triplos.")
    return graph

def upload_to_fuseki(graph):
    endpoint = current_app.config['FUSEKI_GSP_ENDPOINT']
    # --- INÍCIO DA CORREÇÃO ---
    # Define as credenciais de autenticação para o Fuseki
    auth = (current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    # --- FIM DA CORREÇÃO ---
    try:
        # Usa as credenciais no pedido DELETE
        requests.delete(endpoint, params={'default': ''}, auth=auth).raise_for_status()
    except requests.exceptions.RequestException as e:
        current_app.logger.warning(f"Não foi possível limpar o grafo no Fuseki: {e}")
    try:
        # Usa as credenciais no pedido POST
        response = requests.post(
            endpoint, 
            params={'default': ''}, 
            data=graph.serialize(format='turtle'), 
            headers={'Content-Type': 'text/turtle'},
            auth=auth
        )
        response.raise_for_status()
        current_app.logger.info("Novos dados carregados no Fuseki.")
        return True
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"ERRO ao carregar para o Fuseki: {e}")
        return False

def get_ontology_summary():
    sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
    # --- INÍCIO DA CORREÇÃO ---
    # Define as credenciais para as consultas SPARQL
    sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    # --- FIM DA CORREÇÃO ---
    sparql.setReturnFormat(JSON)
    query = f"PREFIX rdfs: <{RDFS}> PREFIX inst: <{BASE_URI}> SELECT ?type_label (GROUP_CONCAT(DISTINCT ?ex; SEPARATOR=\", \") AS ?examples) WHERE {{ ?s a ?type ; rdfs:label ?ex . ?type rdfs:label ?type_label . FILTER(STRSTARTS(STR(?type), STR(inst:))) }} GROUP BY ?type_label ORDER BY ?type_label"
    sparql.setQuery(query)
    types_res = sparql.query().convert()
    types = [{"type": r['type_label']['value'], "examples": r['examples']['value'].split(', ')} for r in types_res["results"]["bindings"]]
    return {"types": types, "relations": ["hasMaterial", "isContainedIn", "isOfType", "aggregates"]}