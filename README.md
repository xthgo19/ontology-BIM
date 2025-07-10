# 🏗️ Assistente e Validador BIM Unificado

## 📋 Visão Geral

O nosso projeto ataca a dificuldade de validar e consultar modelos de construção (BIM) de forma eficiente e intuitiva. A solução é uma aplicação web que funciona como um assistente de engenharia virtual. Utiliza a biblioteca `pyshacl` para validar o modelo `.ifc` contra um conjunto de regras, a API do Ollama para gerar sugestões de correção inteligentes, e o `spaCy` para interpretar perguntas em linguagem natural, permitindo explorar o modelo através de um chatbot e uma visualização de grafo. A aplicação é desenvolvida em Python, utilizando Flask como backend e Apache Jena Fuseki como base de conhecimento.

---

## 🗺️ Mapa do Repositório

- **`app/`**: Contém todo o código-fonte da aplicação Flask.
- **`data/`**: Contém os ficheiros de dados, como as regras de validação da ontologia.
- **`nlu_model/`**: Pasta onde o modelo de NLU treinado é guardado.
- **`uploads/`**: Pasta temporária para os ficheiros `.ifc` carregados pelos utilizadores.

---

## 🧩 Módulos do Projeto

- **Motor de Validação**: `app/services/validation_engine.py`
- **Gestor da Base de Conhecimento**: `app/services/fuseki_manager.py`
- **Lógica do Chatbot**: `app/services/chatbot_logic.py`
- **Análise Térmica**: `app/services/thermal_analysis.py` - Módulo para cálculo da transmitância térmica (Valor U) de paredes, considerando múltiplas camadas e suas propriedades.

---

## 🚀 Como Rodar

### 1. Clone o repositório:

```bash
git clone <url-do-seu-repositorio-aqui>
```

### 2. Crie e ative um ambiente virtual:

```bash
# Cria um ambiente virtual chamado 'venv'
python -m venv venv

# Ativa o ambiente virtual (no Windows)
.\venv\Scripts\activate
```

### 3. Instale as dependências:

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
```

### 4. Treine o modelo de NLU:

```bash
python setup_nlu.py
```

### 5. Inicie os serviços externos (Fuseki e Ollama):

Certifique-se de que o Docker Desktop está a correr.

```bash
docker-compose up -d
```

#### Configuração inicial dos serviços (apenas na primeira vez):

- **Fuseki**: Aceda a [http://localhost:3030](http://localhost:3030), faça login com `nome:admin` e `senha:admin123` e crie um dataset "Persistent" chamado `BIM_Knowledge_Base`.
- **Ollama**: Execute no terminal:

```bash
docker exec -it ollama-server ollama pull gemma:2b
```

### 6. Execute o projeto:

Com o ambiente virtual ativado, inicie o servidor Flask:

```bash
python run.py
```

Aceda à aplicação no seu navegador em [http://127.0.0.1:5001](http://127.0.0.1:5001).

---

## 🔗 Links Úteis

- [IfcConvert](https://github.com/IfcOpenShell/IfcOpenShell/releases/tag/ifcconvert-0.8.2)

---

## 📈 Resumo e Próximos Passos Recomendados

O projeto está num excelente ponto. As funcionalidades essenciais estão a funcionar e a base está sólida. Os próximos passos deveriam focar-se em refinar a experiência do utilizador e em adicionar mais valor analítico.

### Melhorar a Visualização do Grafo:

- Permitir que o utilizador expanda os nós do grafo (clicar num nó para ver as suas próprias relações).
- Adicionar mais cores e ícones para diferentes tipos de elementos (paredes, portas, etc.).

### Expandir o Conhecimento do Chatbot:

- Treinar o modelo de NLU com mais exemplos de perguntas para o tornar mais robusto.
- Ensinar o chatbot a responder a perguntas mais complexas que envolvam mais do que uma relação (ex: "Quais os materiais das paredes do primeiro andar?").

### Aprofundar a Validação:

- Criar um ficheiro de regras SHACL mais extenso e detalhado, com validações mais complexas e específicas do domínio da construção.

#### Exemplos de Melhorias:

- **Validação Quantitativa**: Verificar se valores numéricos estão dentro de um intervalo esperado (ex: "a espessura de uma parede de exterior deve ser entre 20cm e 40cm").
- **Regras de Conformidade com Normas**: Adicionar regras que verifiquem a conformidade com normas específicas da construção (ex: normas de acessibilidade, segurança contra incêndio, etc.).
- **Consistência de Materiais**: Garantir que elementos do mesmo tipo (ex: todas as `IfcDoor` do tipo "Porta Corta-Fogo") usem os materiais corretos.

---

## 🛠️ Funcionalidades Adicionais

### Análise Preditiva de Desempenho e Otimização de Projeto

Este projeto agora inclui um módulo inicial para Análise Preditiva de Desempenho, começando com o cálculo da transmitância térmica (Valor U) de paredes. Esta funcionalidade permite:

- **Cálculo de Valor U**: Utiliza as propriedades de espessura e condutividade de múltiplas camadas para determinar a eficiência térmica de uma parede.
- **Integração Futura**: Abre caminho para simulações mais complexas de desempenho energético, iluminação natural e acústica, transformando o ontology-BIM numa ferramenta proativa para otimização de design.

#### Exemplo de Requisição:

```json
{
  "layers": [
    {"thickness": 0.15, "conductivity": 0.77},  
    {"thickness": 0.05, "conductivity": 0.035}, 
    {"thickness": 0.015, "conductivity": 0.22}  
  ]
}
```

#### Exemplo de Resposta:

```json
{
  "u_value": 1.23
}
```



