# 🏗️ Assistente e Validador BIM Unificado

## 📋 Visão Geral

O nosso projeto ataca a dificuldade de validar e consultar modelos de construção (BIM) de forma eficiente e intuitiva. A solução é uma aplicação web que funciona como um assistente de engenharia virtual. Utiliza a biblioteca `pyshacl` para validar o modelo `.ifc` contra um conjunto de regras, a API do Ollama para gerar sugestões de correção inteligentes, e o `spaCy` para interpretar perguntas em linguagem natural, permitindo explorar o modelo através de um chatbot e uma visualização de grafo. A aplicação é desenvolvida em Python, utilizando Flask como backend e Apache Jena Fuseki como base de conhecimento.

## 🗺️ Mapa do Repositório

*   **`app/`**: Contém todo o código-fonte da aplicação Flask.
*   **`data/`**: Contém os ficheiros de dados, como as regras de validação da ontologia.
*   **`nlu_model/`**: Pasta onde o modelo de NLU treinado é guardado.
*   **`uploads/`**: Pasta temporária para os ficheiros `.ifc` carregados pelos utilizadores.

## 🧩 Módulos do Projeto

Para detalhes específicos sobre cada parte do projeto, consulte o código-fonte nos seguintes módulos:

*   **Motor de Validação**: `app/services/validation_engine.py`
*   **Gestor da Base de Conhecimento**: `app/services/fuseki_manager.py`
*   **Lógica do Chatbot**: `app/services/chatbot_logic.py`
*   **Análise Térmica**: `app/services/thermal_analysis.py` - Módulo para cálculo da transmitância térmica (Valor U) de paredes, considerando múltiplas camadas e suas propriedades.

## ✨ Novas Funcionalidades e Melhorias Recentes

### 1. **Visualizador 3D IFC Aprimorado**

Foi implementado um visualizador 3D robusto e eficiente para modelos IFC, utilizando Three.js puro no frontend e processamento de geometria no backend com `ifcopenshell`. Isso resolve problemas de dependência e otimiza o carregamento.

*   **Processamento de Geometria no Backend**: A extração e preparação dos dados 3D do IFC (`vertices`, `indices`, `normals`, `colors`) são realizadas no servidor, garantindo maior estabilidade e compatibilidade.
*   **Renderização Three.js Pura**: O frontend utiliza diretamente a biblioteca Three.js via CDN, eliminando a necessidade de `web-ifc-three` e `IFCLoader.js`, o que simplifica o projeto e evita conflitos de dependência.
*   **Destaque de Elementos com Falha**: Elementos do modelo 3D que falham na validação são automaticamente destacados em vermelho, facilitando a identificação visual de problemas.
*   **Interatividade Aprimorada**: Ao clicar em um objeto no visualizador 3D, suas informações são exibidas no chatbot, permitindo uma exploração mais intuitiva do modelo.
*   **Controles de Visualização**: Adicionados botões para alternar a transparência de elementos (paredes, lajes, telhados) para visualização interna, e controles de câmera para vistas superior, frontal e reset.
*   **Orientação Correta**: O modelo 3D é automaticamente ajustado para uma orientação correta ao ser carregado.

### 2. **Otimização de Performance**

Melhorias no processo de carregamento e renderização do modelo 3D para garantir uma experiência mais fluida, mesmo com modelos maiores.

## 🚀 Como Rodar

### 1. Clone o repositório:

```shell
git clone <url-do-seu-repositorio-aqui>
