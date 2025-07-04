import os
import spacy
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import current_app
from rdflib import Namespace
from rdflib.namespace import RDFS, RDF

nlp = None

def _load_nlp_model():
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load(current_app.config['NLU_MODEL_PATH'])
            current_app.logger.info("Modelo de NLU carregado.")
        except IOError:
            current_app.logger.error("Modelo de NLU não encontrado.")
            nlp = False

def _format_property_name(uri):
    if '#' in uri:
        name = uri.split('#')[-1]
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    return uri.split('/')[-1]

def _get_bidirectional_graph(node_uri, central_node_label):
    sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
    sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    sparql.setReturnFormat(JSON)

    query = f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?s ?p ?o ?s_label ?o_label
        WHERE {{
          {{ BIND(<{node_uri}> AS ?s) ?s ?p ?o . }}
          UNION
          {{ BIND(<{node_uri}> AS ?o) ?s ?p ?o . }}
          OPTIONAL {{ ?s rdfs:label ?s_label . }}
          OPTIONAL {{ ?o rdfs:label ?o_label . }}
          FILTER(?s != ?o)
        }}
    """
    sparql.setQuery(query)
    results = sparql.query().convert()["results"]["bindings"]

    nodes = [{'id': node_uri, 'label': central_node_label, 'color': '#68D391', 'size': 25}]
    edges = []
    added_nodes = {node_uri}

    if not results:
        return {"nodes": nodes, "edges": edges}

    for res in results:
        if res['p']['value'] == str(RDFS.label):
            continue

        s_uri = res['s']['value']
        o_uri = res['o']['value']

        if s_uri not in added_nodes:
            s_label = res.get('s_label', {}).get('value', _format_property_name(s_uri))
            nodes.append({'id': s_uri, 'label': s_label})
            added_nodes.add(s_uri)

        if res['o']['type'] == 'uri' and o_uri not in added_nodes:
            o_label = res.get('o_label', {}).get('value', _format_property_name(o_uri))
            nodes.append({'id': o_uri, 'label': o_label})
            added_nodes.add(o_uri)

        if res['o']['type'] == 'uri':
            edge_label = _format_property_name(res['p']['value'])
            edges.append({'from': s_uri, 'to': o_uri, 'label': edge_label})
            
    return {"nodes": nodes, "edges": edges}

def process_user_question(user_text):
    _load_nlp_model()
    if not nlp: return {"answer": "O modelo de NLU não está carregado.", "graph_data": None}
    
    doc = nlp(user_text)
    intent = max(doc.cats, key=doc.cats.get)

    if intent == "saudacao": return {"answer": "Olá! Sou seu assistente BIM.", "graph_data": None}
    if intent == "despedida": return {"answer": "Até mais!", "graph_data": None}
    
    if intent == "perguntar_propriedade":
        # --- INÍCIO DA MODIFICAÇÃO ---
        obj_name = None
        # Procura primeiro pelo padrão específico do construtor de consultas
        specific_match = re.search(r"objeto '([^']*)'", user_text)
        if specific_match:
            obj_name = specific_match.group(1)
        else:
            # Se não encontrar, procura pelo primeiro texto genérico entre aspas
            generic_match = re.search(r"['\"]([^'\"]+)['\"]", user_text)
            if generic_match:
                obj_name = generic_match.group(1)

        if not obj_name:
            return {"answer": "Não consegui identificar um objeto na sua pergunta.", "graph_data": None}
        # --- FIM DA MODIFICAÇÃO ---

        sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
        sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
        sparql.setReturnFormat(JSON)
        uri_query = f'PREFIX rdfs: <{RDFS}> SELECT ?s WHERE {{ ?s rdfs:label "{obj_name}" . }} LIMIT 1'
        sparql.setQuery(uri_query)
        uri_results = sparql.query().convert()["results"]["bindings"]
        
        if not uri_results:
            return {"answer": f"Não encontrei '{obj_name}'.", "graph_data": None}
            
        subject_uri = uri_results[0]['s']['value']
        
        graph_data = _get_bidirectional_graph(subject_uri, obj_name)

        return {
            "answer": f"Exibindo informações para '{obj_name}'.",
            "graph_data": graph_data
        }

    return {"answer": "Não entendi a sua pergunta.", "graph_data": None}

def get_graph_for_node(node_uri):
    sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
    sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    sparql.setReturnFormat(JSON)
    label_query = f'PREFIX rdfs: <{RDFS}> SELECT ?label WHERE {{ <{node_uri}> rdfs:label ?label . }} LIMIT 1'
    sparql.setQuery(label_query)
    label_results = sparql.query().convert()["results"]["bindings"]
    node_label = label_results[0]['label']['value'] if label_results else _format_property_name(node_uri)
    return _get_bidirectional_graph(node_uri, node_label)

def get_full_graph():
    sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
    sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
    sparql.setReturnFormat(JSON)
    
    query = f"""
        PREFIX rdfs: <{RDFS}>
        SELECT ?s ?p ?o ?s_label ?o_label
        WHERE {{
          ?s ?p ?o .
          OPTIONAL {{ ?s rdfs:label ?s_label . }}
          OPTIONAL {{ ?o rdfs:label ?o_label . }}
          FILTER(isURI(?o))
        }}
        LIMIT 500
    """
    sparql.setQuery(query)
    results = sparql.query().convert()["results"]["bindings"]

    nodes = []
    edges = []
    added_nodes = set()

    for res in results:
        s_uri, o_uri, p_uri = res['s']['value'], res['o']['value'], res['p']['value']

        if s_uri not in added_nodes:
            s_label = res.get('s_label', {}).get('value', _format_property_name(s_uri))
            nodes.append({'id': s_uri, 'label': s_label})
            added_nodes.add(s_uri)

        if o_uri not in added_nodes:
            o_label = res.get('o_label', {}).get('value', _format_property_name(o_uri))
            nodes.append({'id': o_uri, 'label': o_label})
            added_nodes.add(o_uri)

        edges.append({'from': s_uri, 'to': o_uri, 'label': _format_property_name(p_uri)})

    return {"nodes": nodes, "edges": edges}