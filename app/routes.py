import os
import uuid
import mimetypes
import subprocess
import json
from flask import render_template, request, jsonify, current_app, send_from_directory
from flask_cors import CORS
from app import app
from .services import validation_engine, fuseki_manager, chatbot_logic
from .services.thermal_analysis import calculate_u_value
from rdflib.namespace import RDFS
import ifcopenshell

CORS(app)
mimetypes.add_type('application/wasm', '.wasm')

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/ifc_models/<path:filename>')
def serve_ifc_model(filename):
    """Serve um ficheiro da pasta de uploads."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@app.route("/validate", methods=["POST"])
def validate_ifc_model():
    if "ifc_file" not in request.files:
        return jsonify({"error": "Nenhum ficheiro enviado."}), 400
    file = request.files["ifc_file"]
    if file.filename == "" or not file.filename.lower().endswith(".ifc"):
        return jsonify({"error": "Ficheiro inválido. Apenas .ifc é suportado."}), 400

    ifc_filename = str(uuid.uuid4()) + ".ifc"
    ifc_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], ifc_filename)
    file.save(ifc_file_path)

    try:
        glb_filename = ifc_filename.replace(".ifc", ".glb")
        glb_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], glb_filename)
        
        # !!! ATENÇÃO: VERIFIQUE SE ESTE CAMINHO ESTÁ CORRETO PARA O SEU COMPUTADOR !!!
        ifc_convert_path = "C:\\Users\\Samuel\\Downloads\\ifcconvert-0.8.2-win64\\IfcConvert.exe"
        
        command = [ifc_convert_path, ifc_file_path, glb_file_path]
        subprocess.run(command, check=True, capture_output=True, text=True)
        
        ifc_file = ifcopenshell.open(ifc_file_path)
        products = ifc_file.by_type("IfcProduct")
        metadata = {}
        for product in products:
            if product.GlobalId:
                guid = product.GlobalId
                metadata[guid] = {
                    "type": product.is_a(),
                    "name": product.Name,
                    "GlobalId": guid
                }

        validation_results = validation_engine.validate_model(ifc_file_path)
        conflicting_nodes = [r['element'] for r in validation_results if r.get('type') == 'CONFLITO' and r.get('element')]
        
        fuseki_manager.upload_to_fuseki(fuseki_manager.convert_ifc_to_rdf(ifc_file_path))

        glb_url_path = f"/ifc_models/{glb_filename}"
        
        return jsonify({
            "validation": validation_results,
            "conflicting_nodes": conflicting_nodes,
            "model_path": glb_url_path,
            "metadata": metadata  # <-- Envia os metadados para o frontend
        })

    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"O comando IfcConvert falhou: {e.stderr}")
        return jsonify({"error": f"Erro crítico na conversão do modelo: {e.stderr}"}), 500
    except Exception as e:
        current_app.logger.error(f"ERRO CRÍTICO: {e}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500
    finally:
        if os.path.exists(ifc_file_path):
            os.remove(ifc_file_path)

@app.route("/ask", methods=["POST"])
def ask_chatbot():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Pergunta não fornecida."}), 400
    return jsonify(chatbot_logic.process_user_question(data["question"]))

@app.route('/graph-data')
def get_graph_data():
    object_name = request.args.get('object')
    if not object_name:
        return jsonify({"nodes": [], "edges": []})
    sparql = chatbot_logic._get_sparql_wrapper()
    uri_query = f'PREFIX rdfs: <{RDFS}> SELECT ?s WHERE {{ ?s rdfs:label "{object_name}" . }} LIMIT 1'
    sparql.setQuery(uri_query)
    uri_results = sparql.query().convert()["results"]["bindings"]
    if not uri_results:
        return jsonify({"nodes": [], "edges": []})
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