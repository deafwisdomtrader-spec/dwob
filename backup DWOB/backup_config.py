import tkinter as tk


def abrir_config(janela):

    if hasattr(janela, "config_aberta") and janela.config_aberta.winfo_exists():
        janela.config_aberta.lift()
        return

    config = tk.Toplevel(janela)
    janela.config_aberta = config

    config.title("Configurações - DWOB")
    config.geometry("900x600")
    config.configure(bg="#0b0f14")

    # =========================
    # MENU LATERAL
    # =========================
    menu = tk.Frame(config, bg="#0a0f14", width=60)
    menu.pack(side="left", fill="y")
    menu.pack_propagate(False)

    tk.Label(
        menu, text="DW", fg="white", bg="#0a0f14", font=("Arial", 10, "bold")
    ).pack(pady=10)

    def criar_botao(icon, ativo=False):
        cor = "#00c853" if ativo else "#6c7a89"
        bg = "#11161c" if ativo else "#0a0f14"

        tk.Label(
            menu, text=icon, fg=cor, bg=bg, font=("Arial", 14), width=4, height=2
        ).pack(pady=10)

    criar_botao("📊")
    criar_botao("🏠")
    criar_botao("📅")
    criar_botao("⚙️", True)

    tk.Frame(config, bg="#1c252e", width=1).pack(side="left", fill="y")

    # =========================
    # MAIN
    # =========================
    main = tk.Frame(config, bg="#0b0f14")
    main.pack(side="left", fill="both", expand=True)

    # =========================
    # HEADER
    # =========================
    header = tk.Frame(main, bg="#0a0f14", height=40)
    header.pack(fill="x")

    tk.Label(header, text="CONFIGURAÇÕES", fg="white", bg="#0a0f14").pack(
        side="left", padx=10
    )

    header_right = tk.Frame(header, bg="#0a0f14")
    header_right.pack(side="right", padx=10)

    canvas = tk.Canvas(
        header_right, width=40, height=40, bg="#0a0f14", highlightthickness=0
    )
    canvas.pack(side="left", padx=5)

    canvas.create_oval(6, 2, 35, 35, fill="#00c853")
    canvas.create_text(20, 20, text="ON", fill="black")

    tk.Label(header_right, text="🇧🇷", bg="#11161c").pack(side="left", padx=2)
    tk.Label(header_right, text="🇪🇸", bg="#11161c").pack(side="left", padx=2)
    tk.Label(header_right, text="🇺🇸", bg="#11161c").pack(side="left", padx=2)

    # =========================
    # CORPO
    # =========================
    corpo = tk.Frame(main, bg="#0b0f14")
    corpo.pack(fill="both", expand=True, padx=20, pady=20)

    grid = tk.Frame(corpo, bg="#0b0f14")
    grid.pack(fill="both", expand=True)

    grid.grid_columnconfigure(0, weight=1)
    grid.grid_columnconfigure(1, weight=1)

    def entry_dark(parent):
        return tk.Entry(
            parent, bg="#11161c", fg="white", insertbackground="white", relief="flat"
        )

    # =========================
    # ESQUERDA
    # =========================
    col_esq = tk.Frame(grid, bg="#0b0f14")
    col_esq.grid(row=0, column=0, padx=10, sticky="n")

    tk.Label(col_esq, text="Estratégia", fg="white", bg="#0b0f14").pack(anchor="w")

    estrategia = tk.StringVar(value="MHI 2")
    drop1 = tk.OptionMenu(col_esq, estrategia, "MHI 1", "MHI 2", "MHI 3")
    drop1.config(bg="#11161c", fg="white", relief="flat")
    drop1["menu"].config(bg="#11161c", fg="white")
    drop1.pack(fill="x", pady=5)

    tk.Label(col_esq, text="Assertividade", fg="white", bg="#0b0f14").pack(anchor="w")
    e1 = entry_dark(col_esq)
    e1.insert(0, "75")
    e1.pack(fill="x")

    tk.Label(col_esq, text="Probabilidade", fg="white", bg="#0b0f14").pack(anchor="w")
    e2 = entry_dark(col_esq)
    e2.insert(0, "60")
    e2.pack(fill="x")

    tk.Label(col_esq, text="Delay (s)", fg="white", bg="#0b0f14").pack(anchor="w")
    e3 = entry_dark(col_esq)
    e3.insert(0, "2")
    e3.pack(fill="x")

    tk.Label(col_esq, text="Tipo Entrada", fg="white", bg="#0b0f14").pack(anchor="w")

    tipo = tk.StringVar(value="Normal")
    drop2 = tk.OptionMenu(col_esq, tipo, "Normal", "Agressiva", "Conservadora")
    drop2.config(bg="#11161c", fg="white", relief="flat")
    drop2["menu"].config(bg="#11161c", fg="white")
    drop2.pack(fill="x")

    # MARTINGALE
    usar_martingale = tk.BooleanVar()
    tk.Checkbutton(
        col_esq,
        text="Martingale",
        variable=usar_martingale,
        fg="white",
        bg="#0b0f14",
        selectcolor="#0b0f14",
    ).pack(anchor="w", pady=5)

    tk.Label(col_esq, text="Nível Martingale", fg="white", bg="#0b0f14").pack(
        anchor="w"
    )

    martingale_nivel = entry_dark(col_esq)
    martingale_nivel.insert(0, "2")
    martingale_nivel.pack(fill="x")

    # =========================
    # DIREITA
    # =========================
    col_dir = tk.Frame(grid, bg="#0b0f14")
    col_dir.grid(row=0, column=1, padx=10, sticky="n")

    rsi = tk.BooleanVar()
    tk.Checkbutton(
        col_dir,
        text="Usar RSI",
        variable=rsi,
        fg="white",
        bg="#0b0f14",
        selectcolor="#0b0f14",
    ).pack(anchor="w")

    tendencia = tk.BooleanVar()
    tk.Checkbutton(
        col_dir,
        text="Confirmar Tendência",
        variable=tendencia,
        fg="white",
        bg="#0b0f14",
        selectcolor="#0b0f14",
    ).pack(anchor="w")

    media = tk.BooleanVar()
    tk.Checkbutton(
        col_dir,
        text="Médias Móveis",
        variable=media,
        fg="white",
        bg="#0b0f14",
        selectcolor="#0b0f14",
    ).pack(anchor="w")

    m1 = entry_dark(col_dir)
    m1.insert(0, "9")
    m1.pack(fill="x")
    m2 = entry_dark(col_dir)
    m2.insert(0, "21")
    m2.pack(fill="x")
    m3 = entry_dark(col_dir)
    m3.insert(0, "50")
    m3.pack(fill="x")

    lateral = tk.BooleanVar()
    tk.Checkbutton(
        col_dir,
        text="Evitar Lateral",
        variable=lateral,
        fg="white",
        bg="#0b0f14",
        selectcolor="#0b0f14",
    ).pack(anchor="w")

    dupla = tk.BooleanVar()
    tk.Checkbutton(
        col_dir,
        text="Confirmação Dupla",
        variable=dupla,
        fg="white",
        bg="#0b0f14",
        selectcolor="#0b0f14",
    ).pack(anchor="w")

    # ESTOCÁSTICO
    stoch = tk.BooleanVar()
    tk.Checkbutton(
        col_dir,
        text="Oscilador Estocástico",
        variable=stoch,
        fg="white",
        bg="#0b0f14",
        selectcolor="#0b0f14",
    ).pack(anchor="w", pady=5)

    tk.Label(col_dir, text="%K", fg="white", bg="#0b0f14").pack(anchor="w")

    k = entry_dark(col_dir)
    k.insert(0, "14")
    k.pack(fill="x")

    tk.Label(col_dir, text="%D", fg="white", bg="#0b0f14").pack(anchor="w")

    d = entry_dark(col_dir)
    d.insert(0, "3")
    d.pack(fill="x")

    # BOTÃO
    tk.Button(corpo, text="Salvar", bg="#00c853", fg="black").pack(pady=20)
