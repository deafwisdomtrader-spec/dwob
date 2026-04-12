import tkinter as tk
from PIL import Image, ImageTk
import json
import os
import webbrowser

IQ_Option = None
try:
    from iqoptionapi.api import IQOptionAPI as IQ_Option
except Exception:
    # Permite importar o módulo sem a dependência instalada (útil para testes UI locais)
    IQ_Option = None
import sqlite3
import threading
import time

DB = "clientes.db"


def abrir_whatsapp():
    numero = "553492601630"  # 🔥 coloca seu número
    mensagem = "Olá, já fiz o depósito e quero minha chave"

    link = f"https://wa.me/{numero}?text={mensagem}"
    webbrowser.open(link)


ARQUIVO = "config/user.json"
ARQ_LICENCA = "config/licenca.json"


# =========================
# SALVAR LOGIN
# =========================
def salvar_login(email, senha):
    os.makedirs("config", exist_ok=True)

    with open(ARQUIVO, "w") as f:
        json.dump({"email": email, "senha": senha}, f)


# =========================
# LICENÇA
# =========================
def salvar_licenca():
    os.makedirs("config", exist_ok=True)
    with open(ARQ_LICENCA, "w") as f:
        json.dump({"liberado": True}, f)


def licenca_liberada():
    try:
        with open(ARQ_LICENCA, "r") as f:
            dados = json.load(f)
            return dados.get("liberado", False)
    except:
        return False


# =========================
# CENTRALIZAR
# =========================
def centralizar(janela, largura=600, altura=500):
    janela.update_idletasks()

    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)

    janela.geometry(f"{largura}x{altura}+{x}+{y}")


