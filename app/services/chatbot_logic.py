import os
import spacy
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import current_app
from rdflib import Namespace
from rdflib.namespace import RDFS, RDF

BASE_URI = "http://exemplo.org/bim#"
inst = Namespace(BASE_URI)
nlp = None

RELATIONSHIP_KEYWORD_MAP = {
    'material': 'hasMaterial',
    'materiais': 'hasMaterial',
    'composição': 'hasMaterial',
    'tipo': 'isDefinedBy',
    'tipos': 'isDefinedBy',
    'classe': 'type',
    'classes': 'type',
    'onde': 'isContainedIn',
    'localização': 'isContainedIn',
    'contido em': 'isContainedIn',
    'contém': 'contains',
    'agrega': 'aggregates',
    'partes': 'aggregates'
}

CLASS_KEYWORD_MAP = {
    'paredes': 'IfcWall',
    'parede': 'IfcWall',
    'lajes': 'IfcSlab',
    'laje': 'IfcSlab',
    'pisos': 'IfcSlab',
    'piso': 'IfcSlab',
    'móveis': 'IfcFurniture',
    'móvel': 'IfcFurniture',
    'portas': 'IfcDoor',
    'porta': 'IfcDoor',
    'janelas': 'IfcWindow',
    'janela': 'IfcWindow',
    'telhados': 'IfcRoof',
    'telhado': 'IfcRoof',
    'vigas': 'IfcBeam',
    'viga': 'IfcBeam'
}

INVERSE_PROPERTY_MAP = {
    "inst:contains": "está contido em",
    "inst:aggregates": "é parte de",
    "inst:isDefinedBy": "define o tipo de",
}

def _load_nlp_model():
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load(current_app.config['NLU_MODEL_PATH'])
        except IOError:
            current_app.logger.error("Modelo de NLU não encontrado.")
            nlp = False

def _format_property_name(uri):
    if '#' in uri:
        name = uri.split('#')[-1]
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    return uri.split('/')[-1]

def _get_sparql_wrapper():
    sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
    sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    sparql.setReturnFormat(JSON)
    return sparql

