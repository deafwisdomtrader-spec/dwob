# Painel DWOB - MHI EVO

Painel GUI em Python para monitoramento e operação do robô MHI (integração opcional com IQ Option).

Resumo
- Interface gráfica simples baseada em `tkinter`.
- Camada de adaptação para variações do pacote `iqoptionapi` (`iq_adapter.py`).
- Modo `DummyIQ` para testar a interface sem conectar à corretora.

Requisitos
- Python 3.10+ (Windows recomendado para execução com `tkinter`).
- Recommended: criar virtualenv e instalar dependências abaixo.

Instalação (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Executando

```powershell
python painel.py
```

Modo de teste (sem conta real)
- Para rodar sem conectar à IQ Option, use a variável de ambiente `USE_DUMMY_IQ=1`:

```powershell
$env:USE_DUMMY_IQ = "1"  # PowerShell
python painel.py
```

Configuração
- Há um arquivo de exemplo `config/user.example.json`. Copie para `config/user.json` e preencha as credenciais apenas se for necessário.
- Nunca comite credenciais reais. O repositório contém instruções e exemplos para evitar vazamento de segredos.

Notas sobre `iqoptionapi`
- Existem forks e versões diferentes do pacote `iqoptionapi` que expõem interfaces distintas (`iqoptionapi.api` vs `iqoptionapi.stable_api`).
- O projeto inclui `iq_adapter.py` para compatibilidade; para uso em produção, prefira fixar (pin) uma versão conhecida do pacote ou manter o adapter.

Publicação / Empacotamento
- Verifique `.gitignore` e remova arquivos sensíveis antes de subir para o GitHub.
- Use `USE_DUMMY_IQ=1` para demonstrações públicas.

Ajuda
- **Gerar e commitar `requirements.txt`** com versões do seu ambiente (feito).
- **Revisar e remover arquivos sensíveis do histórico Git** (posso executar se confirmar).
- **Preparar empacotamento com PyInstaller** e instruções de distribuição.

--
Arquivo gerado automaticamente por assistente — edite conforme necessário.
