# RoboBulkChatBot

> **Versão de portfólio.** Código real de produção, anonimizado: nomes de empresa, clientes, pessoas, hosts, e-mails e credenciais foram trocados por valores fictícios (`Acme`, `Banco Alfa`, `10.0.0.x`, `empresa.example`). Toda configuração sensível vem do `.env` (modelo em `.env.example`). O código não aponta para nenhum sistema real.

Automação que baixa diariamente o relatório **"Campanhas (Excel)"** do painel
**[voxi.example](https://voxi.example)** referente ao **dia anterior (D-1)** e publica o arquivo no
compartilhamento SMB `\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT`.

> Jira: [KAN-485](https://empresa.atlassian.net/browse/KAN-485) · Padrão Grupo Acme.

## Fluxo

Login → `/relatorios` → seleciona "Campanhas (Excel)" → Data Início/Fim = D-1 → "Exportar Excel"
→ grava o arquivo (nome original) no SMB de destino. Detalhes em [`docs/01-ARQUITETURA.md`](docs/01-ARQUITETURA.md).

## Pré-requisitos

- Python 3.11+
- Acesso ao voxi.example (usuário/senha) e ao compartilhamento SMB `10.0.0.72`.

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Configuração

1. Copie `.env.example` para `.env`.
2. Preencha `VOXI_USERNAME`, `VOXI_PASSWORD`, `SMB_USER`, `SMB_PASSWORD` (e confira as URLs/paths).

Nada de segredo vai para o Git — o `.env` está no `.gitignore`.

## Como rodar

```bash
python main.py
```

Opções úteis:

```bash
python main.py --data 2026-08-26      # força uma data especifica (formato YYYY-MM-DD)
python main.py --no-headless          # abre o navegador visivel (debug / primeiro login)
```

Sem argumentos, o robô usa **D-1** (ontem) e o modo definido em `VOXI_HEADLESS`.

## Agendamento (Windows)

Use o `exportar_campanhas.bat` (entra na pasta, ativa a venv se houver, roda o robô, grava
`src/infrastructure/logging/log/agendador.log` e retorna o exit code). Cadastre no Agendador de
Tarefas para rodar 1x/dia com `VOXI_HEADLESS=true`.

Criar a tarefa (ex.: todo dia às 06:00) — rode uma vez, como administrador:

```bat
schtasks /Create /TN "RoboBulkChatBot_Campanhas" /TR "C:\Robos\RoboBulkChatBot\exportar_campanhas.bat" /SC DAILY /ST 06:00 /RL HIGHEST /F
```

Rodar manualmente uma vez para testar: `schtasks /Run /TN "RoboBulkChatBot_Campanhas"`.
Logs da aplicação e do agendador ficam em `src/infrastructure/logging/log/`.

## Estrutura

```
RoboBulkChatBot/
├── main.py
├── requirements.txt
├── .env.example
├── docs/                 # 01-arquitetura, 02-documentacao, 03-testes, 04-homologacao
├── src/
│   ├── application/service/relatorio_campanhas_service.py
│   ├── infrastructure/
│   │   ├── voxi/         # session, login, scraper do relatorio
│   │   ├── smb/          # destino SMB
│   │   └── logging/      # log_config
│   └── shared/utils/     # env_load
└── tests/
```

## Solução de problemas

- **Pede login toda vez:** apague `src/infrastructure/voxi/session/storage.json` e rode 1x com
  `--no-headless` para revalidar a sessão.
- **Falha ao gravar no SMB:** confira `SMB_USER/SMB_PASSWORD` e se a máquina enxerga `10.0.0.72`.
- **Seletor mudou no site:** ajuste os textos/seletores em `voxi_relatorio_scraper.py`.
