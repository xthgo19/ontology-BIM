def calculate_u_value(layers):
    """
    Calcula o valor U (transmitância térmica) de uma parede composta por múltiplas camadas.

    Args:
        layers (list): Uma lista de dicionários, onde cada dicionário representa uma camada
                       e contém 'thickness' (espessura em metros) e 'conductivity' (condutividade
                       térmica em W/(m.K)).

    Returns:
        float: O valor U da parede em W/(m².K).
    """
    total_resistance = 0
    for layer in layers:
        # Resistência térmica de uma camada = espessura / condutividade
        resistance = layer['thickness'] / layer['conductivity']
        total_resistance += resistance

    # Adicionar resistências superficiais (valores típicos para ar parado)
    # Resistência superficial interna (Rsi) e externa (Rse)
    # Valores típicos para paredes: Rsi = 0.13 m².K/W, Rse = 0.04 m².K/W
    # Fonte: NBR 15220-2 (para Brasil) ou ISO 6946
    Rsi = 0.13
    Rse = 0.04
    total_resistance += Rsi + Rse

    # Valor U = 1 / Resistência Total
    u_value = 1 / total_resistance
    return u_value

# Exemplo de uso (para testes internos)
if __name__ == '__main__':
    # Exemplo de uma parede com tijolo, isolamento e gesso
    wall_layers = [
        {'thickness': 0.15, 'conductivity': 0.77},  # Tijolo
        {'thickness': 0.05, 'conductivity': 0.035}, # Lã de rocha (isolamento)
        {'thickness': 0.015, 'conductivity': 0.22}  # Gesso
    ]
    u_value = calculate_u_value(wall_layers)
    print(f"O valor U da parede é: {u_value:.2f} W/(m².K)")

