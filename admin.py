import tkinter as tk
from tkinter import messagebox


def criar_admin():
    """Placeholder de admin: mostra uma caixa simples sem funcionalidades sensíveis."""
    try:
        # Usa messagebox simples para evitar problemas com janelas pai ausentes
        messagebox.showinfo("Admin", "Área administrativa (placeholder).")
    except Exception:
        pass
