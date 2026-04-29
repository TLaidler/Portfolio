# Documentação acadêmica das fórmulas

> Referências: Hazzan, S. & Pompeo, J. N. *Matemática Financeira*, 6ª ed.; Banco Central do Brasil — Caderno de Educação Financeira; Beracha, E. & Johnson, K. (2012) — *Lessons from Over 30 Years of Buy versus Rent Decisions*.

---

## 1. Conversão de taxa anual para mensal

Existem duas convenções:

| Convenção | Fórmula | Onde se usa |
|---|---|---|
| **Equivalente / composta** (default) | `i_m = (1 + i_a)^(1/12) − 1` | Mercado financeiro, contratos modernos, finanças acadêmicas. |
| **Nominal / proporcional** | `i_m = i_a / 12` | Alguns contratos da CEF, exercícios didáticos antigos. |

### Por que a equivalente é a forma correta

A taxa equivalente preserva a invariância da capitalização composta:
```
(1 + i_m)^12 = 1 + i_a
```
Já a taxa nominal viola essa identidade: `(1 + i_a/12)^12 > 1 + i_a` para `i_a > 0`. Capitalizar mensalmente à `i_a/12` resulta em uma taxa anual *efetiva* maior que `i_a`. Portanto, na convenção nominal, o tomador paga mais do que parece.

Este projeto usa **equivalente por padrão**. A convenção nominal está disponível via flag `rate_convention="nominal"` para reproduzir contratos CEF.

---

## 2. Tabela PRICE (Sistema Francês — parcelas constantes)

Notação: `PV` = valor financiado, `i` = taxa mensal, `n` = prazo em meses, `SD_k` = saldo devedor após o pagamento do mês k.

**Parcela constante:**
```
PMT = PV · [ i · (1 + i)^n ] / [ (1 + i)^n − 1 ]
```

**Decomposição mensal:**
```
J_k    = SD_{k-1} · i              (juros do mês k)
A_k    = PMT − J_k                 (amortização do mês k)
SD_k   = SD_{k-1} − A_k            (novo saldo devedor)
```

**Forma fechada do saldo devedor:**
```
SD_k = PV · [ (1 + i)^n − (1 + i)^k ] / [ (1 + i)^n − 1 ]
```

**Total de juros:** `Σ J_k = n · PMT − PV`.

### Validação canônica (Hazzan & Pompeo, cap. 6)

| Parâmetro | Valor |
|---|---|
| PV | R$ 100.000,00 |
| i | 1% a.m. |
| n | 120 meses |
| PMT esperado | **R$ 1.434,71** |

Nosso teste `test_hazzan_pompeo_120_months` valida com tolerância R$ 0,02.

---

## 3. Tabela SAC (Sistema de Amortização Constante)

**Amortização constante:**
```
A = PV / n
```

**Mês k (k = 1, ..., n):**
```
SD_{k−1} = PV − (k − 1) · A
J_k      = SD_{k−1} · i
PMT_k    = A + J_k
SD_k     = SD_{k−1} − A
```

**Total de juros (forma fechada — soma de PA):**
```
Σ J_k = i · PV · (n + 1) / 2
```

### SAC × PRICE — comparação acadêmica

- SAC paga **menos juros nominais totais** (porque amortiza mais cedo).
- PRICE tem **parcela inicial menor** (mais previsível).
- **Em VPL descontado pela própria taxa do empréstimo, são equivalentes** (princípio de equivalência financeira).

A escolha não é "qual é melhor", e sim "qual fluxo de caixa cabe no orçamento do tomador".

---

## 4. Custo de oportunidade — comprar vs alugar+investir

### 4.1 Cenário A — Comprar (financiar)

Patrimônio do comprador no mês k:
```
W_A(k) = V_0 · (1 + g)^(k/12) − SD_k
```
onde:
- `V_0` = valor do imóvel hoje;
- `g` = taxa anual de valorização do imóvel (default 0, opcional usar IGP-M, IPCA ou índice FipeZap);
- `SD_k` = saldo devedor (calculado pela tabela SAC ou PRICE).

