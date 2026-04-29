# Arquitetura

## Princípios

1. **Separação de domínio e infraestrutura.** `app/services/` contém matemática pura, sem dependências de Flask, requests ou scraper. Permite reuso em notebooks Jupyter.
2. **Funções puras + dataclasses imutáveis** no núcleo de cálculo.
3. **App factory pattern + Blueprints** para testabilidade e modularização.
4. **Validação na borda** com Pydantic v2; o domínio assume entradas já validadas.
5. **`Decimal` em todo dinheiro** (`ROUND_HALF_EVEN`); `float` é proibido em valores monetários.

## Camadas

```
Frontend (Jinja2 + HTMX + Plotly) ──→ Routes (Flask Blueprints)
                                       │
                                       ▼
                                   Schemas (Pydantic v2)
                                       │ valida
                                       ▼
                                   Services (puro Python)
                                       │
                              ┌────────┼─────────────┐
                              ▼        ▼             ▼
                       amortization  bacen_client  scrapers
                                                     │
                                                     ▼
                                              cache SQLite
```

## Comunicação frontend↔backend (híbrido HTMX + JSON)

- **Form submit:** HTMX `hx-post` → backend renderiza fragmento Jinja → HTMX troca DOM. Sem JS para essa parte; KPIs e tabela vêm prontos do servidor.
- **Gráficos:** mesma resposta HTML embute o JSON do resultado em `data-payload`. JS lê e chama Plotly.
- **Endpoint duplo:** mesma rota retorna HTML por padrão e JSON com `?format=json`.

## BACEN — degradação graciosa

1. Tenta cache em `instance/bacen_cache.json` (TTL 24h).
2. Se expirado/ausente, chama API SGS pública.
3. Em falha de rede: retorna cache expirado com `is_stale=true`.
4. Se nem cache existe: retorna `default` configurado em `.env`.
5. Se nem default: levanta `BacenUnavailableError` (HTTP 503).

## Scrapers — princípios não-negociáveis

- API interna JSON > HTML SSR > Playwright.
- Respeitar `robots.txt`.
- Cache obrigatório de 6h.
- Rate limit: 1 req/s, delay 2-5s, backoff 8→16→32→64→128s em 429/503.
- Sem proxies pagos, sem captcha solvers, sem login autenticado.
- LGPD: parser descarta `phone`, `owner_name`, `email`.
- Falhar gracioso: retorna `ScrapeError` → UI oferece input manual de aluguel.

## Estrutura de testes

- **Unitários (CI):** `services/` com casos canônicos de Hazzan & Pompeo.
- **Integração:** marcados `@pytest.mark.integration`, rodam sob demanda.
- **Cobertura-alvo:** `services/` ≥ 95%, total ≥ 85%.

## Roadmap

- v2: scraper de São Paulo + filtro por bairro.
- v3: filtros avançados (m², mobiliado, ar-condicionado).
- v4: CET (TIR numérica), modelagem de IR sobre rendimentos, custos de transação.
