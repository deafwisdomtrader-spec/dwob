# Painel DWOB - MHI EVO

Projeto GUI em Python que implementa um painel para monitoramento/controle de um robô MHI (integração com IQ Option).

Como executar (Windows):

1. Crie e ative um virtualenv no diretório do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
python -m pip install -r requirements.txt
```

3. Execute:

```powershell
python painel.py
```

Notas importantes:
- O projeto usa `tkinter` (incluso no Python padrão) e `Pillow` para manipulação de imagens.
- A integração com IQ Option depende do pacote `iqoptionapi`. O código tenta usar `iqoptionapi.api` e faz fallback quando necessário.
- Arquivo `painel.py` foi ajustado para mensagens de log em português e para mostrar `logo.png` no popup de Stop.

Modificações recentes:
- Tradução de logs para português.
- Popup de Stop exibe `images/logo.png` acima do campo de valor.
- Adicionado `.gitignore`.

Se quiser, posso gerar um `requirements.txt` com versões específicas a partir do seu ambiente virtual.
