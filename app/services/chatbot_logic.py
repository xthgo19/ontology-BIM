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
    """Formata uma URI de propriedade para um nome legível."""
    if '#' in uri:
        name = uri.split('#')[-1]
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    return uri.split('/')[-1]

def process_user_question(user_text):
    _load_nlp_model()
    if not nlp:
        return {"answer": "O modelo de NLU não está carregado.", "graph_data": None}
    
    doc = nlp(user_text)
    intent = max(doc.cats, key=doc.cats.get)

    if intent == "saudacao": return {"answer": "Olá! Sou seu assistente BIM.", "graph_data": None}
    if intent == "despedida": return {"answer": "Até mais!", "graph_data": None}
    
    if intent == "perguntar_propriedade":
        obj_match = re.search(r"['\"]([^'\"]+)['\"]", user_text)
        if not obj_match: return {"answer": "Não consegui identificar o objeto na pergunta.", "graph_data": None}
        obj_name = obj_match.group(1)

        BASE_URI = current_app.config['BASE_URI']
        inst = Namespace(BASE_URI)

        sparql = SPARQLWrapper(current_app.config['FUSEKI_QUERY_ENDPOINT'])
        sparql.setCredentials(current_app.config['FUSEKI_USER'], current_app.config['FUSEKI_PASSWORD'])
        sparql.setReturnFormat(JSON)
        
        query = f"""
            PREFIX rdfs: <{RDFS}> 
            PREFIX inst: <{inst}> 
            SELECT ?s ?p ?o ?o_label
            WHERE {{ 
                ?s rdfs:label "{obj_name}" . 
                ?s ?p ?o . 
                OPTIONAL {{?o rdfs:label ?o_label}} 
            }}
        """
        sparql.setQuery(query)
        results = sparql.query().convert()["results"]["bindings"]
        
        if not results: return {"answer": f"Não encontrei informações para '{obj_name}'.", "graph_data": None}
        
        answers = []
        subject_uri = results[0]['s']['value']
        
        nodes = [{'id': subject_uri, 'label': obj_name, 'color': '#f56565', 'size': 25}]
        edges = []
        added_nodes = {subject_uri}

        for res in results:
            prop_uri = res['p']['value']
            prop_name_raw = prop_uri.split('#')[-1]
            
            if res['o']['type'] == 'uri':
                target_uri = res['o']['value']
                if target_uri not in added_nodes:
                    target_label = res.get('o_label', {}).get('value', _format_property_name(target_uri))
                    nodes.append({'id': target_uri, 'label': target_label})
                    added_nodes.add(target_uri)

            if prop_uri == str(RDF.type):
                val = _format_property_name(res['o']['value'])
                answers.append(f"- Classe: {val}")
            elif prop_name_raw == 'isOfType':
                 val = res.get('o_label', {}).get('value', _format_property_name(res['o']['value']))
                 answers.append(f"- Tipo: {val}")
            elif prop_uri != str(RDFS.label):
                prop_name_formatted = _format_property_name(prop_uri)
                val = res.get('o_label', {}).get('value', _format_property_name(res['o']['value']))
                answers.append(f"- {prop_name_formatted}: {val}")

        for res in results:
            if res['o']['type'] == 'uri':
                prop_uri = res['p']['value']
                target_uri = res['o']['value']
                if prop_uri != str(RDFS.label):
                    label = "Classe" if prop_uri == str(RDF.type) else _format_property_name(prop_uri)
                    edges.append({'from': subject_uri, 'to': target_uri, 'label': label})

        graph_data = {"nodes": nodes, "edges": edges}
        unique_answers = sorted(list(set(answers)))

        return {
            "answer": f"Informações para '{obj_name}':\n" + "\n".join(unique_answers),
            "graph_data": graph_data
        }

    return {"answer": "Desculpe, não entendi a sua pergunta.", "graph_data": None}