import logging
import time

try:
    from iqoptionapi.api import IQOptionAPI as _IQOptionAPI
except Exception:
    _IQOptionAPI = None


class IQ_Option:
    """Light adapter that proxies to installed iqoptionapi.api.IQOptionAPI.

    Provides minimal compatibility methods expected by `painel.py`:
    `connect`, `check_connect`, `get_balance`, `change_balance`, `buy`,
    `check_win_v3`, `get_candles`, stream start/stop and attribute proxying.
    """

    def __init__(self, email=None, password=None, *args, **kwargs):
        self._email = email
        self._password = password
        self._client = None
        if _IQOptionAPI is not None:
            try:
                self._client = _IQOptionAPI(email, password)
            except Exception:
                try:
                    # some forks use different ctor signatures
                    self._client = _IQOptionAPI(email, password, *args, **kwargs)
                except Exception as e:
                    logging.warning("iq_adapter: failed to instantiate client: %s", e)

    def connect(self):
        if self._client is None:
            return False
        try:
            if hasattr(self._client, "connect"):
                return self._client.connect()
            # some variants use "connect_api" or similar
            for name in ("connect_api", "start", "open"):
                fn = getattr(self._client, name, None)
                if callable(fn):
                    try:
                        return fn()
                    except Exception:
                        continue
        except Exception:
            logging.exception("iq_adapter.connect error")
        return False

    def check_connect(self):
        if self._client is None:
            return False
        try:
            if hasattr(self._client, "check_connect"):
                return self._client.check_connect()
            if hasattr(self._client, "connected"):
                return bool(getattr(self._client, "connected"))
            # fallback: assume connected if client exists
            return True
        except Exception:
            logging.exception("iq_adapter.check_connect error")
            return False

    def get_balance(self):
        if self._client is None:
            return None
        try:
            # common method
            for name in ("get_balance", "get_balance_v2", "get_balance_sync"):
                fn = getattr(self._client, name, None)
                if callable(fn):
                    try:
                        b = fn()
                        return float(b) if b is not None else None
                    except Exception:
                        continue

            # try get_balances -> dict/list
            if hasattr(self._client, "get_balances"):
                try:
                    b = self._client.get_balances()
                    # if dict with 'balance' key
                    if isinstance(b, dict):
                        for v in b.values():
                            try:
                                return float(v)
                            except Exception:
                                continue
                    # if list-like
                    if isinstance(b, (list, tuple)) and b:
                        try:
                            return float(b[0])
                        except Exception:
                            pass
                except Exception:
                    pass

            # profile attribute fallback
            prof = getattr(self._client, "profile", None)
            if prof is not None:
                # profile may be dict-like or object
                if isinstance(prof, dict):
                    for k in ("balance", "saldo", "balance_amount"):
                        if k in prof:
                            try:
                                return float(prof[k])
                            except Exception:
                                continue
                else:
                    for attr in ("balance", "saldo"):
                        v = getattr(prof, attr, None)
                        if v is not None:
                            try:
                                return float(v)
                            except Exception:
                                continue

            # last resort: try method getprofile() if present
            if hasattr(self._client, "getprofile"):
                try:
                    p = self._client.getprofile()
                    if isinstance(p, dict):
                        for k in ("balance", "saldo"):
                            if k in p:
                                try:
                                    return float(p[k])
                                except Exception:
                                    continue
                except Exception:
                    pass
        except Exception:
            logging.exception("iq_adapter.get_balance error")
        return None

    def change_balance(self, target):
        if self._client is None:
            return False
        fn = getattr(self._client, "change_balance", None) or getattr(
            self._client, "set_balance", None
        )
        if callable(fn):
            try:
                return fn(target)
            except Exception:
                logging.exception("iq_adapter.change_balance error")
                return False
        return False

    def buy(self, amount, par, direcao, timeframe=1):
        if self._client is None:
            return (False, None)
        fn = getattr(self._client, "buy", None) or getattr(
            self._client, "execute_buy", None
        )
        if callable(fn):
            try:
                return fn(amount, par, direcao, timeframe)
            except Exception:
                logging.exception("iq_adapter.buy error")
        return (False, None)

    def check_win_v3(self, id_op):
        if self._client is None:
            return None
        fn = getattr(self._client, "check_win_v3", None) or getattr(
            self._client, "check_win", None
        )
        if callable(fn):
            try:
                return fn(id_op)
            except Exception:
                logging.exception("iq_adapter.check_win_v3 error")
        return None

    def get_candles(self, par, timeframe, qtd, to_timestamp):
        if self._client is None:
            return []
        fn = getattr(self._client, "get_candles", None)
        if callable(fn):
            try:
                return fn(par, timeframe, qtd, to_timestamp)
            except Exception:
                logging.exception("iq_adapter.get_candles error")
        return []

    def start_candles_stream(self, par, tf_seconds):
        fn = getattr(self._client, "start_candles_stream", None) or getattr(
            self._client, "start_candles", None
        )
        if callable(fn):
            try:
                return fn(par, tf_seconds)
            except Exception:
                logging.exception("iq_adapter.start_candles_stream error")
        return False

    def stop_candles_stream(self, par):
        fn = getattr(self._client, "stop_candles_stream", None) or getattr(
            self._client, "stop_candles", None
        )
        if callable(fn):
            try:
                return fn(par)
            except Exception:
                logging.exception("iq_adapter.stop_candles_stream error")
        return False

    def get_option_open_by_other_pc(self):
        fn = getattr(self._client, "get_option_open_by_other_pc", None) or getattr(
            self._client, "get_open_options", None
        )
        if callable(fn):
            try:
                return fn()
            except Exception:
                logging.exception("iq_adapter.get_option_open_by_other_pc error")
        return {}

    def __getattr__(self, name):
        # proxy any other attribute to underlying client
        if name.startswith("_"):
            raise AttributeError(name)
        client = object.__getattribute__(self, "_client")
        if client is not None and hasattr(client, name):
            return getattr(client, name)
        raise AttributeError(name)


