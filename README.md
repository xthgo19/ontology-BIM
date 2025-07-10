# 🏗️ Assistente e Validador BIM Unificado

## 📋 Visão Geral do Projeto

O projeto **Assistente e Validador BIM Unificado** aborda a complexidade da validação e consulta de modelos de construção (BIM) de forma eficiente e intuitiva. A solução é uma aplicação web que atua como um assistente de engenharia virtual, integrando diversas tecnologias para oferecer uma experiência abrangente e interativa. O objetivo principal é simplificar a validação de modelos IFC contra um conjunto de regras predefinidas, bem como permitir a exploração e consulta desses modelos através de uma interface de chatbot e visualização de grafo, tudo isso com o suporte de inteligência artificial para sugestões de correção inteligentes.

### Problema

A validação e consulta de modelos BIM frequentemente envolvem processos manuais complexos e ferramentas fragmentadas, dificultando a identificação de inconsistências e a extração de informações relevantes. A falta de uma plataforma unificada que combine validação automatizada, consulta em linguagem natural e visualização interativa resulta em ineficiências e erros no ciclo de vida do projeto de construção.

### Solução

Nossa aplicação web oferece uma solução integrada que centraliza a validação, consulta e visualização de modelos BIM. Utilizando uma combinação de `pyshacl` para validação de modelos IFC, a API do Ollama para geração de sugestões de correção baseadas em IA, e `spaCy` para processamento de linguagem natural, o sistema permite que engenheiros e outros profissionais da construção interajam com os modelos de forma mais eficiente e intuitiva. A arquitetura robusta, baseada em Flask e Apache Jena Fuseki, garante escalabilidade e desempenho.

## ✨ Funcionalidades Principais

O **Assistente e Validador BIM Unificado** oferece um conjunto de funcionalidades poderosas para otimizar o trabalho com modelos BIM:

*   **Validação de Modelos IFC**: Utiliza a biblioteca `pyshacl` para validar modelos `.ifc` contra um conjunto de regras SHACL, garantindo a conformidade e a qualidade dos dados do modelo.
*   **Sugestões de Correção Inteligentes**: Integração com a API do Ollama para gerar sugestões de correção inteligentes para os problemas identificados durante a validação, auxiliando os usuários na retificação de erros.
*   **Chatbot Interativo com NLU**: Permite a exploração do modelo BIM através de um chatbot que interpreta perguntas em linguagem natural, utilizando `spaCy` para processamento de linguagem natural. Isso possibilita consultas complexas e intuitivas sobre os elementos do modelo.
*   **Visualização de Grafo**: Apresenta as relações entre os elementos do modelo BIM em um formato de grafo, facilitando a compreensão da estrutura e das dependências do projeto.
*   **Visualizador 3D IFC Aprimorado**: Um visualizador 3D robusto e eficiente para modelos IFC, desenvolvido com Three.js puro no frontend e processamento de geometria no backend com `ifcopenshell`. Este visualizador oferece:
    *   **Processamento de Geometria no Backend**: Extração e preparação dos dados 3D do IFC (`vertices`, `indices`, `normals`, `colors`) realizadas no servidor, garantindo maior estabilidade e compatibilidade.
    *   **Renderização Three.js Pura**: O frontend utiliza diretamente a biblioteca Three.js via CDN, eliminando dependências complexas e otimizando o carregamento.
    *   **Destaque de Elementos com Falha**: Elementos do modelo 3D que falham na validação são automaticamente destacados em vermelho, facilitando a identificação visual de problemas.
    *   **Interatividade Aprimorada**: Ao clicar em um objeto no visualizador 3D, suas informações são exibidas no chatbot, permitindo uma exploração mais intuitiva do modelo.
    *   **Controles de Visualização**: Botões para alternar a transparência de elementos (paredes, lajes, telhados) para visualização interna, e controles de câmera para vistas superior, frontal e reset.
    *   **Orientação Correta**: O modelo 3D é automaticamente ajustado para uma orientação correta ao ser carregado.
*   **Análise Térmica**: Módulo para cálculo da transmitância térmica (Valor U) de paredes, considerando múltiplas camadas e suas propriedades, essencial para avaliações de desempenho energético.
*   **Otimização de Performance**: Melhorias contínuas no processo de carregamento e renderização do modelo 3D para garantir uma experiência mais fluida, mesmo com modelos maiores.

## 🗺️ Arquitetura do Projeto

O projeto é estruturado em módulos lógicos para facilitar o desenvolvimento, manutenção e escalabilidade. A seguir, uma visão geral da estrutura de diretórios e dos principais componentes:

