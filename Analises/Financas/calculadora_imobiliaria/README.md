# Calculadora Imobiliária

Simulador Flask de financiamento imobiliário (SAC e PRICE) com integração BACEN, análise de mercado de aluguéis (QuintoAndar + ZapImóveis) e comparativo "comprar vs alugar+investir".

> **Aviso:** ferramenta educacional. Não constitui recomendação financeira. Uso pessoal e didático apenas — sem redistribuição comercial dos dados coletados.

## Setup

### Início rápido (1 clique)

- **Windows:** dê duplo-clique em `start.bat`.
- **Linux / macOS:** `./start.sh` no terminal.

Os scripts criam o `.venv`, instalam dependências, copiam `.env.example` → `.env`, sobem o Flask e abrem o navegador em `http://127.0.0.1:5000/`.

### Setup manual

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # Linux/macOS

python run.py
```

## Páginas

| Rota | Descrição |
|---|---|
| `/` | Home com hero e proposta de valor. |
| `/simulador` | Calculadora SAC × PRICE com KPIs, tabela de amortização e gráfico de saldo devedor. |
| `/mercado` | Aluguéis médios coletados de QuintoAndar e ZapImóveis (Rio de Janeiro). |
| `/custo-oportunidade` | Comparação patrimonial Comprar vs Alugar+Investir, com toggle de cenários. |

## Stack

- **Backend:** Flask 3 + Pydantic v2 + Decimal em todo cálculo monetário.
- **Frontend:** Tailwind CSS (CDN) + Alpine.js + HTMX + Plotly.js + Lucide icons + Inter/JetBrains Mono.
- **Dados externos:** API SGS BACEN (Selic, IPCA, CDI) com cache JSON 24h.
- **Scrapers:** httpx + tenacity, cache SQLite 6h, fallback gracioso para input manual.

## Testes

```bash
pip install -r requirements-dev.txt
pytest tests/unit/ -v
```

Cobertura validada contra valores publicados em Hazzan & Pompeo, *Matemática Financeira*, 6ª ed.

## Documentação

- [docs/FORMULAS.md](docs/FORMULAS.md) — derivação acadêmica de SAC, PRICE, custo de oportunidade.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — princípios e camadas.
- [docs/API.md](docs/API.md) — contrato REST.

## Licenciamento dos dados

Os scrapers de QuintoAndar e ZapImóveis foram desenvolvidos com:
- respeito a `robots.txt` em runtime;
- rate limit interno (1 req/s teto, delay 2-5s);
- cache obrigatório de 6h;
- limite de 100 listagens por consulta;
- descarte de campos pessoais (telefone, e-mail, nome) na extração.

Uso pessoal e educacional. **Não use para fins comerciais ou redistribuição.**
