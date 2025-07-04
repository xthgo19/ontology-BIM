import os
import uuid
from flask import render_template, request, jsonify, current_app
from app import app
from .services import validation_engine, fuseki_manager, chatbot_logic

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate_ifc_model():
    if 'ifc_file' not in request.files: return jsonify({"error": "Nenhum ficheiro enviado."}), 400
    file = request.files['ifc_file']
    if file.filename == '' or not file.filename.lower().endswith('.ifc'):
        return jsonify({"error": "Ficheiro inválido. Apenas .ifc é suportado."}), 400

    filename = str(uuid.uuid4()) + '.ifc'
    ifc_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    try:
        file.save(ifc_file_path)
        validation_results = validation_engine.validate_model(ifc_file_path)
        rdf_graph = fuseki_manager.convert_ifc_to_rdf(ifc_file_path)
        if not rdf_graph or not fuseki_manager.upload_to_fuseki(rdf_graph):
            validation_results.append({"type": "ERRO", "message": "Falha ao carregar modelo no motor de consulta."})
            return jsonify(validation_results), 500
        return jsonify(validation_results)
    except Exception as e:
        current_app.logger.error(f"ERRO CRÍTICO: {e}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500
    finally:
        if os.path.exists(ifc_file_path): os.remove(ifc_file_path)

@app.route('/ask', methods=['POST'])
def ask_chatbot():
    data = request.get_json()
    if not data or 'question' not in data: return jsonify({"error": "Pergunta não fornecida."}), 400
    return jsonify(chatbot_logic.process_user_question(data['question']))

@app.route('/ontology-summary')
def get_ontology_summary():
    try:
        return jsonify(fuseki_manager.get_ontology_summary())
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar resumo da ontologia: {e}", exc_info=True)
        return jsonify({"error": "Não foi possível obter os dados da ontologia."}), 500

@app.route('/api/expand-graph', methods=['POST'])
def expand_graph():
    data = request.get_json()
    if not data or 'node_uri' not in data: return jsonify({"error": "URI do nó não fornecido."}), 400
    try:
        return jsonify(chatbot_logic.get_graph_for_node(data['node_uri']))
    except Exception as e:
        current_app.logger.error(f"Erro ao focar no nó do grafo: {e}", exc_info=True)
        return jsonify({"error": "Não foi possível obter os dados de foco do nó."}), 500

# --- INÍCIO DO NOVO CÓDIGO ---
@app.route('/api/full-graph')
def full_graph():
    """Endpoint para buscar o grafo completo."""
    try:
        graph_data = chatbot_logic.get_full_graph()
        return jsonify(graph_data)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar o grafo completo: {e}", exc_info=True)
        return jsonify({"error": "Não foi possível gerar o grafo completo."}), 500
# --- FIM DO NOVO CÓDIGO ---