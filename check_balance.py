import json
import time
import os
import painel

# If running in local dummy mode, avoid reading real config or connecting
if os.getenv("USE_DUMMY_IQ") == "1":

    class DummyIQ:
        def __init__(self):
            try:
                self._balance = float(os.getenv("ADMIN_SALDO", "1000"))
            except Exception:
                self._balance = 1000.0

        def connect(self):
            return (True, None)

        def change_balance(self, mode):
            return True

        def get_balance(self):
            return float(self._balance)

    Iq = DummyIQ()
    painel.Iq = Iq
    print("Modo Dummy: usando DummyIQ para check_balance")
else:
    creds = json.load(open("config/user.json"))
    print("Credenciais:", creds.get("email"))
    # instantiate via adapter-aware class
    try:
        Iq = painel.IQ_Option(creds.get("email"), creds.get("senha"))
    except TypeError:
        # fallback: try passing host/email/password for incompatible constructors
        try:
            Iq = painel.IQ_Option(
                "iqoption.com", creds.get("email"), creds.get("senha")
            )
        except Exception as e:
            print("Falha ao instanciar Iq:", e)
            Iq = None
    print("Instância Iq:", type(Iq))
    painel.Iq = Iq

    # attempt connect
    try:
        ok = painel.safe_iq_call(lambda: painel.Iq.connect(), timeout=6, name="connect")
        print("Resultado conexão:", ok)
    except Exception as e:
        print("Exceção conexão:", e)

    try:
        painel.safe_iq_call(
            lambda: painel.Iq.change_balance("PRACTICE"),
            timeout=6,
            name="change_balance",
        )
    except Exception as e:
        print("Exceção change_balance:", e)

    saldo = painel.safe_iq_call(
        lambda: painel.Iq.get_balance(), timeout=6, name="get_balance"
    )
    print("SALDO_DEMO:", saldo)
