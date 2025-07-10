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
import ifcopenshell.geom

CORS(app)
mimetypes.add_type(\'application/wasm\', \'.wasm\')

@app.route("/\")
def index():
    return render_template("index.html")

@app.route(\\'/ifc_models/<path:filename>\\')
def serve_ifc_model(filename):
    \"\"\"Serve um ficheiro da pasta de uploads.\"\"\"
    return send_from_directory(current_app.config[\'UPLOAD_FOLDER\'], filename)

def extract_ifc_geometry(ifc_file_path):
    \"\"\"\n    Extrai a geometria dos elementos IFC usando ifcopenshell.geom\n    Retorna uma lista de elementos com geometria e metadados\n    \"\"\"\n    try:
        model = ifcopenshell.open(ifc_file_path)
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        settings.set(settings.WELD_VERTICES, True)
        
        elements_data = []
        
        # Processar todos os produtos IFC que têm representação geométrica
        for element in model.by_type("IfcProduct"):
            if element.Representation:
                try:
                    # Criar a forma geométrica
                    shape = ifcopenshell.geom.create_shape(settings, element)
                    geometry = shape.geometry
                    
                    # Extrair vértices e faces
                    verts = list(geometry.verts)
                    faces = list(geometry.faces)
                    
                    # Reorganizar vértices em grupos de 3 (x, y, z)
                    vertices = []
                    for i in range(0, len(verts), 3):
                        vertices.extend([verts[i], verts[i+1], verts[i+2]])
                    
                    # Reorganizar faces em grupos de 3 (triângulos)
                    indices = []
                    for i in range(0, len(faces), 3):
                        indices.extend([faces[i], faces[i+1], faces[i+2]])
                    
                    # Obter informações do elemento
                    element_data = {
                        \'globalId\': element.GlobalId,
                        \'type\': element.is_a(),
                        \'name\': element.Name or \'\',
                        \'description\': getattr(element, \'Description\', \'\') or \'\',
                        \'vertices\': vertices,
                        \'indices\': indices,
                        \'material\': None  # Pode ser expandido para incluir informações de material
                    }
                    
                    # Tentar obter informações de material se disponível
                    try:
                        if hasattr(element, \'HasAssociations\'):
                            for association in element.HasAssociations:
                                if association.is_a(\'IfcRelAssociatesMaterial\'):
                                    material = association.RelatingMaterial
                                    if hasattr(material, \'Name\'):
                                        element_data[\'material\'] = material.Name
                                    break
                    except:
                        pass  # Ignorar erros de material
                    
                    elements_data.append(element_data)
                    
                except Exception as e:
                    current_app.logger.warning(f"Erro ao processar geometria para {element.GlobalId}: {e}")
                    continue
        
        current_app.logger.info(f"Processados {len(elements_data)} elementos com geometria")
        return elements_data
        
    except Exception as e:
        current_app.logger.error(f"Erro ao extrair geometria IFC: {e}")
        return []

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
        # Abrir o arquivo IFC para validação e extração de metadados
        ifc_file = ifcopenshell.open(ifc_file_path)
        
        # Extrair geometria usando ifcopenshell.geom
        current_app.logger.info("Iniciando extração de geometria...")
        elements_3d_data = extract_ifc_geometry(ifc_file_path)
        
        # Extrair metadados dos produtos
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

        # Executar validação
        validation_results = validation_engine.validate_model(ifc_file_path)
        conflicting_nodes = [r[\'element\'] for r in validation_results if r.get(\'type\') == \'CONFLITO\' and r.get(\'element\')]
        
        # Upload para Fuseki
        fuseki_manager.upload_to_fuseki(fuseki_manager.convert_ifc_to_rdf(ifc_file_path))
        
        return jsonify({
            "validation": validation_results,
            "conflicting_nodes": conflicting_nodes,
            "elements_3d_data": elements_3d_data,  # Nova chave com dados de geometria
            "metadata": metadata,
            "geometry_count": len(elements_3d_data)  # Informação adicional
        })

    except Exception as e:
        current_app.logger.error(f"ERRO CRÍTICO: {e}", exc_info=True)
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500
    finally:
        # Manter o arquivo IFC temporariamente para debug, mas pode ser removido em produção
        # if os.path.exists(ifc_file_path):
        #     os.remove(ifc_file_path)
        pass

@app.route("/process_ifc_geometry", methods=["POST"])
def process_ifc_geometry():
    """
    Rota dedicada apenas para processar geometria IFC
    Útil para testes ou processamento separado
    """
    if "ifc_file" not in request.files:
        return jsonify({"error": "Nenhum ficheiro enviado."}), 400
    
    file = request.files["ifc_file"]
    if file.filename == "" or not file.filename.lower().endswith(".ifc"):
        return jsonify({"error": "Ficheiro inválido. Apenas .ifc é suportado."}), 400

    ifc_filename = str(uuid.uuid4()) + ".ifc"
    ifc_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], ifc_filename)
    file.save(ifc_file_path)

    try:
        elements_3d_data = extract_ifc_geometry(ifc_file_path)
        
        return jsonify({
            "elements_3d_data": elements_3d_data,
            "geometry_count": len(elements_3d_data),
            "status": "success"
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao processar geometria: {e}", exc_info=True)
        return jsonify({"error": "Erro ao processar geometria IFC."}), 500
    finally:
        if os.path.exists(ifc_file_path):
            os.remove(ifc_file_path)

@app.route("/ask", methods=["POST"])
def ask_chatbot():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Pergunta não fornecida."}), 400
    return jsonify(chatbot_logic.process_user_question(data["question"]))

@app.route(\\'/graph-data\\')
def get_graph_data():
    object_name = request.args.get(\'object\')
    if not object_name:
        return jsonify({"nodes": [], "edges": []})
    sparql = chatbot_logic._get_sparql_wrapper()
    uri_query = f\'PREFIX rdfs: <{RDFS}> SELECT ?s WHERE {{ ?s rdfs:label "{object_name}" . }} LIMIT 1\'
    sparql.setQuery(uri_query)
    uri_results = sparql.query().convert()["results"]["bindings"]
    if not uri_results:
        return jsonify({"nodes": [], "edges": []})
    node_uri = uri_results[0][\'s\'][\'value\']
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

