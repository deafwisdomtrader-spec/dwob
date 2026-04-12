import tkinter as tk


# =========================
# CENTRALIZAR
# =========================
def centralizar(janela, w=900, h=600):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (w // 2)
    y = (janela.winfo_screenheight() // 2) - (h // 2)
    janela.geometry(f"{w}x{h}+{x}+{y}")


# =========================
# ABRIR CONTROLE
# =========================
def abrir_controle(root):
    win = tk.Toplevel(root)
    win.withdraw()

    try:
        win.title("Controle - DWOB")
        win.configure(bg="#0f172a")

        win.update_idletasks()
        centralizar(win)

    except Exception as e:
        print("ERRO AO ABRIR CONTROLE:", e)

    win.deiconify()

    # =========================
    # FECHAR
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
        text="🎮 Controle do Sistema",
        bg="#0f172a",
        fg="white",
        font=("Arial", 16, "bold"),
    ).pack(pady=10)

    status_lbl = tk.Label(
        corpo,
        text="Status: PARADO",
        fg="#ef4444",
        bg="#0f172a",
        font=("Arial", 12, "bold"),
    )
    status_lbl.pack(pady=10)

    # =========================
    # FUNÇÕES
    # =========================
    def iniciar():
        status_lbl.config(text="Status: RODANDO", fg="#22c55e")

    def parar():
        status_lbl.config(text="Status: PARADO", fg="#ef4444")

    # =========================
    # BOTÕES
    # =========================
    tk.Button(
        corpo,
        text="▶ Iniciar",
        command=iniciar,
        bg="#22c55e",
        fg="black",
        font=("Arial", 10, "bold"),
        cursor="hand2",
    ).pack(pady=5)

    tk.Button(
        corpo,
        text="⏹ Parar",
        command=parar,
        bg="#ef4444",
        fg="white",
        font=("Arial", 10, "bold"),
        cursor="hand2",
    ).pack(pady=5)
