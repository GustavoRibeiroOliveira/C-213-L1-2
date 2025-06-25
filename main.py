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
Erro = ctrl.Antecedent(np.arange(0, 32.1, 1), 'Erro')
DeltaErro = ctrl.Antecedent(np.arange(0, 32.1, 1), 'DeltaErro')
PMotor = ctrl.Consequent(np.arange(0, 91, 1), 'PMotor')

Erro['ZE'] = fuzzy.trimf(Erro.universe, [0, 0.3, 0.6])
Erro['MP'] = fuzzy.trimf(Erro.universe, [0.3, 0.6, 1.2])
Erro['P'] = fuzzy.trimf(Erro.universe, [0.6, 1.2, 2.4])
Erro['M'] = fuzzy.trimf(Erro.universe, [1.2, 2.4, 3.6])
Erro['A'] = fuzzy.trapmf(Erro.universe, [2.4, 3.6, 32, 32])

DeltaErro['ZE'] = fuzzy.trimf(Erro.universe, [0, 0.3, 0.6])
DeltaErro['MP'] = fuzzy.trimf(Erro.universe, [0.3, 0.6, 1.2])
DeltaErro['P'] = fuzzy.trimf(Erro.universe, [0.6, 1.2, 2.4])
DeltaErro['M'] = fuzzy.trimf(Erro.universe, [1.2, 2.4, 3.6])
DeltaErro['A'] = fuzzy.trapmf(Erro.universe, [2.4, 3.6, 32, 32])

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
R1 = ctrl.Rule(Erro['ZE'] & DeltaErro['ZE'], PMotor['I'])
R2 = ctrl.Rule(Erro['MP'] & DeltaErro['ZE'], PMotor['P'])
R3 = ctrl.Rule(Erro['P'] & DeltaErro['ZE'], PMotor['P'])
R4 = ctrl.Rule(Erro['M'] & DeltaErro['ZE'], PMotor['P'])
R5 = ctrl.Rule(Erro['A'] & DeltaErro['ZE'], PMotor['M'])

R6 = ctrl.Rule(Erro['ZE'] & DeltaErro['MP'], PMotor['P'])
R7 = ctrl.Rule(Erro['MP'] & DeltaErro['MP'], PMotor['P'])
R8 = ctrl.Rule(Erro['P'] & DeltaErro['MP'], PMotor['P'])
R9 = ctrl.Rule(Erro['M'] & DeltaErro['MP'], PMotor['M'])
R10 = ctrl.Rule(Erro['A'] & DeltaErro['MP'], PMotor['M'])

R11 = ctrl.Rule(Erro['ZE'] & DeltaErro['P'], PMotor['P'])
R12 = ctrl.Rule(Erro['MP'] & DeltaErro['P'], PMotor['P'])
R13 = ctrl.Rule(Erro['P'] & DeltaErro['P'], PMotor['M'])
R14 = ctrl.Rule(Erro['M'] & DeltaErro['P'], PMotor['M'])
R15 = ctrl.Rule(Erro['A'] & DeltaErro['P'], PMotor['A'])

R16 = ctrl.Rule(Erro['ZE'] & DeltaErro['M'], PMotor['P'])
R17 = ctrl.Rule(Erro['MP'] & DeltaErro['M'], PMotor['M'])
R18 = ctrl.Rule(Erro['P'] & DeltaErro['M'], PMotor['M'])
R19 = ctrl.Rule(Erro['M'] & DeltaErro['M'], PMotor['A'])
R20 = ctrl.Rule(Erro['A'] & DeltaErro['M'], PMotor['A'])

R21 = ctrl.Rule(Erro['ZE'] & DeltaErro['A'], PMotor['M'])
R22 = ctrl.Rule(Erro['MP'] & DeltaErro['A'], PMotor['M'])
R23 = ctrl.Rule(Erro['P'] & DeltaErro['A'], PMotor['A'])
R24 = ctrl.Rule(Erro['M'] & DeltaErro['A'], PMotor['A'])
R25 = ctrl.Rule(Erro['A'] & DeltaErro['A'], PMotor['A'])

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
    erro_anterior = abs(posicao_atual - setpoint)

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

        erro = abs(posicao_atual - setpoint)
        delta_erro = abs(erro - erro_anterior)

        if erro <= 0.03:
            em_execucao = False
            return

        controle.input['Erro'] = erro
        controle.input['DeltaErro'] = delta_erro
        controle.compute()
        try:
            potencia = controle.output['PMotor'] / 100
        except KeyError:
            print("Erro ao acessar PMotor. Verifique as entradas e regras.")
            print("Entradas:")
            print(f"Erro = {erro}, DeltaErro = {delta_erro}")
            print(f"posicao_atual = {posicao_atual}")
            print(f"setpoint = {setpoint}")
            print("Saídas disponíveis:", controle.output)
            return

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
