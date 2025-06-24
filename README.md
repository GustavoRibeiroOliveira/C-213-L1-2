# Controle Fuzzy de Elevador

Este projeto implementa um sistema de controle fuzzy para simular o movimento de um elevador entre diferentes andares. O sistema consiste em um servidor Python que processa o controle fuzzy e uma interface web que permite interagir com o elevador.

## Funcionalidades

- Controle fuzzy baseado em erro e taxa de variação do erro (delta)
- Interface web intuitiva com botões para cada andar
- Visualização em tempo real da posição do elevador
- Gráfico dinâmico mostrando a trajetória do elevador
- Sistema de reset para retornar ao térreo
- Indicação visual do andar atual e do destino

## Componentes

1. **Backend (Python)**:
   - Implementa o sistema de controle fuzzy usando a biblioteca `skfuzzy`
   - Comunicação MQTT para troca de mensagens com a interface web
   - Simulação do comportamento dinâmico do elevador

2. **Frontend (HTML/JavaScript)**:
   - Interface interativa com botões para cada andar
   - Conexão MQTT via WebSocket
   - Gráfico dinâmico usando Chart.js
   - Visualização do status em tempo real

## Como Executar

### Pré-requisitos

- Python 3.x
- Bibliotecas Python: `paho-mqtt`, `numpy`, `skfuzzy`
- Navegador web moderno

### Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências Python:

```bash
pip install -r requirements.txt
```

### Execução

- Rode o servidor MQTT

```bash
python main.py
```

- Rode o HTML

```bash
start .\index.html
```
