# bot.py

IQ_Option = None
try:
    from iqoptionapi.api import IQOptionAPI as IQ_Option
except Exception:
    IQ_Option = None

import time

Iq = None


# =========================
# CONECTAR
# =========================
def conectar(email, senha):
    global Iq

    Iq = IQ_Option(email, senha)
    check, reason = Iq.connect()

    if check:
        print("Conectado ✔")
        return True
    else:
        print("Erro:", reason)
        return False


# =========================
# PEGAR VELAS
# =========================
def pegar_velas(par="EURUSD", timeframe=60, qtd=3):
    global Iq

    if not Iq:
        print("Não conectado")
        return []

    velas = Iq.get_candles(par, timeframe, qtd, time.time())
    return velas


# =========================
# ANALISE MHI SIMPLES
# =========================
def analisar_mhi(velas):
    if len(velas) < 3:
        return "AGUARDAR"

    cores = []

    for v in velas:
        if v["close"] > v["open"]:
            cores.append("verde")
        else:
            cores.append("vermelho")

    verde = cores.count("verde")
    vermelho = cores.count("vermelho")

    if verde > vermelho:
        return "PUT"
    else:
        return "CALL"
