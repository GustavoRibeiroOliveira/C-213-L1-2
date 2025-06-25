import numpy as np
import time
import paho.mqtt.client as mqtt
import skfuzzy as fuzzy
import skfuzzy.control as ctrl
import threading
import pandas as pd
from tabulate import tabulate
import re

# === Fuzzy System Setup ===
Erro = ctrl.Antecedent(np.arange(-32, 32.1, 1), 'Erro')
DeltaErro = ctrl.Antecedent(np.arange(-32, 32.1, 1), 'DeltaErro')
PMotor = ctrl.Consequent(np.arange(0, 91, 1), 'PMotor')

Erro['MN'] = fuzzy.trapmf(Erro.universe, [-32, -32, -1.2, -0.6])
Erro['PN'] = fuzzy.trimf(Erro.universe, [-1.2, -0.6, 0])
Erro['ZE'] = fuzzy.trimf(Erro.universe, [-0.6, 0, 0.6])
Erro['PP'] = fuzzy.trimf(Erro.universe, [0, 0.6, 1.2])
Erro['MP'] = fuzzy.trapmf(Erro.universe, [0.6, 1.2, 32, 32])

DeltaErro['MN'] = fuzzy.trapmf(Erro.universe, [-32, -32, -1.2, -0.6])
DeltaErro['PN'] = fuzzy.trimf(Erro.universe, [-1.2, -0.6, 0])
DeltaErro['ZE'] = fuzzy.trimf(Erro.universe, [-0.6, 0, 0.6])
DeltaErro['PP'] = fuzzy.trimf(Erro.universe, [0, 0.6, 1.2])
DeltaErro['MP'] = fuzzy.trapmf(Erro.universe, [0.6, 1.2, 32, 32])

PMotor['I'] = fuzzy.trimf(PMotor.universe, [0, 15.75, 31.5])
PMotor['P'] = fuzzy.trimf(PMotor.universe, [15.75, 31.5, 45])
PMotor['M'] = fuzzy.trimf(PMotor.universe, [31.5, 45, 90])
PMotor['A'] = fuzzy.trimf(PMotor.universe, [45, 90, 90])

# regras = []
# nomes_erro = ['MN', 'PN', 'ZE', 'PP', 'MP']
# nomes_delta = ['MN', 'PN', 'ZE', 'PP', 'MP']
# saida_map = [
#     ['MA', 'MA', 'A', 'A', 'M'],
#     ['MA', 'A', 'A', 'M', 'M'],
#     ['MA', 'A', 'M', 'P', 'MP'],
#     ['A', 'A', 'M', 'M', 'MP'],
#     ['A', 'M', 'M', 'MP', 'MP']
# ]
#
# for i, e in enumerate(nomes_erro):
#     for j, d in enumerate(nomes_delta):
#         s = saida_map[i][j]
#         regras.append(ctrl.Rule(Erro[e] & DeltaErro[d], PMotor[s]))

# Definição das regras fuzzy
R1 = ctrl.Rule(Erro['MN'] & DeltaErro['MN'], PMotor['A'])
R2 = ctrl.Rule(Erro['PN'] & DeltaErro['MN'], PMotor['A'])
R3 = ctrl.Rule(Erro['ZE'] & DeltaErro['MN'], PMotor['A'])
R4 = ctrl.Rule(Erro['PP'] & DeltaErro['MN'], PMotor['M'])
R5 = ctrl.Rule(Erro['MP'] & DeltaErro['MN'], PMotor['M'])

R6 = ctrl.Rule(Erro['MN'] & DeltaErro['PN'], PMotor['A'])
R7 = ctrl.Rule(Erro['PN'] & DeltaErro['PN'], PMotor['A'])
R8 = ctrl.Rule(Erro['ZE'] & DeltaErro['PN'], PMotor['M'])
R9 = ctrl.Rule(Erro['PP'] & DeltaErro['PN'], PMotor['M'])
R10 = ctrl.Rule(Erro['MP'] & DeltaErro['PN'], PMotor['M'])

R11 = ctrl.Rule(Erro['MN'] & DeltaErro['ZE'], PMotor['A'])
R12 = ctrl.Rule(Erro['PN'] & DeltaErro['ZE'], PMotor['M'])
R13 = ctrl.Rule(Erro['ZE'] & DeltaErro['ZE'], PMotor['M'])
R14 = ctrl.Rule(Erro['PP'] & DeltaErro['ZE'], PMotor['M'])
R15 = ctrl.Rule(Erro['MP'] & DeltaErro['ZE'], PMotor['P'])

