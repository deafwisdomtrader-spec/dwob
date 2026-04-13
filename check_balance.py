import json
import time
import painel

creds = json.load(open("config/user.json"))
print("Credenciais:", creds.get("email"))
# instantiate via adapter-aware class
try:
    Iq = painel.IQ_Option(creds.get("email"), creds.get("senha"))
except TypeError:
    # fallback: try passing host/email/password for incompatible constructors
    try:
        Iq = painel.IQ_Option("iqoption.com", creds.get("email"), creds.get("senha"))
    except Exception as e:
        print("Falha ao instanciar Iq:", e)
        Iq = None
print("Instância Iq:", type(Iq))
# assign to painel.Iq so safe_iq_call uses it
painel.Iq = Iq
# attempt connect
try:
    ok = painel.safe_iq_call(lambda: painel.Iq.connect(), timeout=6, name="connect")
    print("Resultado conexão:", ok)
except Exception as e:
    print("Exceção conexão:", e)
try:
    painel.safe_iq_call(
        lambda: painel.Iq.change_balance("PRACTICE"), timeout=6, name="change_balance"
    )
    except Exception as e:
        print("Exceção change_balance:", e)
saldo = painel.safe_iq_call(
    lambda: painel.Iq.get_balance(), timeout=6, name="get_balance"
)
print("SALDO_DEMO:", saldo)
