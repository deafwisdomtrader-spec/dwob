import sys

print("PY", sys.executable)

try:
    import iqoptionapi.api as a

    print("api OK", getattr(a, "IQOptionAPI", None))
except Exception as e:
    print("api err", repr(e))

try:
    import iqoptionapi.stable_api as s

    print("stable OK", [n for n in dir(s) if "IQ" in n.upper()][:50])
except Exception as e:
    print("stable err (esperado em versões modernas)", repr(e))

try:
    import iqoptionapi as m

    print("module OK", [n for n in dir(m) if "IQ" in n.upper()][:50])
except Exception as e:
    print("module err", repr(e))