R16 = ctrl.Rule(Erro['MN'] & DeltaErro['PP'], PMotor['M'])
R17 = ctrl.Rule(Erro['PN'] & DeltaErro['PP'], PMotor['M'])
R18 = ctrl.Rule(Erro['ZE'] & DeltaErro['PP'], PMotor['M'])
R19 = ctrl.Rule(Erro['PP'] & DeltaErro['PP'], PMotor['P'])
R20 = ctrl.Rule(Erro['MP'] & DeltaErro['PP'], PMotor['P'])

R21 = ctrl.Rule(Erro['MN'] & DeltaErro['MP'], PMotor['M'])
R22 = ctrl.Rule(Erro['PN'] & DeltaErro['MP'], PMotor['M'])
R23 = ctrl.Rule(Erro['ZE'] & DeltaErro['MP'], PMotor['P'])
R24 = ctrl.Rule(Erro['PP'] & DeltaErro['MP'], PMotor['P'])
R25 = ctrl.Rule(Erro['MP'] & DeltaErro['MP'], PMotor['P'])

# Montagem da base de regras
qtdRegras = len(Erro.terms) * len(DeltaErro.terms)
BaseRegras = [globals()[f'R{regra}'] for regra in range(1, qtdRegras + 1)]

sistema_ctrl = ctrl.ControlSystem(BaseRegras)

tabela = []
logicaTabela = 'E'
for erro in Erro.terms:
    for deltaErro in DeltaErro.terms:
        for regra in BaseRegras:
            antecedente = str(regra).split('IF ')[1].split(' THEN')[0].replace('AND ', '')
            consequente = str(regra).split('IF ')[1].split(' THEN')[1].split('AND ')[0]

            classificacoes = re.findall(r'\[(.*?)\]', (antecedente + consequente))
            if erro == classificacoes[0] and deltaErro == classificacoes[1]:
                tabela.append([classificacoes[0], classificacoes[1], classificacoes[2]])
                break

# Print da tabela:
df = pd.DataFrame(tabela, columns=[Erro.label, logicaTabela, PMotor.label])
pivotTable = pd.DataFrame(
    df.pivot(index=logicaTabela, columns=Erro.label, values=PMotor.label).reindex(index=DeltaErro.terms,
                                                                                      columns=Erro.terms))
pivotTable.index.name = f'{pivotTable.index.name}\033[0m'
print(tabulate(pivotTable, headers='keys', tablefmt='fancy_grid', stralign='center', showindex='always'))

# MQTT Setup
broker = 'broker.hivemq.com'
topic_setpoint = 'elevador/destino'
topic_posicao = 'elevador/posicao'
topic_resetar = 'elevador/resetar'

posicao_atual = 4
setpoint = 4
em_execucao = False
parar_controle = False


# Função que simula o controle fuzzy
def controle_loop():
    global posicao_atual, setpoint, em_execucao, parar_controle
    if em_execucao:
        return
    em_execucao = True
    parar_controle = False

    Ts = 0.2

    k1 = 1 if setpoint > posicao_atual else -1
    erro_anterior = posicao_atual - setpoint

    for i in range(10):
        if parar_controle:
            em_execucao = False
            return
        potencia_inicial = 0.0315 * (i + 1)
        posicao_atual = abs(k1 * posicao_atual * 0.999 + potencia_inicial * 0.251287)
        client.publish(topic_posicao, round(posicao_atual, 3))
        time.sleep(Ts)

    # Controle fuzzy
    controle = ctrl.ControlSystemSimulation(sistema_ctrl)

    while True:
        if parar_controle:
            em_execucao = False
            return

        erro = posicao_atual - setpoint
        delta_erro = erro - erro_anterior

        if abs(erro) <= 0.03:
            break

        controle.input['Erro'] = erro
        controle.input['DeltaErro'] = delta_erro
        controle.compute()
        potencia = controle.output['PMotor'] / 100

        posicao_atual = abs(k1 * posicao_atual * 0.9995 + potencia * 0.212312)
        client.publish(topic_posicao, round(posicao_atual, 3))
        time.sleep(Ts)

        erro_anterior = erro
        k1 = 1 if setpoint > posicao_atual else -1

    em_execucao = False


# Callback do MQTT
def on_message(client, userdata, msg):
    global setpoint, posicao_atual, em_execucao, parar_controle
    try:
        if msg.topic == topic_setpoint:
            novo = float(msg.payload.decode())
            setpoint = novo
            threading.Thread(target=controle_loop).start()
        elif msg.topic == topic_resetar:
            print("Reset solicitado!")
            parar_controle = True
            setpoint = 4
            posicao_atual = 4
            client.publish(topic_posicao, round(posicao_atual, 3))
    except Exception as e:
        print("Erro ao processar mensagem:", e)


client = mqtt.Client()
client.connect(broker, 1883, 60)
client.subscribe(topic_setpoint)
client.subscribe(topic_resetar)
client.on_message = on_message

print("Aguardando comandos MQTT...")
client.loop_forever()
