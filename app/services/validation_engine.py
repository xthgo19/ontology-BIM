import ifcopenshell
from rdflib import Graph, Namespace, Literal, RDF
from rdflib.namespace import SH
from pyshacl import validate
import requests
from flask import current_app
from pathlib import Path # Importa a classe Path

IFC_NS = Namespace("http://exemplo.org/ifc/")
PROP_NS = Namespace("http://exemplo.org/ifc/property#")

def _populate_rdf_graph_for_validation(ifc_file_path):
    model = ifcopenshell.open(ifc_file_path)
    products = model.by_type("IfcProduct")
    rdf_graph = Graph()
    rdf_graph.bind("ifc", IFC_NS)
    rdf_graph.bind("prop", PROP_NS)

    for element in products:
        if not element.GlobalId: continue
        uri = IFC_NS[element.GlobalId]
        rdf_graph.add((uri, RDF.type, IFC_NS[element.is_a()]))
        if element.Name:
            rdf_graph.add((uri, IFC_NS["name"], Literal(element.Name)))
        
        if hasattr(element, 'ContainedInStructure') and element.ContainedInStructure:
            for rel in element.ContainedInStructure:
                if hasattr(rel, 'RelatingStructure') and rel.RelatingStructure:
                    container = rel.RelatingStructure
                    rdf_graph.add((uri, PROP_NS["ContainedInStructure"], IFC_NS[container.GlobalId]))
            
        if hasattr(element, 'FillsVoids'):
            for rel in element.FillsVoids:
                if hasattr(rel, 'RelatingOpeningElement'):
                    opening = rel.RelatingOpeningElement
                    rdf_graph.add((uri, PROP_NS["FillsVoids"], IFC_NS[opening.GlobalId]))
    return rdf_graph

def _get_llm_suggestion(conflict_description):
    prompt = f"Você é um especialista em BIM. Forneça uma sugestão de correção clara e concisa para o seguinte conflito: {conflict_description}"
    try:
        payload = {"model": "gemma3:4b", "messages": [{"role": "user", "content": prompt}], "stream": False}
        response = requests.post(current_app.config['OLLAMA_API_URL'], json=payload, timeout=60)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("message", {}).get("content", "Nenhuma sugestão disponível.").strip()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao comunicar com o LLM: {e}")
        return "Não foi possível obter uma sugestão da IA."

def validate_model(ifc_file_path):
    current_app.logger.info("A iniciar validação...")
    data_graph = _populate_rdf_graph_for_validation(ifc_file_path)
    
    shacl_rules_path_str = current_app.config['SHACL_RULES_PATH']
    shacl_rules_uri = Path(shacl_rules_path_str).as_uri()
    current_app.logger.info(f"A carregar regras SHACL de: {shacl_rules_uri}")
    
    shacl_graph = Graph().parse(shacl_rules_uri, format="turtle")

    conforms, results_graph, _ = validate(
        data_graph, 
        shacl_graph=shacl_graph, 
        inference='rdfs', 
        ont_graph=None,
        advanced=True,
        debug=False,
        meta_shacl=False,
        abort_on_first=False,
        )
    
    print(f"Conformidade: {_}")

    validation_report = []
    if conforms:
        validation_report.append({"type": "SUCESSO", "message": "O modelo está em conformidade."})
        return validation_report

    for s in results_graph.subjects(SH.resultSeverity, SH.Violation):
        message = str(results_graph.value(s, SH.resultMessage) or "Mensagem não definida.")
        focus_node = str(results_graph.value(s, SH.focusNode) or "N/A").replace(str(IFC_NS), "ifc:")
        suggestion = _get_llm_suggestion(message)
        validation_report.append({"type": "CONFLITO", "element": focus_node, "message": message, "suggestion_llm": suggestion})
    return validation_report