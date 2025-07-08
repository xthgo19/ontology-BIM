import os
import uuid
from flask import render_template, request, jsonify, current_app, send_from_directory
from app import app
from .services import validation_engine, fuseki_manager, chatbot_logic
from .services.thermal_analysis import calculate_u_value
from rdflib.namespace import RDFS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/validate", methods=["POST"])
def validate_ifc_model():
    if "ifc_file" not in request.files: return jsonify({"error": "Nenhum ficheiro enviado."}), 400
    file = request.files["ifc_file"]
    if file.filename == "" or not file.filename.lower().endswith(".ifc"):
        return jsonify({"error": "Ficheiro inválido. Apenas .ifc é suportado."}), 400

    filename = str(uuid.uuid4()) + ".ifc"
    ifc_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    try:
        file.save(ifc_file_path)
        validation_results = validation_engine.validate_model(ifc_file_path)

        # Extrai os nós com conflito para destacar no grafo
        conflicting_nodes = [
            result['element']
            for result in validation_results
            if result.get('type') == 'CONFLITO' and result.get('element')
        ]
        
        # Converte para RDF e carrega no Fuseki
        rdf_graph = fuseki_manager.convert_ifc_to_rdf(ifc_file_path)
        if not rdf_graph or not fuseki_manager.upload_to_fuseki(rdf_graph):
            validation_results.append({"type": "ERRO", "message": "Falha ao carregar modelo no motor de consulta."})
            return jsonify({
                "validation": validation_results, 
                "conflicting_nodes": conflicting_nodes
            }), 500
            
        # Retorna o relatório e os nós com conflito
        return jsonify({
            "validation": validation_results,
            "conflicting_nodes": conflicting_nodes
        })
    except Exception as e:
        current_app.logger.error(f"ERRO CRÍTICO: {e}", exc_info=True)
        # Garante que o ficheiro é removido em caso de erro
        if os.path.exists(ifc_file_path): os.remove(ifc_file_path)
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500
    # O ficheiro não é removido no `finally` para permitir a visualização 3D na Tarefa 2

@app.route("/ask", methods=["POST"])
def ask_chatbot():
    data = request.get_json()
    if not data or "question" not in data: return jsonify({"error": "Pergunta não fornecida."}), 400
    return jsonify(chatbot_logic.process_user_question(data["question"]))

@app.route('/graph-data')
def get_graph_data():
    object_name = request.args.get('object')
    if not object_name: return jsonify({"nodes": [], "edges": []})
    sparql = chatbot_logic._get_sparql_wrapper()
    # Assume que o ID no grafo é a URI completa
    uri_query = f'PREFIX rdfs: <{RDFS}> SELECT ?s WHERE {{ ?s rdfs:label "{object_name}" . }} LIMIT 1'
    sparql.setQuery(uri_query)
    uri_results = sparql.query().convert()["results"]["bindings"]
    if not uri_results: return jsonify({"nodes": [], "edges": []})
    node_uri = uri_results[0]['s']['value']
    graph_data = chatbot_logic._get_bidirectional_graph(node_uri, object_name)
    return jsonify(graph_data)

@app.route("/ontology-summary")
def get_ontology_summary():
    try:
        return jsonify(fuseki_manager.get_ontology_summary())
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar resumo da ontologia: {e}", exc_info=True)
        return jsonify({"error": "Não foi possível obter os dados da ontologia."}), 500

@app.route("/api/full-graph")
def full_graph():
    try:
        graph_data = chatbot_logic.get_full_graph()
        return jsonify(graph_data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar o grafo completo: {e}", exc_info=True)
        return jsonify({"error": "Não foi possível gerar o grafo completo."}), 500

@app.route("/calculate_u_value", methods=["POST"])
def calculate_u_value_route():
    data = request.get_json()
    if not data or "layers" not in data:
        return jsonify({"error": "Dados de camadas não fornecidos."}), 400
    
    try:
        u_value = calculate_u_value(data["layers"])
        return jsonify({"u_value": u_value})
    except Exception as e:
        current_app.logger.error(f"Erro ao calcular o valor U: {e}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro ao calcular o valor U."}), 500