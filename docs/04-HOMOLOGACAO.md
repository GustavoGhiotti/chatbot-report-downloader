# 04 — Homologação (Fase 7)

> **Projeto:** RoboBulkChatBot · **Jira:** [KAN-485](https://empresa.atlassian.net/browse/KAN-485)
> **Regra:** o projeto só é considerado **entregue** após esta homologação aprovada com evidências.

## 1. Pré-condições

- [ ] `.env` preenchido (`VOXI_USERNAME`, `VOXI_PASSWORD`, `SMB_USER`, `SMB_PASSWORD`).
- [ ] `pip install -r requirements.txt` executado.
- [ ] `python -m playwright install chromium` executado.
- [ ] Máquina com acesso ao voxi.example e ao compartilhamento `\\10.0.0.72\Automacao`.

## 2. Checklist de aceite

Homologação funcional executada em **2026-08-27** (data de referência D-1 = 2026-08-26).

| # | Critério | Status | Evidência |
|---|---|---|---|
| 1 | Código compila sem erros | ✅ OK | `python -m compileall main.py src` → exit 0 |
| 2 | Testes automatizados passam | ✅ OK | `Ran 10 tests ... OK` |
| 3 | Login efetuado e sessão salva | ✅ OK | log `VoxiLogin - Login concluido com sucesso` + `storage.json` criado |
| 4 | Reuso de sessão (não relogar) | ✅ OK | 2ª execução: `Reutilizando sessao salva` / `Sessao ja autenticada` |
| 5 | Tipo "Campanhas (Excel)" selecionado | ✅ OK | log `Selecionando tipo de relatorio: Campanhas (Excel)` |
| 6 | Data Início/Fim = D-1 | ✅ OK | log `Data Inicio/Fim definido para 26/08/2026` |
| 7 | Download do `.xlsx` realizado | ✅ OK | `Download concluido: campanhas_itens_2026-08-26_a_2026-08-26.xlsx` |
| 8 | Arquivo publicado no SMB | ✅ OK | `\\10.0.0.72\...\RELATORIOS_CAMPANHAS_CHATBOT\campanhas_itens_2026-08-26_a_2026-08-26.xlsx` — 7096 bytes |
| 9 | Erro de credencial tratado (exit 1) | ⏳ Pendente | teste opcional com senha inválida (código já trata: log de erro + exit 1) |
| 10 | Execução agendada (headless) | ◐ Parcial | execução headless OK (`python main.py`); falta cadastrar no Agendador de Tarefas |

> **Correções aplicadas durante a homologação** (todas em Fase 5, KAN-492):
> - `voxi_login`: helper `_tem_campo` faltante; detecção de login corrigida.
> - `voxi_session`: aguardar a SPA estabilizar (`networkidle`) antes de checar login — o site redireciona `/relatorios → /login` de forma assíncrona.
> - `voxi_relatorio_scraper`: o calendário é `react-day-picker`; a seleção do dia passou a usar o `aria-label` completo (ex.: `26 de agosto de 2026`), evitando ambiguidade com dias "de fora".
> - `smb_destino`: credenciais SMB agora **opcionais** — sem elas, usa a sessão já autenticada do Windows (padrão dos outros robôs).

## 3. Roteiro de homologação

```bash
# 1. Primeira execução (visivel, para validar login e salvar sessao)
python main.py --no-headless

# 2. Segunda execução (deve reutilizar a sessao, sem pedir login)
python main.py --no-headless

# 3. Execucao headless (como rodara agendado)
python main.py

# 4. Conferir o arquivo no destino SMB
#    \\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT
```

## 4. Evidências anexadas

_(Cole aqui os prints/logs de cada item pendente do checklist ao homologar.)_

## 5. Aprovação

| Papel | Nome | Data | Aprovado? |
|---|---|---|---|
| Desenvolvimento | | | ☐ |
| Responsável / Solicitante | | | ☐ |

## 6. Pendências / Observações conhecidas

- Os seletores do **calendário** (`react-day-picker`) e do **combobox** (Radix) foram escritos de
  forma defensiva (múltiplos fallbacks). Se o voxi.example alterar o layout, ajustar
  `src/infrastructure/voxi/voxi_relatorio_scraper.py`.
- O nome do arquivo publicado é o **nome original** gerado pelo site; execuções repetidas para a
  mesma data sobrescrevem o arquivo no destino.

---

**Critério de pronto (Fase 7):** todos os itens do checklist marcados, evidências anexadas e
aprovação registrada. Só então o projeto é considerado **entregue**.
