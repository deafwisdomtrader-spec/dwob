import tkinter as tk
from datetime import datetime
import random


# =========================
# CENTRALIZAR
# =========================
def centralizar(janela, w=900, h=600):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (w // 2)
    y = (janela.winfo_screenheight() // 2) - (h // 2)
    janela.geometry(f"{w}x{h}+{x}+{y}")


# =========================
# ABRIR MERCADO
# =========================
def abrir_mercado(root):
    win = tk.Toplevel(root)
    win.withdraw()

    try:
        win.title("Mercado - DWOB")
        win.configure(bg="#0f172a")

        win.update_idletasks()
        centralizar(win)

    except Exception as e:
        print("ERRO AO ABRIR MERCADO:", e)

    win.deiconify()

    # =========================
    # FUNÇÃO FECHAR
    # =========================
    def fechar():
        win.destroy()

    # =========================
    # MENU LATERAL
    # =========================
    menu = tk.Frame(win, bg="#020617", width=80)
    menu.pack(side="left", fill="y")
    menu.pack_propagate(False)

    # =========================
    # LOGO
    # =========================
    topo = tk.Frame(menu, bg="#020617")
    topo.pack(pady=15)

    try:
        logo_img = tk.PhotoImage(file="images/logo.png").subsample(30, 30)
        topo.logo_img = logo_img
        tk.Label(topo, image=logo_img, bg="#020617").pack()
    except:
        print("logo não carregado")

    # =========================
    # BOTÃO HOME
    # =========================
    def criar_botao(texto, comando=None):
        btn = tk.Button(
            menu,
            text=texto,
            fg="#94a3b8",
            bg="#020617",
            activebackground="#0f172a",
            activeforeground="white",
            font=("Arial", 16),
            bd=0,
            cursor="hand2",
            command=comando,
        )

        btn.pack(fill="x", pady=8)

        btn.bind("<Enter>", lambda e: btn.config(bg="#0f172a", fg="white"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#020617", fg="#94a3b8"))

    criar_botao("🏠", fechar)

    # =========================
    # LINHA DIVISÓRIA
    # =========================
    tk.Frame(win, bg="#1e293b", width=1).pack(side="left", fill="y")

    # =========================
    # CONTEÚDO
    # =========================
    corpo = tk.Frame(win, bg="#0f172a")
    corpo.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        corpo,
        text="📊 Mercado em Tempo Real",
        bg="#0f172a",
        fg="white",
        font=("Arial", 16, "bold"),
    ).pack(pady=10)

    lbl_data = tk.Label(corpo, bg="#0f172a", fg="white", font=("Arial", 12))
    lbl_data.pack(pady=5)

    lbl_hora = tk.Label(corpo, bg="#0f172a", fg="white", font=("Arial", 14, "bold"))
    lbl_hora.pack(pady=5)

    lbl_status = tk.Label(corpo, bg="#0f172a", font=("Arial", 14, "bold"))
    lbl_status.pack(pady=10)

    lbl_movimento = tk.Label(corpo, bg="#0f172a", font=("Arial", 12))
    lbl_movimento.pack(pady=5)

    # =========================
    # ATUALIZAÇÃO
    # =========================
    def atualizar():
        agora = datetime.now()

        data = agora.strftime("%d/%m/%Y")
        hora = agora.strftime("%H:%M:%S")

        status = random.choice(["BOM", "RUIM"])
        movimento = random.choice(["ALTO", "MÉDIO", "BAIXO"])

        lbl_data.config(text=f"📅 Data: {data}")
        lbl_hora.config(text=f"⏰ Hora: {hora}")

        if status == "BOM":
            lbl_status.config(text="🟢 Mercado BOM", fg="#22c55e")
        else:
            lbl_status.config(text="🔴 Mercado RUIM", fg="#ef4444")

        lbl_movimento.config(text=f"📈 Movimento: {movimento}", fg="white")

        win.after(1000, atualizar)

    atualizar()
