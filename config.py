import tkinter as tk
import json
import os

ARQUIVO_CONFIG = "configuracoes.json"


# =========================
# CARREGAR CONFIG
# =========================
def carregar_config():
    if not os.path.exists(ARQUIVO_CONFIG):
        return {
            "estrategia": "MHI 2",
            "assertividade": 75,
            "probabilidade": 60,
            "delay": 0,
            "rsi": False,
        }

    with open(ARQUIVO_CONFIG, "r") as f:
        return json.load(f)


# =========================
# SALVAR CONFIG
# =========================
def salvar_config(config):
    with open(ARQUIVO_CONFIG, "w") as f:
        json.dump(config, f, indent=4)


# =========================
# CENTRALIZAR
# =========================
def centralizar(janela, w=500, h=400):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (w // 2)
    y = (janela.winfo_screenheight() // 2) - (h // 2)
    janela.geometry(f"{w}x{h}+{x}+{y}")


# =========================
# ABRIR CONFIGURAÇÃO
# =========================
def abrir_config(root):
    config = carregar_config()

    win = tk.Toplevel(root)
    win.title("Configuração - DWOB")
    win.configure(bg="#0f172a")
    centralizar(win)

    # =========================
    # CONTEÚDO
    # =========================
    main = tk.Frame(win, bg="#0f172a")
    main.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        main,
        text="CONFIGURAÇÕES",
        bg="#0f172a",
        fg="white",
        font=("Arial", 16, "bold"),
    ).pack(pady=10)

    # =========================
    # CAMPOS
    # =========================

    # estratégia
    tk.Label(main, text="Estratégia", bg="#0f172a", fg="white").pack()
    estrategia_var = tk.StringVar(value=config["estrategia"])
    tk.Entry(main, textvariable=estrategia_var).pack(pady=5)

    # assertividade
    tk.Label(main, text="Assertividade (%)", bg="#0f172a", fg="white").pack()
    assert_var = tk.IntVar(value=config["assertividade"])
    tk.Entry(main, textvariable=assert_var).pack(pady=5)

    # probabilidade
    tk.Label(main, text="Probabilidade (%)", bg="#0f172a", fg="white").pack()
    prob_var = tk.IntVar(value=config["probabilidade"])
    tk.Entry(main, textvariable=prob_var).pack(pady=5)

    # delay
    tk.Label(main, text="Delay", bg="#0f172a", fg="white").pack()
    delay_var = tk.IntVar(value=config["delay"])
    tk.Entry(main, textvariable=delay_var).pack(pady=5)

    # RSI
    rsi_var = tk.BooleanVar(value=config["rsi"])
    tk.Checkbutton(
        main,
        text="Ativar RSI",
        variable=rsi_var,
        bg="#0f172a",
        fg="white",
        selectcolor="#0f172a",
    ).pack(pady=10)

    # =========================
    # SALVAR
    # =========================
    def salvar():
        novo = {
            "estrategia": estrategia_var.get(),
            "assertividade": assert_var.get(),
            "probabilidade": prob_var.get(),
            "delay": delay_var.get(),
            "rsi": rsi_var.get(),
        }

        salvar_config(novo)
        win.destroy()

    tk.Button(
        main,
        text="Salvar",
        bg="#00c853",
        fg="black",
        font=("Arial", 10, "bold"),
        command=salvar,
    ).pack(pady=15)
