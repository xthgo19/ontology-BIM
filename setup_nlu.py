import spacy
from spacy.training.example import Example
import random
import os

def run_nlu_training():
    """
    Cria e treina um modelo de classificação de texto (NLU) com base
    em exemplos de frases e suas intenções correspondentes.
    """
    NLU_MODEL_PATH = "./nlu_model"
    
    # Verifica se o modelo já existe para não treinar desnecessariamente
    if os.path.exists(NLU_MODEL_PATH):
        print(f"-> A pasta '{NLU_MODEL_PATH}' já existe. O treino do modelo NLU será ignorado.")
        print("-> Se desejar treinar novamente, apague a pasta 'nlu_model' e execute este script outra vez.")
        return

    print("-> A iniciar o treino do modelo de NLU...")

    # Dados de treinamento: pares de (frase de exemplo, dicionário de intenções).
    TRAIN_DATA = [
        ("oi", {"cats": {"saudacao": 1.0, "despedida": 0.0, "perguntar_propriedade": 0.0}}),
        ("olá", {"cats": {"saudacao": 1.0, "despedida": 0.0, "perguntar_propriedade": 0.0}}),
        ("bom dia", {"cats": {"saudacao": 1.0, "despedida": 0.0, "perguntar_propriedade": 0.0}}),
        ("tchau", {"cats": {"saudacao": 0.0, "despedida": 1.0, "perguntar_propriedade": 0.0}}),
        ("até logo", {"cats": {"saudacao": 0.0, "despedida": 1.0, "perguntar_propriedade": 0.0}}),
        ("qual o material do 'floor'?", {"cats": {"saudacao": 0.0, "despedida": 0.0, "perguntar_propriedade": 1.0}}),
        ("onde está a 'parede-01'?", {"cats": {"saudacao": 0.0, "despedida": 0.0, "perguntar_propriedade": 1.0}}),
        ("qual o tipo do 'pilar-C'?", {"cats": {"saudacao": 0.0, "despedida": 0.0, "perguntar_propriedade": 1.0}}),
        ("o que a 'laje-1' contém?", {"cats": {"saudacao": 0.0, "despedida": 0.0, "perguntar_propriedade": 1.0}}),
        ("mostre a composição da 'viga-v5'", {"cats": {"saudacao": 0.0, "despedida": 0.0, "perguntar_propriedade": 1.0}}),
    ]
    
    # Cria um modelo de linguagem vazio para o português
    nlp_train = spacy.blank("pt")
    
    # Adiciona um componente de classificação de texto (textcat)
    textcat = nlp_train.add_pipe("textcat")
    
    # Adiciona as possíveis categorias (labels) de intenção ao classificador
    textcat.add_label("saudacao")
    textcat.add_label("despedida")
    textcat.add_label("perguntar_propriedade")
    
    # Inicia o treinamento
    optimizer = nlp_train.initialize()
    
    print("-> A treinar o modelo...")
    for i in range(15): # Número de épocas de treino
        random.shuffle(TRAIN_DATA)
        losses = {}
        for text, annotations in TRAIN_DATA:
            doc = nlp_train.make_doc(text)
            example = Example.from_dict(doc, annotations)
            nlp_train.update([example], sgd=optimizer, losses=losses)
        print(f"   Época {i+1}/15 - Perda: {losses['textcat']:.4f}")

    # Salva o modelo treinado na pasta especificada
    nlp_train.to_disk(NLU_MODEL_PATH)
    print(f"\n-> Modelo de NLU treinado e salvo com sucesso em '{NLU_MODEL_PATH}'.")

if __name__ == "__main__":
    run_nlu_training()