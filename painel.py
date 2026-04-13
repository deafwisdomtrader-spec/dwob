from PIL import Image, ImageTk, ImageDraw
import tkinter.font as tkFont
from admin import criar_admin
from tkinter import ttk
import os
from login import abrir_login
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import scrolledtext

IQ_Option = None
try:
    # Prefer the local adapter which normalizes different iqoptionapi variants
    from iq_adapter import IQ_Option
except Exception:
    IQ_Option = None
    try:
        from iqoptionapi.api import IQOptionAPI as IQ_Option
    except Exception:
        IQ_Option = None
import threading
import datetime
import time
import random
import itertools
import traceback

try:
    from mercado import abrir_mercado
    from controle import abrir_controle
    from config import abrir_config
except ImportError as e:
    print(f"Módulos não encontrados: {e}")


# Pool de workers para chamadas IQ - evita tempestade de threads E gargalo de fila
import queue as _queue

_iq_queue = _queue.Queue()
_iq_workers_started = 0
_IQ_NUM_WORKERS = 3


def _iq_worker():
    """Worker que processa chamadas IQ da fila."""
    while True:
        try:
            item = _iq_queue.get(timeout=5)
        except _queue.Empty:
            continue
        if item is None:
            break
        fn, timeout, name, result_event, result_box = item
        try:
            start = time.perf_counter()
            res = [None, None]  # [value, error]

            def _run():
                try:
                    res[0] = fn()
                except Exception as e:
                    res[1] = e

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(timeout)
            duration = time.perf_counter() - start
            call_name = name or str(fn)

            if t.is_alive():
                result_box["timeout"] = True
                print(f"TIMEOUT IQ: {call_name} {duration:.1f}s")
            elif res[1] is not None:
                result_box["error"] = res[1]
                print(f"ERRO IQ: {call_name} {duration:.1f}s -> {res[1]}")
            else:
                result_box["value"] = res[0]
                if duration >= 0.5:
                    print(f"IQ LENTO: {call_name} {duration:.1f}s")
        except Exception as e:
            result_box["error"] = e
        finally:
            result_event.set()


def _ensure_iq_workers():
    global _iq_workers_started
    while _iq_workers_started < _IQ_NUM_WORKERS:
        _iq_workers_started += 1
        threading.Thread(target=_iq_worker, daemon=True).start()


def safe_iq_call(fn, timeout=3, name=None):
    """Envia chamada IQ para pool de workers. Bloqueia atÃ© resultado ou timeout.
    NUNCA chamar da thread principal do Tkinter!"""
    try:
        if not Iq:
            return None
        _ensure_iq_workers()
        result_event = threading.Event()
        result_box = {}
        _iq_queue.put((fn, timeout, name, result_event, result_box))
        if not result_event.wait(timeout + 5):
            return None
        if "timeout" in result_box or "error" in result_box:
            return None
        return result_box.get("value")
    except Exception as e:
        print("safe_iq_call error:", e)
        return None


iq_lock = threading.Lock()
threads_rodando = 0
MAX_THREADS = 1
threads_lock = threading.Lock()
data_lock = threading.Lock()
ultimo_detectado = False
loop_auto_rodando = False
candle_thread_rodando = False

ultima_verificacao = 0

log = None
lbl_timer = None
lbl_hora = None

ultimo_saldo = None
ultimo_update_saldo = 0
ultimo_request = 0
ultimo_saldo_operacao = None
ultimo_log_candle = None
ultimo_candle_operado = None
saldo_cache = {"demo": None, "real": None}

candles = []

stop_ativo = False
tipo_stop = None
data_atual = None

ids_manual_processados = set()
ids_processados = set()
ids_resultado_processados = set()

lucro_demo = 0
lucro_real = 0
wins_demo = 0
wins_real = 0
loss_demo = 0
loss_real = 0


def _get_server_now():
    """Tempo IQ interpolado: base = servidor, gap = perf_counter local."""
    if ultimo_server_time is None:
        return None
    if _server_sync_local is None:
        return ultimo_server_time
    elapsed = time.perf_counter() - _server_sync_local
    return ultimo_server_time + elapsed


def atualizar_timer():
    """Timer preciso com interpolaÃ§Ã£o IQ."""
    global lbl_timer
    try:
        agora = _get_server_now()
        if agora and lbl_timer is not None:
            timeframe = 60
            restante = timeframe - (agora % timeframe)
            minutos = int(restante) // 60
            segundos = int(restante) % 60
            texto = f"{minutos:02d}:{segundos:02d}"
            cor = "#ff3333" if restante <= 10 else "#ffffff"
            lbl_timer.config(text=texto, fg=cor)
    except Exception:
        pass
    janela.after(200, atualizar_timer)


def atualizar_hora():
    """Hora precisa com interpolaÃ§Ã£o IQ."""
    global lbl_hora
    try:
        agora = _get_server_now()
        if agora and lbl_hora is not None:
            horario = datetime.datetime.fromtimestamp(int(agora))
            texto = horario.strftime("%H:%M:%S")
            lbl_hora.config(text=texto)
    except Exception:
        pass
    janela.after(200, atualizar_hora)


candles = []
candles_antigo = []
box_win = None
box_loss = None

Iq = None


def reconectar_iq():
    try:
        print("Reconectando IQ...")
        Iq.connect()
        time.sleep(1)
        print("Reconectado")
    except Exception as e:
        print("ERRO RECONEXÃO:", e)


def pegar_candles_iq(par="EURUSD-OTC", timeframe=60, qtd=20):
    global Iq
    try:
        if not Iq:
            return []

        # usa safe_iq_call para evitar bloqueio prolongado
        velas = safe_iq_call(
            lambda: Iq.get_candles(par, timeframe, qtd, time.time()),
            timeout=3,
            name="get_candles",
        )

        if not velas:
            return []
        lista = [[v["open"], v["close"], v["max"], v["min"]] for v in velas]
        return lista
    except Exception as e:
        return []


def abrir_admin(event=None):
    senha = simpledialog.askstring("Acesso restrito", "Senha admin:", show="*")
    if senha is None:
        return
    if senha == os.getenv("ADMIN_SENHA"):
        criar_admin()
    else:
        messagebox.showerror("Erro", "Senha incorreta")


def gerar_catalogo(n=5):
    catalogo = {}
    for combinacao in itertools.product(["V", "R"], repeat=n):
        padrao = "".join(combinacao)
        catalogo[padrao] = {"CALL": 0, "PUT": 0}
    return catalogo


catalogo = gerar_catalogo(5)

padrao = "VRVRV"
dados = catalogo.get(padrao)
if dados:
    print(dados)


def obter_padrao(candles, n=5):
    if not candles or len(candles) < n:
        return None

    ultimas = candles[-n:]
    padrao = ""

    for vela in ultimas:
        abertura = vela[0]
        fechamento = vela[1]

        if fechamento > abertura:
            padrao += "V"
        elif fechamento < abertura:
            padrao += "R"
        else:
            padrao += "D"  # DOJI

    return padrao


def escrever_log(widget, msg, tipo="info"):
    if widget is None:
        return
    widget.config(state="normal")
    try:
        linhas = int(widget.index("end-1c").split(".")[0])
        if linhas > 150:
            widget.delete("1.0", "5.0")
    except (IndexError, ValueError, tk.TclError):
        pass
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    # Evita logs duplicados consecutivos (inclusive saldo/lucro)
    try:
        ultimalinha = widget.get("end-2l", "end-1c").strip()
    except Exception:
        ultimalinha = ""
    novalinha = f"[{agora}] {msg}"

    # Remove hora para comparar sÃ³ mensagem
    def limpa_hora(linha):
        if linha.startswith("[") and "]" in linha:
            return linha.split("]", 1)[1].strip()
        return linha.strip()

    if limpa_hora(ultimalinha) != limpa_hora(novalinha):
        widget.insert("end", novalinha + "\n", tipo)
        widget.see("end")
    widget.config(state="disabled")


def salvar_historico(texto):
    try:
        data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("historico.txt", "a", encoding="utf-8") as f:
            f.write(f"[{data}] {texto}\n")
    except Exception as e:
        if log:
            janela.after(0, escrever_log, log, f"ERRO HISTÓRICO: {e}", "info")


def criar_avatar_circular(path, tamanho=60):
    try:
        img = Image.open(path).convert("RGBA").resize((tamanho, tamanho), Image.LANCZOS)
        mask = Image.new("L", (tamanho, tamanho), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, tamanho, tamanho), fill=255)
        img.putalpha(mask)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print("ERRO AVATAR:", e)
        return None


janela = tk.Tk()
janela.withdraw()  # esconde IMEDIATAMENTE - sem flash branco
janela.title("DWOB - MHI EVO")
janela.geometry("1000x700+-2000+-2000")
janela.configure(bg="#000000")
janela.bind("<Control-Alt-Shift-F12>", abrir_admin)

try:
    janela.iconbitmap("images/logo.ico")
except Exception as e:
    print("ERRO FAVICON:", e)


def centralizar(j, w=1000, h=700):
    j.update_idletasks()
    x = (j.winfo_screenwidth() // 2) - (w // 2)
    y = (j.winfo_screenheight() // 2) - (h // 2)
    j.geometry(f"{w}x{h}+{x}+{y}")


rodando = False
modo_operacao = "manual"
valor_inicial = 2.0
valor_atual = valor_inicial
gale_atual = 0
gale_max = 2
info_label = None
wins = 0
loss = 0
lucro_total = 0
ultimo_lucro_mostrado = None
operando = False
saldo_anterior = None
ultimo_sinal = None
ultima_vela_analisada = None


def _draw_rounded_rect(canvas, x1, y1, x2, y2, raio, cor, tag):
    """Desenha retÃ¢ngulo arredondado no canvas."""
    r = raio
    canvas.create_arc(
        (x1, y1, x1 + r * 2, y1 + r * 2),
        start=90,
        extent=90,
        fill=cor,
        outline=cor,
        tags=tag,
    )
    canvas.create_arc(
        (x2 - r * 2, y1, x2, y1 + r * 2),
        start=0,
        extent=90,
        fill=cor,
        outline=cor,
        tags=tag,
    )
    canvas.create_arc(
        (x1, y2 - r * 2, x1 + r * 2, y2),
        start=180,
        extent=90,
        fill=cor,
        outline=cor,
        tags=tag,
    )
    canvas.create_arc(
        (x2 - r * 2, y2 - r * 2, x2, y2),
        start=270,
        extent=90,
        fill=cor,
        outline=cor,
        tags=tag,
    )
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=cor, outline=cor, tags=tag)
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=cor, outline=cor, tags=tag)