def _get_bidirectional_graph(node_uri, central_node_label):
    sparql = _get_sparql_wrapper()
    query = f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?s ?p ?o ?s_label ?o_label
        WHERE {{
          {{ BIND(<{node_uri}> AS ?s) ?s ?p ?o . }} UNION {{ BIND(<{node_uri}> AS ?o) ?s ?p ?o . }}
          OPTIONAL {{ ?s rdfs:label ?s_label . }} OPTIONAL {{ ?o rdfs:label ?o_label . }}
          FILTER(?s != ?o)
        }}
    """
    sparql.setQuery(query)
    results = sparql.query().convert()["results"]["bindings"]
    nodes = [{'id': node_uri, 'label': central_node_label, 'color': '#68D391', 'size': 25}]
    edges, added_nodes = [], {node_uri}
    if not results: return {"nodes": nodes, "edges": edges}
    for res in results:
        if res['p']['value'] == str(RDFS.label): continue
        s_uri, o_uri = res['s']['value'], res['o']['value']
        if s_uri not in added_nodes:
            nodes.append({'id': s_uri, 'label': res.get('s_label', {}).get('value', _format_property_name(s_uri))}); added_nodes.add(s_uri)
        if res['o']['type'] == 'uri' and o_uri not in added_nodes:
            nodes.append({'id': o_uri, 'label': res.get('o_label', {}).get('value', _format_property_name(o_uri))}); added_nodes.add(o_uri)
        if res['o']['type'] == 'uri':
            edges.append({'from': s_uri, 'to': o_uri, 'label': _format_property_name(res['p']['value'])})
    return {"nodes": nodes, "edges": edges}

def extract_bim_object(text):
    explicit_match = re.search(r"objeto '([^']*)'", text, re.IGNORECASE)
    if explicit_match: return explicit_match.group(1)
    fallback_match = re.search(r"['\"]([^'\"]+)['\"]", text)
    if fallback_match: return fallback_match.group(1)
    return None

def extract_bim_property(text):
    match = re.search(r"relação '([^']*)'", text, re.IGNORECASE)
    if match: return match.group(1).lower()
    text_lower = text.lower()
    for keyword, tech_relation in RELATIONSHIP_KEYWORD_MAP.items():
        if keyword in text_lower:
            return tech_relation
    return "label"

def process_complex_query(text):
    match = re.search(r"(?:qual|quais) (?:o|os|a|as) ([\w\s-]+) (?:de|das|dos) (?:todas as|todos os|da|do) ([\w\s-]+) (?:que estão em|no|na) ['\"]([^'\"]+)['\"]", text, re.IGNORECASE)
    if not match:
        return None

    target_prop_keyword, target_class_keyword, container_name = match.groups()
    
    target_prop = RELATIONSHIP_KEYWORD_MAP.get(target_prop_keyword.lower())
    ifc_class_name = CLASS_KEYWORD_MAP.get(target_class_keyword.lower())
    
    if not target_prop: return f"Não reconheço a propriedade '{target_prop_keyword}'."
    if not ifc_class_name: return f"Não reconheço a classe de objeto '{target_class_keyword}'."
    
    target_class_uri = f"inst:{ifc_class_name}"
    target_prop_uri = f"inst:{target_prop}"

    sparql = _get_sparql_wrapper()
    
    query = f"""
        PREFIX rdfs: <{RDFS}> PREFIX inst: <{BASE_URI}> PREFIX rdf: <{RDF}>
        SELECT DISTINCT ?answerLabel
        WHERE {{
            ?container rdfs:label "{container_name}" .
            {{ ?element inst:isContainedIn ?container . }} UNION {{ ?container inst:aggregates ?element . }}
            ?element rdf:type {target_class_uri} .
            ?element {target_prop_uri} ?target_value .
            OPTIONAL {{ ?target_value rdfs:label ?label . }}
            BIND(COALESCE(?label, REPLACE(STR(?target_value), ".*[/#]", "")) AS ?answerLabel)
        }}
    """
    try:
        sparql.setQuery(query)
        results = sparql.query().convert()["results"]["bindings"]
        if results:
            values = sorted([f"'{item['answerLabel']['value']}'" for item in results])
            return f"Os '{target_prop_keyword}' para '{target_class_keyword}' em '{container_name}' são: {', '.join(values)}."
        else:
            return f"Não encontrei resultados para a sua consulta."
    except Exception as e:
        current_app.logger.error(f"Erro na consulta complexa: {e}")
        return "Ocorreu um erro ao processar sua pergunta complexa."

def query_specific_property(object_name, property_label):
    if not object_name:
        return "Não consegui identificar sobre qual elemento você está perguntando."

    predicate_tech = RELATIONSHIP_KEYWORD_MAP.get(property_label.lower(), property_label)
    predicate = f'inst:{predicate_tech}'
    if predicate_tech == 'type': predicate = 'rdf:type'
    elif predicate_tech == 'label': predicate = 'rdfs:label'
    
    sparql = _get_sparql_wrapper()
    try:
        query_outgoing = f"""
            PREFIX rdfs: <{RDFS}> PREFIX inst: <{BASE_URI}> PREFIX rdf: <{RDF}>
            SELECT DISTINCT ?finalLabel WHERE {{
                ?element rdfs:label "{object_name}" .
                ?element {predicate} ?value .
                OPTIONAL {{ ?value rdfs:label ?valueLabel . }}
                BIND(COALESCE(?valueLabel, REPLACE(STR(?value), ".*[/#]", "")) AS ?finalLabel)
            }}
        """
        sparql.setQuery(query_outgoing)
        results = sparql.query().convert()["results"]["bindings"]
        if results:
            values = [f"'{item['finalLabel']['value']}'" for item in results]
            return f"A propriedade '{property_label}' para '{object_name}' é: {', '.join(values)}."

        inverse_relation_phrase = INVERSE_PROPERTY_MAP.get(predicate)
        if inverse_relation_phrase:
            query_incoming = f"""
                PREFIX rdfs: <{RDFS}> PREFIX inst: <{BASE_URI}>
                SELECT DISTINCT ?subjectLabel WHERE {{
                    ?object rdfs:label "{object_name}" .
                    ?subject {predicate} ?object .
                    ?subject rdfs:label ?subjectLabel .
                }}
            """
            sparql.setQuery(query_incoming)
            inverse_results = sparql.query().convert()["results"]["bindings"]
            if inverse_results:
                subjects = [f"'{item['subjectLabel']['value']}'" for item in inverse_results]
                return f"Os seguintes objetos '{inverse_relation_phrase}' o objeto '{object_name}': {', '.join(subjects)}."
    except Exception as e:
        current_app.logger.error(f"Erro na consulta SPARQL: {e}")
        return "Ocorreu um erro ao consultar a base de dados."
    return f"Desculpe, não encontrei a propriedade '{property_label}' para o objeto '{object_name}'."


def process_user_question(user_text):
    _load_nlp_model()
    if not nlp: return {"answer": "O modelo de NLU não está carregado."}
    
    complex_answer = process_complex_query(user_text)
    if complex_answer:
        return {"answer": complex_answer}

    intent = max(nlp(user_text).cats, key=nlp(user_text).cats.get)
    if intent == "saudacao": return {"answer": "Olá! Sou seu assistente BIM."}
    if intent == "despedida": return {"answer": "Até mais!"}

    if intent == "perguntar_propriedade":
        bim_object = extract_bim_object(user_text)
        bim_property = extract_bim_property(user_text)
        response_text = query_specific_property(bim_object, bim_property)
        return {"answer": response_text, "object": bim_object}

    return {"answer": "Não entendi a sua pergunta."}

def get_graph_for_node(node_uri):
    sparql = _get_sparql_wrapper()
    label_query = f'PREFIX rdfs: <{RDFS}> SELECT ?label WHERE {{ <{node_uri}> rdfs:label ?label . }} LIMIT 1'
    sparql.setQuery(label_query)
    label_results = sparql.query().convert()["results"]["bindings"]
    node_label = label_results[0]['label']['value'] if label_results else _format_property_name(node_uri)
    return _get_bidirectional_graph(node_uri, node_label)

def get_full_graph():
    sparql = _get_sparql_wrapper()
    query = f"""
        PREFIX rdfs: <{RDFS}> SELECT ?s ?p ?o ?s_label ?o_label
        WHERE {{
          ?s ?p ?o .
          OPTIONAL {{ ?s rdfs:label ?s_label . }} OPTIONAL {{ ?o rdfs:label ?o_label . }}
          FILTER(isURI(?o))
        }} LIMIT 500
    """
    sparql.setQuery(query)
    results = sparql.query().convert()["results"]["bindings"]
    nodes, edges, added_nodes = [], [], set()
    for res in results:
        s_uri, o_uri, p_uri = res['s']['value'], res['o']['value'], res['p']['value']
        if s_uri not in added_nodes:
            nodes.append({'id': s_uri, 'label': res.get('s_label', {}).get('value', _format_property_name(s_uri))}); added_nodes.add(s_uri)
        if o_uri not in added_nodes:
            nodes.append({'id': o_uri, 'label': res.get('o_label', {}).get('value', _format_property_name(o_uri))}); added_nodes.add(o_uri)
        edges.append({'from': s_uri, 'to': o_uri, 'label': _format_property_name(p_uri)})
    return {"nodes": nodes, "edges": edges}