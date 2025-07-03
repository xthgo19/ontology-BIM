import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-segura'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    NLU_MODEL_PATH = os.path.join(BASE_DIR, 'nlu_model')
    SHACL_RULES_PATH = os.path.join(BASE_DIR, 'data', 'ifc-ontology.ttl')
    
    # --- INÍCIO DA CORREÇÃO ---
    # Adicionadas credenciais para o Fuseki
    FUSEKI_USER = os.environ.get('FUSEKI_USER') or 'admin'
    FUSEKI_PASSWORD = os.environ.get('FUSEKI_PASSWORD') or 'admin123'
    # --- FIM DA CORREÇÃO ---

    FUSEKI_QUERY_ENDPOINT = os.environ.get("FUSEKI_QUERY_ENDPOINT", "http://localhost:3030/BIM_Knowledge_Base/query")
    FUSEKI_GSP_ENDPOINT = os.environ.get("FUSEKI_GSP_ENDPOINT", "http://localhost:3030/BIM_Knowledge_Base/data")
    OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/chat")
    BASE_URI = "http://exemplo.org/bim#"