def criar_card(parent, cor="#0f1620", raio=8, borda_cor=None, borda_esp=2):
    canvas = tk.Canvas(parent, bg=parent.cget("bg"), highlightthickness=0)
    frame = tk.Frame(canvas, bg=cor)
    window_id = canvas.create_window((0, 0), window=frame, anchor="nw")

    def desenhar(event):
        canvas.delete("bg")
        w = event.width
        h = event.height
        if borda_cor:
            _draw_rounded_rect(canvas, 0, 0, w, h, raio, borda_cor, "bg")
            b = borda_esp
            _draw_rounded_rect(canvas, b, b, w - b, h - b, max(raio - b, 2), cor, "bg")
            canvas.coords(window_id, b, b)
            canvas.itemconfig(window_id, width=w - b * 2, height=h - b * 2)
        else:
            _draw_rounded_rect(canvas, 0, 0, w, h, raio, cor, "bg")
            canvas.coords(window_id, 0, 0)
            canvas.itemconfig(window_id, width=w, height=h)
        canvas.tag_raise(window_id)

    canvas.bind("<Configure>", desenhar)
    return canvas, frame


def criar_box_info(parent, titulo, valor, cor_topo, cor_texto):
    raio = 8
    canvas = tk.Canvas(parent, highlightthickness=0, bg=parent.cget("bg"))
    canvas.config(width=120, height=60)
    frame = tk.Frame(canvas, bg="#000000")
    window_id = canvas.create_window((0, 0), window=frame, anchor="nw")
    frame.config(width=120, height=60)
    frame.pack_propagate(False)

    topo = tk.Frame(frame, bg=cor_topo, height=20)
    topo.pack(fill="x")
    tk.Label(
        topo, text=titulo, bg=cor_topo, fg="white", font=("Arial", 8, "bold")
    ).pack()
    corpo = tk.Frame(frame, bg="#000000")
    corpo.pack(fill="both", expand=True)
    lbl = tk.Label(
        corpo, text=valor, bg="#000000", fg=cor_texto, font=("Arial", 10, "bold")
    )
    lbl.pack(expand=True, fill="both")

    def desenhar(event=None):
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 2 or h < 2:
            return
        canvas.delete("bg")
        cor = "#000000"
        canvas.create_arc(
            (0, 0, raio * 2, raio * 2),
            start=90,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_arc(
            (w - raio * 2, 0, w, raio * 2),
            start=0,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_arc(
            (0, h - raio * 2, raio * 2, h),
            start=180,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_arc(
            (w - raio * 2, h - raio * 2, w, h),
            start=270,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_rectangle(raio, 0, w - raio, h, fill=cor, outline=cor, tags="bg")
        canvas.create_rectangle(0, raio, w, h - raio, fill=cor, outline=cor, tags="bg")
        canvas.coords(window_id, 0, 0)
        canvas.itemconfig(window_id, width=w, height=h)

    canvas.bind("<Configure>", desenhar)
    return canvas, lbl


def criar_rounded_btn(
    parent,
    text,
    bg_cor,
    fg_cor,
    font_tuple,
    width=None,
    height=None,
    padx=0,
    pady=0,
    cursor="hand2",
):
    raio = 8
    canvas = tk.Canvas(parent, highlightthickness=0, bg=parent.cget("bg"))
    if width and height:
        canvas.config(width=width, height=height)

    lbl = tk.Label(
        canvas, text=text, bg=bg_cor, fg=fg_cor, font=font_tuple, cursor=cursor
    )
    window_id = canvas.create_window((0, 0), window=lbl, anchor="nw")

    def desenhar(event=None):
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 2 or h < 2:
            return
        canvas.delete("bg")
        cor = lbl.cget("bg")
        canvas.create_arc(
            (0, 0, raio * 2, raio * 2),
            start=90,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_arc(
            (w - raio * 2, 0, w, raio * 2),
            start=0,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_arc(
            (0, h - raio * 2, raio * 2, h),
            start=180,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_arc(
            (w - raio * 2, h - raio * 2, w, h),
            start=270,
            extent=90,
            fill=cor,
            outline=cor,
            tags="bg",
        )
        canvas.create_rectangle(raio, 0, w - raio, h, fill=cor, outline=cor, tags="bg")
        canvas.create_rectangle(0, raio, w, h - raio, fill=cor, outline=cor, tags="bg")
        canvas.coords(window_id, 0, 0)
        canvas.itemconfig(window_id, width=w, height=h)

    canvas.bind("<Configure>", desenhar)
    lbl._canvas = canvas
    lbl._desenhar = desenhar
    return canvas, lbl


def gerar_sinal():
    return random.choice(["CALL", "PUT"])


def fazer_entrada(par, valor, direcao):
    global Iq, operando, ultimo_saldo_operacao

    if operando:
        return

    try:
        if not Iq:
            janela.after(0, escrever_log, log, "IQ desconectado", "info")
            return

        operando = True

        def executar_entrada():
            global operando, ultimo_saldo_operacao

            try:
                # salva saldo antes
                try:
                    ultimo_saldo_operacao = safe_iq_call(
                        lambda: Iq.get_balance(), timeout=3, name="get_balance"
                    )
                except Exception as e:
                    print(f"ERRO SALDO OPERAÇÃO: {e}")
                    ultimo_saldo_operacao = None

                timeframe = 1  # M1

                res = safe_iq_call(
                    lambda: Iq.buy(valor, par, direcao, timeframe),
                    timeout=5,
                    name="buy",
                )

                if isinstance(res, tuple):
                    status, id_op = res
                else:
                    status = False
                    id_op = None

                if status:
                    janela.after(
                        0,
                        escrever_log,
                        log,
                        f"ENTRADA {direcao.upper()} R${valor:.2f}",
                        "info",
                    )

                    # chama resultado automático
                    acompanhar_resultado(id_op)

                else:
                    operando = False
                    janela.after(0, escrever_log, log, "ERRO AO ENTRAR", "info")

            except Exception as e:
                operando = False
                janela.after(0, escrever_log, log, f"ERRO ENTRADA: {e}", "info")

        threading.Thread(target=executar_entrada, daemon=True).start()

    except Exception as e:
        operando = False
        janela.after(0, escrever_log, log, f"ERRO ENTRADA: {e}", "info")


def acompanhar_resultado(id_op):
    def verificar():
        global operando, valor_atual, valor_inicial, gale_atual, gale_max
        global ids_resultado_processados
        global wins, loss, lucro_total, ultimo_sinal, candles, catalogo

        # BLOQUEIA DUPLICADO
        if id_op in ids_resultado_processados:
            return

        ids_resultado_processados.add(id_op)

        # ATUALIZA RESULTADO GLOBAL
        def atualizar_resultado(lucro):
            global wins, loss, lucro_total

            with data_lock:
                lucro_total += lucro
                if lucro > 0:
                    wins += 1
                else:
                    loss += 1

            print("RESULTADO ATUALIZADO:", lucro_total, wins, loss)

            janela.after(0, atualizar_painel)

        try:
            if not Iq:
                janela.after(0, escrever_log, log, "IQ desconectado", "info")
                operando = False
                return

            lucro = 0  # seguranÃ§a

            # Espera 55s antes de checar (operação M1 = 60s)
            # Sem isso, check_win_v3 fica dando timeout 60x e entope a fila
            time.sleep(55)

            # pega resultado IQ (agora a operaÃ§Ã£o jÃ¡ expirou ou estÃ¡ perto)
            inicio = time.time()

            while True:
                resultado = safe_iq_call(
                    lambda: Iq.check_win_v3(id_op), timeout=8, name="check_win_v3"
                )

                if resultado is not None:
                    break

                if time.time() - inicio > 60:
                    print("Timeout check_win")
                    operando = False
                    return

                time.sleep(3)

            # calcula lucro
            if isinstance(resultado, tuple):
                status, valor = resultado
                if not status or valor is None:
                    operando = False
                    return
                lucro = float(valor)
            else:
                lucro = float(resultado)

            lucro = round(lucro, 2)

            print("RESULTADO REAL:", lucro)

            atualizar_resultado(lucro)

            # APRENDIZADO (CATÁLOGO)
            padrao = obter_padrao(candles)

            print("DEBUG PADRÃO:", padrao)
            print("DEBUG SINAL:", ultimo_sinal)

            if padrao:
                if padrao not in catalogo:
                    catalogo[padrao] = {"CALL": 0, "PUT": 0}

                if lucro > 0:
                    if ultimo_sinal == "CALL":
                        catalogo[padrao]["CALL"] += 1
                    elif ultimo_sinal == "PUT":
                        catalogo[padrao]["PUT"] += 1

                elif lucro < 0:
                    if ultimo_sinal == "CALL":
                        catalogo[padrao]["PUT"] += 1
                    elif ultimo_sinal == "PUT":
                        catalogo[padrao]["CALL"] += 1

                print("CATÁLOGO:", catalogo.get(padrao))

                # log + gale
                if lucro > 0:
                    msg = f"GANHO +R${lucro:.2f}"
                    janela.after(0, lambda m=msg: escrever_log(log, m, "win"))
                salvar_historico(msg)
                valor_atual = valor_inicial
                gale_atual = 0

            elif lucro < 0:
                msg = f"PERDA R${lucro:.2f}"
                janela.after(0, lambda m=msg: escrever_log(log, m, "loss"))
                salvar_historico(msg)

                if gale_atual < gale_max:
                    gale_atual += 1
                    valor_atual = valor_atual * 2.2
                    janela.after(
                        0,
                        escrever_log,
                        log,
                        f"GALE {gale_atual}/{gale_max} -> R${valor_atual:.2f}",
                        "info",
                    )
                else:
                    valor_atual = valor_inicial
                    gale_atual = 0

            if verificar_stop():
                operando = False
                janela.after(0, atualizar_painel)
                return

            operando = False
            janela.after(0, atualizar_painel)

        except Exception as e:
            janela.after(0, escrever_log, log, f"ERRO RESULTADO: {e}", "info")
            operando = False

    threading.Thread(target=verificar, daemon=True).start()


def monitor_manual():
    def executar():
        global Iq, ids_processados, ultimo_detectado, ids_manual_processados

        if len(ids_processados) > 500:
            ids_processados.clear()

        try:
            if not Iq:
                return

            abertas = safe_iq_call(
                lambda: Iq.get_option_open_by_other_pc(),
                timeout=3,
                name="get_option_open_by_other_pc",
            )

            # CORRETO:
            if abertas:
                ultimo_detectado = True
            else:
                ultimo_detectado = False

            if isinstance(abertas, dict):
                for op_id in list(abertas.keys()):
                    if modo_operacao == "auto":
                        continue

                    op_data = abertas[op_id]
                    if not isinstance(op_data, dict):
                        continue
                    msg = op_data.get("msg")
                    if not isinstance(msg, dict):
                        continue

                    op_id_real = msg.get("id")
                    if not op_id_real:
                        continue

                    op_id_str = str(op_id_real)

                    if op_id_str in ids_processados:
                        continue
                    ids_processados.add(op_id_str)

                    direcao = msg.get("dir", "N/A")
                    valor = msg.get("sum", "N/A")
                    ativo = msg.get("active", "N/A")

                    janela.after(
                        0,
                        escrever_log,
                        log,
                        f"Operação {direcao.upper()} | R${valor} | {ativo}",
                        "info",
                    )
                    janela.after(0, lambda i=op_id_str: acompanhar_manual(i))

        except Exception as e:
            janela.after(0, escrever_log, log, f"ERRO monitor_manual: {e}", "info")

    threading.Thread(target=executar, daemon=True).start()
    janela.after(3000, monitor_manual)


def acompanhar_manual(op_id):
    global threads_rodando, ids_resultado_processados
    global wins, loss, lucro_total

    if op_id in ids_resultado_processados:
        return

    with threads_lock:
        if threads_rodando >= MAX_THREADS:
            janela.after(500, lambda: acompanhar_manual(op_id))
            return
        threads_rodando += 1

    def worker():
        global threads_rodando
        global wins, loss, lucro_total
        global ids_resultado_processados

        # robô ativo = não duplica resultado
        if modo_operacao == "auto":
            return

        try:
            # evita duplicar resultado
            if op_id in ids_resultado_processados:
                return

            ids_resultado_processados.add(op_id)

            # saldo inicial
            try:
                saldo_inicial = safe_iq_call(
                    lambda: Iq.get_balance(), timeout=3, name="get_balance"
                )
            except Exception:
                saldo_inicial = None

            if saldo_inicial is None:
                return

            # espera tempo da operação (OTIMIZADO)
            for _ in range(61):  # ~61 segundos (nÃ£o trava seco)
                time.sleep(1)

            # pegar saldo final (mais rápido)
            saldo_final = None
            for _ in range(5):
                try:
                    saldo_final = safe_iq_call(
                        lambda: Iq.get_balance(), timeout=2, name="get_balance"
                    )
                    if saldo_final is not None:
                        break
                except Exception:
                    pass
                time.sleep(1)

            if saldo_final is None:
                return

            # cálculo lucro
            lucro = round(saldo_final - saldo_inicial, 2)

            # evita duplicação invisível
            if lucro == 0:
                return

            # resultado
            with data_lock:
                if lucro > 0:
                    wins += 1
                    texto = f"GANHO +R${lucro:.2f}"
                    janela.after(0, escrever_log, log, texto, "win")
                else:
                    loss += 1
                    texto = f"PERDA R${lucro:.2f}"
                    janela.after(0, escrever_log, log, texto, "loss")

                # soma só UMA vez
                lucro_total += lucro

            salvar_historico(texto)

            # atualiza painel 1x só
            janela.after(0, atualizar_painel)

        except Exception as e:
            janela.after(0, escrever_log, log, f"ERRO WORKER: {e}", "info")

        finally:
            global threads_rodando
            with threads_lock:
                threads_rodando = max(0, threads_rodando - 1)

    # SEMPRE thread separada, nunca bloqueia UI
    threading.Thread(target=worker, daemon=True).start()


def verificar_stop():
    global lucro_total, rodando, modo_operacao, operando
    global stop_ativo, tipo_stop

    try:
        gain_txt = entry_gain.get().replace(",", ".").strip()
        loss_txt = entry_loss.get().replace(",", ".").strip()
        gain = float(gain_txt) if gain_txt else 0
        loss = float(loss_txt) if loss_txt else 0

        if stop_ativo:
            return True

        if gain > 0 and lucro_total >= gain:
            stop_ativo = True
            tipo_stop = "gain"
            rodando = False
            operando = False
            modo_operacao = "manual"
            mostrar_alerta_stop("gain")
            lbl_modo.config(text="META BATIDA", fg="#ffd600")
            lbl_on_status.itemconfig("dot", fill="#ff3333", outline="#ff3333")
            lbl_on_status.itemconfig("dot_text", text="OFF")
            escrever_log(log, f"STOP GAIN atingido (+R${lucro_total:.2f})", "win")
            return True

        if loss > 0 and lucro_total <= -loss:
            stop_ativo = True
            tipo_stop = "loss"
            rodando = False
            operando = False
            modo_operacao = "manual"
            lbl_modo.config(text="STOP LOSS", fg="#ff5252")
            lbl_on_status.itemconfig("dot", fill="#ff3333", outline="#ff3333")
            lbl_on_status.itemconfig("dot_text", text="OFF")
            mostrar_alerta_stop("loss")
            escrever_log(log, f"STOP LOSS atingido (R${lucro_total:.2f})", "loss")
            return True

    except Exception as e:
        escrever_log(log, f"ERRO STOP: {e}", "info")

    return False


def verificar_reset_diario():
    global data_atual, lucro_total, stop_ativo, tipo_stop
    try:
        hoje = datetime.date.today()
        if data_atual is None:
            data_atual = hoje
            return
        if hoje != data_atual:
            data_atual = hoje
            lucro_total = 0
            stop_ativo = False
            tipo_stop = None
            escrever_log(log, "NOVO DIA - reset automático", "info")
            try:
                lbl_modo.config(text="AUTO LIBERADO", fg="#00e676")
                lbl_on_status.itemconfig("dot", fill="#00e676", outline="#00e676")
                lbl_on_status.itemconfig("dot_text", text="ON")
            except:
                pass
            atualizar_painel()
    except Exception as e:
        escrever_log(log, f"ERRO RESET DIÃRIO: {e}", "info")


def loop_reset_diario():
    verificar_reset_diario()
    janela.after(60000, loop_reset_diario)


def reset_meia_noite():
    global lucro_total, stop_ativo, tipo_stop, data_atual
    try:
        lucro_total = 0
        stop_ativo = False
        tipo_stop = None
        data_atual = datetime.date.today()
        escrever_log(log, "RESET AUTOMÁTICO 00:00", "info")
        try:
            lbl_modo.config(text="NOVO DIA", fg="#00e676")
            lbl_on_status.itemconfig("dot", fill="#00e676", outline="#00e676")
            lbl_on_status.itemconfig("dot_text", text="ON")
        except:
            pass
        atualizar_painel()
    except Exception as e:
        escrever_log(log, f"ERRO RESET 00:00: {e}", "info")
    agendar_reset_meia_noite()


def agendar_reset_meia_noite():
    try:
        agora = datetime.datetime.now()
        amanha = agora + datetime.timedelta(days=1)
        meia_noite = datetime.datetime(amanha.year, amanha.month, amanha.day, 0, 0, 0)
        segundos = (meia_noite - agora).total_seconds()
        ms = int(segundos * 1000)
        print(f"Reset em {int(segundos)} segundos")
        janela.after(ms, reset_meia_noite)
    except Exception as e:
        escrever_log(log, f"ERRO AGENDAR RESET: {e}", "info")


def atualizar_contador_reset():
    global lbl_reset
    try:
        agora = datetime.datetime.now()
        amanha = agora + datetime.timedelta(days=1)
        meia_noite = datetime.datetime(amanha.year, amanha.month, amanha.day, 0, 0, 0)
        restante = meia_noite - agora
        total_segundos = int(restante.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        texto = f"Reset\n{horas:02d}:{minutos:02d}:{segundos:02d}"
        cor = "#ff5252" if total_segundos <= 60 else "#aaaaaa"
        if lbl_reset:
            lbl_reset.config(text=texto, fg=cor)
    except Exception as e:
        print("ERRO contador:", e)
    janela.after(1000, atualizar_contador_reset)


def atualizar_barra_meta():
    global barra_meta, lbl_meta, lucro_total
    try:
        barra_meta.delete("all")
        largura = barra_meta.winfo_width()
        if largura <= 1:
            barra_meta.after(100, atualizar_barra_meta)
            return
        gain_txt = entry_gain.get().replace(",", ".").strip()
        loss_txt = entry_loss.get().replace(",", ".").strip()
        gain = float(gain_txt) if gain_txt else 0
        loss = float(loss_txt) if loss_txt else 0

        if gain > 0:
            progresso_gain = max(0, min(lucro_total / gain, 1))
            falta_gain = max(gain - lucro_total, 0)
        else:
            progresso_gain = 0
            falta_gain = 0

        if loss > 0:
            progresso_loss = max(0, min(abs(lucro_total) / loss, 1))
            falta_loss = max(loss - abs(lucro_total), 0)
        else:
            progresso_loss = 0
            falta_loss = 0

        if lucro_total >= 0:
            progresso = progresso_gain
            cor = "#00ff88"
            texto = f"Gain: {int(progresso_gain*100)}% | Falta: R$ {falta_gain:.2f}"
        else:
            progresso = progresso_loss
            cor = "#ff4d4d"
            texto = f"Loss: {int(progresso_loss*100)}% | Falta: R$ {falta_loss:.2f}"

        largura_preenchida = int(largura * progresso)
        barra_meta.create_rectangle(0, 0, largura_preenchida, 10, fill=cor, outline="")
        if lbl_meta:
            lbl_meta.config(text=texto, fg=cor)
    except Exception as e:
        print("ERRO barra:", e)
    janela.after(1000, atualizar_barra_meta)


def mostrar_alerta_stop(tipo):
    try:
        if tipo == "loss":
            texto = "STOP LOSS ATINGIDO"
            cor = "#ff5252"
        else:
            texto = "META ATINGIDA"
            cor = "#ffd600"

        # Tenta usar overlay global seguro: verifica via globals() para evitar NameError
        try:
            frame = globals().get("frame_alerta_stop")
            lbl = globals().get("lbl_alerta_stop")
            if frame is not None and lbl is not None:
                try:
                    lbl.config(text=texto, fg=cor)
                    frame.lift()

                    def esconder():
                        try:
                            frame.lower()
                        except Exception:
                            pass

                    janela.after(4000, esconder)
                    return
                except Exception:
                    # se falhar ao usar o overlay, tentamos recriá-lo abaixo
                    pass
        except Exception:
            pass

        # Tenta criar o overlay global se não existir (mais robusto que fallback imediato)
        try:
            if globals().get("frame_alerta_stop") is None:
                f = tk.Frame(janela, bg="#000000")
                f.place(relx=0, rely=0, relwidth=1, relheight=1)
                f.lower()
                l = tk.Label(
                    f,
                    text=texto,
                    bg="#000000",
                    fg=cor,
                    font=("Segoe UI Black", 40, "bold"),
                )
                l.pack(expand=True)
                globals()["frame_alerta_stop"] = f
                globals()["lbl_alerta_stop"] = l
                f.lift()

                def esconder2():
                    try:
                        f.lower()
                    except Exception:
                        pass

                janela.after(4000, esconder2)
                return
        except Exception:
            pass

        # fallback mínimo: label simples no topo
        alerta = tk.Label(
            janela,
            text=texto,
            bg="#000000",
            fg=cor,
            font=("Segoe UI Black", 14),
            pady=5,
        )

        alerta.place(relx=0.5, y=10, anchor="n")

        janela.after(
            4000, lambda: (alerta.destroy() if alerta.winfo_exists() else None)
        )

    except Exception:
        traceback.print_exc()


def garantir_conexao():
    global Iq, ultima_verificacao
    try:
        agora = time.time()
        if agora - ultima_verificacao < 30:
            return
        ultima_verificacao = agora

        def verificar_conexao():
            try:
                if not Iq:
                    return
                conectado = safe_iq_call(
                    lambda: Iq.check_connect(), timeout=2, name="check_connect"
                )
                if not conectado:
                    janela.after(0, escrever_log, log, "Reconectando...", "info")
                    safe_iq_call(lambda: Iq.connect(), timeout=4, name="connect")
                    time.sleep(0.5)
                    if safe_iq_call(
                        lambda: Iq.check_connect(), timeout=2, name="check_connect"
                    ):
                        janela.after(0, escrever_log, log, "Reconectado", "info")
                        try:
                            safe_iq_call(
                                lambda: Iq.start_candles_stream(par_var.get(), 60, 10),
                                timeout=3,
                                name="start_candles_stream",
                            )
                        except Exception:
                            pass
                        janela.after(4000, alerta.destroy)
                        janela.after(0, escrever_log, log, "Falha", "info")
            except Exception as e:
                janela.after(0, escrever_log, log, f"ERRO: {e}", "info")

        threading.Thread(target=verificar_conexao, daemon=True).start()
    except Exception as e:
        janela.after(0, escrever_log, log, f"ERRO RECONEXÃƒO: {e}", "info")


def loop_conexao():
    try:
        garantir_conexao()
    except Exception as e:
        janela.after(0, escrever_log, log, f"ERRO LOOP CONEXÃƒO: {e}", "info")
    janela.after(5000, loop_conexao)


def atualizar_saldo_cache():
    global ultimo_saldo, ultimo_update_saldo

    try:
        agora = time.time()
        if agora - ultimo_update_saldo < 3:
            return

        ultimo_update_saldo = agora

        def pegar_saldo():
            try:
                if not Iq:
                    return
                saldo = safe_iq_call(
                    lambda: Iq.get_balance(), timeout=3, name="get_balance"
                )
                if saldo is None or not isinstance(saldo, (int, float)) or saldo < 0:
                    return
                global ultimo_saldo, saldo_cache
                ultimo_saldo = saldo
                tipo = modo.get() if modo else "demo"
                saldo_cache[tipo] = saldo
                janela.after(0, lambda: atualizar_saldo(saldo))
            except Exception as e:
                janela.after(0, escrever_log, log, f"ERRO SALDO: {e}", "info")

        threading.Thread(target=pegar_saldo, daemon=True).start()

    except Exception as e:
        janela.after(0, escrever_log, log, f"ERRO CACHE: {e}", "info")


def loop_saldo():
    try:
        atualizar_saldo_cache()
    except Exception as e:
        janela.after(0, escrever_log, log, f"ERRO LOOP SALDO: {e}", "info")
    janela.after(3000, loop_saldo)


def atualizar_painel():
    global lucro_total, ultimo_lucro_mostrado

    if ultimo_lucro_mostrado != lucro_total:
        print("ATUALIZANDO UI REAL:", lucro_total)
    ultimo_lucro_mostrado = lucro_total  # â† DEPOIS

    try:
        if box_win is not None and box_loss is not None:
            box_win.config(text=f"Wins\n{wins}")
            box_loss.config(text=f"Loss\n{loss}")
    except Exception as e:
        print("ERRO BOX:", e)

    try:
        valor = (
            f"R$ {lucro_total:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        cor = (
            "#00ff88"
            if lucro_total > 0
            else "#ff4d4d" if lucro_total < 0 else "#ffffff"
        )
        if lbl_lucro:
            lbl_lucro.config(text=valor, fg=cor)
    except Exception as e:
        print("ERRO LUCRO:", e)

    try:
        if ultimo_saldo is not None:
            atualizar_saldo(ultimo_saldo)
    except Exception as e:
        janela.after(0, escrever_log, log, f"ERRO SALDO UI: {e}", "info")


ultimo_id = None


def trocar_conta():
    global Iq, modo, ultimo_update_saldo, saldo_cache

    if not Iq:
        janela.after(0, escrever_log, log, "IQ desconectado", "info")
        return

    if modo is None:
        janela.after(0, escrever_log, log, "Modo não definido", "info")
        return

    ultimo_update_saldo = 0
    tipo = modo.get() if hasattr(modo, "get") else "demo"

    # Mostrar saldo cache instantaneamente
    cached = saldo_cache.get(tipo)
    if cached is not None:
        janela.after(0, lambda: atualizar_saldo(cached))

    def executar():
        global saldo_cache
        try:
            if tipo == "demo":
                Iq.change_balance("PRACTICE")
                janela.after(0, escrever_log, log, "DEMO", "info")
            else:
                Iq.change_balance("REAL")
                janela.after(0, escrever_log, log, "REAL", "info")

            try:
                saldo = Iq.get_balance()
                if saldo is not None:
                    saldo_cache[tipo] = saldo
                    janela.after(0, escrever_log, log, f"SALDO: R${saldo:.2f}", "info")
                    janela.after(0, lambda: atualizar_saldo(saldo))
            except Exception as e:
                janela.after(0, escrever_log, log, f"ERRO SALDO: {e}", "info")
        except Exception as e:
            janela.after(0, escrever_log, log, f"ERRO TROCAR CONTA: {e}", "info")

    threading.Thread(target=executar, daemon=True).start()


ultimo_server_time = None
_server_sync_local = None  # perf_counter no momento da sincronizaÃ§Ã£o


def montar_painel():
    global lbl_saldo, lbl_timer, lbl_lucro, lbl_resultado
    global box_win, box_loss, log
    global entrada_var, par_var, timeframe_var, estrategia_var, radio_var
    global ultimo_server_time

    entrada_var = tk.StringVar(value="MÃ£o Fixa")
    par_var = tk.StringVar(value="EURUSD-OTC")
    timeframe_var = tk.StringVar(value="M1")
    estrategia_var = tk.StringVar(value="M1-MHI")
    radio_var = tk.StringVar(value="entrada")

    box_entrada = tk.Frame(janela, bg="#0f141a")
    box_entrada.pack()

    lbl_timer = tk.Label(box_entrada, text="00:00", fg="black", font=("Arial", 1))
    lbl_timer.pack()
    lbl_timer.pack_forget()

    atualizar_timer()
    atualizar_hora()

    menu = tk.Frame(janela, bg="#0a0f14", width=60)
    menu.pack(side="left", fill="y")
    menu.pack_propagate(False)

    topo = tk.Frame(menu, bg="#0a0f14")
    topo.pack(side="top", fill="x")

    try:
        avatar_img = criar_avatar_circular("images/avatar.png", 50)
        avatar = tk.Label(topo, image=avatar_img, bg="#0a0f14")
        avatar.image = avatar_img
    except Exception as e:
        print("ERRO AVATAR:", e)
        avatar = tk.Label(topo, text="Usuário", bg="#0a0f14", fg="white")

    avatar.pack(pady=15)

    meio = tk.Frame(menu, bg="#0a0f14")
    meio.pack(expand=True)

    baixo = tk.Frame(menu, bg="#0a0f14", height=60)
    baixo.pack(side="bottom", fill="x", pady=3)
    baixo.pack_propagate(False)

    def criar_botao_menu(parent, texto, comando=None):
        frame = tk.Frame(parent, bg="#0a0f14", width=70, height=70)
        frame.pack(fill="x", pady=8)
        frame.pack_propagate(False)
        borda = tk.Frame(frame, bg="#0a0f14")
        borda.place(relx=0.5, rely=0.5, anchor="center", width=30, height=30)
        lbl = tk.Label(
            borda,
            text=texto,
            bg="#0a0f14",
            fg="#9ca3af",
            font=("Segoe UI Emoji", 18),
            cursor="hand2",
        )
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        def entrar(e):
            borda.config(bg="#072A3F")
            frame.config(bg="#111827")
            lbl.config(bg="#111827", fg="#00e676")

        def sair(e):
            borda.config(bg="#0a0f14")
            frame.config(bg="#0a0f14")
            lbl.config(bg="#0a0f14", fg="#9ca3af")

        def clicar(e):
            borda.config(bg="#00e676")
            lbl.config(fg="#0a0f14")
            frame.after(120, lambda: lbl.config(fg="#00e676"))
            frame.after(120, lambda: borda.config(bg="#111827"))
            if comando:
                comando()

        for w in (frame, lbl, borda):
            w.bind("<Enter>", entrar)
            w.bind("<Leave>", sair)
            w.bind("<Button-1>", clicar)

        return frame

    criar_botao_menu(meio, "Início", lambda: escrever_log(log, "Tela inicial", "info"))
    criar_botao_menu(meio, "Mercado", lambda: abrir_mercado(janela))
    criar_botao_menu(meio, "Controle", lambda: abrir_controle(janela))
    criar_botao_menu(meio, "Config", lambda: abrir_config(janela))

    btn_sair = tk.Label(
        baixo,
        text="Sair",
        bg="#0a0f14",
        fg="#ef4444",
        font=("Arial", 12, "bold"),
        cursor="hand2",
    )
    btn_sair.pack(pady=15)
    btn_sair.bind("<Enter>", lambda e: btn_sair.config(bg="#111827"))
    btn_sair.bind("<Leave>", lambda e: btn_sair.config(bg="#0a0f14"))
    btn_sair.bind("<Button-1>", lambda e: janela.destroy())

    tk.Frame(janela, bg="#1e293b", width=1).pack(side="left", fill="y")

    main = tk.Frame(janela, bg="#0b0f14")
    main.pack(side="left", fill="both", expand=True)

    header = tk.Frame(main, bg="#0b0f14")
    header.pack(fill="x", padx=10, pady=5)

    linha1 = tk.Frame(header, bg="#0b0f14")
    linha1.pack(fill="x")

    tk.Label(
        linha1,
        text="DWOB - MHI EVO",
        fg="white",
        bg="#0b0f14",
        font=("Arial", 10, "bold"),
    ).pack(side="left")

    tk.Label(
        linha1,
        text="RobÃ´ de MHI",
        fg="#6b7280",
        bg="#0b0f14",
        font=("Arial", 8),
    ).pack(side="left", padx=(5, 0))

    lbl_estrategia_header = tk.Label(
        linha1,
        text="I ESTRATÃ‰GIA MHI",
        fg="white",
        bg="#0b0f14",
        font=("Arial", 9, "bold"),
    )
    lbl_estrategia_header.pack(side="right", padx=5)

    global lbl_modo
    lbl_modo = tk.Label(linha1, text="", fg="#ff5252", bg="#0b0f14", font=("Arial", 1))

    def carregar_flag(nome):
        try:
            caminho = os.path.join("images", nome)
            img = Image.open(caminho).resize((20, 20))
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print("ERRO FLAG:", e)
            return None

    flag_br = carregar_flag("brasil.png")
    flag_es = carregar_flag("espanha.png")
    flag_us = carregar_flag("usa.png")

    frame_right = tk.Frame(linha1, bg="#0b0f14")
    frame_right.pack(side="right", padx=5)

    global lbl_on_status
    on_canvas = tk.Canvas(
        frame_right, width=24, height=24, bg="#0b0f14", highlightthickness=0
    )
    on_canvas.pack(side="left", padx=(0, 6))
    on_canvas.create_oval(1, 1, 23, 23, fill="#ff3333", outline="#ff3333", tags="dot")
    on_canvas.create_text(
        12, 12, text="OFF", fill="black", font=("Arial", 5, "bold"), tags="dot_text"
    )
    lbl_on_status = on_canvas

    for flag in (flag_br, flag_es, flag_us):
        if flag:
            lbl = tk.Label(frame_right, image=flag, bg="#0b0f14")
            lbl.pack(side="left", padx=2)
            lbl.image = flag

    linha2 = tk.Frame(header, bg="#0b0f14")
    linha2.pack(fill="x", pady=5)

    global lbl_reset
    lbl_reset = tk.Label(
        linha2,
        text="Reset: --:--:--",
        bg="#0b0f14",
        fg="#aaaaaa",
        font=("Arial", 10, "bold"),
    )
    lbl_reset.pack(side="right", padx=10)

    global lbl_saldo, lbl_lucro, lbl_resultado

    box_saldo, lbl_saldo = criar_box_info(
        linha2, "Saldo atual", "R$ 0,00", "#0e4ba7", "#ff9800"
    )
    box_saldo.pack(side="left", padx=5)

    box_lucro, lbl_lucro = criar_box_info(
        linha2, "Lucro / Perda", "R$ 0,00", "#0e4ba7", "#ffffff"
    )
    box_lucro.pack(side="left", padx=5)

    lbl_resultado = tk.Label(
        linha2, text="", bg="#0f141a", fg="#ffffff", font=("Arial", 10, "bold")
    )
    lbl_resultado.pack(side="left", padx=5)

    global barra_meta, lbl_meta

    frame_meta = tk.Frame(main, bg="#0b0f14")
    frame_meta.pack(fill="x", padx=10, pady=5)

    lbl_meta = tk.Label(
        frame_meta,
        text="Meta: 0%",
        bg="#0b0f14",
        fg="#aaaaaa",
        font=("Arial", 9, "bold"),
    )
    lbl_meta.pack(anchor="w")

    barra_meta = tk.Canvas(frame_meta, height=10, bg="#1f2937", highlightthickness=0)
    barra_meta.pack(fill="x", pady=3)

    frame_modo = tk.Frame(linha2, bg="#0b0f14")
    frame_modo.pack(side="left", padx=10)

    global modo
    modo = tk.StringVar(value="demo")

    def selecionar_modo(tipo):
        global wins, loss, lucro_total, stop_ativo, tipo_stop
        global lucro_demo, lucro_real, wins_demo, wins_real, loss_demo, loss_real

        # â† salva estado atual antes de trocar
        if modo.get() == "demo":
            lucro_demo = lucro_total
            wins_demo = wins
            loss_demo = loss
        else:
            lucro_real = lucro_total
            wins_real = wins
            loss_real = loss

        # â† restaura estado da conta que vai entrar
        if tipo == "demo":
            lucro_total = lucro_demo
            wins = wins_demo
            loss = loss_demo
            btn_demo.config(bg="#ffd600", fg="black")
            btn_real.config(bg="#1f2937", fg="white")
            btn_demo._desenhar()
            btn_real._desenhar()
        else:
            lucro_total = lucro_real
            wins = wins_real
            loss = loss_real
            btn_real.config(bg="#00e676", fg="black")
            btn_demo.config(bg="#1f2937", fg="white")
            btn_real._desenhar()
            btn_demo._desenhar()

        modo.set(tipo)
        stop_ativo = False
        tipo_stop = None
        atualizar_painel()
        trocar_conta()

    btn_demo_canvas, btn_demo = criar_rounded_btn(
        frame_modo,
        " DEMO ",
        "#ffd600",
        "black",
        ("Arial", 10, "bold"),
        width=80,
        height=30,
    )
    btn_demo_canvas.pack(side="left", padx=5)
    btn_demo.bind("<Button-1>", lambda e: selecionar_modo("demo"))

    btn_real_canvas, btn_real = criar_rounded_btn(
        frame_modo,
        " REAL ",
        "#1f2937",
        "white",
        ("Arial", 10, "bold"),
        width=80,
        height=30,
    )
    btn_real_canvas.pack(side="left", padx=5)
    btn_real.bind("<Button-1>", lambda e: selecionar_modo("real"))

    trocar_conta()

    linha3 = tk.Frame(header, bg="#0b0f14")
    linha3.pack(fill="x", pady=5)

    global ocultar_saldo
    ocultar_saldo = tk.BooleanVar()

    def aplicar_ocultacao():
        try:
            if ocultar_saldo.get():
                if lbl_saldo:
                    lbl_saldo.config(text="R$ ****")
                if lbl_lucro:
                    lbl_lucro.config(text="R$ ****")
            else:
                if ultimo_saldo is not None:
                    atualizar_saldo(ultimo_saldo)
                atualizar_painel()
        except Exception as e:
            print("ERRO ocultar:", e)

    chk_ocultar = tk.Checkbutton(
        linha3,
        text="Ocultar saldo",
        variable=ocultar_saldo,
        command=aplicar_ocultacao,
        bg="#0b0f14",
        fg="white",
        selectcolor="#0b0f14",
        activebackground="#0b0f14",
        font=("Arial", 9),
    )
    chk_ocultar.pack(side="left", padx=10)

    btn_gain_canvas, btn_gain_lbl = criar_rounded_btn(
        linha3,
        " Stop Gain ",
        "#00c853",
        "black",
        ("Arial", 8, "bold"),
        width=80,
        height=22,
    )
    btn_gain_canvas.pack(side="left", padx=(10, 5))

    global entry_gain
    entry_gain = tk.Entry(
        linha3,
        width=8,
        bg="#1a1f27",
        fg="white",
        insertbackground="white",
        relief="flat",
    )
    entry_gain.pack(side="left", padx=5)
    entry_gain.insert(0, "0,00")

    btn_loss_canvas, btn_loss_lbl = criar_rounded_btn(
        linha3,
        " Stop Loss ",
        "#d50000",
        "white",
        ("Arial", 8, "bold"),
        width=80,
        height=22,
    )
    btn_loss_canvas.pack(side="left", padx=(10, 5))

    global entry_loss
    entry_loss = tk.Entry(
        linha3,
        width=8,
        bg="#1a1f27",
        fg="white",
        insertbackground="white",
        relief="flat",
    )
    entry_loss.pack(side="left", padx=5)
    entry_loss.insert(0, "0,00")

    card_entrada, box_entrada_inner = criar_card(
        linha2, "#0f141a", raio=12, borda_cor="#1e88e5", borda_esp=3
    )
    card_entrada.pack(side="right", padx=5)
    card_entrada.config(width=160, height=85)

    tk.Label(
        box_entrada_inner,
        text="PrÃ³xima entrada",
        bg="#0f141a",
        fg="white",
        font=("Arial", 9),
    ).pack(pady=(4, 0))

    lbl_timer = tk.Label(
        box_entrada_inner,
        text="00:00",
        bg="#0f141a",
        fg="white",
        font=("Arial", 20, "bold"),
    )
    lbl_timer.pack()

    global lbl_hora
    lbl_hora = tk.Label(
        box_entrada_inner, text="--:--", bg="#0f141a", fg="#aaaaaa", font=("Arial", 10)
    )
    lbl_hora.pack(pady=(0, 4))

    box_loss_canvas, box_loss = criar_rounded_btn(
        linha2,
        "Loss\n0",
        "#d50000",
        "white",
        ("Arial", 12, "bold"),
        width=70,
        height=55,
    )
    box_loss_canvas.pack(side="right", padx=5)

    box_win_canvas, box_win = criar_rounded_btn(
        linha2,
        "Wins\n0",
        "#00c853",
        "white",
        ("Arial", 12, "bold"),
        width=70,
        height=55,
    )
    box_win_canvas.pack(side="right", padx=5)

    # â”€â”€ Barra inferior (licenÃ§a + versÃ£o) â”€â”€
    barra_inferior = tk.Frame(main, bg="#0a0e13", height=24)
    barra_inferior.pack(side="bottom", fill="x")
    barra_inferior.pack_propagate(False)

    lbl_licenca = tk.Label(
        barra_inferior,
        text="LICENCIADO PARA deafwisdomtrade@gmail.com  |  @copy Deaf Wisdom OB",
        bg="#0a0e13",
        fg="#4b5563",
        font=("Arial", 7),
    )
    lbl_licenca.pack(side="left", padx=10)

    lbl_versao = tk.Label(
        barra_inferior,
        text="VersÃ£o 1.0.0",
        bg="#0a0e13",
        fg="#4b5563",
        font=("Arial", 7),
    )
    lbl_versao.pack(side="right", padx=10)

    container = tk.Frame(main, bg="#0b0f14")
    container.pack(fill="both", expand=True, padx=5, pady=5)
    container.grid_columnconfigure(0, weight=3)
    container.grid_columnconfigure(1, weight=6)
    container.grid_rowconfigure(0, weight=1)

    esq = tk.Frame(container, bg="#0b0f14")
    esq.grid(row=0, column=0, sticky="nsew")

    dir = tk.Frame(container, bg="#0b0f14")
    dir.grid(row=0, column=1, sticky="nsew")

    esq.grid_rowconfigure(0, weight=0)
    esq.grid_rowconfigure(1, weight=12)
    esq.grid_columnconfigure(0, weight=1)

    card, grafico = criar_card(esq, "#000000")  # Fundo preto puro
    card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    canvas = tk.Canvas(grafico, bg="#000000", highlightthickness=0)  # Fundo preto puro
    canvas.pack(fill="both", expand=True, pady=(8, 8))
    canvas.bind("<Button-1>", lambda e: None)
    canvas.bind("<B1-Motion>", lambda e: None)

    global candles
    candles = [
        [100, 140, 150, 90],
        [140, 110, 160, 100],
        [110, 170, 180, 105],
        [170, 130, 175, 120],
        [130, 150, 150, 150],
    ]

    def desenhar_tudo():
        global canvas_grid_desenhado
        altura = canvas.winfo_height()
        if altura < 50:
            altura = 250
        largura = canvas.winfo_width()

        # Fundo gradiente: topo azul marinho escuro, base preto puro
        canvas.delete("all")
        for i in range(altura):
            t = i / max(altura - 1, 1)
            # Topo: azul marinho escuro (#16203a), Base: preto puro (#000000)
            r = int(0x16 + (0x00 - 0x16) * t)
            g = int(0x20 + (0x00 - 0x20) * t)
            b = int(0x3A + (0x00 - 0x3A) * t)
            cor = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, largura, i, fill=cor, tags="bg")

        # Grid minimalista cinza
        for i in range(1, 4):
            y = i * altura // 4
            canvas.create_line(
                0,
                y,
                largura,
                y,
                fill="#353332",
                width=1,
                tags="grid",
            )
        for i in range(1, 4):
            xg = i * largura // 4
            canvas.create_line(
                xg,
                0,
                xg,
                altura,
                fill="#353332",
                width=1,
                tags="grid",
            )
        canvas.grid_desenhado = True

        # ðŸš€ LIMPA SÃ“ AS VELAS (nÃ£o toca grid)
        canvas.delete("candle", "linha", "preco")

        if not candles:
            return
        valores = [v for c in candles for v in c]
        if not valores:
            return

        min_val = min(valores)
        max_val = max(valores)
        if max_val == min_val:
            return

        ultimo = candles[-1]
        preco_atual = ultimo[1]
        y_preco = 20 + (max_val - preco_atual) / (max_val - min_val) * (altura - 40)

        # Caixa de preÃ§o estilo IQ Option
        cor_linha = "#ff9800"
        caixa_larg = 74
        caixa_alt = 22
        seta_larg = 12
        x_caixa = largura - caixa_larg - 8
        y1 = y_preco - caixa_alt // 2
        y2 = y_preco + caixa_alt // 2

        # Linha atÃ© a caixa (pontilhada)
        canvas.create_line(
            0,
            y_preco,
            x_caixa,
            y_preco,
            fill=cor_linha,
            width=2,
            dash=(3, 3),
            tags="linha",
        )

        # Caixa com seta
        pontos = [
            x_caixa,
            y1,
            x_caixa + caixa_larg - seta_larg,
            y1,
            x_caixa + caixa_larg,
            y_preco,
            x_caixa + caixa_larg - seta_larg,
            y2,
            x_caixa,
            y2,
        ]
        canvas.create_polygon(
            pontos,
            fill=cor_linha,
            outline="",
            tags="preco",
        )

        texto_preco = f"{preco_atual:.5f}"
        # Separar parte inteira e decimal final
        if "." in texto_preco:
            parte, decimal = texto_preco.split(".")
            decimal1 = decimal[:-2]
            decimal2 = decimal[-2:]
            texto1 = parte + "." + decimal1
            texto2 = decimal2
        else:
            texto1 = texto_preco
            texto2 = ""

        # Texto principal (Arial Narrow, sem negrito, mais prÃ³ximo da borda, cor preta)
        canvas.create_text(
            x_caixa + 10,
            y_preco,
            text=texto1,
            fill="#111",
            font=("Arial Narrow", 12),
            anchor="w",
            tags="preco",
        )
        # Texto final (Arial Narrow, menor, cor preta)
        canvas.create_text(
            x_caixa + 10 + 38,
            y_preco,
            text=texto2,
            fill="#111",
            font=("Arial Narrow", 14),
            anchor="w",
            tags="preco",
        )

        qtd = len(candles)
        espaco = 90
        largura_total = qtd * espaco
        x = (largura - largura_total) // 2

        for c in candles:
            abertura, fechamento, maxima, minima = c
            desenhar_candle(
                canvas, x, abertura, fechamento, maxima, minima, min_val, max_val
            )
            x += espaco

    # ðŸ”¥ CONTROLE GLOBAL (coloca lÃ¡ em cima do cÃ³digo)
    candle_thread_rodando = False

    def atualizar_candle_real():
        global candle_thread_rodando

        # ðŸš« evita mÃºltiplas threads
        if candle_thread_rodando:
            canvas.after(1000, atualizar_candle_real)  # ðŸ”¥ MUITO IMPORTANTE
            return

        def buscar():
            global candle_thread_rodando
            candle_thread_rodando = True

            try:
                if not Iq:
                    return

                par = par_var.get()
                novos = None

                try:
                    dados = safe_iq_call(
                        lambda: Iq.get_realtime_candles(par, 60),
                        timeout=3,
                        name="get_realtime_candles",
                    )
                except Exception:
                    dados = None

                if dados and isinstance(dados, dict):
                    lista = sorted(dados.values(), key=lambda x: x["from"])
                    if len(lista) >= 5:
                        novos = [
                            [v["open"], v["close"], v["max"], v["min"]]
                            for v in lista[-5:]
                        ]

                if not novos:
                    tf_map = {"M1": 60, "M5": 300, "M15": 900}
                    try:
                        tf_value = timeframe_var.get() if timeframe_var else "M1"
                        tf_seconds = tf_map.get(tf_value, 60)
                    except:
                        tf_seconds = 60
                    novos = pegar_candles_iq(par, tf_seconds, 5)

                if novos and len(novos) >= 5:

                    def atualizar():
                        global candles
                        candles[:] = novos
                        janela.after(1000, desenhar_tudo)

                    janela.after(0, atualizar)

            except Exception as e:
                janela.after(0, escrever_log, log, f"ERRO CANDLE: {e}", "info")

            finally:
                candle_thread_rodando = False

        # ðŸš€ cria thread (SEM check_connect)
        if Iq:
            threading.Thread(target=buscar, daemon=True).start()

        # ðŸ” LOOP SEMPRE CONTINUA (NUNCA PARA)
        canvas.after(1000, atualizar_candle_real)

    # ðŸš€ inicia o loop (mantÃ©m isso)
    canvas.after(1000, atualizar_candle_real)

    def redraw_delay(event):
        if canvas.winfo_width() > 100:
            canvas.after(200, desenhar_tudo)

    canvas.bind("<Configure>", redraw_delay)

    baixo_esq = tk.Frame(esq, bg="#0b0f14")
    baixo_esq.grid(row=1, column=0, sticky="nsew")
    baixo_esq.grid_rowconfigure(0, weight=1)
    baixo_esq.grid_columnconfigure(0, weight=1)
    baixo_esq.grid_columnconfigure(1, weight=1)

    card, log_box = criar_card(baixo_esq, "#0d0e0f")
    card.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    card.config(height=210)  # aumenta altura do bloco log

    log = scrolledtext.ScrolledText(
        log_box,
        bg="#000000",
        fg="#1d3c4b",
        insertbackground="white",
        font=("Consolas", 10),
        bd=0,
        relief="flat",
        highlightthickness=0,
        padx=6,
        pady=6,
        height=8,
    )
    log.pack(fill="both", expand=True)
    log.config(state="disabled", borderwidth=0)
    log.vbar.config(
        troughcolor="#0f141a", bg="#111827", activebackground="#1f2937", width=6
    )

    escrever_log(log, "Sistema iniciado...", "info")
    escrever_log(log, "Sistema pronto", "info")

    log.tag_config("win", foreground="#00ff88")
    log.tag_config("loss", foreground="#ff4d4d")
    log.tag_config("info", foreground="#7dd3fc")

    card, extra_box = criar_card(baixo_esq, "#000000")
    card.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
    card.config(height=210)  # aumenta altura do bloco aguardando

    global info_label
    info_label = tk.Label(
        extra_box,
        text="Aguardando",
        fg="#00e676",
        bg="#000000",
        font=("Segoe UI Black", 28),
    )
    info_label.pack(expand=True, fill="both")

    def atualizar_put_call():
        global candles, ultimo_sinal, gale_atual
        global rodando, operando, loop_auto_rodando
        global ultimo_candle_operado, ultimo_log_candle, info_label
        global ultimo_server_time

        if not loop_auto_rodando:
            return

        try:
            if modo_operacao != "auto" or not rodando:
                loop_auto_rodando = False
                return

            if not Iq or ultimo_server_time is None:
                janela.after(1000, atualizar_put_call)
                return

            agora = _get_server_now() or ultimo_server_time
            segundos = agora % 60
            candle_atual = agora // 60

            # ðŸ§  log sÃ³ 1x
            if candle_atual != ultimo_log_candle:
                ultimo_log_candle = candle_atual
                janela.after(0, escrever_log, log, "Nova vela", "info")

            # ðŸš« evita repetir entrada
            if candle_atual == ultimo_candle_operado:
                janela.after(1000, atualizar_put_call)
                return

            # â³ sÃ³ entra nos primeiros segundos
            if segundos > 1:
                janela.after(1000, atualizar_put_call)
                return

            if operando:
                janela.after(1000, atualizar_put_call)
                return

            direcao = None
            padrao = obter_padrao(candles)

            if padrao and len(padrao) == 5:
                if padrao in catalogo:
                    dados = catalogo[padrao]
                    total = dados["CALL"] + dados["PUT"]

                    if total >= 5:
                        if dados["CALL"] > dados["PUT"] * 1.3:
                            direcao = "call"
                        elif dados["PUT"] > dados["CALL"] * 1.3:
                            direcao = "put"

                if not direcao:
                    direcao = random.choice(["call", "put"])
            else:
                direcao = random.choice(["call", "put"])

            # â›” DOJI
            if candles:
                ultima = candles[-1]
                if ultima[0] == ultima[1]:
                    janela.after(1000, atualizar_put_call)
                    return

            # ðŸš€ ENTRADA
            if direcao:
                ultimo_candle_operado = candle_atual

                janela.after(0, escrever_log, log, f"{direcao.upper()}", "info")

                if direcao == "call":
                    ultimo_sinal = "CALL"
                    info_label.config(text="CALL ↑", fg="#00e676")
                else:
                    ultimo_sinal = "PUT"
                    info_label.config(text="PUT ↓", fg="#ff5252")

                fazer_entrada(par_var.get(), valor_atual, direcao)

        except Exception as e:
            janela.after(0, escrever_log, log, f"ERRO AUTO: {e}", "info")

        # ðŸ” loop leve (nÃ£o trava CPU)
        if rodando and loop_auto_rodando:
            janela.after(1000, atualizar_put_call)

    dir.grid_rowconfigure(0, weight=0)
    dir.grid_rowconfigure(1, weight=8)
    dir.grid_columnconfigure(0, weight=1)

    card_ctrl, controles = criar_card(dir, "#000000")
    card_ctrl.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def iniciar_auto():
        global rodando, modo_operacao, lucro_total, stop_ativo, tipo_stop
        global loop_auto_rodando, operando, wins, loss

        operando = False
        loop_auto_rodando = False

        if rodando:
            return

        rodando = True
        modo_operacao = "auto"
        wins = 0
        loss = 0
        lucro_total = 0
        stop_ativo = False
        tipo_stop = None

        escrever_log(log, "ROBÔ AUTOMÁTICO ATIVO", "info")
        lbl_modo.config(text="AUTO", fg="#00e676")
        lbl_on_status.itemconfig("dot", fill="#00e676", outline="#00e676")
        lbl_on_status.itemconfig("dot_text", text="ON")

        if not loop_auto_rodando:
            loop_auto_rodando = True
            atualizar_put_call()

    def parar_auto():
        global rodando, modo_operacao, operando, loop_auto_rodando

        rodando = False
        operando = False
        loop_auto_rodando = False
        modo_operacao = "manual"

        escrever_log(log, "MODO MANUAL ATIVO", "info")
        lbl_modo.config(text="MANUAL", fg="#ff5252")
        lbl_on_status.itemconfig("dot", fill="#ff3333", outline="#ff3333")
        lbl_on_status.itemconfig("dot_text", text="OFF")
        info_label.config(text="Aguardando", fg="#00e676")

    def entrada_manual(direcao):
        global operando, modo_operacao
        janela.after(0, escrever_log, log, f"ENTRADA: {direcao.upper()}", "info")
        modo_operacao = "manual"
        if not operando:
            fazer_entrada(par_var.get(), valor_atual, direcao)

    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Custom.TCombobox",
        fieldbackground="#1565c0",
        background="#1565c0",
        foreground="white",
    )
    style.map(
        "Custom.TCombobox",
        fieldbackground=[("readonly", "#1565c0")],
        foreground=[("readonly", "white")],
    )

    frame_ctrl = tk.Frame(controles, bg="#000000")
    frame_ctrl.pack(pady=0)

    tk.Radiobutton(
        frame_ctrl,
        text="Entrada:",
        variable=radio_var,
        value="entrada",
        bg="#000000",
        fg="white",
        selectcolor="#000000",
    ).grid(row=0, column=0, sticky="w", pady=15)

    ttk.Combobox(
        frame_ctrl,
        textvariable=entrada_var,
        values=["MÃ£o Fixa", "Soros", "Martingale"],
        state="readonly",
        width=16,
        style="Custom.TCombobox",
    ).grid(row=0, column=1, padx=15)

    tk.Label(
        frame_ctrl,
        text="Melhor Par",
        bg="#000000",
        fg="white",
        font=("Arial", 10, "bold"),
    ).grid(row=1, column=0, sticky="w", padx=10, pady=10)

    combo_par = ttk.Combobox(
        frame_ctrl,
        textvariable=par_var,
        values=["EURUSD-OTC", "NZDUSD-OTC"],
        state="readonly",
        width=16,
        style="Custom.TCombobox",
    )
    combo_par.grid(row=1, column=1, padx=10, pady=10)

    ultimo_par = None

    def mudar_par(event=None):
        global ultimo_par
        novo_par = par_var.get()
        janela.after(0, escrever_log, log, f"Par alterado: {novo_par}", "info")

        def _do_change():
            global ultimo_par
            try:
                if ultimo_par:
                    try:
                        Iq.stop_candles_stream(ultimo_par)
                    except Exception:
                        pass
                try:
                    Iq.start_candles_stream(novo_par, 60, 10)
                    janela.after(0, escrever_log, log, f"Stream atualizado", "info")
                except Exception as e:
                    janela.after(0, escrever_log, log, f"ERRO STREAM: {e}", "info")
            finally:
                ultimo_par = novo_par

        threading.Thread(target=_do_change, daemon=True).start()

    combo_par.bind("<<ComboboxSelected>>", mudar_par)

    tk.Label(frame_ctrl, text="Timeframe", bg="#000000", fg="white").grid(
        row=2, column=0, sticky="w", pady=5
    )

    combo_time = ttk.Combobox(
        frame_ctrl,
        textvariable=timeframe_var,
        values=["M1", "M5", "M15"],
        state="readonly",
        width=16,
        style="Custom.TCombobox",
    )
    combo_time.grid(row=2, column=1, padx=10, pady=10)

    def mudar_timeframe(event=None):
        novo_tf = timeframe_var.get()

        # 1m = 60s, 5m = 300s, 15m = 900s
        tf_map = {"M1": 60, "M5": 300, "M15": 900}
        tf_seconds = tf_map.get(novo_tf, 60)

        janela.after(
            0, escrever_log, log, f"Timeframe: {novo_tf} ({tf_seconds}s)", "info"
        )

        def _do_change():
            try:
                if Iq:
                    par = par_var.get()
                    try:
                        Iq.stop_candles_stream(par)
                    except Exception:
                        pass
                    time.sleep(0.2)
                    try:
                        Iq.start_candles_stream(par, tf_seconds, 10)
                        janela.after(0, escrever_log, log, f"Stream atualizado", "info")
                    except Exception as e:
                        janela.after(0, escrever_log, log, f"ERRO: {e}", "info")
            except Exception as e:
                janela.after(0, escrever_log, log, f"ERRO: {e}", "info")

        threading.Thread(target=_do_change, daemon=True).start()

    combo_time.bind("<<ComboboxSelected>>", mudar_timeframe)

    tk.Radiobutton(
        frame_ctrl,
        text="Melhor Estrat.",
        variable=radio_var,
        value="estrategia",
        bg="#000000",
        fg="white",
        selectcolor="#000000",
    ).grid(row=3, column=0, sticky="w", pady=15)

    ttk.Combobox(
        frame_ctrl,
        textvariable=estrategia_var,
        values=["M1-MHI", "M5-MHI", "MHI 2.0"],
        state="readonly",
        width=16,
        style="Custom.TCombobox",
    ).grid(row=3, column=1, padx=10, pady=10)

    btn_frame = tk.Frame(controles, bg="#000000")
    btn_frame.pack(anchor="n", pady=(5, 2))
    btn_frame.grid_columnconfigure(0, weight=1)
    btn_frame.grid_columnconfigure(1, weight=1)

    btn_iniciar_canvas, btn_iniciar_lbl = criar_rounded_btn(
        btn_frame,
        "Iniciar",
        "#0d8640",
        "white",
        ("Arial", 11, "bold"),
        width=100,
        height=36,
    )
    btn_iniciar_canvas.grid(row=0, column=0, padx=(10, 5), pady=5)
    btn_iniciar_lbl.bind("<Button-1>", lambda e: iniciar_auto())

    btn_parar_canvas, btn_parar_lbl = criar_rounded_btn(
        btn_frame,
        "Parar",
        "#961B1B",
        "white",
        ("Arial", 11, "bold"),
        width=100,
        height=36,
    )
    btn_parar_canvas.grid(row=0, column=1, padx=(5, 10), pady=5)
    btn_parar_lbl.bind("<Button-1>", lambda e: parar_auto())

    baixo_dir = tk.Frame(dir, bg="#0b0f14")
    baixo_dir.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    card, estrategia_box = criar_card(baixo_dir, "#000000")
    card.pack(fill="both", expand=True, pady=(0, 5))

    tk.Misc.tkraise(card_ctrl)

    lbl_titulo = tk.Label(
        estrategia_box,
        text="ESTRATÃ‰GIA",
        fg="#6b7280",
        bg="#000000",
        font=("Segoe UI", 9),
        anchor="center",
    )
    lbl_titulo.pack(pady=(8, 0))

    lbl_nome = tk.Label(
        estrategia_box,
        text="MHI",
        fg="#3b82f6",
        bg="#000000",
        font=("Segoe UI Black", 18, "bold"),
        anchor="center",
    )
    lbl_nome.pack(pady=(0, 0))

    lbl_time = tk.Label(
        estrategia_box,
        text=timeframe_var.get(),
        fg="#e5e7eb",
        bg="#000000",
        font=("Segoe UI", 10, "bold"),
        anchor="center",
    )
    lbl_time.pack(pady=(0, 0))

    lbl_par = tk.Label(
        estrategia_box,
        text=par_var.get(),
        fg="#4b5563",
        bg="#000000",
        font=("Segoe UI", 9),
        anchor="center",
    )
    lbl_par.pack(pady=(0, 10))

    def atualizar_estrategia(*args):
        try:
            lbl_time.config(text=timeframe_var.get())
            lbl_par.config(text=par_var.get())
            nome = estrategia_var.get()
            lbl_nome.config(text="MHI" if "MHI" in nome else nome)
        except Exception as e:
            print("ERRO atualizar_estrategia:", e)

    try:
        timeframe_var.trace_remove("write", timeframe_var.trace_info()[0][1])
        par_var.trace_remove("write", par_var.trace_info()[0][1])
        estrategia_var.trace_remove("write", estrategia_var.trace_info()[0][1])
    except (IndexError, tk.TclError):
        pass

    timeframe_var.trace_add("write", atualizar_estrategia)
    par_var.trace_add("write", atualizar_estrategia)
    estrategia_var.trace_add("write", atualizar_estrategia)

    global frame_alerta_stop, lbl_alerta_stop

    frame_alerta_stop = tk.Frame(janela, bg="#000000")
    frame_alerta_stop.place(relx=0, rely=0, relwidth=1, relheight=1)
    frame_alerta_stop.lower()

    lbl_alerta_stop = tk.Label(
        frame_alerta_stop,
        text="",
        bg="#000000",
        fg="#ff5252",
        font=("Segoe UI Black", 40, "bold"),
    )
    lbl_alerta_stop.pack(expand=True)


def desenhar_candle(canvas, x, abertura, fechamento, maxima, minima, min_val, max_val):
    altura_canvas = canvas.winfo_height() or 300
    margem = 20
    altura_util = altura_canvas - (margem * 2)

    if max_val == min_val:
        return

    def normalizar(valor):
        return margem + (max_val - valor) / (max_val - min_val) * altura_util

    y_open = normalizar(abertura)
    y_close = normalizar(fechamento)
    y_high = normalizar(maxima)
    y_low = normalizar(minima)

    y1 = min(y_open, y_close)
    y2 = max(y_open, y_close)

    # ðŸŽ¯ CORES IQ OPTION MAIS VIVAS
    if fechamento > abertura:
        cor = "#00ff44"  # verde forte
        cor_pavio = "#00ff44"
    else:
        cor = "#ff2d2d"  # vermelho forte
        cor_pavio = "#ff2d2d"

    # ðŸ”¥ PAVIO (fino, IQ Option)
    canvas.create_line(
        x,
        y_high,
        x,
        y_low,
        fill=cor_pavio,
        width=2,
        tags="candle",
    )

    # ðŸ”¥ CORPO (grosso, sem borda)
    largura = 32
    canvas.create_rectangle(
        x - largura,
        y1,
        x + largura,
        y2,
        fill=cor,
        outline="",
        tags="candle",
    )


def atualizar_saldo(valor):
    global lbl_saldo, modo
    try:
        if "ocultar_saldo" in globals() and ocultar_saldo.get():
            if lbl_saldo:
                lbl_saldo.config(text="R$ ****")
            return

        valor_formatado = (
            f"R$ {float(valor):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        cor = "#ff9800" if (modo and modo.get() == "demo") else "#00ff88"

        if lbl_saldo:
            lbl_saldo.config(text=valor_formatado, fg=cor, font=("Segoe UI Black", 10))
    except Exception as e:
        janela.after(0, escrever_log, log, f"ERRO SALDO: {e}", "info")


def iniciar(Iq_recebido, saldo=None, email=None, senha=None):
    global Iq, candles, ultimo_server_time
    Iq = Iq_recebido

    def atualizar_server_time():
        """Busca tempo IQ e salva referÃªncia local para interpolaÃ§Ã£o."""
        global ultimo_server_time, _server_sync_local
        while True:
            try:
                if Iq:
                    ts = Iq.get_server_timestamp()
                    if ts:
                        ultimo_server_time = int(ts)
                        _server_sync_local = time.perf_counter()
            except Exception:
                pass
            time.sleep(1)

    threading.Thread(target=atualizar_server_time, daemon=True).start()

    montar_painel()

    janela.after(0, escrever_log, log, "IQ conectado com sucesso", "info")

    # Iniciar stream e carregar candles em segundo plano para nÃ£o travar UI
    def _init_stream_and_candles():
        try:
            tf_map = {"M1": 60, "M5": 300, "M15": 900}
            tf_value = timeframe_var.get() if timeframe_var else "M1"
            tf_seconds = tf_map.get(tf_value, 60)
            try:
                Iq.start_candles_stream("EURUSD-OTC", tf_seconds, 10)
            except Exception as e:
                print("ERRO STREAM:", e)

            novos = pegar_candles_iq("EURUSD-OTC", tf_seconds, 5)
            if novos:

                def _apply():
                    global candles
                    candles[:] = novos

                janela.after(0, _apply)

            janela.after(0, escrever_log, log, "Candles carregados", "info")
        except Exception as e:
            janela.after(0, escrever_log, log, f"ERRO INICIAR STREAM: {e}", "info")

    threading.Thread(target=_init_stream_and_candles, daemon=True).start()

    # Precarregar saldos de ambas contas
    def _preload_balances():
        global saldo_cache
        try:
            # Pega saldo demo (conta inicial)
            saldo_demo = Iq.get_balance()
            if saldo_demo is not None:
                saldo_cache["demo"] = saldo_demo
            # Troca pra real, pega saldo, volta pra demo
            Iq.change_balance("REAL")
            saldo_real = Iq.get_balance()
            if saldo_real is not None:
                saldo_cache["real"] = saldo_real
            Iq.change_balance("PRACTICE")
        except Exception:
            pass

    threading.Thread(target=_preload_balances, daemon=True).start()

    loop_reset_diario()
    monitor_manual()
    loop_conexao()
    loop_saldo()

    agendar_reset_meia_noite()
    atualizar_contador_reset()
    atualizar_barra_meta()

    # Renderiza invisÃ­vel â†’ pinta tudo â†’ mostra (sem flash branco)
    janela.attributes("-alpha", 0)  # totalmente transparente
    janela.geometry("1000x650+-2000+-2000")
    janela.deiconify()
    janela.update()  # renderiza todos os widgets
    janela.update_idletasks()
    centralizar(janela)  # move pro centro
    janela.attributes("-alpha", 1)  # mostra de vez

    janela.after(500, escrever_log, log, "Candles carregados", "info")


abrir_login(janela, iniciar)
janela.mainloop()