```
ontology-BIM/
├── app/                          # Código-fonte da aplicação Flask
│   ├── __init__.py
│   ├── routes.py                 # Definição das rotas da aplicação
│   ├── services/                 # Módulos de serviço e lógica de negócio
│   │   ├── chatbot_logic.py      # Lógica do chatbot e integração NLU
│   │   ├── fuseki_manager.py     # Gestão da base de conhecimento Apache Jena Fuseki
│   │   ├── thermal_analysis.py   # Módulo para cálculo de transmitância térmica
│   │   └── validation_engine.py  # Motor de validação de modelos IFC
│   ├── static/                   # Arquivos estáticos (CSS, JavaScript, WASM)
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/                   # Scripts JavaScript para o frontend
│   │   │   ├── api.js
│   │   │   ├── graph.js
│   │   │   ├── main.js
│   │   │   └── ui.js
│   │   └── wasm/                 # Arquivos WebAssembly para o visualizador 3D
│   │       ├── web-ifc-mt.wasm
│   │       └── web-ifc.wasm
│   └── templates/                # Modelos HTML da aplicação
│       └── index.html
├── data/                         # Ficheiros de dados e ontologias
│   └── ifc-ontology.ttl          # Regras de validação da ontologia
├── nlu_model/                    # Modelo de NLU treinado (spaCy)
│   ├── config.cfg
│   ├── meta.json
│   ├── textcat/
│   └── vocab/
├── uploads/                      # Pasta temporária para arquivos .ifc carregados
├── INSTRUCOES_IMPLEMENTACAO.md   # Documento com instruções de implementação
├── README.md                     # Este arquivo README
├── SOLUCAO_IMPLEMENTADA.md       # Documentação detalhada da solução implementada
├── config.py                     # Configurações da aplicação
├── docker-compose.yml            # Configuração para Docker Compose
├── geometry_test_output.json     # Exemplo de dados de teste de geometria
├── requirements.txt              # Dependências Python do projeto
├── run.py                        # Script para iniciar a aplicação Flask
├── setup_nlu.py                  # Script para configurar o modelo NLU
├── test_enhanced_solution.py     # Script de testes para a solução aprimorada
└── test_geometry_only.py         # Script de teste isolado de extração de geometria
```

## 🛠️ Tecnologias Utilizadas

O projeto utiliza uma variedade de tecnologias e bibliotecas para oferecer suas funcionalidades:

*   **Backend**: Python, Flask
*   **Validação BIM**: `pyshacl`
*   **Processamento de Linguagem Natural (NLU)**: `spaCy`
*   **Inteligência Artificial (Sugestões)**: API do Ollama
*   **Base de Conhecimento**: Apache Jena Fuseki
*   **Processamento de Geometria IFC**: `ifcopenshell`
*   **Visualização 3D**: Three.js (frontend)
*   **Contêineres**: Docker, Docker Compose

## 🚀 Como Rodar o Projeto

Para configurar e executar o projeto localmente, siga os passos abaixo:

### 1. Clone o repositório

```bash
git clone https://github.com/AntiKevin/ontology-BIM.git
cd ontology-BIM
```

### 2. Instale as dependências Python

É recomendado usar um ambiente virtual para gerenciar as dependências:

```bash
python -m venv venv
source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Configure o modelo NLU

Execute o script de configuração do modelo NLU:

```bash
python setup_nlu.py
```

### 4. Inicie o Apache Jena Fuseki

O Apache Jena Fuseki é usado como base de conhecimento. Você pode iniciá-lo via Docker Compose:

```bash
docker-compose up -d fuseki
```

Certifique-se de que o Fuseki esteja acessível na porta configurada (geralmente 3030).

### 5. Inicie a aplicação Flask

```bash
python run.py
```

A aplicação estará disponível em `http://localhost:5000` (ou a porta configurada).

## 📄 Documentação Adicional

Para mais detalhes sobre a implementação e as funcionalidades específicas, consulte os seguintes documentos no repositório:

*   [`INSTRUCOES_IMPLEMENTACAO.md`](INSTRUCOES_IMPLEMENTACAO.md): Detalhes sobre as instruções de implementação.
*   [`SOLUCAO_IMPLEMENTADA.md`](SOLUCAO_IMPLEMENTADA.md): Documentação aprofundada sobre a solução implementada, incluindo o visualizador 3D aprimorado.

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests para melhorias, correções de bugs ou novas funcionalidades.

## 📜 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE). (Assumindo licença MIT, se houver uma licença diferente, por favor, ajuste.)

## 📧 Contato

Para dúvidas ou sugestões, entre em contato com os mantenedores do projeto.

