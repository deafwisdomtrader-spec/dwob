import json
import time
import painel

creds = json.load(open("config/user.json"))
print("Creds:", creds.get("email"))
Iq = painel.IQ_Option(creds.get("email"), creds.get("senha"))
print("Iq instance:", type(Iq))
# assign to painel.Iq so safe_iq_call uses it
painel.Iq = Iq
# attempt connect
try:
    ok = painel.safe_iq_call(lambda: painel.Iq.connect(), timeout=6, name="connect")
    print("connect result:", ok)
except Exception as e:
    print("connect exception", e)
try:
    painel.safe_iq_call(
        lambda: painel.Iq.change_balance("PRACTICE"), timeout=6, name="change_balance"
    )
except Exception as e:
    print("change_balance exception", e)
saldo = painel.safe_iq_call(
    lambda: painel.Iq.get_balance(), timeout=6, name="get_balance"
)
print("SALDO_DEMO:", saldo)
