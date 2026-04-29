# API REST

Todos os endpoints retornam JSON quando chamados com `?format=json` ou cabeçalho `Accept: application/json`. Caso contrário, retornam fragmentos HTML para HTMX.

## Health

`GET /api/health` → `{ status, timestamp, bacen_cache_age_seconds }`

## Simulação

`POST /api/simulate`

**Body:**
```json
{
  "property_value": 500000,
  "down_payment": 100000,
  "annual_rate": 0.115,
  "term_years": 30,
  "system": "SAC",
  "rate_convention": "equivalent",
  "monthly_income": 15000
}
```
Aceita `term_months` ao invés de `term_years` (mas não os dois juntos).

**Resposta (`?format=json`):**
```json
{
  "summary": {
    "system": "SAC", "property_value": "500000.00", "down_payment": "100000.00",
    "financed_amount": "400000.00", "annual_rate": "0.115",
    "monthly_rate": "0.009110", "term_months": 360,
    "first_payment": "4756.10", "last_payment": "1121.64",
    "total_paid": "1057920.86", "total_interest": "657920.86",
    "income_commitment_pct": "0.3171", "income_commitment_alert": true
  },
  "installments": [{ "month": 1, "payment": "4756.10", "interest": "3644.99",
                     "principal": "1111.11", "balance": "398888.89" }, ...]
}
```

## Custo de oportunidade

`POST /api/opportunity-cost` — body completo em [opportunity.py](../app/schemas/opportunity.py).

Retorna `summary` (verdict, breakeven_month, patrimônios finais nominal e real) + `points[]` mês a mês.

## BACEN

- `GET /api/bacen/selic` — Selic anualizada
- `GET /api/bacen/ipca` — IPCA acumulado 12m
- `GET /api/bacen/cdi` — CDI anualizado

Todos retornam `{ value, is_stale, fetched_at }`.

## Mercado de aluguéis

`GET /api/rentals/search?city=Rio+de+Janeiro&neighborhood=Botafogo`

**Resposta:**
- `200` → `{ stats: { mean, median, p25, p75, n, mean_per_m2, median_per_m2, by_source, stale }, listings: [...] }`
- `503` → `{ error: "...", available: false }` quando scrapers falham (use input manual).

## Códigos de erro

- `422`: validação Pydantic — body `{ errors: [{ field, message }, ...] }`.
- `503`: serviço externo indisponível (BACEN sem cache nem default; scrapers bloqueados).
