# 03 — Plano de Testes (Fase 6)

> **Projeto:** RoboBulkChatBot · **Jira:** [KAN-485](https://empresa.atlassian.net/browse/KAN-485)

## 1. Estratégia

O robô tem duas naturezas de código:

- **Lógica pura** (parsing de datas do calendário, leitura de flags do `.env`, montagem do caminho
  SMB) — coberta por **testes automatizados** (`unittest`, sem rede).
- **Integração com site/SMB** (login, seleção, calendário, download, gravação) — coberta por
  **teste manual/homologação** contra o ambiente real (ver `docs/04-HOMOLOGACAO.md`), pois depende
  de credenciais e da rede interna.

Framework: `unittest` (stdlib, sem dependências extras).

## 2. Como rodar

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## 3. Casos automatizados

| ID | Arquivo | O que valida | Resultado esperado |
|---|---|---|---|
| T01 | `test_parse_mes_ano.py` | Cabeçalho do calendário em português (`agosto de 2026`) | `date(2026, 8, 1)` |
| T02 | `test_parse_mes_ano.py` | Português com maiúsculas/espaços | `date(2025, 12, 1)` |
| T03 | `test_parse_mes_ano.py` | Cabeçalho em inglês (`August 2026`) | `date(2026, 8, 1)` |
| T04 | `test_parse_mes_ano.py` | Texto sem ano | `None` |
| T05 | `test_parse_mes_ano.py` | Texto vazio / `None` | `None` |
| T06 | `test_env_bool.py` | Valores verdadeiros (`1/true/sim/y...`) | `True` |
| T07 | `test_env_bool.py` | Valores falsos (`0/false/nao/vazio...`) | `False` |
| T08 | `test_env_bool.py` | Ausência de valor usa o padrão | respeita `padrao` |
| T09 | `test_smb_destino.py` | Montagem do caminho UNC de destino | `\\...\arquivo.xlsx` |
| T10 | `test_smb_destino.py` | Normaliza barra final do share | sem `\` duplicado |

## 4. Casos de integração (manuais — homologação)

| ID | Cenário | Passos | Resultado esperado |
|---|---|---|---|
| M01 | Login e sessão | Rodar `python main.py --no-headless` sem `storage.json` | Loga, salva sessão, abre `/relatorios` |
| M02 | Reuso de sessão | Rodar novamente | Não pede login (usa `storage.json`) |
| M03 | Seleção do tipo | Observar o combobox | Fica em "Campanhas (Excel)" |
| M04 | Data D-1 | Observar Data Início/Fim | Ambas = ontem (`dd/mm/aaaa`) |
| M05 | Export/download | Clicar Exportar (automático) | Arquivo `.xlsx` baixado em `downloads/` |
| M06 | Publicação SMB | Conferir destino | Arquivo presente no compartilhamento |
| M07 | Data no 1º do mês | `--data <ultimo dia do mes anterior>` | Calendário navega ao mês anterior e seleciona |
| M08 | Credencial inválida | `.env` com senha errada | Log de erro claro, exit code 1, sem crash |

## 5. Evidências

Execução automatizada (Fase 6):

```
Ran 10 tests in 0.002s
OK
```

Evidências dos casos manuais (M01–M08) são anexadas na homologação (`docs/04-HOMOLOGACAO.md`).

## 6. Critério de pronto (Fase 6) ✅

- [x] Casos principais e de erro cobertos (automático + plano manual).
- [x] Testes automatizados passando (10/10).