"""Adaptador compatível com a interface esperada por `painel.py`.
Ele tenta adaptar `iqoptionapi.api.IQOptionAPI` para métodos usados no código.
"""

import logging
import time

try:
    from iqoptionapi.api import IQOptionAPI as _RealIQ
except Exception:
    _RealIQ = None


class IQ_Option:
    def __init__(self, *args, **kwargs):
        self._client = None
        self._args = args
        self._kwargs = kwargs
        if _RealIQ is None:
            logging.warning("iq_adapter: pacote iqoptionapi.api não disponível")
            return
        try:
            # Tenta construir diretamente com os args fornecidos
            self._client = _RealIQ(*args, **kwargs)
        except TypeError:
            # Variante comum: usuário pode passar (username, password)
            try:
                if len(args) == 2:
                    username, password = args
                    try:
                        self._client = _RealIQ("iqoption.com", username, password)
                    except Exception:
                        self._client = _RealIQ(username, password)
                else:
                    self._client = None
            except Exception:
                self._client = None
        except Exception:
            self._client = None

    def connect(self):
        if not self._client:
            return False
        result = False
        for name in ("connect", "start", "login"):
            fn = getattr(self._client, name, None)
            if callable(fn):
                try:
                    result = fn()
                    # don't return immediately — allow post-init attempts below
                    break
                except Exception:
                    continue

        # Some variants require an extra websocket/session init step
        try:
            # small delay to let client set attributes
            time.sleep(0.1)
        except Exception:
            pass

        try:
            # If client exposes a `wss`/`ws` attribute but it's None, try common starters
            for ws_attr in ("wss", "ws", "websocket", "_wss", "_ws"):
                attr = getattr(self._client, ws_attr, None)
                if attr is None:
                    for init_name in (
                        "start",
                        "start_stream",
                        "start_public_stream",
                        "start_websocket",
                        "open",
                        "open_ws",
                        "init",
                        "init_ws",
                        "init_wss",
                        "connect_ws",
                    ):
                        init_fn = getattr(self._client, init_name, None)
                        if callable(init_fn):
                            try:
                                init_fn()
                                time.sleep(0.05)
                            except Exception:
                                continue
                # if attribute became truthy, assume ok
                if getattr(self._client, ws_attr, None):
                    return True
        except Exception:
            pass

        # fallback: return boolean result from attempted call or check_connect
        if result:
            return True
        return self.check_connect()

    def check_connect(self):
        if not self._client:
            return False
        for name in ("check_connect", "is_connected", "connected"):
            fn = getattr(self._client, name, None)
            try:
                if callable(fn):
                    return fn()
            except Exception:
                continue
        # fallback: try attribute
        try:
            if bool(getattr(self._client, "connected", False)):
                return True
        except Exception:
            pass

        # check common websocket/socket attributes for a live connection
        try:
            for ws_attr in ("wss", "ws", "websocket", "_wss", "_ws"):
                w = getattr(self._client, ws_attr, None)
                if w:
                    # heuristics: if object has `connected` or `sock` or truthy, assume connected
                    if getattr(w, "connected", False) or getattr(
                        w, "is_connected", False
                    ):
                        return True
                    if getattr(w, "sock", None):
                        return True
                    return True
        except Exception:
            pass

        return False

    def get_balance(self):
        if not self._client:
            return None
        # Try common callable methods first
        candidates = (
            "get_balance",
            "get_balance_v2",
            "get_balances",
            "getbalances",
            "get_all_wealth",
            "get_all_balances",
            "get_balance_by_account",
            "profile",
            "get_profile",
        )

        def extract_numeric(obj):
            try:
                if obj is None:
                    return None
                if isinstance(obj, (int, float)):
                    return float(obj)
                if isinstance(obj, str):
                    s = obj.strip().replace(",", ".")
                    try:
                        return float(s)
                    except Exception:
                        return None
                if isinstance(obj, dict):
                    # common keys
                    for k in ("balance", "Balance", "available", "amount", "value"):
                        v = obj.get(k)
                        if isinstance(v, (int, float)):
                            return float(v)
                        if isinstance(v, str):
                            try:
                                return float(v.replace(",", "."))
                            except Exception:
                                pass
                    # nested structures (e.g., {'PRACTICE': {'balance': 123.0}})
                    for v in obj.values():
                        if isinstance(v, dict):
                            n = extract_numeric(v)
                            if n is not None:
                                return n
                if isinstance(obj, (list, tuple)) and obj:
                    for item in obj:
                        n = extract_numeric(item)
                        if n is not None:
                            return n
            except Exception:
                return None
            return None

        # Special-case: some clients expose a `profile` object with balance info
        try:
            prof = getattr(self._client, "profile", None)
            if prof is not None:
                try:
                    # check common mangled/private attrs and msg dict
                    for attr in (
                        "_Profile__balance",
                        "_Profile__balances",
                        "_Profile__msg",
                        "balance",
                        "balances",
                        "msg",
                    ):
                        try:
                            v = getattr(prof, attr, None)
                        except Exception:
                            v = None
                        n = extract_numeric(v)
                        if n is not None:
                            return n

                    # try __dict__ parsing
                    try:
                        d = getattr(prof, "__dict__", None)
                    except Exception:
                        d = None
                    if isinstance(d, dict):
                        n = extract_numeric(d)
                        if n is not None:
                            return n
                except Exception:
                    pass
        except Exception:
            pass

        for name in candidates:
            fn = getattr(self._client, name, None)
            try:
                if callable(fn):
                    res = fn()
                    n = extract_numeric(res)
                    if n is not None:
                        return n
                    # sometimes returns dict of accounts
                    if isinstance(res, dict):
                        # look for PRACTICE or practice
                        for acct in ("PRACTICE", "practice", "DEMO", "demo"):
                            acc = res.get(acct)
                            n = extract_numeric(acc)
                            if n is not None:
                                return n
                        # try top-level numeric values
                        n = extract_numeric(res)
                        if n is not None:
                            return n
            except Exception:
                continue

        # Try attributes on the client
        for attr in (
            "balance",
            "balances",
            "account_balance",
            "practice_balance",
            "available_balance",
        ):
            try:
                v = getattr(self._client, attr, None)
            except Exception:
                v = None
            n = extract_numeric(v)
            if n is not None:
                return n

        return None

    def buy(self, amount, par, direcao, timeframe):
        if not self._client:
            return False
        # tenta variações da API
        try:
            fn = getattr(self._client, "buy", None)
            if callable(fn):
                res = fn(amount, par, direcao, timeframe)
                # normaliza para (status, id)
                if isinstance(res, tuple):
                    return res
                if isinstance(res, dict):
                    opid = res.get("id") or res.get("order_id")
                    return (True, opid) if opid else (True, None)
                if isinstance(res, bool):
                    return (res, None)
                # se inteiro -> id
                if isinstance(res, int):
                    return (True, res)
                return (False, None)
        except Exception:
            pass
        return (False, None)

    def check_win_v3(self, op_id):
        if not self._client:
            return None
        for name in ("check_win_v3", "check_win", "get_operation_result"):
            fn = getattr(self._client, name, None)
            try:
                if callable(fn):
                    return fn(op_id)
            except Exception:
                continue
        return None

    def get_candles(self, par, timeframe, qtd, timestamp=None):
        if not self._client:
            return []
        fn = getattr(self._client, "get_candles", None)
        try:
            if callable(fn):
                if timestamp is None:
                    return fn(par, timeframe, qtd)
                return fn(par, timeframe, qtd, timestamp)
        except Exception:
            pass
        return []

    def start_candles_stream(self, par, tf_seconds):
        if not self._client:
            return False
        for name in ("start_candles_stream", "start_candles_stream_v2", "start_stream"):
            fn = getattr(self._client, name, None)
            try:
                if callable(fn):
                    return fn(par, tf_seconds)
            except Exception:
                continue
        return False

    def stop_candles_stream(self, par):
        if not self._client:
            return False
        for name in ("stop_candles_stream", "stop_stream"):
            fn = getattr(self._client, name, None)
            try:
                if callable(fn):
                    return fn(par)
            except Exception:
                continue
        return False

    def change_balance(self, target):
        if not self._client:
            return None
        fn = getattr(self._client, "change_balance", None)
        try:
            if callable(fn):
                return fn(target)
        except Exception:
            pass
        return None

    def get_option_open_by_other_pc(self):
        if not self._client:
            return None
        for name in ("get_option_open_by_other_pc", "get_open_options"):
            fn = getattr(self._client, name, None)
            try:
                if callable(fn):
                    return fn()
            except Exception:
                continue
        return None

    def __getattr__(self, name):
        if self._client and hasattr(self._client, name):
            return getattr(self._client, name)
        raise AttributeError(name)
