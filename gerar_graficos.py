import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzzy

def plot_mf(x, funcs, labels, filename, zoom=None, xlabel="Universo"):
    plt.figure(figsize=(6, 3))
    for f, label in zip(funcs, labels):
        plt.plot(x, f, linewidth=2, label=label)
    plt.ylim([-0.05, 1.05])
    if zoom:
        plt.xlim(zoom)
    plt.title(f"Função de Pertinência - {filename.replace('.png','')}")
    plt.xlabel(xlabel)
    plt.ylabel("μ")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()

# Erro e DeltaErro
x = np.linspace(0, 33, 10000)
erro = [
    fuzzy.trimf(x, [0, 0.3, 0.6]),
    fuzzy.trimf(x, [0.3, 0.6, 1.2]),
    fuzzy.trimf(x, [0.6, 1.2, 2.4]),
    fuzzy.trimf(x, [1.2, 2.4, 3.6]),
    fuzzy.trapmf(x, [2.4, 3.6, 32, 32])
]
plot_mf(x, erro, ['ZE','MP','P','M','A'], 'erro.png', zoom=[0, 5], xlabel="Erro (m)")
plot_mf(x, erro, ['ZE','MP','P','M','A'], 'deltaerro.png', zoom=[0, 5], xlabel="Delta Erro (m)")

# PMotor
x2 = np.linspace(0, 100, 1000)
pmotor = [
    fuzzy.trimf(x2, [0, 15.75, 31.5]),
    fuzzy.trimf(x2, [15.75, 31.5, 45]),
    fuzzy.trimf(x2, [31.5, 45, 90]),
    fuzzy.trimf(x2, [45, 90, 90])
]
plot_mf(x2, pmotor, ['I','P','M','A'], 'pmotor.png', zoom=[0, 90], xlabel="Potência do Motor (%)")
