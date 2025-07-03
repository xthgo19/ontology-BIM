import os
import uuid
from flask import render_template, request, jsonify, current_app
# Importa a instância 'app' que foi criada no __init__.py
from app import app
from .services import validation_engine, fuseki_manager, chatbot_logic

# A linha "app = create_app()" foi removida daqui, pois era a causa do erro.

@app.route('/')
def index():
    """ Rota principal que renderiza a interface do utilizador. """
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate_ifc_model():
    """
    Endpoint para receber um ficheiro .ifc, executar a validação
    e carregar o modelo no Fuseki.
    """
    if 'ifc_file' not in request.files:
        return jsonify({"error": "Nenhum ficheiro enviado."}), 400
    
    file = request.files['ifc_file']
    if file.filename == '' or not file.filename.lower().endswith('.ifc'):
        return jsonify({"error": "Ficheiro inválido. Apenas .ifc é suportado."}), 400

    # Gera um nome de ficheiro único para evitar conflitos
    filename = str(uuid.uuid4()) + '.ifc'
    ifc_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(ifc_file_path)
        current_app.logger.info(f"Ficheiro '{file.filename}' guardado temporariamente como '{filename}'.")

        # 1. Executa o motor de validação
        validation_results = validation_engine.validate_model(ifc_file_path)
        
        # 2. Converte e carrega o modelo no Fuseki
        rdf_graph = fuseki_manager.convert_ifc_to_rdf(ifc_file_path)
        
        if not rdf_graph or not fuseki_manager.upload_to_fuseki(rdf_graph):
            validation_results.append({
                "type": "ERRO",
                "message": "O modelo foi validado, mas falhou ao ser carregado no motor de consulta. O chatbot pode não funcionar corretamente."
            })
            return jsonify(validation_results), 500

        return jsonify(validation_results)

    except Exception as e:
        current_app.logger.error(f"ERRO CRÍTICO durante a validação/carregamento: {e}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500
    finally:
        # Garante que o ficheiro temporário é sempre removido
        if os.path.exists(ifc_file_path):
            os.remove(ifc_file_path)
            current_app.logger.info(f"Ficheiro temporário '{filename}' removido.")

@app.route('/ask', methods=['POST'])
def ask_chatbot():
    """ Endpoint que recebe uma pergunta e a encaminha para a lógica do chatbot. """
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "Pergunta não fornecida."}), 400
        
    user_text = data['question']
    response = chatbot_logic.process_user_question(user_text)
    
    return jsonify(response)

@app.route('/ontology-summary')
def get_ontology_summary():
    """ Endpoint para popular o construtor de consultas na interface. """
    try:
        summary = fuseki_manager.get_ontology_summary()
        return jsonify(summary)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar resumo da ontologia: {e}", exc_info=True)
        return jsonify({"error": "Não foi possível obter os dados da ontologia do servidor."}), 500