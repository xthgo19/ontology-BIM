from app import app

if __name__ == '__main__':
    # Executa a aplicação. debug=True é útil para desenvolvimento.
    # O host '0.0.0.0' torna a aplicação acessível na sua rede local.
    app.run(host='0.0.0.0', port=5001, debug=True)