# =========================
# LOGIN
# =========================
def abrir_login(root, callback_sucesso):
    janela = tk.Toplevel(root)
    janela.withdraw()  # esconde imediatamente

    janela.iconbitmap("images/logo.ico")
    janela.title("Login DWOB")
    janela.configure(bg="#154569")
    janela.resizable(False, False)

    janela.geometry("600x500+-2000+-2000")

    # =========================
    # CONTAINER
    # =========================
    container = tk.Frame(janela, bg="#154569")
    container.pack(expand=True)

    # =========================
    # ESQUERDA
    # =========================
    left = tk.Frame(container, bg="#154569")
    left.pack(side="left", padx=(0, 40))

    box_avatar = tk.Frame(left, bg="#154569")
    box_avatar.pack(anchor="e")

    # AVATAR
    try:
        img = Image.open("images/logo.webp").resize((100, 100))
        avatar = ImageTk.PhotoImage(img)

        lbl_img = tk.Label(box_avatar, image=avatar, bg="#154569")
        lbl_img.image = avatar
        lbl_img.pack()
    except:
        tk.Label(
            box_avatar,
            text="DWOB",
            fg="white",
            bg="#154569",
            font=("Arial", 30, "bold"),
        ).pack()

    tk.Label(
        box_avatar,
        text="Usuário",
        fg="#a9cce3",
        bg="#154569",
        font=("Arial", 12),
    ).pack(pady=(5, 5))

    # =========================
    # CORRETORA (ESQUERDA)
    # =========================
    tk.Label(
        box_avatar,
        text="Corretora",
        fg="#a9cce3",
        bg="#154569",
        font=("Arial", 10),
    ).pack(pady=(10, 2))

    corretora_var = tk.StringVar()
    corretora_var.set("Selecione")

    from tkinter import ttk

    icons = {}

    def carregar_icone(nome, arquivo):
        try:
            img = Image.open(arquivo).resize((16, 16))
            icons[nome] = ImageTk.PhotoImage(img)
        except:
            icons[nome] = None

    carregar_icone("IQ Option", "images/iq.png")
    carregar_icone("Quotex", "images/quotex.png")
    carregar_icone("Binomo", "images/binomo.png")

    # =========================
    # 🔥 DROPDOWN INSANO
    # =========================

    import json

    ARQ_CONFIG = "config/dropdown.json"

    def salvar_opcao(valor):
        os.makedirs("config", exist_ok=True)
        with open(ARQ_CONFIG, "w") as f:
            json.dump({"corretora": valor}, f)

    def carregar_opcao():
        try:
            with open(ARQ_CONFIG, "r") as f:
                return json.load(f).get("corretora", "Selecione")
        except:
            return "Selecione"

    lista_corretoras = [
        "Selecione",
        "IQ Option",
        "Quotex",
        "Binomo",
        "Pocket Option",
        "Ebinex",
        "Olymp Trade",
    ]

    corretora_var.set(carregar_opcao())

    frame_dropdown = tk.Frame(box_avatar, bg="#1b2a35")
    frame_dropdown.pack(pady=5)

    btn_dropdown = tk.Label(
        frame_dropdown,
        text="  " + corretora_var.get(),
        image=icons.get(corretora_var.get()),
        compound="left",
        bg="#1b2a35",
        fg="white",
        anchor="w",
        padx=10,
        width=180,
    )
    btn_dropdown.pack(side="left", ipady=6)

    lbl_saldo = tk.Label(
        box_avatar, text="", fg="#00e676", bg="#154569", font=("Arial", 9)
    )
    lbl_saldo.pack(pady=(2, 0))

    # seta
    btn_seta = tk.Label(
        frame_dropdown, text="▼", bg="#1b2a35", fg="white", cursor="hand2"
    )
    btn_seta.pack(side="right", padx=5)

    # =========================
    # POPUP COM SOMBRA
    # =========================
    popup = tk.Toplevel(janela)
    popup.withdraw()
    popup.overrideredirect(True)
    popup.configure(bg="#212A35")
    overlay = tk.Toplevel(janela)
    overlay.withdraw()
    overlay.overrideredirect(True)
    overlay.attributes("-alpha", 0.8)  # 🔥 transparência
    overlay.configure(bg="black")

    # ✅ PRIMEIRO CRIA
    container_popup = tk.Frame(popup, bg="#1b2a35", bd=0)
    container_popup.pack(padx=2, pady=2)

    # ✅ DEPOIS CONFIGURA
    container_popup.config(
        bg="#1b2a35", highlightthickness=1, highlightbackground="#2c3e50"
    )

    opcoes = []
    indice_hover = -1

    # =========================
    # ABRIR
    # =========================
    def abrir_dropdown(event=None):
        btn_seta.config(text="▲")  # 🔥 muda seta

        janela.update_idletasks()

        x = janela.winfo_rootx() + frame_dropdown.winfo_x()
        y = (
            janela.winfo_rooty()
            + frame_dropdown.winfo_y()
            + frame_dropdown.winfo_height()
        )

        popup.geometry(f"{frame_dropdown.winfo_width()}x1+{x}+{y}")

        # 🔥 cobre a tela inteira
        overlay.geometry(
            f"{janela.winfo_screenwidth()}x{janela.winfo_screenheight()}+0+0"
        )
        overlay.deiconify()
        overlay.lift()

        popup.lift()
        popup.deiconify()

        animar_altura(0, len(lista_corretoras) * 28)

    def fechar_dropdown(event=None):
        btn_seta.config(text="▼")
        popup.withdraw()
        overlay.withdraw()

    def animar_altura(atual, final):
        if atual >= final:
            return

        atual += 12
        popup.geometry(
            f"{frame_dropdown.winfo_width()}x{atual}+{popup.winfo_x()}+{popup.winfo_y()}"
        )
        janela.after(8, lambda: animar_altura(atual, final))

    # =========================
    # FECHAR
    # =========================
    def fechar_dropdown(event=None):
        btn_seta.config(text="▼")  # 🔥 volta seta
        popup.withdraw()

    # =========================
    # SELEÇÃO
    # =========================
    def selecionar(valor):
        corretora_var.set(valor)
        salvar_opcao(valor)

        btn_dropdown.config(text="  " + valor, image=icons.get(valor))

        ao_mudar_corretora()
        fechar_dropdown()

    # =========================
    # CRIAR OPÇÕES
    # =========================
    for i, item in enumerate(lista_corretoras):
        lbl = tk.Label(
            container_popup, text=item, bg="#1b2a35", fg="white", anchor="w", padx=10
        )
        lbl.pack(fill="x", ipady=5)

        opcoes.append(lbl)

        lbl.bind("<Button-1>", lambda e, v=item: selecionar(v))

        def on_enter(e, w=lbl, idx=i):
            global indice_hover
            indice_hover = idx
            atualizar_hover()

        lbl.bind("<Enter>", on_enter)

    # =========================
    # HOVER
    # =========================
    def atualizar_hover():
        atual = corretora_var.get()

        for i, w in enumerate(opcoes):
            if lista_corretoras[i] == atual:
                w.config(bg="#1f3b4d")  # selecionado fixo
            elif i == indice_hover:
                w.config(bg="#2c3e50")
            else:
                w.config(bg="#1b2a35")

    # =========================
    # TECLADO
    # =========================
    def key_nav(event):
        global indice_hover

        if not popup.winfo_viewable():
            return

        if event.keysym == "Down":
            indice_hover = (indice_hover + 1) % len(opcoes)
        elif event.keysym == "Up":
            indice_hover = (indice_hover - 1) % len(opcoes)
        elif event.keysym == "Return":
            if 0 <= indice_hover < len(opcoes):
                selecionar(lista_corretoras[indice_hover])

        atualizar_hover()

    janela.bind("<Down>", key_nav)
    janela.bind("<Up>", key_nav)
    janela.bind("<Return>", key_nav)

    # =========================
    # EVENTOS
    # =========================
    btn_dropdown.bind("<Button-1>", abrir_dropdown)
    btn_seta.bind("<Button-1>", abrir_dropdown)

    def clique_fora(event):
        widget = event.widget

        # não fecha se clicou no dropdown ou popup
        if widget in (btn_dropdown, btn_seta):
            return

        if widget == popup:
            return

        parent = widget
        while parent:
            if parent == popup:
                return
            parent = getattr(parent, "master", None)

        fechar_dropdown()

    janela.bind("<Button-1>", clique_fora, add="+")

    # =========================
    # DIREITA
    # =========================
    right = tk.Frame(container, bg="#154569")
    right.pack(side="left")

    box = tk.Frame(right, bg="#154569", padx=40, pady=40)
    box.pack(anchor="w")

    # ✅ cria status
    status_label = tk.Label(box, text="", fg="yellow", bg="#154569")
    status_label.pack(pady=10)

    # LOGO CENTRAL
    try:
        img2 = Image.open("images/logo.png").resize((80, 80))
        logo2 = ImageTk.PhotoImage(img2)

        lbl_logo = tk.Label(box, image=logo2, bg="#154569")
        lbl_logo.image = logo2
        lbl_logo.pack(pady=(0, 10))
    except:
        pass

    # EMAIL
    tk.Label(box, text="Email", fg="white", bg="#154569").pack(anchor="w")
    entry_email = tk.Entry(
        box,
        width=40,
        font=("Arial", 12),  # 🔥 aumenta altura
        bg="#1b2a35",
        fg="white",
        insertbackground="white",
        relief="flat",
    )
    entry_email.pack(pady=8, ipady=4)

    # SENHA
    entry_senha = tk.Entry(
        box,
        show="*",
        width=40,
        font=("Arial", 12),
        bg="#1b2a35",
        fg="white",
        insertbackground="white",
        relief="flat",
    )
    entry_senha.pack(pady=8, ipady=4)

    # 🔑 CHAVE
    tk.Label(box, text="Chave de acesso", fg="white", bg="#154569").pack(anchor="w")
    entry_chave = tk.Entry(box, width=30)
    entry_chave.pack(pady=(5, 0))

    # 💰 BOTÕES AFILIADO (LADO A LADO)

    def abrir_link():
        webbrowser.open(
            "https://iqoption.net/lp/mobile-partner-pwa/?aff=332220&aff_model=revenue&afftrack=deafwisdomtraderob"
        )

    import threading

    # =========================
    # BOTÃO ENTRAR (NÃO TRAVA)
    # =========================
    def entrar():
        btn_entrar.config(state="disabled")
        status_label.config(text="🔄 Conectando...", fg="yellow")

        threading.Thread(target=login_iq, daemon=True).start()

    btn_entrar = tk.Button(
        box,
        text="Entrar",
        bg="#294B96",
        fg="#ffffff",
        width=20,
        relief="flat",
        activebackground="#42a5f5",
        command=entrar,
    )

    btn_entrar.pack(pady=20)
    btn_entrar.config(state="disabled")

    # 🔥 FRAME DOS BOTÕES
    frame_botoes = tk.Frame(box, bg="#154569")
    frame_botoes.pack(pady=(0, 10))

    # 💰 BOTÃO DEPOSITAR
    tk.Button(
        frame_botoes,
        text="💰 Depositar",
        bg="#8b5c14",
        fg="white",
        font=("Arial", 10, "bold"),
        bd=0,
        padx=10,
        pady=5,
        cursor="hand2",
        command=abrir_link,
    ).pack(side="left", padx=5)

    # 💬 BOTÃO WHATSAPP
    tk.Button(
        frame_botoes,
        text="💬 WhatsApp",
        bg="#0d863a",
        fg="white",
        font=("Arial", 10, "bold"),
        bd=0,
        padx=10,
        pady=5,
        cursor="hand2",
        command=abrir_whatsapp,
    ).pack(side="left", padx=5)

    # =========================
    # LOGIN REAL (THREAD)
    # =========================
    def login_iq():
        global Iq

        corretora = corretora_var.get()

        if corretora != "IQ Option":
            janela.after(
                0,
                lambda: status_label.config(
                    text="⚠️ Primeiro selecione IQ Option", fg="#ffcc00"
                ),
            )
            janela.after(0, lambda: btn_entrar.config(state="normal"))
            return

        email = entry_email.get().strip()
        senha = entry_senha.get().strip()
        chave = entry_chave.get().strip()

        if not email or not senha:
            janela.after(0, lambda: status_label.config(text="Preencha email e senha"))
            janela.after(0, lambda: btn_entrar.config(state="normal"))
            return

        try:
            # 🔥 CONECTA IQ (se IQ_Option ausente, usa DummyIQ para testes locais)
            if IQ_Option is None:

                class DummyIQ:
                    def __init__(self, *a, **k):
                        pass

                    def connect(self):
                        return (True, None)

                    def change_balance(self, mode):
                        return True

                    def get_balance(self):
                        return 1000.0

                    def buy(self, valor, par, direcao, timeframe):
                        return (True, 12345)

                    def check_win_v3(self, id_op):
                        return (True, 1.0)

                    def start_candles_stream(self, *a, **k):
                        return None

                    def stop_candles_stream(self, *a, **k):
                        return None

                    # Métodos adicionais usados pelo painel (stubs simples)
                    def get_option_open_by_other_pc(self):
                        return {}

                    def check_connect(self):
                        return True

                    def get_candles(self, par, timeframe, qtd, now):
                        # Retorna lista de candles simples: dicts com open/close/max/min
                        now = int(time.time())
                        res = []
                        for i in range(qtd):
                            o = 1.0 + (i % 5) * 0.001
                            c = o + (0.001 if i % 2 == 0 else -0.0005)
                            res.append(
                                {
                                    "open": o,
                                    "close": c,
                                    "max": max(o, c),
                                    "min": min(o, c),
                                }
                            )
                        return res

                    def get_realtime_candles(self, par, timeframe=60):
                        now = int(time.time())
                        # Retorna dicionário similar ao real: key-> {from, open, close, max, min}
                        out = {}
                        for i in range(10):
                            ts = now - (9 - i) * timeframe
                            out[str(i)] = {
                                "from": ts,
                                "open": 1.0,
                                "close": 1.0 + (i % 2) * 0.001,
                                "max": 1.002,
                                "min": 0.998,
                            }
                        return out

                    def get_server_timestamp(self):
                        return int(time.time())

                Iq = DummyIQ()
            else:
                Iq = IQ_Option(email, senha)

            check, reason = Iq.connect()

            if check:
                print("✅ Conectado IQ")

                Iq.change_balance("PRACTICE")
                saldo = Iq.get_balance()

                janela.after(0, atualizar_saldo)

                def sucesso():
                    janela.destroy()
                    callback_sucesso(Iq, saldo, email, senha)

                # ✅ status (ok manter)
                janela.after(
                    0,
                    lambda: status_label.config(
                        text="✅ Conectado com sucesso", fg="#00e676"
                    ),
                )

                salvar_login(email, senha)
                salvar_licenca()

                janela.after(0, sucesso)

            else:
                print("❌ Falha:", reason)

                janela.after(
                    0,
                    lambda: status_label.config(
                        text="❌ Email ou senha incorretos", fg="red"
                    ),
                )

                janela.after(0, lambda: btn_entrar.config(state="normal"))

        except Exception as e:
            print("ERRO LOGIN:", e)

            janela.after(
                0, lambda: status_label.config(text="❌ Erro conexão", fg="red")
            )

            janela.after(0, lambda: btn_entrar.config(state="normal"))

    def atualizar_saldo():
        # Busca saldo em thread para não travar a UI
        def _fetch():
            try:
                if Iq:
                    saldo = Iq.get_balance()
                    cor = "#00e676" if saldo > 0 else "#ff5252"

                    def _update():
                        try:
                            lbl_saldo.config(text=f"Saldo: R$ {saldo:.2f}", fg=cor)

                            if hasattr(atualizar_saldo, "ultimo"):
                                if saldo > atualizar_saldo.ultimo:
                                    lbl_saldo.config(bg="#0d2f1c")
                                    janela.after(
                                        300, lambda: lbl_saldo.config(bg="#154569")
                                    )
                                elif saldo < atualizar_saldo.ultimo:
                                    lbl_saldo.config(bg="#3a0d0d")
                                    janela.after(
                                        300, lambda: lbl_saldo.config(bg="#154569")
                                    )

                            atualizar_saldo.ultimo = saldo
                        except Exception:
                            pass

                    janela.after(0, _update)
            except Exception:
                pass
            finally:
                janela.after(2000, atualizar_saldo)

        threading.Thread(target=_fetch, daemon=True).start()

    # ✅ AGORA SIM a função
    def ao_mudar_corretora(*args):
        corretora = corretora_var.get()

        if corretora == "IQ Option":
            status_label.config(text="✔ IQ Option selecionada", fg="#00e676")
            btn_entrar.config(state="normal")
        else:
            status_label.config(text="⚠️ Selecione IQ Option", fg="#ffcc00")
            btn_entrar.config(state="disabled")

    # ✅ só depois conecta
    corretora_var.trace_add("write", ao_mudar_corretora)

    # Renderiza invisível → pinta tudo → mostra (sem flash)
    janela.attributes("-alpha", 0)
    janela.deiconify()
    janela.update()
    janela.update_idletasks()
    centralizar(janela)
    janela.attributes("-alpha", 1)
