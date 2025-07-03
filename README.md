# 🏗️ Assistente e Validador BIM Unificado
## 📋 Visão Geral
O nosso projeto ataca a dificuldade de validar e consultar modelos de construção (BIM) de forma eficiente e intuitiva. A solução é uma aplicação web que funciona como um assistente de engenharia virtual. Utiliza a biblioteca pyshacl para validar o modelo .ifc contra um conjunto de regras, a API do Ollama para gerar sugestões de correção inteligentes, e o spaCy para interpretar perguntas em linguagem natural, permitindo explorar o modelo através de um chatbot e uma visualização de grafo. A aplicação é desenvolvida em Python, utilizando Flask como backend e Apache Jena Fuseki como base de conhecimento.

## 🗺️ Mapa do Repositório
app/: Contém todo o código-fonte da aplicação Flask.

data/: Contém os ficheiros de dados, como as regras de validação da ontologia.

nlu_model/: Pasta onde o modelo de NLU treinado é guardado.

uploads/: Pasta temporária para os ficheiros .ifc carregados pelos utilizadores.

## 🧩 Módulos do Projeto
Para detalhes específicos sobre cada parte do projeto, consulte o código-fonte nos seguintes módulos:

Motor de Validação: app/services/validation_engine.py

Gestor da Base de Conhecimento: app/services/fuseki_manager.py

Lógica do Chatbot: app/services/chatbot_logic.py

## 🚀 Como Rodar
Clone o repositório:

git clone <url-do-seu-repositorio-aqui>

Crie e ative um ambiente virtual:

## Cria um ambiente virtual chamado 'venv'
python -m venv venv

## Ativa o ambiente virtual (no Windows)
.\venv\Scripts\activate

Instale as dependências:

pip install -r requirements.txt
python -m spacy download pt_core_news_sm

Treine o modelo de NLU:

python setup_nlu.py

Inicie os serviços externos (Fuseki e Ollama):

Certifique-se de que o Docker Desktop está a correr.

Execute o Docker Compose para iniciar os contentores em segundo plano:

docker-compose up -d

Configure os serviços (apenas na primeira vez):

Fuseki: Aceda a http://localhost:3030, faça login com nome:admin/senha:admin123 e crie um dataset "Persistent" chamado BIM_Knowledge_Base.

Ollama: Execute no terminal docker exec -it ollama-server ollama pull gemma:2b.

Execute o projeto:

Com o ambiente virtual ativado, inicie o servidor Flask:

python run.py

Aceda à aplicação no seu navegador em http://127.0.0.1:5001.

________________________________________________________________________________________________

Resumo e Próximos Passos Recomendados
O projeto está num excelente ponto. As funcionalidades essenciais estão a funcionar e a base está sólida. Os próximos passos deveriam focar-se em refinar a experiência do utilizador e em adicionar mais valor analítico.

Melhorar a Visualização do Grafo:

Permitir que o utilizador expanda os nós do grafo (clicar num nó para ver as suas próprias relações).

Adicionar mais cores e ícones para diferentes tipos de elementos (paredes, portas, etc.).

Expandir o Conhecimento do Chatbot:

Treinar o modelo de NLU com mais exemplos de perguntas para o tornar mais robusto.

Ensinar o chatbot a responder a perguntas mais complexas que envolvam mais do que uma relação (ex: "Quais os materiais das paredes do primeiro andar?").

Aprofundar a Validação:

Criar um ficheiro de regras SHACL mais extenso e detalhado, com validações mais complexas e específicas do domínio da construção.

1. Melhorias no Módulo de Validação
O motor de validação é poderoso, mas pode ser ainda mais preciso e informativo.

Regras SHACL Mais Abrangentes: As regras atuais são um ótimo começo. O próximo passo seria expandir o ficheiro data/ifc-ontology.ttl com validações mais específicas e complexas, como:

Validação Quantitativa: Verificar se valores numéricos estão dentro de um intervalo esperado (ex: "a espessura de uma parede de exterior deve ser entre 20cm e 40cm").

Regras de Conformidade com Normas: Adicionar regras que verifiquem a conformidade com normas específicas da construção (ex: normas de acessibilidade, segurança contra incêndio, etc.).

Consistência de Materiais: Garantir que elementos do mesmo tipo (ex: todas as IfcDoor do tipo "Porta Corta-Fogo") usem os materiais corretos.

Níveis de Severidade no Relatório: Em vez de apenas "Conflito", o relatório de validação poderia classificar os problemas em diferentes níveis, como:

🔴 Crítico: Erros que comprometem a integridade do modelo (ex: uma porta sem parede).

🟡 Aviso: Inconsistências que devem ser revistas, mas não bloqueiam o fluxo (ex: um espaço sem nome).

🔵 Informativo: Sugestões de boas práticas.
Isto ajudaria o utilizador a priorizar as correções.

2. Evolução do Chatbot e da Consulta Semântica
O chatbot funciona bem para perguntas diretas. O próximo nível é torná-lo um verdadeiro assistente de análise.

Perguntas Complexas (Multi-salto): Atualmente, o chatbot responde a perguntas sobre um único elemento. A evolução seria permitir perguntas que cruzam informações, como:

"Liste todas as portas nas paredes do primeiro andar."

"Quais os materiais de todos os elementos contidos no '00 groundfloor'?"

Isto exigiria a construção de consultas SPARQL mais complexas no backend.

Memória de Contexto: Dar ao chatbot uma "memória" de curto prazo. Se o utilizador pergunta "Qual o material da parede-01?", a pergunta seguinte "E a sua espessura?" deveria ser entendida no contexto da "parede-01", sem que o utilizador precise de a repetir.

Integração Bidirecional com o Grafo: Tornar a interação mais dinâmica:

Grafo -> Chat: Clicar num nó do grafo (ex: no nó stone_sand-lime) poderia automaticamente fazer uma pergunta ao chatbot, como "Quais os elementos que usam o material 'stone_sand-lime'?".

3. Melhorias na Interface e Experiência do Utilizador (UI/UX)
A maior evolução para o utilizador seria ver o modelo.

Visualização 3D do Modelo: Esta seria a melhoria de maior impacto. Integrar um visualizador 3D de ficheiros .ifc (usando bibliotecas JavaScript como three.js com um loader de IFC, ou web-ifc-viewer). Isto permitiria:

Destacar Elementos: Quando o utilizador consulta um elemento no chatbot ou quando um conflito é reportado, o elemento correspondente seria destacado a vermelho no modelo 3D.

Navegação Visual: Clicar num elemento no modelo 3D poderia abrir as suas informações no painel de consulta.

Relatórios Exportáveis: Adicionar um botão para exportar o Relatório de Validação para formatos como PDF ou CSV, facilitando a partilha com outras equipas.

4. Arquitetura e Performance
À medida que o projeto cresce, a arquitetura precisa de acompanhar.

Processamento Assíncrono para Ficheiros Grandes: A validação de um ficheiro .ifc grande pode demorar vários minutos. Atualmente, o utilizador tem de esperar com o navegador aberto. A solução ideal seria:

O utilizador carrega o ficheiro.

A tarefa de validação é enviada para uma fila de processamento em segundo plano (usando ferramentas como Celery com Redis ou RabbitMQ).

O utilizador pode fechar o navegador e é notificado (ex: por email ou numa dashboard) quando o relatório estiver pronto.

Gestão de Múltiplos Projetos: A aplicação atual lida com um ficheiro de cada vez. Uma evolução natural seria adicionar um sistema de utilizadores e uma dashboard onde cada utilizador pudesse gerir e consultar os seus diferentes projetos carregados.