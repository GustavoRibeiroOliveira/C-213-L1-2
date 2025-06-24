import numpy as np
import time
import paho.mqtt.client as mqtt
import skfuzzy as fuzzy
import skfuzzy.control as ctrl
import threading

# === Fuzzy System Setup ===
Erro = ctrl.Antecedent(np.arange(-36, 36.1, 0.1), 'Erro')
DeltaErro = ctrl.Antecedent(np.arange(-3, 3.1, 0.1), 'DeltaErro')
PMotor = ctrl.Consequent(np.arange(0, 101, 1), 'PMotor')

Erro['MN'] = fuzzy.trapmf(Erro.universe, [-36, -36, -3, -0.4])
Erro['PN'] = fuzzy.trimf(Erro.universe, [-0.4, -0.2, 0])
Erro['ZE'] = fuzzy.trimf(Erro.universe, [-0.2, 0, 0.2])
Erro['PP'] = fuzzy.trimf(Erro.universe, [0, 0.2, 0.4])
Erro['MP'] = fuzzy.trapmf(Erro.universe, [0.4, 3, 36, 36])

DeltaErro['MN'] = fuzzy.trapmf(DeltaErro.universe, [-36, -36, -3, -0.4])
DeltaErro['PN'] = fuzzy.trimf(DeltaErro.universe, [-0.4, -0.2, 0])
DeltaErro['ZE'] = fuzzy.trimf(DeltaErro.universe, [-0.2, 0, 0.2])
DeltaErro['PP'] = fuzzy.trimf(DeltaErro.universe, [0, 0.2, 0.4])
DeltaErro['MP'] = fuzzy.trapmf(DeltaErro.universe, [0.4, 3, 36, 36])

PMotor['MP'] = fuzzy.trimf(PMotor.universe, [0, 10, 20])
PMotor['P'] = fuzzy.trimf(PMotor.universe, [10, 20, 30])
PMotor['M'] = fuzzy.trimf(PMotor.universe, [20, 30, 40])
PMotor['A'] = fuzzy.trimf(PMotor.universe, [30, 40, 50])
PMotor['MA'] = fuzzy.trimf(PMotor.universe, [40, 65, 90])

regras = []
nomes_erro = ['MN', 'PN', 'ZE', 'PP', 'MP']
nomes_delta = ['MN', 'PN', 'ZE', 'PP', 'MP']
saida_map = [
    ['MA', 'MA', 'A',  'A',  'M'],
    ['MA', 'A',  'A',  'M',  'M'],
    ['MA', 'A',  'M',  'P',  'MP'],
    ['A',  'A',  'M',  'M',  'MP'],
    ['A',  'M',  'M',  'MP', 'MP']
]

for i, e in enumerate(nomes_erro):
    for j, d in enumerate(nomes_delta):
        s = saida_map[i][j]
        regras.append(ctrl.Rule(Erro[e] & DeltaErro[d], PMotor[s]))

sistema_ctrl = ctrl.ControlSystem(regras)

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

    # Rampa inicial
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

        if abs(erro) <= 0.01:
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
