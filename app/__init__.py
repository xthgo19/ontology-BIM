import os
import logging
from flask import Flask
from config import Config

# Cria a instância da aplicação Flask diretamente
app = Flask(__name__)

# Carrega as configurações do ficheiro config.py
app.config.from_object(Config)

# Configura o logging para vermos informações úteis no terminal
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

# Garante que a pasta de uploads exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Importa as rotas no final para evitar importações circulares.
# O Python irá ler este ficheiro, criar a 'app', e só depois carregar as rotas
# que dependem da 'app'.
from app import routes

app.logger.info('Aplicação BIM Unificada iniciada com sucesso.')