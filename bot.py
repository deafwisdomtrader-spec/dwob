# bot.py

IQ_Option = None
try:
    from iq_adapter import IQ_Option
except Exception:
    IQ_Option = None
    try:
        from iqoptionapi.api import IQOptionAPI as IQ_Option
    except Exception:
        IQ_Option = None
import os

import time

Iq = None


# =========================
# CONECTAR
# =========================
def conectar(email, senha):
    global Iq

    # Respeita modo dummy para testes locais
    if os.getenv("USE_DUMMY_IQ") == "1":

        class DummyIQ:
            def __init__(self):
                try:
                    self._balance = float(os.getenv("ADMIN_SALDO", "1000"))
                except Exception:
                    self._balance = 1000.0

            def connect(self):
                return (True, None)

            def get_balance(self):
                return float(self._balance)

        Iq = DummyIQ()
    else:
        Iq = IQ_Option(email, senha)

    check, reason = Iq.connect() if hasattr(Iq, "connect") else (True, None)

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
