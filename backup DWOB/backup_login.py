import tkinter as tk
from PIL import Image, ImageTk
import json
import os
import webbrowser

IQ_Option = None
try:
    from iqoptionapi.api import IQOptionAPI as IQ_Option
except Exception:
    IQ_Option = None
import sqlite3
import threading

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
def centralizar(janela, largura=600, altura=400):
    janela.update_idletasks()

    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)

    janela.geometry(f"{largura}x{altura}+{x}+{y}")


# =========================
# LOGIN
# =========================
def abrir_login(root, callback_sucesso):
    janela = tk.Toplevel(root)

    janela.iconbitmap("images/logo.ico")
    janela.title("Login DWOB")
    janela.configure(bg="#154569")
    janela.resizable(False, False)

    janela.geometry("600x400")
    janela.after(10, lambda: centralizar(janela))

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

    def ao_mudar_corretora(*args):
        corretora = corretora_var.get()

        if corretora == "IQ Option":
            status_label.config(text="✔ IQ Option selecionada", fg="#00e676")
            btn_entrar.config(state="normal")
        else:
            status_label.config(text="⚠️ Selecione IQ Option", fg="#ffcc00")
            btn_entrar.config(state="disabled")

    corretora_var.trace_add("write", ao_mudar_corretora)

    dropdown = tk.OptionMenu(
        box_avatar,
        corretora_var,
        "Selecione",
        "IQ Option",
        "Quotex",
        "Binomo",
        "Pocket Option",
    )

    dropdown.config(
        bg="#1b2a35",
        fg="white",
        activebackground="#2196f3",
        activeforeground="white",
        relief="flat",
    )

    dropdown.pack(pady=5)

    # =========================
    # DIREITA
    # =========================
    right = tk.Frame(container, bg="#154569")
    right.pack(side="left")

    box = tk.Frame(right, bg="#154569", padx=40, pady=40)
    box.pack(anchor="w")

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
        width=30,
        bg="#1b2a35",
        fg="white",
        insertbackground="white",
        relief="flat",
    )
    entry_email.pack(pady=5)

    # SENHA
    tk.Label(box, text="Senha", fg="white", bg="#154569").pack(anchor="w")
    entry_senha = tk.Entry(
        box,
        show="*",
        width=30,
        bg="#1b2a35",
        fg="white",
        insertbackground="white",
        relief="flat",
    )
    entry_senha.pack(pady=5)

    # 🔑 CHAVE
    tk.Label(box, text="Chave de acesso", fg="white", bg="#154569").pack(anchor="w")
    entry_chave = tk.Entry(box, width=30)
    entry_chave.pack(pady=(5, 0))

    # STATUS
    status_label = tk.Label(box, text="", fg="yellow", bg="#154569")
    status_label.pack(pady=10)

    # 💰 BOTÕES AFILIADO (LADO A LADO)

    def abrir_link():
        webbrowser.open(
            "https://iqoption.net/lp/mobile-partner-pwa/?aff=332220&aff_model=revenue&afftrack=deafwisdomtraderob"
        )

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

    import threading

    # =========================
    # BOTÃO ENTRAR (NÃO TRAVA)
    # =========================
    def entrar():
        btn_entrar.config(state="disabled")
        status_label.config(text="🔄 Conectando...", fg="yellow")

        threading.Thread(target=login_iq, daemon=True).start()

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
            # 🔥 CONECTA IQ
            Iq = IQ_Option(email, senha)
            check, reason = Iq.connect()

            if check:
                print("✅ Conectado IQ")

                Iq.change_balance("PRACTICE")
                saldo = Iq.get_balance()

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

    # 🔥 BOTÃO PRIMEIRO
    btn_entrar = tk.Button(
        box,
        text="Entrar",
        bg="#2196f3",
        fg="white",
        width=20,
        relief="flat",
        activebackground="#42a5f5",
        command=entrar,
    )

    btn_entrar.pack(pady=20)

    btn_entrar.config(state="disabled")  # começa bloqueado
