# 02 — Documentação Técnica

> **Projeto:** RoboBulkChatBot · **Jira:** [KAN-485](https://empresa.atlassian.net/browse/KAN-485)

---

## 1. Visão geral

O **RoboBulkChatBot** automatiza a extração diária do relatório **"Campanhas (Excel)"** do painel
**voxi.example**. Todo dia ele acessa o site, faz login, abre a tela de Relatórios, escolhe o tipo
"Campanhas (Excel)", define o período como **D-1** (o dia anterior, tanto em Data Início quanto em
Data Fim), exporta o Excel e publica o arquivo no compartilhamento de rede
`\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT`.

**O que ele faz:** login com reuso de sessão, seleção do relatório, filtro de data D-1, download e
publicação no SMB. **O que ele não faz:** não transforma nem valida o conteúdo do relatório, não
envia e-mail/notificação, e não trata outros tipos de relatório (embora `VOXI_TIPO_RELATORIO`
permita apontar para outro tipo, se necessário).

## 2. Stack e dependências

| Camada | Tecnologia | Versão | Por que foi escolhida |
|---|---|---|---|
| Linguagem | Python | 3.11+ | Padrão dos robôs do grupo. |
| Automação web | Playwright | 1.57.0 | Já usado nos robôs de scraping; controla download nativamente. |
| Config | python-dotenv | 1.0.1 | Carrega segredos do `.env`. |
| SMB | smbprotocol (`smbclient`) | 1.15.0 | Grava no compartilhamento de destino (padrão RoboCargas/AOA). |

> Todas as versões estão fixadas em [`requirements.txt`](../requirements.txt).

## 3. Pré-requisitos

- Python 3.11+ e `pip`.
- Navegador Chromium do Playwright (`python -m playwright install chromium`).
- Credenciais válidas do voxi.example.
- Acesso de rede ao host `10.0.0.72` e permissão de escrita no compartilhamento `Automacao`.

## 4. Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium

copy .env.example .env
# edite o .env com os valores reais (VOXI_USERNAME, VOXI_PASSWORD, SMB_USER, SMB_PASSWORD)

python main.py
```

## 5. Variáveis de ambiente

| Variável | Descrição | Obrigatória | Exemplo |
|---|---|---|---|
| `VOXI_LOGIN_URL` | URL de login | Sim | `https://voxi.example/login` |
| `VOXI_RELATORIOS_URL` | URL da tela de relatórios | Sim | `https://voxi.example/relatorios` |
| `VOXI_USERNAME` | E-mail ou `nome.sobrenome` | Sim | `desenvolvimento@...` |
| `VOXI_PASSWORD` | Senha | Sim | `••••••` |
| `VOXI_TIPO_RELATORIO` | Texto exato da opção do combobox | Sim | `Campanhas (Excel)` |
| `VOXI_HEADLESS` | `true`/`false` (janela do navegador) | Não (def. `true`) | `true` |
| `VOXI_SESSION_PATH` | Caminho do `storage_state` salvo | Não | `src/.../session/storage.json` |
| `VOXI_TIMEOUT_MS` | Timeout padrão das ações (ms) | Não (def. `60000`) | `60000` |
| `SMB_SERVER` | Host do servidor SMB | Sim | `10.0.0.72` |
| `SMB_SHARE_PATH` | Caminho UNC de destino | Sim | `\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT` |
| `SMB_USER` | Usuário de rede | Sim | `dominio\usuario` |
| `SMB_PASSWORD` | Senha do usuário de rede | Sim | `••••••` |
| `ROBO_DEBUG` | Log em nível DEBUG | Não (def. `false`) | `false` |

## 6. Como usar

```bash
python main.py                    # exporta o relatorio de campanhas de D-1 (ontem)
python main.py --data 2026-08-26  # forca uma data especifica (YYYY-MM-DD)
python main.py --no-headless      # navegador visivel (debug / revalidar login)
```

**Saída esperada:** arquivo `<nome-original>.xlsx` gravado em
`\\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT` e log de sucesso no console e em
`src/infrastructure/logging/log/robo_bulk_chatbot.log`.

## 7. Estrutura de pastas do projeto

```
RoboBulkChatBot/
├── main.py                                   # entrada: CLI + dispara o serviço
├── requirements.txt
├── .env.example
├── docs/                                      # documentacao do padrao (01..04)
├── src/
│   ├── application/service/
│   │   └── relatorio_campanhas_service.py     # orquestra login -> export -> SMB
│   ├── infrastructure/
│   │   ├── voxi/
│   │   │   ├── voxi_session.py                # abre navegador + garante login
│   │   │   ├── voxi_login.py                  # preenche e-mail/senha
│   │   │   └── voxi_relatorio_scraper.py      # seleciona tipo, datas D-1, exporta
│   │   ├── smb/
│   │   │   └── smb_destino.py                 # grava no compartilhamento SMB
│   │   └── logging/
│   │       └── log_config.py                  # logging rotativo
│   └── shared/utils/
│       └── env_load.py                        # VOXI_CONFIG / SMB_CONFIG a partir do .env
└── tests/                                      # testes automatizados
```

## 8. Como rodar em produção / deploy

Agendamento no **Agendador de Tarefas do Windows** na máquina do robô: executar
`python C:\Robos\RoboBulkChatBot\main.py` 1x/dia com `VOXI_HEADLESS=true`. A conta que roda a
tarefa precisa de acesso ao SMB de destino.

## 9. Manutenção e contato

- Responsável: Equipe de Desenvolvimento — Grupo Acme.
- **Pede login sempre:** apague o `storage.json` e rode 1x com `--no-headless`.
- **Erro de SMB:** valide `SMB_USER/SMB_PASSWORD` e conectividade com `10.0.0.72`.
- **Seletor mudou no site:** ajuste textos/seletores em `voxi_relatorio_scraper.py`.

---

**Critério de pronto (Fase 4):** um dev novo clona, instala e roda o projeto usando apenas
este documento. ✅