### 4.2 Cenário B-isobudget (orçamento mensal igual)

**Premissa:** o tomador gastaria o mesmo valor mensal nos dois cenários. Quando a parcela > aluguel, a diferença `Δ_k = PMT_k − R_k` é investida à Selic. Quando aluguel > parcela, há déficit (saca do investimento).

```
W_B^iso(k) = D · (1 + i_S)^k + Σ_{j=1}^{k} Δ_j · (1 + i_S)^(k−j)
```

onde `D` = entrada, `i_S` = Selic mensal (equivalente de Selic anual).

Esta é a comparação **academicamente mais defensável** porque preserva o poder de gasto do tomador entre os cenários.

### 4.3 Cenário B-real (desembolso real)

**Premissa:** o tomador desembolsa apenas o aluguel; a diferença com a parcela é considerada consumo livre. Apenas a entrada é investida.

```
W_B^real(k) = D · (1 + i_S)^k
```

Mais favorável ao "alugar" — reflete comportamento humano realista, mas viesa o resultado.

A interface oferece toggle entre os dois modelos com banner explicativo.

### 4.4 Reajuste de aluguel

```
R_k = R_0 · (1 + π)^⌊(k − 1)/12⌋
```
onde `π` = IPCA esperado (anual). Por padrão usa IPCA do BACEN.

### 4.5 Break-even

```
k* = min { k ∈ {1, ..., n} : W_A(k) ≥ W_B(k) }
```
Resolvido por iteração mês a mês (sem forma fechada por causa da variabilidade de `PMT_k` em SAC).

### 4.6 Payback da entrada via spread

Quanto tempo o spread mensal entre aluguel e juros do financiamento, capitalizado na Selic, demora para "pagar" a entrada imobilizada?

```
T = min { T : Σ_{k=1}^{T} (R_k − J_k) · (1 + i_S)^(T−k) ≥ D }
```

### 4.7 Valores reais (deflator IPCA)

Toda série pode ser convertida em valor real (poder de compra de hoje):
```
W_real(k) = W_nominal(k) / (1 + π)^(k/12)
```

A interface do `/custo-oportunidade` permite alternar entre nominal e real.

---

## 5. Comprometimento da renda

Regra prudencial do BACEN para crédito habitacional: **comprometimento ≤ 30% da renda bruta**.

```
comprometimento = PMT_1 / renda_mensal_bruta
```

Se > 30%, o sistema mostra alerta vermelho. Bancos podem rejeitar o financiamento; ainda que aceitem, o stress orçamentário é alto.

---

## 6. Limitações conhecidas do modelo

1. **Custos de transação não modelados:** ITBI (~3%), escritura (~1%), avaliação (~R$ 3-5k). Estes oneram o cenário Comprar.
2. **Seguros (MIP/DFI), IPTU, condomínio, manutenção:** não modelados. Onerariam o cenário Comprar entre 0,5%-1,5% do valor do imóvel ao ano.
3. **CET (Custo Efetivo Total)** não calculado — apenas a taxa contratual de juros. CET inclui seguros e tarifas e seria a TIR do fluxo do tomador. Marcado como TODO.
4. **Selic e IPCA tratados como constantes** ao longo do prazo. Realidade: ambos variam. Para análise de sensibilidade, recalcular com diferentes valores.
5. **Imposto de Renda sobre rendimentos**: não modelado. A Selic real líquida (pós-IR) é menor que a bruta — entre 15-22,5% conforme prazo. **Isso favorece comprar.**
6. **Liquidez do imóvel:** ativo ilíquido vs investimento líquido (CDI). Não há prêmio de liquidez modelado.
7. **Reajuste do aluguel:** assumido anual com IPCA. Contratos reais podem usar IGP-M ou ter cláusulas específicas.

Estas limitações estão documentadas no accordion **Metodologia** da página `/custo-oportunidade`.
