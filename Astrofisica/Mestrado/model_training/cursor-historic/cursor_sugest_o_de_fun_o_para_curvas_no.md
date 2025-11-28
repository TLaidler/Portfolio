# Sugestão de função para curvas no data base
_Exported on 11/28/2025 at 17:37:15 GMT-3 from Cursor (2.1.32)_

---

**User**

Leia esse arquivo .py com atenção. Me sugira uma função nova que busque todas as curvas positivas/negativas (parâmetro escolhido pelo usuário) do data base.

---

**Cursor**

### Sugestão de função

Abaixo uma função nova que retorna todas as curvas de luz positivas ou negativas (à sua escolha) diretamente do banco. Ela também pode normalizar os fluxos e limitar a quantidade retornada.

```python
def get_light_curves_by_polarity(polarity='positive', normalized=False, limit=None):
    """
    Busca todas as curvas de luz marcadas como 'positive' ou 'negative' 
    no campo additional_metadata da tabela observations.

    Args:
        polarity (str): 'positive' ou 'negative'.
        normalized (bool): Se True, adiciona 'flux_normalized' em cada curva.
        limit (int|None): Se informado, limita a quantidade de curvas retornadas.

    Returns:
        List[Tuple[curve, object_name, date, observer]]:
            Onde 'curve' é um dicionário com 'time', 'flux' (e opcionalmente 'flux_normalized').
    """
    polarity = (polarity or '').lower()
    if polarity not in ('positive', 'negative'):
        raise ValueError("polarity deve ser 'positive' ou 'negative'.")

    conn = connect_to_database()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, object_name, observation_date, additional_metadata
            FROM observations
            WHERE additional_metadata IS NOT NULL
              AND LOWER(additional_metadata) LIKE ?
            ORDER BY object_name, observation_date, id
        """, (f"%{polarity}%",))

        rows = cursor.fetchall()
        results = []

        for obs_id, obj, date, add_meta in rows:
            cursor.execute("""
                SELECT time, flux
                FROM light_curves
                WHERE observation_id = ?
                ORDER BY time
            """, (obs_id,))
            data = cursor.fetchall()
            if not data:
                continue

            times = [r[0] for r in data]
            fluxes = [r[1] for r in data]

            curve = {"time": times, "flux": fluxes}
            if normalized:
                curve["flux_normalized"] = normalize_flux(fluxes)

            observer = extract_observer_name(add_meta)
            results.append((curve, obj, date, observer))

            if limit is not None and len(results) >= limit:
                break

        return results

    except sqlite3.Error as e:
        print(f"Erro ao recuperar curvas '{polarity}': {e}")
        return []
    finally:
        conn.close()
```

### Como usar (exemplos rápidos)
- **Todas as curvas positivas normalizadas**:
```python
curves_pos = get_light_curves_by_polarity('positive', normalized=True)
```
- **Primeiras 50 curvas negativas (sem normalização)**:
```python
curves_neg = get_light_curves_by_polarity('negative', limit=50)
```
- **Plot das normalizadas**:
```python
plot_normalized_curves(curves_pos)
```

- **Compatível com `save_data_to_csv`** (basta separar listas):
```python
curves = get_light_curves_by_polarity('positive', normalized=True)
curves_dicts = [c for (c, _, _, _) in curves]
observers = [obs for (_, _, _, obs) in curves]
save_data_to_csv(curves_dicts, observers, "ALL", "ALL")
```

- Adiciona `get_light_curves_by_polarity` para buscar todas as curvas por polaridade direto no SQL, com opção de normalização e limite; retorna no mesmo formato usado pelos `plot_*`.

```python
def get_light_curves_by_polarity(polarity='positive', normalized=False, limit=None):
    """
    Busca todas as curvas de luz marcadas como 'positive' ou 'negative' 
    no campo additional_metadata da tabela observations.

    Args:
        polarity (str): 'positive' ou 'negative'.
        normalized (bool): Se True, adiciona 'flux_normalized' em cada curva.
        limit (int|None): Se informado, limita a quantidade de curvas retornadas.

    Returns:
        List[Tuple[curve, object_name, date, observer]]:
            Onde 'curve' é um dicionário com 'time', 'flux' (e opcionalmente 'flux_normalized').
    """
    polarity = (polarity or '').lower()
    if polarity not in ('positive', 'negative'):
        raise ValueError("polarity deve ser 'positive' ou 'negative'.")

    conn = connect_to_database()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, object_name, observation_date, additional_metadata
            FROM observations
            WHERE additional_metadata IS NOT NULL
              AND LOWER(additional_metadata) LIKE ?
            ORDER BY object_name, observation_date, id
        """, (f"%{polarity}%",))

        rows = cursor.fetchall()
        results = []

        for obs_id, obj, date, add_meta in rows:
            cursor.execute("""
                SELECT time, flux
                FROM light_curves
                WHERE observation_id = ?
                ORDER BY time
            """, (obs_id,))
            data = cursor.fetchall()
            if not data:
                continue

            times = [r[0] for r in data]
            fluxes = [r[1] for r in data]

            curve = {"time": times, "flux": fluxes}
            if normalized:
                curve["flux_normalized"] = normalize_flux(fluxes)

            observer = extract_observer_name(add_meta)
            results.append((curve, obj, date, observer))

            if limit is not None and len(results) >= limit:
                break

        return results

    except sqlite3.Error as e:
        print(f"Erro ao recuperar curvas '{polarity}': {e}")
        return []
    finally:
        conn.close()
```

```python
curves_pos = get_light_curves_by_polarity('positive', normalized=True)
```

```python
curves_neg = get_light_curves_by_polarity('negative', limit=50)
```

```python
plot_normalized_curves(curves_pos)
```

```python
curves = get_light_curves_by_polarity('positive', normalized=True)
curves_dicts = [c for (c, _, _, _) in curves]
observers = [obs for (_, _, _, obs) in curves]
save_data_to_csv(curves_dicts, observers, "ALL", "ALL")
```

---

**User**

A função "get_light_curves_by_type" não funciona corretamente pois o formato de "additional_metadata" é TEXT: observer: JordiMarco, is_positive: True.

Queremos verificar quais possuem "is_positive" positivo ou negativo

---

**Cursor**

### Correção: parsear `is_positive` em vez de procurar “positive/negative”

O campo `additional_metadata` é texto do tipo `observer: JordiMarco, is_positive: True`. Em vez de procurar “positive/negative” como substring, parseamos o valor booleado de `is_positive` e filtramos por ele.

Adicione este helper (logo após `extract_observer_name` fica coerente):

```python
def extract_is_positive(additional_metadata):
    """
    Extrai o valor booleano de is_positive do campo additional_metadata.
    Aceita variações como True/False/1/0 (case-insensitive) e ':' ou '='.
    Returns:
        bool | None
    """
    if not additional_metadata:
        return None
    m = re.search(r'is_positive\s*[:=]\s*(true|false|1|0)', additional_metadata, re.IGNORECASE)
    if not m:
        return None
    v = m.group(1).lower()
    return v in ('true', '1')
```

Substitua a sua `get_light_curves_by_type` por esta versão (aceita `'positive'/'negative'` ou bool):

```python
def get_light_curves_by_type(_type='positive', normalized=False, limit=None):
    """
    Busca todas as curvas de luz onde additional_metadata contém is_positive: True/False.

    Args:
        _type (str|bool): 'positive'/'negative' ou True/False.
        normalized (bool): Se True, adiciona 'flux_normalized' em cada curva.
        limit (int|None): Se informado, limita a quantidade de curvas retornadas.

    Returns:
        List[Tuple[curve, object_name, date, observer]]:
            Onde 'curve' é um dicionário com 'time', 'flux' (e opcionalmente 'flux_normalized').
    """
    # Normaliza o alvo para bool
    if isinstance(_type, bool):
        want_positive = _type
    else:
        key = (_type or '').strip().lower()
        if key in ('positive', 'pos', 'true', '1'):
            want_positive = True
        elif key in ('negative', 'neg', 'false', '0'):
            want_positive = False
        else:
            raise ValueError("type deve ser 'positive'/'negative' ou True/False.")

    conn = connect_to_database()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        # Pré-filtra por linhas que mencionem is_positive
        cursor.execute("""
            SELECT id, object_name, observation_date, additional_metadata
            FROM observations
            WHERE additional_metadata IS NOT NULL
              AND LOWER(additional_metadata) LIKE '%is_positive%'
            ORDER BY object_name, observation_date, id
        """)
        rows = cursor.fetchall()
        results = []

        for obs_id, obj, date, add_meta in rows:
            flag = extract_is_positive(add_meta)
            if flag is None or flag != want_positive:
                continue

            cursor.execute("""
                SELECT time, flux
                FROM light_curves
                WHERE observation_id = ?
                ORDER BY time
            """, (obs_id,))
            data = cursor.fetchall()
            if not data:
                continue

            times = [r[0] for r in data]
            fluxes = [r[1] for r in data]
            curve = {"time": times, "flux": fluxes}
            if normalized:
                curve["flux_normalized"] = normalize_flux(fluxes)

            observer = extract_observer_name(add_meta)
            results.append((curve, obj, date, observer))

            if limit is not None and len(results) >= limit:
                break

        return results

    except sqlite3.Error as e:
        print(f"Erro ao recuperar curvas por tipo '{_type}': {e}")
        return []
    finally:
        conn.close()
```

- Exemplo: curvas positivas normalizadas
```python
curves_pos = get_light_curves_by_type('positive', normalized=True)
```

- Exemplo: primeiras 100 negativas
```python
curves_neg = get_light_curves_by_type('negative', limit=100)
```

- Para booleano diretamente
```python
curves_pos = get_light_curves_by_type(True)
```

- Para salvar
```python
curves = get_light_curves_by_type('positive', normalized=True)
curves_dicts = [c for (c, _, _, _) in curves]
observers = [obs for (_, _, _, obs) in curves]
save_data_to_csv(curves_dicts, observers, "ALL", "ALL")
```

- Ajustei a busca para filtrar por `is_positive` de forma robusta (regex) e mantive opção de normalização e limite.

```python
def extract_is_positive(additional_metadata):
    """
    Extrai o valor booleano de is_positive do campo additional_metadata.
    Aceita variações como True/False/1/0 (case-insensitive) e ':' ou '='.
    Returns:
        bool | None
    """
    if not additional_metadata:
        return None
    m = re.search(r'is_positive\s*[:=]\s*(true|false|1|0)', additional_metadata, re.IGNORECASE)
    if not m:
        return None
    v = m.group(1).lower()
    return v in ('true', '1')
```

```python
def get_light_curves_by_type(_type='positive', normalized=False, limit=None):
    """
    Busca todas as curvas de luz onde additional_metadata contém is_positive: True/False.

    Args:
        _type (str|bool): 'positive'/'negative' ou True/False.
        normalized (bool): Se True, adiciona 'flux_normalized' em cada curva.
        limit (int|None): Se informado, limita a quantidade de curvas retornadas.

    Returns:
        List[Tuple[curve, object_name, date, observer]]:
            Onde 'curve' é um dicionário com 'time', 'flux' (e opcionalmente 'flux_normalized').
    """
    # Normaliza o alvo para bool
    if isinstance(_type, bool):
        want_positive = _type
    else:
        key = (_type or '').strip().lower()
        if key in ('positive', 'pos', 'true', '1'):
            want_positive = True
        elif key in ('negative', 'neg', 'false', '0'):
            want_positive = False
        else:
            raise ValueError("type deve ser 'positive'/'negative' ou True/False.")

    conn = connect_to_database()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        # Pré-filtra por linhas que mencionem is_positive
        cursor.execute("""
            SELECT id, object_name, observation_date, additional_metadata
            FROM observations
            WHERE additional_metadata IS NOT NULL
              AND LOWER(additional_metadata) LIKE '%is_positive%'
            ORDER BY object_name, observation_date, id
        """)
        rows = cursor.fetchall()
        results = []

        for obs_id, obj, date, add_meta in rows:
            flag = extract_is_positive(add_meta)
            if flag is None or flag != want_positive:
                continue

            cursor.execute("""
                SELECT time, flux
                FROM light_curves
                WHERE observation_id = ?
                ORDER BY time
            """, (obs_id,))
            data = cursor.fetchall()
            if not data:
                continue

            times = [r[0] for r in data]
            fluxes = [r[1] for r in data]
            curve = {"time": times, "flux": fluxes}
            if normalized:
                curve["flux_normalized"] = normalize_flux(fluxes)

            observer = extract_observer_name(add_meta)
            results.append((curve, obj, date, observer))

            if limit is not None and len(results) >= limit:
                break

        return results

    except sqlite3.Error as e:
        print(f"Erro ao recuperar curvas por tipo '{_type}': {e}")
        return []
    finally:
        conn.close()
```

```python
curves_pos = get_light_curves_by_type('positive', normalized=True)
```

```python
curves_neg = get_light_curves_by_type('negative', limit=100)
```

```python
curves_pos = get_light_curves_by_type(True)
```

```python
curves = get_light_curves_by_type('positive', normalized=True)
curves_dicts = [c for (c, _, _, _) in curves]
observers = [obs for (_, _, _, obs) in curves]
save_data_to_csv(curves_dicts, observers, "ALL", "ALL")
```

---

**User**

Termine de criar a função "get_sampled_light_curves_by_type" de forma que ele selecione apenas as observações com additional_metadata LOWER(additional_metadata) LIKE '%is_positive: True%' ou LOWER(additional_metadata) LIKE '%is_positive: False%'

---

**Cursor**

### Implementação final de `get_sampled_light_curves_by_type`

Abaixo está a versão completa que filtra diretamente por `is_positive: true/false` via SQL, monta as curvas e faz a amostragem. Adicionei também a opção `normalized` (opcional).

```440:492:model_training/astro_data_access.py
def get_sampled_light_curves_by_type(_type='positive', limit=None, normalized=False):
    """
    Busca uma amostra aleatória de curvas de luz do banco de dados,
    filtrando por is_positive: True/False no campo additional_metadata.

    Args:
        _type (str|bool): 'positive'/'negative' ou True/False.
        limit (int, opcional): Número máximo de curvas a retornar (amostradas).
        normalized (bool): Se True, adiciona 'flux_normalized' em cada curva.

    Returns:
        List[Tuple[curve, object_name, date, observer]]
    """
    if isinstance(_type, bool):
        want_positive = _type
    else:
        key = (_type or '').strip().lower()
        if key in ('positive', 'pos', 'true', '1'):
            want_positive = True
        elif key in ('negative', 'neg', 'false', '0'):
            want_positive = False
        else:
            raise ValueError("type deve ser 'positive'/'negative' ou True/False.")

    conn = connect_to_database()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        if want_positive:
            cursor.execute("""
                SELECT id, object_name, observation_date, additional_metadata
                FROM observations
                WHERE additional_metadata IS NOT NULL
                  AND LOWER(additional_metadata) LIKE '%is_positive: true%'
                ORDER BY object_name, observation_date, id
            """)
        else:
            cursor.execute("""
                SELECT id, object_name, observation_date, additional_metadata
                FROM observations
                WHERE additional_metadata IS NOT NULL
                  AND LOWER(additional_metadata) LIKE '%is_positive: false%'
                ORDER BY object_name, observation_date, id
            """)
        rows = cursor.fetchall()

        refs = []
        for obs_id, obj, date, add_meta in rows:
            cursor.execute("""
                SELECT time, flux
                FROM light_curves
                WHERE observation_id = ?
                ORDER BY time
            """, (obs_id,))
            data = cursor.fetchall()
            if not data:
                continue

            times = [r[0] for r in data]
            fluxes = [r[1] for r in data]
            curve = {"time": times, "flux": fluxes}
            if normalized:
                curve["flux_normalized"] = normalize_flux(fluxes)

            observer = extract_observer_name(add_meta)
            refs.append((curve, obj, date, observer))

        if limit and limit < len(refs):
            return random.sample(refs, limit)
        return refs

    except sqlite3.Error as e:
        print(f"Erro ao recuperar amostra por tipo '{_type}': {e}")
        return []
    finally:
        conn.close()
```

- Usei `LOWER(additional_metadata) LIKE '%is_positive: true%'`/`'%is_positive: false%'` para funcionar com `LOWER(...)`.
- A função retorna a lista completa quando `limit` não é fornecido; caso contrário, retorna uma amostra aleatória de tamanho `limit`.

```python
def get_sampled_light_curves_by_type(_type='positive', limit=None, normalized=False):
    """
    Busca uma amostra aleatória de curvas de luz do banco de dados,
    filtrando por is_positive: True/False no campo additional_metadata.

    Args:
        _type (str|bool): 'positive'/'negative' ou True/False.
        limit (int, opcional): Número máximo de curvas a retornar (amostradas).
        normalized (bool): Se True, adiciona 'flux_normalized' em cada curva.

    Returns:
        List[Tuple[curve, object_name, date, observer]]
    """
    if isinstance(_type, bool):
        want_positive = _type
    else:
        key = (_type or '').strip().lower()
        if key in ('positive', 'pos', 'true', '1'):
            want_positive = True
        elif key in ('negative', 'neg', 'false', '0'):
            want_positive = False
        else:
            raise ValueError("type deve ser 'positive'/'negative' ou True/False.")

    conn = connect_to_database()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        if want_positive:
            cursor.execute("""
                SELECT id, object_name, observation_date, additional_metadata
                FROM observations
                WHERE additional_metadata IS NOT NULL
                  AND LOWER(additional_metadata) LIKE '%is_positive: true%'
                ORDER BY object_name, observation_date, id
            """)
        else:
            cursor.execute("""
                SELECT id, object_name, observation_date, additional_metadata
                FROM observations
                WHERE additional_metadata IS NOT NULL
                  AND LOWER(additional_metadata) LIKE '%is_positive: false%'
                ORDER BY object_name, observation_date, id
            """)
        rows = cursor.fetchall()

        refs = []
        for obs_id, obj, date, add_meta in rows:
            cursor.execute("""
                SELECT time, flux
                FROM light_curves
                WHERE observation_id = ?
                ORDER BY time
            """, (obs_id,))
            data = cursor.fetchall()
            if not data:
                continue

            times = [r[0] for r in data]
            fluxes = [r[1] for r in data]
            curve = {"time": times, "flux": fluxes}
            if normalized:
                curve["flux_normalized"] = normalize_flux(fluxes)

            observer = extract_observer_name(add_meta)
            refs.append((curve, obj, date, observer))

        if limit and limit < len(refs):
            return random.sample(refs, limit)
        return refs

    except sqlite3.Error as e:
        print(f"Erro ao recuperar amostra por tipo '{_type}': {e}")
        return []
    finally:
        conn.close()
```

---

**User**

Refaça a função "normalize_flux". Do jeito que está, ele calcula a média geral da curva. O ideal é utilizar a média da parte negativa da curva. Podemos tirar uma média de cada quartil e separar. Jogar fora os dois quartis com menor média e utilizar uma média entre as duas maiores. 

---

**Cursor**

### Nova implementação de `normalize_flux` (média dos 2 melhores quartis contíguos)

A função abaixo segmenta a curva em 4 partes contíguas (quartis em tempo/índice), calcula a média de cada parte, descarta as duas menores e usa a média das duas maiores como baseline. Se o baseline não for positivo, retorna os valores originais.

```222:260:model_training/astro_data_access.py
def normalize_flux(flux_values):
    """
    Normaliza valores de fluxo usando como baseline a média dos dois quartis
    contíguos com maior média (aproxima a parte fora da ocultação).

    Estratégia:
    - Divide a série, na ordem temporal, em 4 segmentos contíguos (quartis).
    - Calcula a média de cada segmento.
    - Descarte os dois segmentos com menor média.
    - O baseline é a média das duas maiores médias.
    - Divide o fluxo inteiro por esse baseline.

    Em casos degenerados (poucos pontos, baseline <= 0 ou não finito),
    faz fallback para a média global positiva; se não for possível, retorna original.
    """
    if not flux_values:
        return []

    arr = np.asarray(flux_values, dtype=float)
    if arr.size == 0:
        return []

    # Considera apenas pontos finitos para estimar baseline
    finite_mask = np.isfinite(arr)
    if not finite_mask.any():
        return flux_values[:]
    arr_valid = arr[finite_mask]

    # Se poucos pontos, fallback para média global positiva
    if arr_valid.size < 4:
        mean_flux = float(np.mean(arr_valid))
        if np.isfinite(mean_flux) and mean_flux > 0:
            return (arr / mean_flux).tolist()
        return flux_values[:]

    # Quartis contíguos em ordem temporal
    segments = np.array_split(arr_valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]

    if not means:
        return flux_values[:]

    # Seleciona as duas maiores médias
    order = np.argsort(means)  # crescente
    top_two = []
    top_two.append(means[order[-1]])
    if len(means) >= 2:
        top_two.append(means[order[-2]])

    baseline = float(np.mean(top_two)) if top_two else float('nan')

    # Validação do baseline
    if not np.isfinite(baseline) or baseline <= 0:
        # fallback: média global positiva dos pontos válidos
        mean_flux = float(np.mean(arr_valid))
        if np.isfinite(mean_flux) and mean_flux > 0:
            return (arr / mean_flux).tolist()
        return flux_values[:]

    return (arr / baseline).tolist()
```

- Usa quartis contíguos (tempo) para estimar baseline fora da ocultação.
- Tem fallbacks seguros para séries curtas ou baseline não positivo.

- Alterei `normalize_flux` para usar a média das duas maiores médias entre 4 segmentos contíguos; inclui fallbacks para poucos pontos e baseline inválido.

```python
def normalize_flux(flux_values):
    """
    Normaliza valores de fluxo usando como baseline a média dos dois quartis
    contíguos com maior média (aproxima a parte fora da ocultação).

    Estratégia:
    - Divide a série, na ordem temporal, em 4 segmentos contíguos (quartis).
    - Calcula a média de cada segmento.
    - Descarte os dois segmentos com menor média.
    - O baseline é a média das duas maiores médias.
    - Divide o fluxo inteiro por esse baseline.

    Em casos degenerados (poucos pontos, baseline <= 0 ou não finito),
    faz fallback para a média global positiva; se não for possível, retorna original.
    """
    if not flux_values:
        return []

    arr = np.asarray(flux_values, dtype=float)
    if arr.size == 0:
        return []

    # Considera apenas pontos finitos para estimar baseline
    finite_mask = np.isfinite(arr)
    if not finite_mask.any():
        return flux_values[:]
    arr_valid = arr[finite_mask]

    # Se poucos pontos, fallback para média global positiva
    if arr_valid.size < 4:
        mean_flux = float(np.mean(arr_valid))
        if np.isfinite(mean_flux) and mean_flux > 0:
            return (arr / mean_flux).tolist()
        return flux_values[:]

    # Quartis contíguos em ordem temporal
    segments = np.array_split(arr_valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]

    if not means:
        return flux_values[:]

    # Seleciona as duas maiores médias
    order = np.argsort(means)  # crescente
    top_two = []
    top_two.append(means[order[-1]])
    if len(means) >= 2:
        top_two.append(means[order[-2]])

    baseline = float(np.mean(top_two)) if top_two else float('nan')

    # Validação do baseline
    if not np.isfinite(baseline) or baseline <= 0:
        # fallback: média global positiva dos pontos válidos
        mean_flux = float(np.mean(arr_valid))
        if np.isfinite(mean_flux) and mean_flux > 0:
            return (arr / mean_flux).tolist()
        return flux_values[:]

    return (arr / baseline).tolist()
```

---

**User**

@simulate_curve.py Me explique didaticamente do que se trata esse script

---

**Cursor**

### Visão geral
`model_training/simulate_curve.py` é um simulador de curvas de luz de ocultações estelares. Ele gera séries temporais de fluxo incluindo:
- difração de Fresnel na imersão/emersão,
- efeitos de anéis e satélite,
- turbulência atmosférica (seeing) e ruídos instrumentais,
- conversões fotométricas (magnitude ↔ fluxo, fótons).

### Principais blocos
- **Constantes e unidades**: define constantes físicas e fatores de conversão usados nas contas.
- **Fotometria**: funções para calcular fluxo a partir de magnitude e converter fluxo em contagem de fótons.
- **Geometria angular**: diâmetro angular, escala de placa e tamanhos projetados.
- **Difração de Fresnel**:
  - `calc_fresnel`: escala de Fresnel.
  - `bar_fresnel`: modelo de curva de Fresnel para intervalos de imersão/emersão (X01/X02). É aplicado ao corpo principal, anéis e satélite.
- **Turbulência atmosférica**: perfis de Cn² por camadas, escolha de regime de seeing, parâmetros como `r0`, variância de fase, fator de média de abertura e variância de irradiância.
- **Ruídos**: ruído térmico (dark), ruído de leitura e “scintillation” via termos lognormais/gaussianos.
- **Cenário da ocultação**: define velocidade, tempos, tamanhos (corpo, anéis, satélite), distância, banda, tempo de exposição etc.; monta o vetor temporal.
- **Geração das curvas**:
  - calcula curvas de Fresnel separadas (corpo, anéis, satélite) e as combina (produto/mistura),
  - gera uma série ruidosa de fluxo por integração de fótons nas janelas de tempo,
  - normaliza (mediana) e plota as curvas.
- **Saída**: gráficos da curva simulada e normalizada; salva figura (ex.: `imags/2.5_0.01.png`) e imprime valores intermediários para diagnóstico.

### Fluxo de execução (resumo)
1. Define parâmetros físicos/observacionais (magnitudes, diâmetros, banda, seeing, tempo de exposição, velocidade).
2. Calcula a escala de Fresnel e as curvas de difração para corpo/anéis/satélite.
3. Simula contagem de fótons com ruídos atmosféricos e instrumentais ao longo do tempo.
4. Normaliza por uma mediana e combina com as curvas de Fresnel.
5. Plota e salva os resultados.

### Observações rápidas
- O script é didático e monolítico; há trechos de depuração e possíveis inconsistências (ex.: uso de `==` onde deveria ser atribuição, uma referência a `self.d_star` fora de classe, unidades m/cm misturadas). Se quiser, posso ajudar a modularizar e corrigir esses pontos.

---

**User**

@simulate_curve.py You are an expert in astrophysics and scientific development in Python.

I want you to completely rewrite the code simulate_curve.py, which is currently a simulator of stellar occultation light curves that includes Fresnel diffraction, rings, satellites, atmospheric turbulence, and instrumental noise.



The goal is to reorganize the code into a modern and modular Python class structure, for example called SyntheticLightCurveSimulator, which should:



Create synthetic light curves based on physical and observational parameters.



Respect the laws of physics and the mathematical rigor of Fresnel diffraction and atmospheric effects.



Be intuitive for use by astronomers and students, allowing the generation of new curves by simply providing basic parameters.



🧩 Class Specifications



Main class: SyntheticLightCurveSimulator



Expected methods:



__init__(...): initializes the physical and observational parameters (magnitudes, distance, diameters, band, exposure time, seeing, velocity, etc.).



simulate(): runs the full simulation (diffraction, seeing, noise, normalization).



plot_curve(save=True): generates and saves a .png plot of the simulated curve.



export_data(save=True): returns a pandas.DataFrame with the simulated time and flux data, and automatically saves it as 'curva_sintetica_1.dat', 'curva_sintetica_2.dat', etc., in the local folder.



🧮 Technical Requirements



Use numpy, pandas, and matplotlib.



Follow scientific best practices and object-oriented programming (OOP) principles.



Document every method with Google-style or NumPy-style docstrings.



Include explanatory comments for all physical equations (e.g., Fresnel scale, magnitude–flux conversion, atmospheric turbulence).



Ensure reproducibility and clarity, even for users with limited Python experience.



Avoid unnecessary dependencies (no external frameworks beyond the essential scientific libraries).



The final plot must include a legend, labeled axes with units, and an informative title (e.g., “Synthetic light curve with diffraction and seeing — V band”).



🧠 Expected Folder Structure

synthetic_curve/

├── simulate_curve.py   # rewritten code (main class)

├── output/

│   ├── curva_sintetica_1.dat

│   ├── curva_sintetica_2.dat

│   └── curves/

│       ├── curva_sintetica_1.png

│       └── curva_sintetica_2.png



📈 Example of Expected Usage

from simulate_curve import SyntheticLightCurveSimulator



sim = SyntheticLightCurveSimulator(

    mag_star=12.5,

    distance_km=4000,

    diameter_km=1200,

    exposure_time=0.1,

    seeing_arcsec=1.0,

    velocity_kms=20,

    include_rings=True,

    include_satellite=False

)



df = sim.simulate()

sim.plot_curve(save=True)

sim.export_data(save=True)



🎯 Final Objective



The script must be fully restructured and self-contained, while maintaining scientific accuracy.

The code should be readable, modular, and educational, allowing future users to easily modify parameters and generate new curves.

The final result should be a publication-grade code, yet simple enough for educational and exploratory purposes.

---

**Cursor**

Vou criar uma classe modular nova em um arquivo `synthetic_curve/simulate_curve.py`, com métodos para simular, plotar e exportar dados, incluindo difração de Fresnel (com fallback sem SciPy), ruído atmosférico e instrumental, além de suporte a anéis e satélite. Em seguida, eu gero as pastas de saída requeridas.

Vou começar criando o novo arquivo com a classe e toda a implementação necessária, incluindo um método de aproximação para Fresnel caso SciPy não esteja disponível, além de garantir as pastas de saída.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Synthetic stellar occultation light-curve simulator.

This module defines the SyntheticLightCurveSimulator class, which generates
publication-grade synthetic light curves for stellar occultations, including:
 - Fresnel diffraction at immersion/emersion edges
 - Optional rings (partial opacity) and satellite (secondary body)
 - Atmospheric scintillation and instrumental noise
 - Normalization to out-of-occultation baseline

Dependencies: numpy, pandas, matplotlib (SciPy optional; used if available).
"""

from __future__ import annotations

import os
import math
import glob
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class SyntheticLightCurveSimulator:
    """Synthetic stellar occultation light-curve simulator.

    This class creates synthetic light curves for a stellar occultation event,
    combining Fresnel diffraction physics with atmospheric and instrumental effects.
    It is designed to be educational, readable, and scientifically grounded.

    Parameters
    ----------
    mag_star : float
        Stellar magnitude (apparent). Used to set relative photon rate.
    distance_km : float
        Observer-to-occulting-body distance in km (for Fresnel scale).
    diameter_km : float
        Projected diameter of the occulting body along the chord, in km.
    velocity_kms : float
        Relative shadow velocity across the star in km/s.
    exposure_time : float
        Exposure time per sample in seconds (cadence). The time step uses this value.
    duration_s : Optional[float]
        Total simulation duration in seconds. If None, computed from diameter/velocity plus margins.
    wavelength_nm : float
        Effective wavelength in nanometers (e.g., 550 nm for V band). Used in Fresnel scale.
    seeing_arcsec : float
        Seeing FWHM in arcseconds (used heuristically to set scintillation level).
    include_rings : bool
        Whether to include ring dips (partial opacity segments).
    rings : Optional[List[Tuple[float, float, float]]]
        List of ring segments, each tuple (center_offset_km, width_km, opacity),
        where opacity is between 0 and 1. center_offset_km is measured from event center
        along the chord; width is the ring radial thickness projected along chord.
    include_satellite : bool
        Whether to include a satellite occultation.
    satellite : Optional[Dict[str, float]]
        Satellite parameters: {"offset_km": float, "diameter_km": float}.
    random_seed : Optional[int]
        Seed for reproducibility of random processes (noise).
    normalize_method : str
        "top_quartiles" (default) or "median_all". Defines how to compute baseline for normalization.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4000.0,
        diameter_km: float = 1200.0,
        velocity_kms: float = 20.0,
        exposure_time: float = 0.1,
        duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        include_rings: bool = False,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        include_satellite: bool = False,
        satellite: Optional[Dict[str, float]] = None,
        random_seed: Optional[int] = None,
        normalize_method: str = "top_quartiles",
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time = float(exposure_time)
        self.duration_s = float(duration_s) if duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.include_rings = bool(include_rings)
        self.rings = rings if rings is not None else []
        self.include_satellite = bool(include_satellite)
        self.satellite = satellite
        self.normalize_method = normalize_method

        # Output folders
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_output_dirs()

        # Randomness
        self.rng = np.random.default_rng(random_seed)

        # Internals populated by simulate()
        self._time_s: Optional[np.ndarray] = None
        self._flux: Optional[np.ndarray] = None
        self._flux_norm: Optional[np.ndarray] = None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def simulate(self) -> pd.DataFrame:
        """Run the full simulation: diffraction, rings/satellite, noise, normalization.

        Returns
        -------
        pandas.DataFrame
            DataFrame with columns: ["time_s", "flux", "flux_norm"].
            "flux" is raw flux including noise; "flux_norm" is normalized to baseline ~ 1.
        """
        # 1) Build time axis and chord coordinate
        t, x = self._build_time_and_chord()

        # 2) Diffraction transmission for the main body (opaque strip)
        T_body = self._opaque_strip_transmission(x, center_km=0.0, width_km=self.diameter_km)

        # 3) Rings (partial opacity strips)
        T_rings = np.ones_like(T_body)
        if self.include_rings and self.rings:
            for (center_offset_km, width_km, opacity) in self.rings:
                T_rings *= self._partial_strip_transmission(
                    x, center_km=center_offset_km, width_km=width_km, opacity=float(opacity)
                )

        # 4) Satellite (opaque strip), if provided
        T_sat = np.ones_like(T_body)
        if self.include_satellite and self.satellite is not None:
            sat_offset = float(self.satellite.get("offset_km", 0.0))
            sat_diam = float(self.satellite.get("diameter_km", 0.0))
            if sat_diam > 0:
                T_sat = self._opaque_strip_transmission(x, center_km=sat_offset, width_km=sat_diam)

        # 5) Combine transmissions (multiplicative – independent attenuators)
        T_total = np.clip(T_body * T_rings * T_sat, 0.0, 1.0)

        # 6) Convert star magnitude to relative photon rate (arbitrary units)
        #    We use a simple magnitude-to-flux relation:
        #        F ~ 10^(-0.4 * mag_star)
        #    Then we scale so that the median baseline is near ~1 after normalization.
        base_flux = self._mag_to_flux(self.mag_star)
        expected_counts = base_flux * T_total

        # 7) Add atmospheric and instrumental noise
        noisy_flux = self._apply_noise(expected_counts)

        # 8) Normalize flux to out-of-occultation baseline
        flux_norm = self._normalize_flux(noisy_flux)

        # 9) Persist in instance and return DataFrame
        self._time_s = t
        self._flux = noisy_flux
        self._flux_norm = flux_norm

        df = pd.DataFrame(
            {
                "time_s": self._time_s,
                "flux": self._flux,
                "flux_norm": self._flux_norm,
            }
        )
        return df

    def plot_curve(self, save: bool = True, show: bool = False, title_suffix: str = "") -> None:
        """Plot the simulated curve with labels, legend, and title.

        Parameters
        ----------
        save : bool
            If True, saves the plot under output/curves/ as PNG.
        show : bool
            If True, calls plt.show() after plotting.
        title_suffix : str
            Extra text appended to the plot title.
        """
        self._require_simulated()

        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(self._time_s, self._flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adimensional]")
        band_label = f"{int(round(self.wavelength_nm))} nm"
        title = f"Curva sintética com difração e seeing — {band_label}"
        if title_suffix:
            title += f" — {title_suffix}"
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()

        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)

    def export_data(self, save: bool = True) -> pd.DataFrame:
        """Return simulated data as DataFrame and optionally save as .dat.

        The file is saved as 'curva_sintetica_N.dat' in 'output/' with N auto-incremented.

        Parameters
        ----------
        save : bool
            If True, saves the data file to disk.

        Returns
        -------
        pandas.DataFrame
            DataFrame with columns: ["time_s", "flux", "flux_norm"].
        """
        self._require_simulated()
        df = pd.DataFrame({"time_s": self._time_s, "flux": self._flux, "flux_norm": self._flux_norm})
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df

    # -------------------------------------------------------------------------
    # Internals — physics & numerics
    # -------------------------------------------------------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        """Create the time axis and chord coordinate X(t) = v * (t - t0).

        If duration is not provided, we include margins of one diameter on each side.
        """
        if self.duration_s is None:
            # total time ~ body crossing time + 2x margin
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time + 2.0 * cross_time
        else:
            total_time = self.duration_s

        n_steps = max(2, int(math.ceil(total_time / self.exposure_time)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])  # center time
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _mag_to_flux(self, mag: float) -> np.ndarray:
        """Convert magnitude to relative photon rate (arbitrary units).

        We use:
            F ∝ 10^(-0.4 * mag)
        This is sufficient for relative curves. Absolute calibration can be set by scaling.
        """
        F0 = 1.0  # relative zero point
        return F0 * 10.0 ** (-0.4 * mag)

    # -------------------- Fresnel diffraction core ---------------------------
    def _fresnel_scale_km(self) -> float:
        """Fresnel scale in km: F = sqrt(lambda * D / 2).

        Notes
        -----
        - wavelength_nm is converted to km (1 nm = 1e-12 km).
        """
        lambda_km = self.wavelength_nm * 1e-12
        F = math.sqrt(max(lambda_km * self.distance_km / 2.0, 1e-30))
        return F

    def _fresnel_C_S(self, u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute Fresnel integrals C(u), S(u).

        This method tries to use SciPy if available for high fidelity, else
        falls back to polynomial/asymptotic approximations adequate for education.

        Parameters
        ----------
        u : np.ndarray
            Dimensionless coordinate (x / Fresnel_scale).

        Returns
        -------
        (C, S) : Tuple[np.ndarray, np.ndarray]
            Fresnel integrals of u.
        """
        try:
            # Optional high-accuracy path
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore

            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback approximation:
        # Adapted from standard rational/power approximations (Numerical Recipes-like).
        # Good for general educational use; not for metrology-grade analysis.
        x = np.abs(u)
        C = np.zeros_like(u, dtype=float)
        S = np.zeros_like(u, dtype=float)

        # Region 1: small arguments (power series)
        mask1 = x <= 1.5
        if np.any(mask1):
            z = u[mask1]
            z2 = z * z
            z4 = z2 * z2
            z6 = z4 * z2
            z8 = z4 * z4
            # Truncated series for C(z) and S(z) (A&S 7.3.1 & 7.3.2, re-scaled u)
            # Note: Using limited terms for performance/simplicity.
            C[mask1] = (
                z
                - (math.pi**2) * (z**5) / 40.0
                + (math.pi**4) * (z**9) / 3456.0
            ) * (1.0 / math.sqrt(2.0 * math.pi))
            S[mask1] = (
                (math.pi) * (z**3) / 6.0
                - (math.pi**3) * (z**7) / 336.0
                + (math.pi**5) * (z**11) / 42240.0
            ) * (1.0 / math.sqrt(2.0 * math.pi))

        # Region 2: large arguments (asymptotic)
        mask2 = ~mask1
        if np.any(mask2):
            z = u[mask2]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[mask2] = c
            S[mask2] = s

        return C, S

    def _knife_edge_transmission(self, x_km: np.ndarray, edge_pos_km: float) -> np.ndarray:
        """Knife-edge diffraction transmission for a semi-infinite opaque plane.

        We use the standard intensity for a straight edge:
            I(u) = 0.5 * [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ]
        where u = (x - edge_pos) / F, with F the Fresnel scale.
        """
        F = self._fresnel_scale_km()
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = self._fresnel_C_S(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    def _opaque_strip_transmission(self, x_km: np.ndarray, center_km: float, width_km: float) -> np.ndarray:
        """Transmission for an opaque strip using two knife edges (immersion/emersion).

        The strip spans [center - width/2, center + width/2].
        Transmission is approximated as the product of a rising and a falling edge:
            T_strip(x) ≈ T_edge(x - x1) * T_edge_rev(x - x2)
        where T_edge_rev(u) = T_edge(-u), ensuring an opaque center region.
        """
        half = 0.5 * width_km
        x1 = center_km - half
        x2 = center_km + half
        T1 = self._knife_edge_transmission(x_km, x1)
        T2 = self._knife_edge_transmission(-x_km, -x2)  # reverse edge
        T = np.clip(T1 * T2, 0.0, 1.0)
        return T

    def _partial_strip_transmission(
        self, x_km: np.ndarray, center_km: float, width_km: float, opacity: float
    ) -> np.ndarray:
        """Transmission for a partially opaque strip (e.g., a ring segment).

        For geometric optics, the inside would transmit (1 - opacity).
        With diffraction smoothing, we blend using the opaque-strip transmission T_opaque:
            T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = self._opaque_strip_transmission(x_km, center_km, width_km)
        return 1.0 - opacity * (1.0 - T_opaque)

    # -------------------- Noise models & normalization -----------------------
    def _apply_noise(self, expected_counts: np.ndarray) -> np.ndarray:
        """Apply atmospheric scintillation and instrumental noise.

        Notes
        -----
        - Scintillation: modeled as multiplicative log-normal noise with sigma set
          heuristically from seeing and exposure time (longer exposures average more).
        - Photon (shot) noise: Poisson around expected counts scaled to a convenient level.
        - Readout noise: Gaussian additive noise in counts (small).
        """
        expected = np.clip(expected_counts, 1e-8, None)

        # Scale counts to a convenient level (arbitrary gain so S/N is reasonable)
        gain = 4e5  # counts per unit relative flux (choose generous to see diffraction cleanly)
        lam = expected * gain * self.exposure_time

        # Photon noise (Poisson)
        lam = np.clip(lam, 0, 1e12)
        shot = self.rng.poisson(lam)

        # Readout noise (Gaussian), standard deviation in counts
        readout_sigma = 5.0
        readout = self.rng.normal(0.0, readout_sigma, size=shot.size)

        # Scintillation: multiplicative log-normal factor
        # Heuristic sigma_ln: worse for poor seeing, better for longer exposure
        sigma_ln = max(0.001, 0.02 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time, 1e-3)))
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=shot.size))

        counts = (shot + readout) * scint

        # Convert back to relative flux units
        flux = counts / (gain * self.exposure_time)
        return np.clip(flux, 0.0, None)

    def _normalize_flux(self, flux: np.ndarray) -> np.ndarray:
        """Normalize flux to an out-of-occultation baseline of ~1.

        Methods
        -------
        - "top_quartiles": split in 4 contiguous quartiles (in time), compute the
          mean of each; discard the two lowest; baseline = mean of top two means.
        - "median_all": baseline = median(flux).
        """
        if self.normalize_method == "median_all":
            baseline = float(np.median(flux))
        else:
            # default: "top_quartiles"
            valid = flux[np.isfinite(flux)]
            if valid.size < 4:
                baseline = float(np.mean(valid)) if valid.size else 1.0
            else:
                segments = np.array_split(valid, 4)
                means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
                if len(means) == 0:
                    baseline = float(np.median(valid))
                else:
                    order = np.argsort(means)
                    top = [means[order[-1]]]
                    if len(means) >= 2:
                        top.append(means[order[-2]])
                    baseline = float(np.mean(top))

        if not np.isfinite(baseline) or baseline <= 0:
            baseline = float(np.median(flux[np.isfinite(flux)])) if np.any(np.isfinite(flux)) else 1.0
            if baseline <= 0 or not np.isfinite(baseline):
                return flux.copy()
        return (flux / baseline).astype(float)

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    def _ensure_output_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        """Find next incremental index for outputs."""
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                stem = os.path.splitext(os.path.basename(path))[0]
                n = int(stem.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulated(self) -> None:
        if self._time_s is None or self._flux is None or self._flux_norm is None:
            raise RuntimeError("Nenhuma simulação encontrada. Chame simulate() antes.")


# ----------------------------- Usage example ---------------------------------
if __name__ == "__main__":
    # Example usage matching the requested API
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4000.0,
        diameter_km=1200.0,
        exposure_time=0.1,
        seeing_arcsec=1.0,
        velocity_kms=20.0,
        include_rings=True,
        rings=[(8000.0, 200.0, 0.2)],  # (center_offset_km, width_km, opacity)
        include_satellite=False,
        satellite=None,
        random_seed=42,
    )
    df = sim.simulate()
    sim.plot_curve(save=True, show=False)
    sim.export_data(save=True)

```

Concluí a reescrita completa em uma classe modular no arquivo `synthetic_curve/simulate_curve.py`, com simulação, plot e exportação, incluindo difração de Fresnel (com fallback sem SciPy), anéis, satélite, ruído atmosférico/instrumental e normalização.

Como usar (exemplo mínimo):
```python
from synthetic_curve.simulate_curve import SyntheticLightCurveSimulator

sim = SyntheticLightCurveSimulator(
    mag_star=12.5,
    distance_km=4000,
    diameter_km=1200,
    exposure_time=0.1,
    seeing_arcsec=1.0,
    velocity_kms=20,
    include_rings=True,
    rings=[(8000.0, 200.0, 0.2)],  # (offset_km, largura_km, opacidade)
    include_satellite=False,
    random_seed=42,
)
df = sim.simulate()
sim.plot_curve(save=True)         # salva em synthetic_curve/output/curves/
sim.export_data(save=True)        # salva em synthetic_curve/output/
```

Observações rápidas
- Difração: usa integral de Fresnel de SciPy quando disponível; caso contrário, aplica aproximações polinomiais/assintóticas documentadas (adequadas para uso educacional).
- Corpo principal: modelado como “faixa opaca” (dois knife-edges); anéis como “faixas parcialmente opacas” com mistura física T = 1 − τ(1 − T_opaca).
- Satélite: faixa opaca deslocada, opcional.
- Ruído: Poisson (fótons), leitura gaussiana e cintilação log-normal (heurística baseada em seeing e tempo de exposição).
- Normalização: por padrão usa média dos 2 maiores quartis contíguos; opção “median_all” disponível.
- Pastas: cria automaticamente `synthetic_curve/output/` e `synthetic_curve/output/curves/` e numera arquivos `curva_sintetica_#.dat` e `.png`.

Resumo das mudanças
- Criei `SyntheticLightCurveSimulator` com métodos `__init__`, `simulate`, `plot_curve` e `export_data`.
- Implementação física: escala de Fresnel, knife-edge, faixa opaca, anéis parciais, satélite e ruído realista.
- Saídas prontas para uso: DataFrame, PNG com legenda/título/labels e arquivos `.dat` numerados em `synthetic_curve/output/`._a += cyc
```

- **Normal

```python
from synthetic_curve.simulate_curve import SyntheticLightCurveSimulator

sim = SyntheticLightCurveSimulator(
    mag_star=12.5,
    distance_km=4000,
    diameter_km=1200,
    exposure_time=0.1,
    seeing_arcsec=1.0,
    velocity_kms=20,
    include_rings=True,
    rings=[(8000.0, 200.0, 0.2)],  # (offset_km, largura_km, opacidade)
    include_satellite=False,
    random_seed=42,
)
df = sim.simulate()
sim.plot_curve(save=True)         # salva em synthetic_curve/output/curves/
sim.export_data(save=True)        # salva em synthetic_curve/output/
```

```plaintext

- **Normal
```

---

**User**

@model_training/synthetic_curve/simulate_curveC&P.py  Preciso que me explique didaticamente o que o código abaixo está fazendo. Sou astronomo e quero criar curvas de luz de ocultações estelares pós fotometria artificiais, para verificar o que seria esperado para um corpo especifico.

---

**Cursor**

### O que este script faz (visão geral)
Ele tenta gerar curvas de luz sintéticas de ocultações estelares, combinando:
- Difração de Fresnel nos instantes de imersão/emersão do corpo principal.
- Contribuições opcionais de anéis (opacidade parcial) e de um satélite (ocultação secundária).
- Efeitos atmosféricos (cintilação/seeing) e ruídos instrumentais.
- Conversões fotométricas simples (magnitude → fluxo; fluxo → fótons).
- Normalização “pós-fotometria” (trazendo o nível de fora da ocultação para ≈1).
- Plots da curva resultante.

A ideia é aproximar o que você esperaria observar para um corpo específico, dados diâmetro, distância, velocidade do evento, anéis, etc.

### Blocos principais do código
- Fotometria e conversões
  - `Fluxo_lambda(magnitude)`: aproxima o fluxo em função da magnitude da estrela.
  - `fluxo_fotons(fluxo, lamb)`: converte fluxo em contagem de fótons.
  - Algumas variantes tentam injetar ruído lognormal na irradiância para simular cintilação.
  
- Escala e difração de Fresnel
  - `calc_fresnel(distance, bandpass)`: calcula a escala de Fresnel \(F=\sqrt{\lambda D/2}\) para distância do corpo e comprimento de onda efetivo.
  - `bar_fresnel(X, X01, X02, opacity, distance, bandpass)`: modelo de faixa (bar) com dois “knife-edges” (imersão/emersão) usando integrais de Fresnel de SciPy para gerar o perfil de difração:
  
```138:156:model_training/synthetic_curve/simulate_curveC&P.py
    import scipy.special as scsp
    ...
    s1, c1 = scsp.fresnel(x1)
    s2, c2 = scsp.fresnel(x2)
    cc = c1 - c2
    ss = s1 - s2
    r_ampli = - (cc + ss) * (opacity / 2.)
    i_ampli = (cc - ss) * (opacity / 2.)
    flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
```

- Turbulência atmosférica e seeing
  - A partir de um valor de seeing, escolhe um perfil empírico de turbulência (coeficientes A, B, C, D e escalas de altura) e obtém grandezas como `r0`, variância de fase e variância de irradiância. Isso determina a intensidade da cintilação (ruído multiplicativo).
  - Usa integrais e fatores de atenuação de abertura para estimar a variância da irradiância (modelo de Saha/Hardy/Tyson em versões simplificadas).

- Ruídos instrumentais
  - Funções esboçadas para ruído térmico e de leitura; em outras rotinas o ruído é injetado via Poisson (contagem de fótons) e ruído lognormal (cintilação).

- Geometria da ocultação e linha do tempo
  - Define o tempo de simulação, o vetor temporal `times` e a coordenada ao longo da corda `Xs = v * t`.
  - Determina início/fim da ocultação principal a partir do diâmetro do corpo e da velocidade.
  - Define segmentos para anéis (com opacidade parcial) e, se desejado, um satélite (offset e diâmetro), criando pares (X01, X02) para cada “faixa” que cruza a estrela.

- Geração das curvas “ópticas” (sem ruído) e combinação
  - Calcula curvas de Fresnel para corpo principal, anéis e satélite; depois multiplica tudo para obter a transmissão total:
  
```870:879:model_training/synthetic_curve/simulate_curveC&P.py
Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)
...
Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)
plt.plot(times,Fres_tot, 'o-', ... )
plt.title("Simulação com Difração de Fresnel")
```

- Síntese de observação com ruído e normalização
  - Em um laço temporal, integra o fluxo observável em cada exposição, aplicando o “estado” geométrico (dentro/fora do corpo, anel, satélite) e ruídos.
  - Normaliza a curva para que a média/mediana fora da ocultação fique ≈1:
  
```904:931:model_training/synthetic_curve/simulate_curveC&P.py
med=np.median(flua[0:40])
for i in range(len(flua)):
    flua[i]=flua[i]/med
...
Flua_fresn=[]
for j in range(len(Flua_fres)):
    Flua_fresn.append(Flua_fres[j]/med)
```

- Visualização
  - Plota e salva figuras (curvas de Fresnel individuais e a curva final normalizada).

### Como os parâmetros controlam a curva
- Corpo principal
  - `diametro_corpo`, `distancia`, `vel` (velocidade do evento) → definem começo/fim da ocultação e o espaçamento das franjas (via Fresnel).
- Anéis
  - Conjuntos início/fim e opacidades → criam atenuações parciais adicionais (franjas mais suaves).
- Satélite
  - Offset e diâmetro → gera uma pequena ocultação separada com sua própria difração.
- Observação
  - `tempexp` (tempo de exposição) e banda `band` → definem amostragem e a escala de Fresnel.
  - `diam_teles`, `readout_noise`, `temperatura` → afetam contagem e ruído.
  - Seeing → controla a cintilação (ruído multiplicativo).

### O que usar para “pós-fotometria”
- A pipeline faz a normalização final (fora da ocultação ≈1), então o resultado imita uma curva “pós-fotometria”.
- Para um corpo específico: ajuste `diametro_corpo`, `distancia`, `vel`, posição dos anéis/satélite e `band`. Ajuste `tempexp` para o seu cadence e `seeing`/`diam_teles` para o local/instrumento.

### Limitações e cuidados
- Há problemas de implementação:
  - Mistura de unidades e constantes; várias prints/experimentos deixados no código.
  - Trechos com bug de atribuição (`==` onde deveria ser `=`) e referência a `self.d_star` em contexto sem classe.
  - Uso extensivo de variáveis globais; funções redundantes e loop não vetorizado (lento).
- Cientificamente, o cerne (difração de Fresnel × geometrias de faixas) está no caminho certo, mas:
  - A física da atmosfera está muito simplificada/heurística.
  - A normalização e a soma com ruído poderiam ser mais consistentes e vetorizadas.

### Sugestão prática
- Para estudos rápidos, ajuste os parâmetros “geométricos” e rode focando nas curvas `Fres`, `Fres_an*`, `Fres_sat` e `Fres_tot`.
- Para um fluxo de trabalho robusto, recomendo migrar para uma classe modular (com docstrings, unidade consistente e controle claro de ruído/normalização), mantendo:
  - escala de Fresnel correta,
  - modelo de “faixa” (bar) para corpo/anéis/satélite,
  - cintilação multiplicativa e ruídos foto-instrumentais configuráveis,
  - saída em DataFrame + plot com eixos e título informativos.

```python
    import scipy.special as scsp
    ...
    s1, c1 = scsp.fresnel(x1)
    s2, c2 = scsp.fresnel(x2)
    cc = c1 - c2
    ss = s1 - s2
    r_ampli = - (cc + ss) * (opacity / 2.)
    i_ampli = (cc - ss) * (opacity / 2.)
    flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
```

```python
Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)
...
Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)
plt.plot(times,Fres_tot, 'o-', ... )
plt.title("Simulação com Difração de Fresnel")
```

```python
med=np.median(flua[0:40])
for i in range(len(flua)):
    flua[i]=flua[i]/med
...
Flua_fresn=[]
for j in range(len(Flua_fres)):
    Flua_fresn.append(Flua_fres[j]/med)
```

---

**User**

Escreva uma versão markdown da sua explicação no arquivo @model_training/synthetic_curve/readme.md . Adicione os comentários de código e ajuste as equações para ficarem aparentes.



@readme.md (1-72) 

---

**Cursor**

Vou atualizar o arquivo de documentação com uma versão didática em Markdown, incluindo fórmulas renderizadas e blocos com trechos de código referenciando o arquivo original.

```markdown
## Visão geral

Este script gera curvas de luz sintéticas de ocultações estelares “pós-fotometria”, combinando:
- Difração de Fresnel nas transições de imersão/emersão do corpo principal.
- Contribuições opcionais de anéis (opacidade parcial) e de um satélite (ocultação secundária).
- Efeitos atmosféricos (cintilação/seeing) e ruídos instrumentais.
- Conversões fotométricas (magnitude → fluxo; fluxo → fótons) e normalização do nível fora da ocultação para ≈ 1.

O objetivo é aproximar o que seria esperado observar para um corpo específico, dadas propriedades geométricas (diâmetro, distância, velocidade do evento) e condições observacionais (banda, tempo de exposição, seeing, etc.).


## Componentes principais

### 1) Fotometria e conversões
- Conversão magnitude → fluxo (escala relativa) usando a relação fotométrica padrão:

\[ F \propto 10^{-0{,}4\,m} \]

- Conversão fluxo → contagem de fótons (usando a energia do fóton \(E = h c / \lambda\)).

Essas rotinas são usadas para escalonar a taxa de fótons observados e, posteriormente, injetar ruídos (Poisson, leitura e cintilação).


### 2) Escala e difração de Fresnel
- A escala de Fresnel é dada por:

\[ F = \sqrt{\frac{\lambda\,D}{2}} \]

onde \( \lambda \) é o comprimento de onda efetivo e \( D \) a distância ao objeto. O código calcula esta escala e usa integrais de Fresnel (SciPy) para modelar o perfil difrativo de uma “faixa” opaca (imersão/emersão).

Trecho que calcula a escala de Fresnel (distância em km, comprimento de onda convertido para km):

```89:111:model_training/synthetic_curve/simulate_curveC&P.py
def calc_fresnel(distance, bandpass):
    """Calculates the Fresnel scale.

    Fresnel Scale = square root of half the multiplication of wavelength and
    object distance.
    """
    bandpass = bandpass*ang_km
    distance = distance*ua
    return np.sqrt(bandpass * distance / 2)
```

Modelo de “faixa” com dois knife-edges (imersão/emersão) usando as integrais de Fresnel de SciPy:

```138:156:model_training/synthetic_curve/simulate_curveC&P.py
import scipy.special as scsp
...
fresnel_scale = calc_fresnel(distance,bandpass)
x = X / fresnel_scale
x01 = X01 / fresnel_scale
x02 = X02 / fresnel_scale
x1 = x - x01
x2 = x - x02
s1, c1 = scsp.fresnel(x1)
s2, c2 = scsp.fresnel(x2)
cc = c1 - c2
ss = s1 - s2
r_ampli = - (cc + ss) * (opacity / 2.)
i_ampli = (cc - ss) * (opacity / 2.)
flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
```

Comentários:
- A transmissão difrativa de uma borda é construída com as integrais de Fresnel \(C(u), S(u)\).
- Para uma “faixa” opaca (corpo), combinam-se duas bordas, gerando o padrão com franjas próximas às transições.


### 3) Turbulência atmosférica (seeing) e cintilação

O script escolhe um conjunto empírico de parâmetros atmosféricos a partir do seeing e deriva grandezas como \(r_0\) e variância de irradiância. A cintilação é modelada como ruído multiplicativo (lognormal), reduzida por tempos de exposição mais longos e abertura do telescópio.

Comentários:
- O modelo é heurístico/simplificado; serve para dar ordem de grandeza do efeito.
- A variância de irradiância depende de integrais de \(C_n^2\) (perfís verticais) e de fatores de “aperture averaging”.


### 4) Geometria da ocultação e linha do tempo
- Define-se o tempo de simulação e a coordenada ao longo da corda \(X(t) = v\,t\).
- Início/fim da ocultação principal são obtidos do diâmetro projetado e da velocidade do evento.
- Anéis e satélite são representados como faixas adicionais (opacidade parcial para anéis; opacidade total para satélite), com seus pares de bordas (imersão/emersão).

Combinação de curvas ópticas (corpo, anéis, satélite) por multiplicação das transmissões:

```870:876:model_training/synthetic_curve/simulate_curveC&P.py
Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)
...
Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)
plt.plot(times,Fres_tot, 'o-',color='black',linewidth= 0.7,markersize=2.3)
```


### 5) Síntese observacional (ruído) e normalização pós-fotometria
- Em cada exposição, integra-se o fluxo esperado (considerando o estado geométrico e difração) e injeta-se ruído (Poisson, leitura, cintilação).
- A curva é normalizada para que o nível fora da ocultação fique ≈ 1 (pós-fotometria). Exemplo do procedimento de normalização usado no script atual:

```904:931:model_training/synthetic_curve/simulate_curveC&P.py
med=np.median(flua[0:40])
for i in range(len(flua)):
    flua[i]=flua[i]/med
...
Flua_fresn=[]
for j in range(len(Flua_fres)):
    Flua_fresn.append(Flua_fres[j]/med)
```

Comentários:
- No reprocessamento moderno, recomenda-se estimar o baseline com robustez (ex.: mediana global ou média dos dois melhores quartis fora da ocultação).


## Como usar para “pós-fotometria”
- Ajuste os parâmetros geométricos do corpo (diâmetro projetado, distância) e a velocidade do evento para o seu caso.
- Configure a banda/λ e o tempo de exposição (amostragem temporal) para aproximar o seu setup.
- Anéis: defina posições (início/fim) e opacidades; Satélite: offset e diâmetro.
- Seeing e diâmetro do telescópio controlam a força da cintilação e do ruído.
- Analise a curva final normalizada (fora da ocultação ~ 1) como faria com dados pós-fotometria reais.


## Limitações observadas
- Mistura de unidades e constantes em alguns trechos; vários prints/trechos experimentais.
- Há bugs pontuais (ex.: `==` no lugar de `=` em algumas atribuições; referência a `self.d_star` fora de classe).
- Uso de variáveis globais e loops não vetorizados (impacto em desempenho e clareza).
- Modelo atmosférico simplificado (heurístico) e normalização que pode ser tornada mais robusta.


## Recomendações
- Migrar para uma classe modular com parâmetros explícitos, docstrings e unidades consistentes.
- Usar um baseline robusto para normalização e vetorização para desempenho.
- Separar nitidamente: “ótica/física” (difração, geometria) vs “detector/atmosfera” (ruídos).


### Como o simulador funciona:

Ele tenta gerar curvas de luz sintéticas de ocultações estelares, combinando:
Difração de Fresnel nos instantes de imersão/emersão do corpo principal.
Contribuições opcionais de anéis (opacidade parcial) e de um satélite (ocultação secundária).
Efeitos atmosféricos (cintilação/seeing) e ruídos instrumentais.
Conversões fotométricas simples (magnitude → fluxo; fluxo → fótons).
Normalização “pós-fotometria” (trazendo o nível de fora da ocultação para ≈1).
Plots da curva resultante.
A ideia é aproximar o que você esperaria observar para um corpo específico, dados diâmetro, distância, velocidade do evento, anéis, etc.
Blocos principais do código
Fotometria e conversões
Fluxo_lambda(magnitude): aproxima o fluxo em função da magnitude da estrela.
fluxo_fotons(fluxo, lamb): converte fluxo em contagem de fótons.
Algumas variantes tentam injetar ruído lognormal na irradiância para simular cintilação.
Escala e difração de Fresnel
calc_fresnel(distance, bandpass): calcula a escala de Fresnel 
F
=
λ
D
/
2
F= 
λD/2
​
  para distância do corpo e comprimento de onda efetivo.
bar_fresnel(X, X01, X02, opacity, distance, bandpass): modelo de faixa (bar) com dois “knife-edges” (imersão/emersão) usando integrais de Fresnel de SciPy para gerar o perfil de difração:
simulate_curveC&P.pyLines 138-156
    import scipy.special as scsp    ...    s1, c1 = scsp.fresnel(x1)    s2, c2 = scsp.fresnel(x2)    cc = c1 - c2    ss = s1 - s2    r_ampli = - (cc + ss) * (opacity / 2.)    i_ampli = (cc - ss) * (opacity / 2.)    flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
Turbulência atmosférica e seeing
A partir de um valor de seeing, escolhe um perfil empírico de turbulência (coeficientes A, B, C, D e escalas de altura) e obtém grandezas como r0, variância de fase e variância de irradiância. Isso determina a intensidade da cintilação (ruído multiplicativo).
Usa integrais e fatores de atenuação de abertura para estimar a variância da irradiância (modelo de Saha/Hardy/Tyson em versões simplificadas).
Ruídos instrumentais
Funções esboçadas para ruído térmico e de leitura; em outras rotinas o ruído é injetado via Poisson (contagem de fótons) e ruído lognormal (cintilação).
Geometria da ocultação e linha do tempo
Define o tempo de simulação, o vetor temporal times e a coordenada ao longo da corda Xs = v * t.
Determina início/fim da ocultação principal a partir do diâmetro do corpo e da velocidade.
Define segmentos para anéis (com opacidade parcial) e, se desejado, um satélite (offset e diâmetro), criando pares (X01, X02) para cada “faixa” que cruza a estrela.
Geração das curvas “ópticas” (sem ruído) e combinação
Calcula curvas de Fresnel para corpo principal, anéis e satélite; depois multiplica tudo para obter a transmissão total:
simulate_curveC&P.pyLines 870-879
Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)...Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)plt.plot(times,Fres_tot, 'o-', ... )plt.title("Simulação com Difração de Fresnel")
Síntese de observação com ruído e normalização
Em um laço temporal, integra o fluxo observável em cada exposição, aplicando o “estado” geométrico (dentro/fora do corpo, anel, satélite) e ruídos.
Normaliza a curva para que a média/mediana fora da ocultação fique ≈1:
simulate_curveC&P.pyLines 904-931
med=np.median(flua[0:40])for i in range(len(flua)):    flua[i]=flua[i]/med...Flua_fresn=[]for j in range(len(Flua_fres)):    Flua_fresn.append(Flua_fres[j]/med)
Visualização
Plota e salva figuras (curvas de Fresnel individuais e a curva final normalizada).
Como os parâmetros controlam a curva
Corpo principal
diametro_corpo, distancia, vel (velocidade do evento) → definem começo/fim da ocultação e o espaçamento das franjas (via Fresnel).
Anéis
Conjuntos início/fim e opacidades → criam atenuações parciais adicionais (franjas mais suaves).
Satélite
Offset e diâmetro → gera uma pequena ocultação separada com sua própria difração.
Observação
tempexp (tempo de exposição) e banda band → definem amostragem e a escala de Fresnel.
diam_teles, readout_noise, temperatura → afetam contagem e ruído.
Seeing → controla a cintilação (ruído multiplicativo).
O que usar para “pós-fotometria”
A pipeline faz a normalização final (fora da ocultação ≈1), então o resultado imita uma curva “pós-fotometria”.
Para um corpo específico: ajuste diametro_corpo, distancia, vel, posição dos anéis/satélite e band. Ajuste tempexp para o seu cadence e seeing/diam_teles para o local/instrumento.
Limitações e cuidados
Há problemas de implementação:
Mistura de unidades e constantes; várias prints/experimentos deixados no código.
Trechos com bug de atribuição (== onde deveria ser =) e referência a self.d_star em contexto sem classe.
Uso extensivo de variáveis globais; funções redundantes e loop não vetorizado (lento).
Cientificamente, o cerne (difração de Fresnel × geometrias de faixas) está no caminho certo, mas:
A física da atmosfera está muito simplificada/heurística.
A normalização e a soma com ruído poderiam ser mais consistentes e vetorizadas.
```

Atualizei o `model_training/synthetic_curve/readme.md` com uma explicação didática em Markdown, incluindo equações em LaTeX, comentários e blocos de referência a trechos do código original (`simulate_curveC&P.py`) para contextualizar a física e as etapas do simulador.

- Estruturei por seções: fotometria, Fresnel, atmosfera/seeing, geometria, ruído/normalização.
- Adicionei fórmulas para Fresnel e magnitude–fluxo.
- Incluí referências de código com trechos-chave (cálculo da escala de Fresnel, modelo de faixa, combinação das curvas, normalização). entrega fator multiplicativo

---

**User**

Como você organizaria esse código (@model_training/synthetic_curve/simulate_curveC&P.py) ? Explique de forma mais conceitual, sem entrar em tantos detalhes.

---

**Cursor**

### Organização conceitual proposta

- **Camada de configuração (inputs)**
  - **Objeto de parâmetros**: reúne tudo que é “entrada” do experimento (astrofísico, geométrico, instrumental e atmosférico): magnitudes, λ/banda, distância, diâmetros (corpo/anel/satélite), velocidade, tempo de exposição, seeing, telescópio, sementes aleatórias.
  - **Unidades claras**: validar e converter logo no início (km, s, nm, arcsec).

- **Camada física (ótica/geométrica)**
  - **Módulo Fresnel**: funções puras para escala de Fresnel e transmissão de borda/faixa (knife-edge e strip), com backend SciPy e fallback aproximado.
  - **Módulo geometria**: linha do tempo, corda X(t), intervalos de imersão/emersão do corpo; anéis como faixas parcialmente opacas; satélite como faixa opaca deslocada.
  - **Composição de transmitâncias**: multiplicar corpo × anéis × satélite para obter a transmitância total ideal (sem ruído).

- **Camada de fotometria e contagem**
  - **Fotometria**: magnitude → fluxo relativo (10^(-0.4 m)); escolha de escala (apenas relativa).
  - **Amostragem temporal**: integração simples por exposição (cadência) sobre a transmitância.

- **Camada de ruído (atmosfera + instrumento)**
  - **Cintilação (seeing)**: ruído multiplicativo (lognormal) com intensidade regulada por seeing e tempo de exposição.
  - **Ruído de fótons**: Poisson sobre a contagem esperada (ganho arbitrário só para S/N razoável).
  - **Ruído de leitura**: gaussiano aditivo pequeno.
  - Tudo vetorizado e desacoplado da física (recebe fluxo ideal e devolve fluxo ruidoso).

- **Camada de normalização (pós-fotometria)**
  - Estratégia robusta (ex.: média dos dois melhores quartis contíguos ou mediana global) para baseline ≈ 1.
  - Opcionalmente oferecer mais de um método.

- **Orquestração (classe principal)**
  - `SyntheticLightCurveSimulator` com:
    - `__init__`: guarda parâmetros, configura RNG e unidades.
    - `simulate()`: monta tempo/corda → transmissões (corpo/anéis/satélite) → fotometria → ruídos → normalização → retorna DataFrame.
    - `plot_curve(save=True)`: gráfico com título, eixos e legenda padronizados.
    - `export_data(save=True)`: arquivos numerados e DataFrame.
  - Métodos privados curtos e coesos para cada etapa (fácil de testar e trocar componentes).

- **Saída e reproducibilidade**
  - Pastas fixas (`output/` e `output/curves/`), nomes auto-incrementais.
  - `random_seed` em um único lugar.

- **Qualidade e manutenção**
  - Docstrings tipo NumPy/Google, `typing`, validação leve dos parâmetros.
  - Comentários só para explicar a física/equações, não o “como do código”.
  - Separação clara entre “física” e “ruído/observação”.

Em resumo: transformar o script monolítico em um pipeline modular e orientado a objetos, onde cada etapa (óptica, geometria, ruído, normalização) é um bloco independente, orquestrado por uma classe simples com API intuitiva.

---

**User**

O que significa mu0?

---

**Cursor**

**μ0** é a permeabilidade magnética do vácuo (constante magnética).  
- Valor típico: μ0 ≈ 4π × 10⁻⁷ H/m = 1,256637061×10⁻⁶ N·A⁻² (o valor no seu código).  
- Unidades: H/m (henry por metro) = N·A⁻².  
- Relação fundamental: junto com ε0 (permissividade elétrica do vácuo), define a velocidade da luz: c = 1/√(μ0 ε0).

---

**User**

O que é ep0?

---

**Cursor**

**ε0 (ep0)** é a permissividade elétrica do vácuo (constante dielétrica do vácuo).
- Valor: ε0 ≈ 8,854187817 × 10⁻¹² F/m (equivale a C²·N⁻¹·m⁻²) — o mesmo do seu código.
- Relações:
  - Com μ0 define a velocidade da luz: \( c = 1/\sqrt{\mu_0 \,\epsilon_0} \).
  - Entra na Lei de Coulomb: \( F = \frac{1}{4\pi \epsilon_0}\,\frac{q_1 q_2}{r^2} \).

---

**User**

Reorganize o código em @simulate_curve.py (1-963) separando em classes e funções com parâmetros bem definidos. Explique tudo didaticamente em comentários e docstrings. O código deve estar funcionando perfeitamente. Deixe comentado também as alterações que foram feitas e o motivo delas. Faça testes com caractéristicas de corpos pequenos famosos como Umbriel e Chariklo (busque na internet os parâmetros necessários). Separe os testes em uma função a parte chamada "testes_extras". Organize como se fosse um desenvolvedor junior que acabou de ler PEP8 Python. 

---

**Cursor**

Vou refatorar completamente `model_training/synthetic_curve/simulate_curve.py` em uma estrutura modular orientada a objetos, com docstrings claras, comentários didáticos, fallback sem SciPy e a função `testes_extras()` com cenários de Umbriel e Chariklo. Também deixarei comentários explicando as alterações e o motivo.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador modular de curvas de luz de ocultações estelares.

Este arquivo reorganiza o antigo script monolítico em classes e funções
coesas, seguindo PEP 8 e boas práticas de programação científica.

Principais componentes:
- Física de Fresnel (difração em bordas "knife-edge" e faixa opaca)
- Geometria do evento (linha do tempo e coordenada ao longo da corda)
- Modelo de ruído (Poisson, leitura, cintilação multiplicativa)
- Normalização "pós-fotometria" (baseline ~ 1)
- Orquestração via uma classe principal de fácil uso

Bibliotecas: numpy, pandas, matplotlib (SciPy é opcional; usado se disponível).

CHANGES (alterações em relação ao código anterior):
- Removidos trechos experimentais, prints soltos e globais redundantes
  (motivo: clareza, reprodutibilidade e manutenibilidade).
- Unidades explicitadas (km, s, nm) e conversões centralizadas
  (motivo: reduzir erros por mistura de unidades).
- Difração de Fresnel isolada em funções puras com fallback sem SciPy
  (motivo: manter acurácia quando disponível e portabilidade quando não).
- Ruídos desacoplados da física (camada separada)
  (motivo: permitir trocar/ligar/desligar ruídos facilmente).
- Normalização robusta por quartis contíguos ou mediana
  (motivo: simular "pós-fotometria" com baseline estável).
- Função `testes_extras()` com cenários aproximados de Umbriel e Chariklo
  (motivo: exemplos práticos com corpos pequenos conhecidos).
"""

from __future__ import annotations

from typing import Optional, Tuple, List
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# Utilidades e constantes
# =============================================================================

SPEED_OF_LIGHT_MS = 299_792_458.0  # m/s (não é usada diretamente, mantida por referência)
NM_TO_KM = 1e-12  # 1 nm = 1e-12 km


def magnitude_to_relative_flux(magnitude: float) -> float:
    """
    Converte magnitude aparente em fluxo relativo (sem calibração absoluta).

    Equação fotométrica padrão:
        F ∝ 10^(-0.4 m)
    """
    return 10.0 ** (-0.4 * float(magnitude))


def normalize_flux_top_quartiles(flux: np.ndarray) -> np.ndarray:
    """
    Normaliza o fluxo dividindo pelo baseline estimado como a média das duas
    maiores médias entre 4 segmentos contíguos (quartis em tempo).

    - Razoável para "pós-fotometria": baseline ~ 1 fora da ocultação.
    - Fallbacks garantem retorno mesmo em séries curtas.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return flux
    if valid.size < 4:
        baseline = float(np.mean(valid))
        baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
        return flux / baseline
    segments = np.array_split(valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
    if len(means) == 0:
        baseline = float(np.median(valid))
    else:
        order = np.argsort(means)
        top = [means[order[-1]]]
        if len(means) >= 2:
            top.append(means[order[-2]])
        baseline = float(np.mean(top))
    if not np.isfinite(baseline) or baseline <= 0:
        baseline = float(np.median(valid))
        if not np.isfinite(baseline) or baseline <= 0:
            return flux
    return flux / baseline


# =============================================================================
# Física de Fresnel (difração)
# =============================================================================

class FresnelPhysics:
    """
    Funções para cálculo de escala de Fresnel e transmitâncias difrativas.
    """

    @staticmethod
    def fresnel_scale_km(distance_km: float, wavelength_nm: float) -> float:
        """
        F = sqrt(lambda * D / 2), com lambda em km e D em km.
        """
        lambda_km = float(wavelength_nm) * NM_TO_KM
        D = float(distance_km)
        return math.sqrt(max(lambda_km * D / 2.0, 1e-30))

    @staticmethod
    def fresnel_CS(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrais de Fresnel (C, S) com SciPy se disponível; caso contrário,
        usa aproximações assintóticas/séries adequadas a fins educacionais.
        """
        try:
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore
            # A escala do argumento varia entre convenções; adotamos um fator
            # para obter bom acordo qualitativo.
            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback aproximado: bom o suficiente didaticamente
        x = np.asarray(u, dtype=float)
        ax = np.abs(x)
        C = np.zeros_like(x)
        S = np.zeros_like(x)

        small = ax <= 1.5
        if np.any(small):
            z = x[small]
            # Séries truncadas (educacional; não metrológico)
            C[small] = (z - (math.pi**2) * (z**5) / 40.0) / math.sqrt(2.0 * math.pi)
            S[small] = ((math.pi) * (z**3) / 6.0 - (math.pi**3) * (z**7) / 336.0) / math.sqrt(
                2.0 * math.pi
            )

        large = ~small
        if np.any(large):
            z = x[large]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[large] = c
            S[large] = s

        return C, S

    @staticmethod
    def knife_edge_transmission(x_km: np.ndarray, edge_pos_km: float,
                                distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Transmitância de difração para uma borda "knife-edge".

        I(u) = 0.5 [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ],
        onde u = (x - x_edge) / F e F é a escala de Fresnel.
        """
        F = FresnelPhysics.fresnel_scale_km(distance_km, wavelength_nm)
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = FresnelPhysics.fresnel_CS(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    @staticmethod
    def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                  distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa opaca: produto de duas bordas (imersão e emersão).
        """
        half = 0.5 * float(width_km)
        x1 = float(center_km) - half
        x2 = float(center_km) + half
        T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
        T2 = FresnelPhysics.knife_edge_transmission(-x_km, -x2, distance_km, wavelength_nm)
        return np.clip(T1 * T2, 0.0, 1.0)

    @staticmethod
    def partial_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                   opacity: float, distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa parcialmente opaca (anéis):
        T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = FresnelPhysics.opaque_strip_transmission(
            x_km, center_km, width_km, distance_km, wavelength_nm
        )
        return 1.0 - float(opacity) * (1.0 - T_opaque)


# =============================================================================
# Modelo de ruído
# =============================================================================

class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.
    """

    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 5.0, gain_counts_per_flux: float = 4e5,
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Aplica Poisson (fótons), ruído de leitura (gaussiano) e cintilação (lognormal).
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 1e-10, None)

        # Converte para contagens (ganho arbitrário para S/N razoável)
        lam = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam = np.clip(lam, 0, 1e12)

        # Poisson (fótons)
        shot = self.rng.poisson(lam)

        # Leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=shot.size)

        # Cintilação (lognormal): pior para seeing ruim e exposições curtas
        sigma_ln = max(0.001, 0.02 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)))
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=shot.size))

        counts = (shot + read) * scint
        flux = counts / (self.gain_counts_per_flux * self.exposure_time_s)
        return np.clip(flux, 0.0, None)


# =============================================================================
# Simulador principal
# =============================================================================

class SyntheticLightCurveSimulator:
    """
    Simulador de curvas de luz sintéticas para ocultações estelares.

    Parâmetros
    ----------
    mag_star : float
        Magnitude aparente da estrela (escala relativa).
    distance_km : float
        Distância observador–corpo (km), usada na escala de Fresnel.
    diameter_km : float
        Diâmetro projetado do corpo (km) ao longo da corda.
    velocity_kms : float
        Velocidade relativa do evento (km/s).
    exposure_time_s : float
        Tempo de exposição por amostra (s).
    total_duration_s : Optional[float]
        Duração total da simulação (s). Se None, é inferida com margem.
    wavelength_nm : float
        Comprimento de onda efetivo (nm), p.ex. 550 nm ~ banda V.
    seeing_arcsec : float
        Seeing (arcsec), controla a cintilação.
    rings : Optional[List[Tuple[float, float, float]]]
        Lista de anéis como (offset_km, width_km, opacity). Opacity em [0,1].
    satellites : Optional[List[Tuple[float, float]]]
        Lista de satélites como (offset_km, diameter_km).
    normalize_method : str
        "top_quartiles" (default) ou "median".
    random_seed : Optional[int]
        Semente para reprodutibilidade dos ruídos.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4_000.0,
        diameter_km: float = 1_200.0,
        velocity_kms: float = 20.0,
        exposure_time_s: float = 0.1,
        total_duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        satellites: Optional[List[Tuple[float, float]]] = None,
        normalize_method: str = "top_quartiles",
        random_seed: Optional[int] = None,
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time_s = float(exposure_time_s)
        self.total_duration_s = float(total_duration_s) if total_duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.rings = rings if rings is not None else []
        self.satellites = satellites if satellites is not None else []
        self.normalize_method = normalize_method

        self.rng = np.random.default_rng(random_seed)
        self.noise = NoiseModel(
            seeing_arcsec=self.seeing_arcsec,
            exposure_time_s=self.exposure_time_s,
            rng=self.rng,
        )

        # Saídas
        self.time_s: Optional[np.ndarray] = None
        self.flux: Optional[np.ndarray] = None
        self.flux_norm: Optional[np.ndarray] = None

        # Diretórios de saída
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_dirs()

    def simulate(self) -> pd.DataFrame:
        """
        Executa a simulação completa:
        - Constrói tempo e coordenada ao longo da corda
        - Calcula transmitância difrativa: corpo × anéis × satélites
        - Converte magnitude em fluxo relativo e aplica transmitância
        - Aplica ruídos (Poisson, leitura, cintilação)
        - Normaliza o fluxo
        """
        t, x = self._build_time_and_chord()

        # Corpo principal (faixa opaca)
        T_body = FresnelPhysics.opaque_strip_transmission(
            x, center_km=0.0, width_km=self.diameter_km,
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )

        # Anéis (faixas parcialmente opacas)
        T_rings = np.ones_like(T_body)
        for (offset_km, width_km, opacity) in self.rings:
            T_rings *= FresnelPhysics.partial_strip_transmission(
                x, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Satélites (faixas opacas deslocadas)
        T_sats = np.ones_like(T_body)
        for (offset_km, diameter_km) in self.satellites:
            T_sats *= FresnelPhysics.opaque_strip_transmission(
                x, center_km=float(offset_km), width_km=float(diameter_km),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Transmitância total
        T_total = np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

        # Fluxo relativo esperado (sem ruído)
        base_flux = magnitude_to_relative_flux(self.mag_star)
        expected_rel_flux = base_flux * T_total

        # Ruído
        noisy_flux = self.noise.apply(expected_rel_flux)

        # Normalização
        if self.normalize_method == "median":
            baseline = float(np.median(noisy_flux[np.isfinite(noisy_flux)]))
            baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
            flux_norm = noisy_flux / baseline
        else:
            flux_norm = normalize_flux_top_quartiles(noisy_flux)

        # Armazena e retorna
        self.time_s = t
        self.flux = noisy_flux
        self.flux_norm = flux_norm
        return pd.DataFrame({"time_s": t, "flux": noisy_flux, "flux_norm": flux_norm})

    def plot_curve(self, save: bool = True, show: bool = False, title: Optional[str] = None) -> str:
        """
        Plota a curva normalizada. Retorna o caminho do PNG salvo (string)
        se `save=True`, caso contrário retorna string vazia.
        """
        self._require_simulation()
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(self.time_s, self.flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adim.]")
        band = f"{int(round(self.wavelength_nm))} nm"
        ttl = title if title else f"Curva sintética com difração e seeing — {band}"
        ax.set_title(ttl)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        png_path = ""
        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)
        return png_path

    def export_data(self, save: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Exporta os dados simulados para um .dat numerado em output/.
        Retorna (DataFrame, caminho_do_arquivo_ou_string_vazia).
        """
        self._require_simulation()
        df = pd.DataFrame({"time_s": self.time_s, "flux": self.flux, "flux_norm": self.flux_norm})
        dat_path = ""
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df, dat_path

    # -------------------------- helpers internos -----------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.total_duration_s is None:
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time * 3.0  # margem: 1x antes e 1x depois
        else:
            total_time = self.total_duration_s
        n_steps = max(2, int(math.ceil(total_time / self.exposure_time_s)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _ensure_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                n = int(name.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulation(self) -> None:
        if self.time_s is None or self.flux is None or self.flux_norm is None:
            raise RuntimeError("Simulação ainda não executada. Chame simulate() antes.")


# =============================================================================
# Testes extras com corpos pequenos (Umbriel e Chariklo)
# =============================================================================

def testes_extras() -> None:
    """
    Executa dois cenários de teste:
    1) Umbriel (satélite de Urano) — sem anéis
    2) Chariklo (Centauro) — com anéis C1R e C2R (parâmetros aproximados)

    Observações:
    - Valores aproximados (ordem de grandeza) para fins didáticos.
    - Distâncias geocêntricas típicas: Urano ~ 2.9e9 km, Chariklo ~ 2.1e9 km.
    - Velocidades típicas de sombra ~ 20–25 km/s.
    - Parâmetros dos anéis de Chariklo (Braga-Ribas+2014):
        - Raios ~ 391 km e 405 km; larguras ~ 7 km e 3 km;
          profundidades óticas τ ~ 0.4 e 0.06 → opacidade ~ 1 - e^{-τ}.
      Para uma ocultação equatorial idealizada, modelamos cada anel por duas faixas
      simétricas (+/- raio) com a mesma largura e opacidade.
    """
    # ------------------------------- Umbriel ---------------------------------
    umbriel = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,        # ~ distância de Urano à Terra (aprox.)
        diameter_km=1169.0,       # diâmetro de Umbriel ~ 1169 km
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        normalize_method="top_quartiles",
        random_seed=123,
    )
    df_u = umbriel.simulate()
    umbriel.plot_curve(save=True, show=False, title="Umbriel — V~550 nm")
    umbriel.export_data(save=True)

    # ------------------------------ Chariklo ---------------------------------
    # Parâmetros aproximados dos anéis (C1R e C2R)
    r1_km, w1_km, tau1 = 391.0, 7.0, 0.4
    r2_km, w2_km, tau2 = 405.0, 3.0, 0.06
    op1 = 1.0 - math.exp(-tau1)
    op2 = 1.0 - math.exp(-tau2)

    rings_chariklo: List[Tuple[float, float, float]] = [
        (+r1_km, w1_km, op1),
        (-r1_km, w1_km, op1),
        (+r2_km, w2_km, op2),
        (-r2_km, w2_km, op2),
    ]

    chariklo = SyntheticLightCurveSimulator(
        mag_star=13.0,
        distance_km=2.1e9,        # Chariklo típico ~ 15 AU (aprox.)
        diameter_km=250.0,        # diâmetro efetivo do corpo (aprox. esfera equiv.)
        velocity_kms=25.0,
        exposure_time_s=0.1,
        wavelength_nm=650.0,      # banda R aproximada
        seeing_arcsec=1.2,
        rings=rings_chariklo,
        satellites=[],            # sem satélites aqui
        normalize_method="top_quartiles",
        random_seed=321,
    )
    df_c = chariklo.simulate()
    chariklo.plot_curve(save=True, show=False, title="Chariklo com anéis — R~650 nm")
    chariklo.export_data(save=True)

    # Prints simples para feedback (como um "junior" faria)
    print("Umbriel: amostras =", len(df_u), " min/max flux_norm =", float(df_u.flux_norm.min()),
          float(df_u.flux_norm.max()))
    print("Chariklo: amostras =", len(df_c), " min/max flux_norm =", float(df_c.flux_norm.min()),
          float(df_c.flux_norm.max()))


# =============================================================================
# Execução direta (exemplo mínimo)
# =============================================================================

if __name__ == "__main__":
    # Exemplo mínimo de uso "out of the box"
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4_000.0,
        diameter_km=1_200.0,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        random_seed=42,
    )
    df = sim.simulate()
    png = sim.plot_curve(save=True, show=False)
    dat_df, dat_path = sim.export_data(save=True)
    print("Arquivo de dados:", dat_path)
    print("Arquivo da figura:", png)

    # Rodar os testes extras com Umbriel e Chariklo
    testes_extras()
import numpy as np
import pandas as pd
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
import random 
import time
import scipy.integrate as integrate
import pandas as pd 

### Simulador de Curva de Luz ###

ua = 149597870 #unidade astronômica em km
ang_km = 1*10**-13 #angstrom para km
ano = 365*24*3600 #segundos em um ano
mu0 = 1.256637061 * 10 ** -6 #N A**-2 #permeabilidade magnética vácuo
ep0 = 8.854187817 * 10 **(-12) #C**2 N**-1 m**-2 #permeabilidade elétrica vácuo
c = 1/(mu0*ep0)**(1/2) #velocidade da luz no vácuo
Cn2 = 1 #condutividade térmica do ar

def calculo_magnitude(magnitude_absoluta, distancia): #em UA
    magnitude_aparente = magnitude_absoluta + 5*np.log10(distancia*(distancia-1))
    return(magnitude_aparente)

def Fluxo_lambda(magnitude):
    Fuxo=(10**(2.5*np.log10(3.44*(10**-12)))+(magnitude))**(1/2.5) #usando equação 20.9 kepler
    Fluxo = (3.69*10**-9)*(10**(magnitude))**(-1/2.5)
    return (Fluxo) #W/m2
# F V=0 3.44 * 10 ** - 8 J /m**2 s**-1 um**-1 === 1000 fotons cm**-2 s**-2 um**-1
#FLuxo 
print(Fluxo_lambda(0)) #W/m²

def Flux_lambda_ruido(magnitude):
    Fluxo=Fluxo_lambda(magnitude)
    tempo = 1
    area = 1
    cn15=integrate.quad(Cn2,0,np.inf)
    ir_saha=19.2*(600*10**-9)**(-7/6)*cn15[1]
    E0 = 3.6*10**-9 #W/m²
    E = (E0*10**(-0.4*magnitude))/tempo/area #W/cm²
    return(np.exp((np.log(E)+np.random.normal(0,ir_saha**(1/2)/area)*tempo)))

def fluxo_fotons(fluxo, lamb):
    h = 6.626196*10**-34 #m2kg/s
    c = 2.997924562*10**8 #m/s
    angstrons_m = 10**(-10) #
    fotons=fluxo*(lamb*angstrons_m)/(h*c)
    return(fotons)
print(fluxo_fotons(Fluxo_lambda(0),5500)/10**4)
print(10**6)
#fotons /m²/s

def diametro_angular(diametro, distancia): #unidades
    diametro_ang=(np.arctan(diametro/(distancia*ua)))*(360/(2*np.pi))*3600*1000
    return(diametro_ang) #segundo de arco

def Escala_placa(pixel, bin, dist_focal): #unidades
    escala_placa = 206265*pixel*bin/(1000*dist_focal)
    return escala_placa #segundo de arco/pixel

def tamanho_angular_corpo(diametro_angular,Escala_placa):
    tamanho = diametro_angular/Escala_placa
    return tamanho

#Exemplo:
ep = Escala_placa(5.86,1,100)
da = diametro_angular(6400,40)
print(tamanho_angular_corpo(da,ep))
#Incerteza de um photon-counting device que segue Estatistica de Poisson é sqrt(N), sendo N o número de fotons contados ToMeasuretheSky p.239

def soma_magnitude(mag1, mag2):
    magnitude_total = -2.5*np.log10(10**(-0.4*mag1)+10**(-0.4*mag2))
    return(magnitude_total)
    #https://www.astro.keele.ac.uk/jkt/pubs/JKTeq-fluxsum.pdf

print(soma_magnitude(21,20))

def fresnel_scale(lamb,dist):
    lamb = lamb*(10**-10)*micrometer_km
    dlamb = lamb*0.001
    dist = dist*ua
    fresnel_scale_1 = calc_fresnel(dist, lamb-dlamb/2.0)
    fresnel_scale_2 = calc_fresnel(dist, lamb+dlamb/2.0)
    fresnel_scale = (fresnel_scale_1 + fresnel_scale_2)/2.0
    return fresnel_scale



# https://www.youtube.com/watch?v=Bi2JWAHhBNg
def calc_fresnel(distance, bandpass):
    """Calculates the Fresnel scale.

    Fresnel Scale = square root of half the multiplication of wavelength and
    object distance.

    Parameters
    ----------
    distance : `int`, `float` array
        Distances, in km.

    bandpass : `int`, `float`, array
        Wavelength, in km.

    Returns
    -------
    fresnel_scale : `float`, array
        Fresnel scale, in km.
    """
    bandpass = bandpass*ang_km
    distance = distance*ua
    return np.sqrt(bandpass * distance / 2)


def bar_fresnel(X, X01, X02, opacity,distance,bandpass):
    """Returns the modelled light curve considering fresnel diffraction.

    Parameters
    ----------
    X : array
        Array with time values converted in km using the event velocity.

    X01 : `int`, `float`
        Immersion time converted in km using the event velocity.

    X02 `int`, `float`
        Emersion time converted in km using the event velocity.

    fresnel_scale : `int`, `float`
        Fresnel scale, in km.

    opacity : `int`, `float`
        Opacity. Opaque = 1.0, transparent = 0.0.

    Returns
    -------
    flux_fresnel : array
        The light curve with fresnel diffraction.
    """
    import scipy.special as scsp

    # Converting from km to units of fresnel scale
    fresnel_scale = calc_fresnel(distance,bandpass)
    x = X / fresnel_scale
    x01 = X01 / fresnel_scale
    x02 = X02 / fresnel_scale
    # Fresnel diffraction parameters
    x1 = x - x01
    x2 = x - x02
    s1, c1 = scsp.fresnel(x1)
    s2, c2 = scsp.fresnel(x2)
    cc = c1 - c2
    ss = s1 - s2
    r_ampli = - (cc + ss) * (opacity / 2.)
    i_ampli = (cc - ss) * (opacity / 2.)
    # Determining the flux considering fresnel diffraction
    flux_fresnel = (1.0 + r_ampli) ** 2 + i_ampli ** 2
    return flux_fresnel

if self.d_star > 0:
# Computing fresnel diffraction for the case where the star size is not negligenciable
    resolucao = (self.d_star/2)/npt_star
    flux_star_1 = np.zeros(len(time_model))
    flux_star_2 = np.zeros(len(time_model))
            # Computing stellar diameter only near the immersion or emersion times
    star_diam = (np.absolute(x - x01) < 3*self.d_star) + (np.absolute(x - x02) < 3*self.d_star)
    p = np.arange(-npt_star, npt_star)*resolucao
    coeff = np.sqrt(np.absolute((self.d_star/2)**2 - p**2))
    for ii in np.where(star_diam == True)[0]:
        xx = x[ii] + p
        flux1 = bar_fresnel(xx, x01, x02, fresnel_scale_1, opacity)
        flux2 = bar_fresnel(xx, x01, x02, fresnel_scale_2, opacity)
        flux_star_1[ii] = np.sum(coeff*flux1)/coeff.sum()
        flux_star_2[ii] = np.sum(coeff*flux2)/coeff.sum()
        flux_star[ii] = (flux_star_1[ii] + flux_star_2[ii])/2.
flux_inst = np.zeros(len(time_obs))

def ka(band):
    k=2*np.pi/band
    return k

#band = 6000 *10**-9

#print(k)
#L=20000
#diam_teles=1.6

aaf = (1+1.07*(((k*(diam_teles/100))**2)/(4*L))**(7/6))**(-1)

#mag_star = 21
#mag_obj = 20
#queda = (mag_star-mag_obj) + 2.5 * (np.log10(10**((mag_star-mag_obj)/2.5)+1))
#ou
#queda2 = 2.5*(np.log10(10**(mag_obj-mag_star)/2.5)+1)
#print(queda)
#print(queda2)

#fluxo_estrela = 10**(mag_star/2.5)
#fluxo_obj = 10**(mag_obj/2.5)
#dif_mag1 = -2.5 * np.log10(fluxo_estrela/fluxo_obj) + 2.5 * np.log10((fluxo_estrela + fluxo_obj) / fluxo_obj)
#dif_mag2 = 2.5 * np.log10((fluxo_estrela + fluxo_obj) / fluxo_estrela)
#print(dif_mag1)
#print(dif_mag2)
	
#aux = (mag_star-mag_obj) * 0.4
#contraste
#contr = 1 / (10**(aux)+1)
#soma_mag = mag_star - (2.5*(np.log10(1/contr)))
#queda_mag = mag_obj - mag_star
#aux = (soma_mag - mag_obj) * 0.4
#botton_flux = 10**(aux)
#print(soma_mag)
#print(queda_mag)
#print(aux)
#print(botton_flux)

#def Fluxo_de_fotons_Observado:
#    Fluxo_observado=*integral*fluxo_fotons*transmissao_atmosferica*eficiencia_telescopio*eficiencia_instrumento*eficiencia_filtro*eficiencia_detector*dlambda
#    Fluxo_deFotons_observado=Area_telescopio*tempo_integracao*Fluxo_observado

#numero de bits da câmera, limita o numero máximo de contagem que a ccd pode obter ...
#ADU = 2^numero de bits-1
#Ganho X eletrons por ADU resultando na capacidade total de pixels da ccd

#ARRUMAR para latitude
def posicao_corda(diametro_objeto, latitude):
    corda_corpo = diametro_objeto*np.cos(latitude)
    inicio = -corda_corpo/2
    fim = corda_corpo/2
    return(corda_corpo)


#ti = 0.1
#k = 2*np.pi/(5500*10**-10)
#L = 1
#area_teles = area_telescopio/10000
#f = Fluxo_lambda(0)
#var_log_amplitude = 0.124* (k/10) ** (7/6) * (L) ** (11/6) * Cn2 #tyson 2.31 
#aaf = (1+1.07*((k*(4*(area_teles)/(np.pi)))/(4*L))**(7/6))**(-1)
#var_irradi = aaf * (np.exp(4 * (var_log_amplitude))-1) #2.33
#ira = (np.random.normal(0,var_irradi**(1/2)))
#print("Fluxo")
#print(f)
#print("var_log")
#print(var_log_amplitude**(1/2))
#print("var ampli 10")
#print(np.log10(var_log_amplitude))
#print("var ampli e")
#print(np.log(var_log_amplitude))
#print("var_irradi")
#print(var_irradi)
#print("Ira")
#print(ira)
#ir = f+(ira)
#print("ir")
#print(ir)
#n_fotons = fluxo_fotons(ir,5500)*area_teles
#print("n_fotons")
#print(n_fotons)
#print("fotons")
#print(fluxo_fotons(f,5500)*area_teles)
#print((4*10**6)*10**(0/2.5)*10**4)
#print(fluxo_fotons(f,6500)*area_teles)

def Cnh2(h):
    Cn2 = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*d*d)
    cn2=Cn2
    return cn2
def Cn22(h):
    Cn2 = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*d*d)
    cn2=Cn2*h**(5/6)
    return cn2
def Cn22h(h):
    Cn2h = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*d*d)
    cn2h = Cn2h*h**(5/3)
    return cn2h

#print(var_log_amplitude)
##var_log = integrate.quad(Cn22,0,20000)
#intensity = 19.2*banda**(-7/6)
#print(var_log[0]*intensity)

############ FASE OK
#f = Fluxo_lambda(18)
#banda = 5000
#area_telescopio = np.pi*30**2 #CM²
#ti = 1
#g=fluxo_fotons(f,banda)*area_telescopio
#maxim=0

def erro_fase(f,var_fase):
    factor = 1
    #n_fotons = fluxo_fotons(f,banda)*area_telescopio*ti
    if f > 20000:
        factor= f / 20000
        f = 20000
        #print("Por questão de tempo coomputacional será realizada uma aproximação no número de fótons")
    x = f/2
    if f < 1:
        factor = 2
        f = 1
    desv_pad_fase = var_fase**(1/2)
    total = 0
    

    maxim = np.arange(0,x,factor)
   # print(maxim)
    if maxim ==[0]:
        return 0
    for i in (maxim):
        j1 = (np.sin(np.random.normal(0, desv_pad_fase)))
        j2 = (np.sin(np.random.normal(0, desv_pad_fase)))
        if j1+j2 > 0.5 or j1+j2 <-0.5:
            total += 2
        else:
            total = total

    return total*factor
#erro_fase(g,5000)    
#print(int(sum(arranjo)))
#print(int(np.random.normal(n_fotons, var_fase**(1/2))))
#for i in arranjo:
#    if arranjo[i] + arranjo [i+1] > 0.5 or arranjo[i] + arranjo[i+1] < -0.5:
#        total = total+2
#    i = i+2
#print(total*factor)


def contagem_fluxo(tempo_atual, mag_obj, mag_star, area_telescopio
, tempo_exposicao, banda, inicio, fim):
   # mag_star = mag_star #combinar com mag obj
    
   #
    ti = tempo_exposicao/100
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = mag_obj
           # print("dentro if 1")
        else:
            magnitude = soma_magnitude(mag_star,mag_obj)
           # print("dentro else 1")
        f = Fluxo_lambda(magnitude)
       # print(f)
        #var_log_amplitude = 0.307* k ** (7/6) * L ** (11/6) * Cn2 #tyson 2.31 
        #aaf = (1+1.07*(k*(area_telescopio/(4*np.pi))/(4*L))**(7/6))**(-1)
        #var_irradi = aaf * (np.exp(4 * (var_log_amplitude))-1) #2.33
        #ira = (np.random.normal(0,var_irradi**(1/2)))*ti
        #ir = f+abs(ira)
        n_fotons = fluxo_fotons(f,banda)*area_telescopio*ti 
       # print(n_fotons)
      #  photons = np.random.poisson(ruido_termico(270,n_fotons,ti))
        #arranjo = list()
        #for i in ((np.arange(0,n_fotons,1))):
        #    arranjo.append(1)
        #p=0
        #for i in arranjo:
        #    fase = (np.random.normal(0, var_fase**(1/2)))
        #    j = ((i/i+np.sin(fase)))    
        #    arranjo[p] = j
        #    p+=1
        f = Flux_lambda_ruido(magnitude,area_telescopio)
        #print(f)
        #f = Fluxo_lambda(magnitude)
        fluxo_total=f
        #fluxo_total += np.random.normal(fluxo_fotons(f,banda),var_irradi**(1/2))*area_telescopio*ti #+ fluxo_fotons(f, banda)*ti#*area_telescopio
        #fluxo_total = fluxo_total#/2 
        
        if fluxo_total < 0:
            fluxo_total = 0 #abs(fluxo_total)
        fluxo_total = fluxo_fotons(fluxo_total,banda)
        t += ti
        tempo_atual += ti
    return(fluxo_total)

        #fluxo_total += n_fotons #+ int(sum(arranjo))*ti  #fluxo_fotons(f, banda)*area_telescopio*ti
        #t += ti
        #tempo_atual += ti
       #
       #  print(fluxo_total)
    #### INSERIR O NUMERO DE FÓTONS E O TEMPO EM UMA TABELA
    #return(int(fluxo_total))

def contagem_fluxo_anel(tempo_atual, mag_obj, mag_star, area_telescopio
, tempo_exposicao, banda, inicio, fim, prof_otica, inicio_anel1, fim_anel1
,inicio_anel2, fim_anel2):
   # mag_star = mag_star #combinar com mag obj
    
   #
    ti = tempo_exposicao/20
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = mag_obj
        elif posicao >= inicio_anel1 and posicao <= fim_anel1:
            magnitude = soma_magnitude((mag_star+mag_star * prof_otica), mag_obj) 
        elif posicao >= inicio_anel2 and posicao <= fim_anel2:
            magnitude = soma_magnitude(mag_obj, (mag_star+mag_star*prof_otica))
        else:
            magnitude = soma_magnitude(mag_star,mag_obj)
        f = Fluxo_lambda(magnitude)
        fluxo_total += fluxo_fotons(f, banda)*area_telescopio*ti
        t += ti
        tempo_atual += ti
    return(fluxo_total)

def contagem_fluxo_anel_satelite(tempo_atual, mag_obj, mag_star,mag_sat, area_telescopio
, tempo_exposicao, banda, inicio, fim, prof_otica, inicio_anel1, fim_anel1
,inicio_anel2, fim_anel2,inicio_sat,fim_sat):
   # mag_star = mag_star #combinar com mag obj
    mag_anel = mag_star-2.5*np.log(np.exp(-prof_otica))
   #
    ti = tempo_exposicao/100
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = soma_magnitude(mag_obj,mag_sat)
        elif posicao >= inicio_anel1 and posicao <= fim_anel1:
            magnitude1 = soma_magnitude(mag_sat,mag_obj)
            magnitude = soma_magnitude((mag_anel), magnitude1) 
        elif posicao >= inicio_anel2 and posicao <= fim_anel2:
            magnitude1 = soma_magnitude(mag_sat,mag_obj)
            magnitude = soma_magnitude(magnitude1, mag_anel)
        elif posicao >= inicio_sat and posicao <= fim_sat:
            magnitude = soma_magnitude(mag_sat, mag_obj) 
        else:
            magnitude1 = soma_magnitude(mag_star,mag_obj)
            magnitude = soma_magnitude(magnitude1,mag_sat)
        f = Flux_lambda_ruido(magnitude)
        #f = Fluxo_lambda(magnitude)
        fluxo_total=f
         #+ fluxo_fotons(f, banda)*ti
        #fluxo_total = fluxo_total#/2 
        
        if fluxo_total < 0:
            fluxo_total = 0 #abs(fluxo_total)
        fluxo_total == fluxo_fotons(fluxo_total,banda)*ti*area_telescopio
        #fluxo_total += fluxo_total*np.random.normal(fluxo_total,var_irradi**(1/2))
        t += ti
        tempo_atual += ti
    return(fluxo_total)

def contagem_fluxo_satelite(tempo_atual, mag_obj, mag_star, mag_sat, area_telescopio
, tempo_exposicao, banda, inicio, fim, inicio_sat, fim_sat):
   # mag_star = mag_star #combinar com mag obj
    
   #
    ti = tempo_exposicao/20
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = soma_magnitude(mag_sat, mag_obj)
        elif posicao >= inicio_sat and posicao <= fim_sat:
            magnitude = soma_magnitude(mag_sat, mag_obj) 
        else:
            magnitude1 = soma_magnitude(mag_star,mag_obj)
            magnitude = soma_magnitude(mag_sat,magnitude1)
        f = Fluxo_lambda(magnitude)
        fluxo_total += fluxo_fotons(f, banda)*ti*area_telescopio
        t += ti
        tempo_atual += ti
    return(fluxo_total)

def contagem_fluxo_ceu(tempo_atual, area_telescopio, tempo_exposicao, banda, inicio, fim):
   # mag_star = mag_star #combinar com mag obj
    ti = tempo_exposicao/20
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        if banda < 4050 and banda >= 2000: #3700
            magnitude = 23.2
        if banda >= 4050 and banda < 4950: #4400
            magnitude = 23.4
        if banda >= 4950 and banda < 5950: #5500
            magnitude = 22.7
        if banda >= 5950 and banda < 7200: #6400 
            magnitude = 22.2
        if banda >= 7200 and banda < 10000: #8000
            magnitude = 22.2
        if banda >= 10000 and banda < 14000: #12000
            magnitude = 20.7
        if banda >= 14000 and banda < 19000: #16000
            magnitude = 20.9
        if banda >= 19000 and banda < 25000: #22000
            magnitude = 21.3
        f = Fluxo_lambda(magnitude)
        fluxo_total += fluxo_fotons(f, banda)*area_telescopio*ti
        t += ti
        tempo_atual += ti
    return(fluxo_total)

#S/N
def signalNoise():
    N = 1#numero de fótons coletados
    npix = 1 #numero de pixels levados em consideração para o S/N 
    Ns = 1 #Número de fótons por pixel do fundo de céu
    Nd = 1 #Número de eletrons de dark current 
    Nr = 1 #Número de eletrons por pixel resultante do ruido de leitura
    return N

#cintilação

def cintilacao(velocidade_vento_chao, altitude, tempo):
   
    result,error = integrate.quad(vel_vento, 5000, 20000, args=(altitude, velocidade_vento_chao))
    
    w=1/15*result
    A=np.exp(random.gauss(altitude, tempo))
    print("O resultado de A é " + str(A))
    cintila = A*(2.2*10**(-53)*(altitude**10)*(w/27)**2*np.exp(-altitude/1000)+1*10**-16*np.exp(-altitude/1500))
    return cintila
####

####seeing 17_08
#tabela 3.1 hardy para referencia dos números
seeing = 2.5#(1.22*500*10**-9)/0.05
h = 4213 
L_prop = 20000 #m
dist_raios = 10 # distancia entre dois raios paralelos que passam pela atmosfera e geram uma diferença de fase deltafi
L=20000
if seeing >= 1.88:
    seeing = 2.5
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 17 * 10 ** -15
    Ha = 100
    B = 27 * 10 ** -17
    Hb = 1500
    C = 3.59 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.05
elif seeing < 1.88 and seeing >= 1.205:
    seeing = 1.26
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 4.5 * 10 ** -15
    Ha = 100
    B = 9 * 10 ** -17
    Hb = 1500
    C = 2 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.1
elif seeing < 1.205 and seeing >= 0.995:
    seeing = 1.15
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 0
    Ha = 1
    B = 27 * 10 ** -17
    Hb = 1500
    C = 5.94 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.11
elif seeing < 0.995 and seeing >= 0.685:
    seeing = 0.84
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 2 * 10 ** -15
    Ha = 100
    B = 7 * 10 ** -17
    Hb = 1500
    C = 1.54 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.15
elif seeing < 0.685 and seeing >= 0.445:
    seeing = 0.53
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 0
    Ha = 1
    B = 1 * 10 ** -17
    Hb = 3000
    C = 1.63 * 10 ** -53 
    Hc = 1000
    D = 1
    Hd = 6500
    r0 = 0.24
elif seeing < 0.445:
    seeing = 0.36
    print("O valor do seeing utilizado será de {:.2f} para se adaptar ao modelo de turbulência" .format(seeing))
    A = 0
    Ha = 1
    B = 1 * 10 ** -17
    Hb = 3000
    C = 1.63 * 10 ** -53 
    Hc = 1000
    D = 0
    Hd = 0
    r0 = 0.34
else:
    print("erro")

#k = 2 * np.pi / (0.55 * 10 **-6)

#deltafi = k*d*deltaN(d) #deltaN é a variação no indice de refração
d = ((np.pi**2)/(np.pi*np.pi*Cn2*L))**(3/5) # espessura da camada de ar responsável pelos efeitos
print(d)
Cn2 = A * np.exp(-h/Ha) + B * np.exp(-h/Hb) + C * (h**(10)) * np.exp(-h/Hc) + D *np.exp((-(h-Hd)**2)/2*dist_raios*dist_raios)
cn10 = integrate.quad(Cnh2,-np.inf,np.inf)
cn11=integrate.quad(Cn22,0,np.inf)
cn12=integrate.quad(Cn22h,-np.inf,np.inf)
#L=(cn12[0]/cn10[0])**(3/5)*100 #5.137 saha
print(Cn2)
print(L)

print(cn11[0])
print(cn10)
print(cn12)
#valido para l0<dist_raios<L0
k=ka(band)
D0 = 1.46 * k ** 2 * Cn2 * L * dist_raios **(5/3)
print(D0)
s2 = seeing *180*60*60/np.pi
print(seeing)
print(s2)

# contar fotons em área equivalente ao telescopio, aplicar a variancia de fase em cada fóton e com base 
#nisso fazer dois fótons interagirem e assim incluir o ruído

#diam_teles = 1.6 #m
#k = 2 * np.pi/ (600*10**-9) #/m

var_fase = 0.134 * (diam_teles/r0) ** (5/3) #2.62 tyson
#var_log_amplitude = 0.124* (k ** (7/6)) * (L_prop ** (11/6) )* Cn2 #2.31 tyson

# a is an aperture-averaging factor
a = (1 + 1.07 * ((k * (diam_teles**2))/(4 * L_prop))**(7/6))**-1
#print(a)

#print(var_fase)
#print("log_amp " + str(var_log_amplitude))

cn15=integrate.quad(Cn22,0,np.inf)
ir_saha=((19.2*band*(10**-9))**(-7/6))*cn15[0]
#print("variancia log intensidade " + str(ir_saha**(1/2))) #Saha 5.139

var_irradi = a * (np.exp(4 * (ir_saha))-1)
print(var_fase)

#print(cn15)


hp=6.62*10**-34 #m²kg/s
#mag_star = 14.83
#print(np.random.normal(0,var_fase**(1/2))) #DIVIDIR POR PI E VERIFICAR SE OCORRE INTERFERENCIA DESTRUTIVA OU CONSTRUTIVA
#print(np.random.normal(0,var_log_amplitude**(1/2)))
#tempexp = 0.44 #s
#compri_onda = 600*10**-9 #m
print(band)
print(tempexp)
ampli = (2*hp/(((band*10**-9)**2) * ep0 * tempexp))**(1/2)
print("a amplitudo vale " + str(ampli))
print(ir_saha)
amp = np.random.normal(np.log(ampli),ir_saha**(1/2))#var_log_amplitude**(1/2))
print(amp)
print(np.exp(amp))

print("A amplitude ficou: "+ str(np.exp(amp)))
#intesit = ((c*ep0*(np.exp(ampli))**2)/2)/10000/tempo
intesity = ((c*ep0*(np.exp(amp))**2)/2)/tempexp/10000 #W/cm²
E0 = 3.6*10**-9 #W/m²
E = (E0*10**(-0.4*mag_star))/tempexp/(np.pi*(diam_teles/2)**2) #W/cm²
#E2=(hp*c/compri_onda)/tempo/(np.pi*(diam_teles/2)**2) #W/cm²
print("A irradiancia é: " + str (E))
#print("A irradiancia 2 é: " + str (E2))
#print("o valor da intensidade é de " + str(intesit))
print("o valor da intensidade variada é de " + str(intesity))
ira = np.random.normal(0,(var_irradi**(1/2))/np.pi*(diam_teles/2)**2)
print("o valor da variancia da irradiancia e " + str (ira*tempexp))
irad = np.random.normal(0,(var_irradi**(1/2))/np.pi*(diam_teles/2)**2)
print("o valor da variancia da irradiancia e " + str (irad*tempexp))

print(np.exp((np.log(E)+np.random.normal(0,ir_saha**(1/2)/np.pi*(diam_teles/2)**2)*tempexp)))

def ruido_termico(Temperatura, numero_pixel, tempo_exp):
    Eg = 1.1557 - (7.021 * 10 **(-4)*Temperatura**2/(1108+Temperatura))
    Tx = 5.86*(10**9)*(Temperatura**(2/8))*np.exp(-(Eg)/(2*(1.23*10**-4)*Temperatura)) # k = 1.23*10**-4 obtido em testes para seguir a relação da literatura
    sig_dark = (Tx*numero_pixel*tempo_exp)**(1/2)
    return sig_dark
print(np.random.poisson(ruido_termico(300,10,4)))

def ruido_leitura(ruido):
    rui_leit=np.random.normal(0,ruido)
    return rui_leit
print(ruido_leitura(2.5))

#Definindo Dados:
flua = []
vel = 30 #[30,31,32]
tmini = 0
temp = tmini
tmaxi = 4000
mag_star = 19 #magnitudes_estrelas = [12,19,21]
mag_obj = 20 #[19 20 25]
distancia = 300 #[240, 300, 520]
magi_sat = -1.25 #Triton -1.25 Miranda 3.49
mag_sat = calculo_magnitude(magi_sat, distancia)
#mag_sat = 25.1
diametro_sat = 2700 #Triton 2700 Miranda 500
distancia_sat = 60000 #Triton 60000 Miranda 250000
diametro_estrela = 1.33 #[0.98, 7.84]
diam_teles = 500 # cm
foco = 1.8 #F
ep = 0.7 #arcsec?
#ep = Escala_placa(13,1,16000)
bina = 1
gain = 0.8
readout_noise = 2.5
temperatura = 215

area_telescopio = np.pi*(diam_teles)**2 #cm²
tempexp = 0.01 #[300, 100, 50, 10, 1]
band = 6200 #[5000, 5500, 6000, 6500, 7000]
diametro_corpo = 19548 #km [18432, 19548, 20665]
centro_ocultacao =  2000 #Triton 2800 miranda 50
inicio = centro_ocultacao - diametro_corpo/vel/2
fim = centro_ocultacao + diametro_corpo/vel/2
cyc = tempexp+0.001#tempexp + 0.01
times = np.arange(tmini, tmaxi, cyc)
Xs = np.arange(tmini*vel,tmaxi*vel,cyc*vel)
X01 = inicio*vel
X02 = fim*vel
#https://arxiv.org/ftp/arxiv/papers/1805/1805.08963.pdf#:~:text=Uranus%20rings%20are%20dense%2C%20made,range%20between%200.1%20and%201.
#https://arxiv.org/pdf/1906.11728.pdf
prof_otica = 0.1 #10-4 a 0.1 (netuno) (0.003 Lassell ring), 0.1 a 1 Urano  [0.0001, 0.003, 0.1, 0.5, 1]
diametro_anel = 51000 #[40900, 53200, 51000, 42000, 37800]
espessura_anel = 10 #[2000, 100, 20, 2, 3500]
inicio_anel1 = centro_ocultacao - diametro_anel/vel/2 - espessura_anel/vel/2
fim_anel1 = centro_ocultacao - diametro_anel/vel/2 + espessura_anel/vel/2
#inicio_anel2 = centro_ocultacao + diametro_anel/vel/2 - espessura_anel/vel/2
#fim_anel2 = centro_ocultacao + diametro_anel/vel/2 + espessura_anel/vel/2
X01_an = inicio_anel1*vel
X02_an = fim_anel1*vel
#X03_an = inicio_anel2*vel
#X04_an = fim_anel2*vel
inicio_sat = centro_ocultacao - distancia_sat/vel/2 - diametro_sat/vel/2
fim_sat = centro_ocultacao - distancia_sat/vel/2 + diametro_sat/vel/2
X01_sat = inicio_sat*vel
X02_sat = fim_sat*vel
print(inicio_sat)
print(fim_sat)
print(inicio_anel1)
print(fim_anel1)
print(inicio)
print(fim)

#prof_otica = 
#print(prof_otica)
#prof_otica = -np.log(1-prof_otica)
#print(prof_otica)
#print(soma_magnitude(mag_obj, (mag_star+mag_star*prof_otica)))
#print(mag_obj)
#print(mag_star)
#print(soma_magnitude(mag_star,mag_obj))
prof_otica2 = 0.1 #10-4 a 0.1 (netuno) (0.003 Lassell ring), 0.1 a 1 Urano  [0.0001, 0.003, 0.1, 0.5, 1]
diametro_anel2 = 51000
espessura_anel2 =20
inicio_anel2 = centro_ocultacao + diametro_anel2/vel/2 - espessura_anel2/vel/2
fim_anel2 = centro_ocultacao + diametro_anel2/vel/2 + espessura_anel2/vel/2

prof_otica3 = 0.0000026
diametro_anel3 = 799000.8
espessura_anel3 = 76.4
inicio_anel3 = centro_ocultacao - diametro_anel3/vel/2 - espessura_anel3/vel/2
fim_anel3 = centro_ocultacao - diametro_anel3/vel/2 + espessura_anel3/vel/2

prof_otica4 = 0.0000353
diametro_anel4 = 824600.22
espessura_anel4 = 5.3
inicio_anel4 = centro_ocultacao + diametro_anel4/vel/2 - espessura_anel4/vel/2
fim_anel4 = centro_ocultacao + diametro_anel4/vel/2 + espessura_anel4/vel/2

X03_an = inicio_anel2*vel
X04_an = fim_anel2*vel
X05_an = inicio_anel3*vel
X06_an = fim_anel3*vel
X07_an = inicio_anel4*vel
X08_an = fim_anel4*vel

def contagem_fluxo_anel2(tempo_atual, mag_obj, mag_star, area_telescopio
, tempo_exposicao, banda, inicio, fim, prof_otica,prof_otica2, prof_otica3,prof_otica4, inicio_anel1, fim_anel1
,inicio_anel2, fim_anel2,inicio_anel3, fim_anel3
,inicio_anel4, fim_anel4):
   # mag_star = mag_star #combinar com mag obj
    mag_anel = mag_star-2.5*np.log(np.exp(-prof_otica))
    mag_anel2 = mag_star-2.5*np.log(np.exp(-prof_otica2))
    mag_anel3 = mag_star-2.5*np.log(np.exp(-prof_otica3))
    mag_anel4 = mag_star-2.5*np.log(np.exp(-prof_otica4))
   #
    ti = tempo_exposicao/100
    t = 0
    fluxo_total = 0
    while t < tempo_exposicao:
        #verifica posição objeto
        posicao = tempo_atual
        if posicao >= inicio and posicao <= fim:
            magnitude = mag_obj
        elif posicao >= inicio_anel1 and posicao <= fim_anel1:
            magnitude1 = mag_obj

            magnitude = soma_magnitude((mag_anel), magnitude1) 
        elif posicao >= inicio_anel2 and posicao <= fim_anel2:
            magnitude1 = mag_obj
            magnitude = soma_magnitude((mag_anel2), magnitude1) 
        elif posicao >= inicio_anel3 and posicao <= fim_anel3:
            magnitude1 = mag_obj
            magnitude = soma_magnitude((mag_anel3), magnitude1)  
        elif posicao >= inicio_anel4 and posicao <= fim_anel4:
            magnitude1 = mag_obj
            magnitude = soma_magnitude((mag_anel4), magnitude1) 
        else:
            magnitude = soma_magnitude(mag_star,mag_obj)
            
        f = Flux_lambda_ruido(magnitude)
        #f = Fluxo_lambda(magnitude)
        fluxo_total=f
         #+ fluxo_fotons(f, banda)*ti
        #fluxo_total = fluxo_total#/2 
        
        if fluxo_total < 0:
            fluxo_total = 0 #abs(fluxo_total)
        fluxo_total == fluxo_fotons(fluxo_total,banda)*ti*area_telescopio
        fluxo_total += fluxo_total*np.random.normal(fluxo_total,var_irradi**(1/2))*5
        t += ti
        tempo_atual += ti
    return(fluxo_total)

calc_fresnel(distancia,band)

Fres_sat=bar_fresnel(Xs,X01_sat,X02_sat,1,distancia,band)

plt.plot(times,Fres_sat, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an1=bar_fresnel(Xs,X01_an,X02_an,prof_otica,distancia,band)
plt.plot(times,Fres_an1, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an2=bar_fresnel(Xs,X03_an,X04_an,prof_otica2,distancia,band)
plt.plot(times,Fres_an2, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an3=bar_fresnel(Xs,X05_an,X06_an,prof_otica3,distancia,band)
plt.plot(times,Fres_an1, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_an4=bar_fresnel(Xs,X07_an,X08_an,prof_otica4,distancia,band)
plt.plot(times,Fres_an1, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres=bar_fresnel(Xs,X01,X02,1,distancia,band)
plt.plot(times,Fres, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')

Fres_tot = (Fres*Fres_sat*Fres_an1*Fres_an2*Fres_an3*Fres_an4)
plt.plot(times,Fres_tot, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo ")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação com Difração de Fresnel")

tempo_a =  tmini
#if fluxo_instante > 20000:
#        print("Por questão de tempo computacional foi realizada uma aproximação no número de fótons")
while tempo_a < tmaxi:
    fluxo_instante = contagem_fluxo_anel2(tempo_a,mag_obj,mag_star, area_telescopio, 
                                                  tempexp, band, inicio, fim, prof_otica, prof_otica2, prof_otica3, prof_otica4, inicio_anel1, 
                                                  fim_anel1, inicio_anel2, fim_anel2, inicio_anel3, fim_anel3, inicio_anel4, fim_anel4)
    #ceu = random.gauss(1,0.03)*contagem_fluxo_ceu(tempo_a, area_telescopio, tempexp,band, inicio, fim) 
    #print(fluxo_instante)
    ####ARRUMAR NO RUIDO TERMICO QUE É COM NUMERO DE PIXEL NÃO COM O FLUXO
    fluxo_instant = fluxo_instante#+(np.random.normal(0,ruido_termico(temperatura,fluxo_instante,tempexp)))#np.random.normal(fluxo_instante, 0.3)#var_fase**(1/2))#ceu+random.gauss(1, 0.03)*fluxo_instante
   # print(fluxo_instante)
    fluxo_instant = fluxo_instante #+ erro_fase(fluxo_instante,var_fase)
    #fluxo_instant = abs(fluxo_instant)
    flua.append(fluxo_instant)
    tempo_a += cyc
print (flua)

plt.plot(times,flua, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo Normalizado")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação P9")

##########NORMALIZAÇÃO
i=0
med=np.median(flua[0:40])
for i in range(len(flua)):
    flua[i]=flua[i]/med
    i=i+1


Flua_fres=[i for i in range(len(flua))]

i=0
while i < len(flua):
    if flua[i] == 1:
        Flua_fres[i]=flua[i]*Fres_tot[i]
    else:
        Flua_fres[i]=(flua[i]+Fres_tot[i])/2
    i+=1
print(flua)
print(Flua_fres)

##########NORMALIZAÇÃO
j=0
med=(np.median(Flua_fres))
Flua_fresn=[]
for j in range(len(Flua_fres)):
    Flua_fresn.append(Flua_fres[j]/med)
    j=j+1

plt.plot(times,Flua_fres, 'o-',color='black',linewidth= 0.7,markersize=2.3)
plt.ylabel("Fluxo Normalizado")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação com Difração de Fresnel")#"{:.1f}s_{:.1f}ms_{:.0f}Mm_{:.0f}UA_{:.0f}_{:.0f}_{:.0f}_{:.1f}m_{:.0f}".format(
        #tempexp,vel,diametro_corpo/1000, distancia, diametro_estrela, mag_star,band, diam_teles/1000,mag_obj))
#plt.savefig("teste")
    #"mSt{:.0f}_{:.1f}s_{:.0f}Mm_Rg_{:.2f}_{:.0f}km_sa_Mir_T_{:.1f}m".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000))
#
# plt.savefig("imags/_{:.1f}s_{:.1f}ms_{:.0f}Mm_{:.0f}UA_{:.0f}_{:.0f}_{:.0f}_{:.1f}m_{:.0f}_sat{:.0f}_{:.0f}_anel_{:.0f}_{:.0f}_{:.4f}.png".format
#    (tempexp, vel, diametro_corpo/1000, distancia, diametro_estrela, mag_star, band, (diam_teles/1000), mag_obj, diametro_sat, distancia_sat, diametro_anel, espessura_anel,prof_otica),dpi = 300)    
                                                     
                                
    #"magStar{:.1f}_{:.1f}s_{:.0f}Mm_Ring_{:.2f}_{:.0f}km_sat_Miranda_Tel_{:.1f}m.png".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000)
    #        ,dpi = 300)                

plt.figure(figsize=(20,6))
plt.plot(times,Flua_fresn, 'o-',color='black',linewidth= 0.7,markersize=1)
plt.ylabel("Fluxo Normalizado")
plt.xlabel('Tempo [segundos]')
plt.title("Simulação P9 seeing 2.5")#"{:.1f}s_{:.1f}ms_{:.0f}Mm_{:.0f}UA_{:.0f}_{:.0f}_{:.0f}_{:.1f}m_{:.0f}".format(
        #tempexp,vel,diametro_corpo/1000, distancia, diametro_estrela, mag_star,band, diam_teles/1000,mag_obj))
#plt.savefig("teste")
    #"mSt{:.0f}_{:.1f}s_{:.0f}Mm_Rg_{:.2f}_{:.0f}km_sa_Mir_T_{:.1f}m".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000))
#
plt.savefig("imags/2.5_0.01.png" ) 
                                                     
    #"magStar{:.1f}_{:.1f}s_{:.0f}Mm_Ring_{:.2f}_{:.0f}km_sat_Miranda_Tel_{:.1f}m.png".format(
    #mag_star,tempexp,diametro_corpo/1000, prof_otica, espessura_anel, diam_teles/1000)
    #        ,dpi = 300)                
```

- Reestruturei `model_training/synthetic_curve/simulate_curve.py` em classes e funções coesas, com docstrings e comentários didáticos.
- Incluí física de Fresnel com fallback sem SciPy, ruído (Poisson, leitura, cintilação), normalização robusta e orquestração via `SyntheticLightCurveSimulator`.
- Adicionei `testes_extras()` com cenários aproximados de Umbriel (sem anéis) e Chariklo (com anéis C1R e C2R), incluindo parâmetros típicos e justificativas nos comentários.
- Deixei comentários no topo explicando todas as alterações e motivos, no estilo “junior + PEP8”.

---

**User**

O código retornou imagens assim (1° imagem), mas eu esperava curvas no formato assim (2° imagem). O que houve? @model_training/synthetic_curve/simulate_curve.py 

---

**Cursor**

- O que aconteceu: o ganho/escala de fótons ficou muito baixo para a magnitude usada. Com mag≈12.5 e o ganho padrão do simulador, o número médio de fótons por exposição ficou < 1, então o ruído de Poisson domina. Resultado: muitos zeros e “picos” ocasionais; ao normalizar, surgem espigões como na 1ª imagem, em vez de uma curva suave como a 2ª.

- Como deveria ser: para curvas “pós-fotometria” parecidas com dados reais, você precisa de milhares de fótons por exposição (S/N alto). A forma difrativa aparecerá e a normalização ficará perto de 1 com dispersão pequena.

Sugestão de ajustes mínimos (sem mudar a física)
1) Aumente a taxa de fótons (ganho) e suavize a cintilação:
- Troque o ganho padrão do ruído para algo alto (ex.: 1e9 counts por unidade de fluxo).
- Faça a cintilação escalar ~ t^-1/2 (mais realista) e com fator menor.

Substitua no arquivo `model_training/synthetic_curve/simulate_curve.py` a classe de ruído pela versão abaixo (apenas estes trechos):

```python
class NoiseModel:
    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 5.0,
                 gain_counts_per_flux: float = 1e9,  # antes: 4e5
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 1e-10, None)

        lam = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam = np.clip(lam, 0, 1e12)

        shot = self.rng.poisson(lam)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=shot.size)

        # cintilação ~ t^{-1/2} e fator menor
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3))**0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=shot.size))

        counts = (shot + read) * scint
        flux = counts / (self.gain_counts_per_flux * self.exposure_time_s)
        return np.clip(flux, 0.0, None)
```

2) Se preferir, aumente também o tempo de exposição (ex.: 0.2–0.5 s) ou use uma estrela mais brilhante (mag 10–11) para reforçar o S/N.

3) Rode novamente os testes:
- Com `gain_counts_per_flux=1e9`, mag≈12.5 e `exposure_time_s=0.1`, o baseline terá ~10^3 fótons por amostra; a curva normalizada deve ficar perto de 1, com ruído bem menor e o formato de ocultação/difração visível.

Por que resolve:
- Mais fótons por exposição → ruído de Poisson relativo cai (∝ 1/√N), eliminando os “picos”.
- Cintilação mais fraca e com dependência t^-1/2 evita modulações multiplicativas grandes.
- A normalização por quartis passa a referenciar um baseline estável, deixando a curva no “formato de dado” esperado.

```python
class NoiseModel:
    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 5.0,
                 gain_counts_per_flux: float = 1e9,  # antes: 4e5
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 1e-10, None)

        lam = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam = np.clip(lam, 0, 1e12)

        shot = self.rng.poisson(lam)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=shot.size)

        # cintilação ~ t^{-1/2} e fator menor
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3))**0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=shot.size))

        counts = (shot + read) * scint
        flux = counts / (self.gain_counts_per_flux * self.exposure_time_s)
        return np.clip(flux, 0.0, None)
```

---

**User**

Aplique suas sugestões anteriores em @model_training/synthetic_curve/simulate_curve.py 


---

**Cursor**

Vou aplicar as mudanças no modelo de ruído: aumentar o ganho para 1e9 e ajustar a fórmula da cintilação com dependência t^-1/2 e fator menor, para reduzir os espigões e melhorar o S/N.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador modular de curvas de luz de ocultações estelares.

Este arquivo reorganiza o antigo script monolítico em classes e funções
coesas, seguindo PEP 8 e boas práticas de programação científica.

Principais componentes:
- Física de Fresnel (difração em bordas "knife-edge" e faixa opaca)
- Geometria do evento (linha do tempo e coordenada ao longo da corda)
- Modelo de ruído (Poisson, leitura, cintilação multiplicativa)
- Normalização "pós-fotometria" (baseline ~ 1)
- Orquestração via uma classe principal de fácil uso

Bibliotecas: numpy, pandas, matplotlib (SciPy é opcional; usado se disponível).

CHANGES (alterações em relação ao código anterior):
- Removidos trechos experimentais, prints soltos e globais redundantes
  (motivo: clareza, reprodutibilidade e manutenibilidade).
- Unidades explicitadas (km, s, nm) e conversões centralizadas
  (motivo: reduzir erros por mistura de unidades).
- Difração de Fresnel isolada em funções puras com fallback sem SciPy
  (motivo: manter acurácia quando disponível e portabilidade quando não).
- Ruídos desacoplados da física (camada separada)
  (motivo: permitir trocar/ligar/desligar ruídos facilmente).
- Normalização robusta por quartis contíguos ou mediana
  (motivo: simular "pós-fotometria" com baseline estável).
- Função `testes_extras()` com cenários aproximados de Umbriel e Chariklo
  (motivo: exemplos práticos com corpos pequenos conhecidos).
"""

from __future__ import annotations

from typing import Optional, Tuple, List
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# Utilidades e constantes
# =============================================================================

SPEED_OF_LIGHT_MS = 299_792_458.0  # m/s (não é usada diretamente, mantida por referência)
NM_TO_KM = 1e-12  # 1 nm = 1e-12 km


def magnitude_to_relative_flux(magnitude: float) -> float:
    """
    Converte magnitude aparente em fluxo relativo (sem calibração absoluta).

    Equação fotométrica padrão:
        F ∝ 10^(-0.4 m)
    """
    return 10.0 ** (-0.4 * float(magnitude))


def normalize_flux_top_quartiles(flux: np.ndarray) -> np.ndarray:
    """
    Normaliza o fluxo dividindo pelo baseline estimado como a média das duas
    maiores médias entre 4 segmentos contíguos (quartis em tempo).

    - Razoável para "pós-fotometria": baseline ~ 1 fora da ocultação.
    - Fallbacks garantem retorno mesmo em séries curtas.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return flux
    if valid.size < 4:
        baseline = float(np.mean(valid))
        baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
        return flux / baseline
    segments = np.array_split(valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
    if len(means) == 0:
        baseline = float(np.median(valid))
    else:
        order = np.argsort(means)
        top = [means[order[-1]]]
        if len(means) >= 2:
            top.append(means[order[-2]])
        baseline = float(np.mean(top))
    if not np.isfinite(baseline) or baseline <= 0:
        baseline = float(np.median(valid))
        if not np.isfinite(baseline) or baseline <= 0:
            return flux
    return flux / baseline


# =============================================================================
# Física de Fresnel (difração)
# =============================================================================

class FresnelPhysics:
    """
    Funções para cálculo de escala de Fresnel e transmitâncias difrativas.
    """

    @staticmethod
    def fresnel_scale_km(distance_km: float, wavelength_nm: float) -> float:
        """
        F = sqrt(lambda * D / 2), com lambda em km e D em km.
        """
        lambda_km = float(wavelength_nm) * NM_TO_KM
        D = float(distance_km)
        return math.sqrt(max(lambda_km * D / 2.0, 1e-30))

    @staticmethod
    def fresnel_CS(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrais de Fresnel (C, S) com SciPy se disponível; caso contrário,
        usa aproximações assintóticas/séries adequadas a fins educacionais.
        """
        try:
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore
            # A escala do argumento varia entre convenções; adotamos um fator
            # para obter bom acordo qualitativo.
            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback aproximado: bom o suficiente didaticamente
        x = np.asarray(u, dtype=float)
        ax = np.abs(x)
        C = np.zeros_like(x)
        S = np.zeros_like(x)

        small = ax <= 1.5
        if np.any(small):
            z = x[small]
            # Séries truncadas (educacional; não metrológico)
            C[small] = (z - (math.pi**2) * (z**5) / 40.0) / math.sqrt(2.0 * math.pi)
            S[small] = ((math.pi) * (z**3) / 6.0 - (math.pi**3) * (z**7) / 336.0) / math.sqrt(
                2.0 * math.pi
            )

        large = ~small
        if np.any(large):
            z = x[large]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[large] = c
            S[large] = s

        return C, S

    @staticmethod
    def knife_edge_transmission(x_km: np.ndarray, edge_pos_km: float,
                                distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Transmitância de difração para uma borda "knife-edge".

        I(u) = 0.5 [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ],
        onde u = (x - x_edge) / F e F é a escala de Fresnel.
        """
        F = FresnelPhysics.fresnel_scale_km(distance_km, wavelength_nm)
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = FresnelPhysics.fresnel_CS(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    @staticmethod
    def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                  distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa opaca: produto de duas bordas (imersão e emersão).
        """
        half = 0.5 * float(width_km)
        x1 = float(center_km) - half
        x2 = float(center_km) + half
        T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
        T2 = FresnelPhysics.knife_edge_transmission(-x_km, -x2, distance_km, wavelength_nm)
        return np.clip(T1 * T2, 0.0, 1.0)

    @staticmethod
    def partial_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                   opacity: float, distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa parcialmente opaca (anéis):
        T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = FresnelPhysics.opaque_strip_transmission(
            x_km, center_km, width_km, distance_km, wavelength_nm
        )
        return 1.0 - float(opacity) * (1.0 - T_opaque)


# =============================================================================
# Modelo de ruído
# =============================================================================

class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.
    """

    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 5.0, gain_counts_per_flux: float = 1e9,
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Aplica Poisson (fótons), ruído de leitura (gaussiano) e cintilação (lognormal).
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 1e-10, None)

        # Converte para contagens (ganho arbitrário para S/N razoável)
        lam = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam = np.clip(lam, 0, 1e12)

        # Poisson (fótons)
        shot = self.rng.poisson(lam)

        # Leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=shot.size)

        # Cintilação (lognormal): pior para seeing ruim e diminui com t^{-1/2}
        # Fator menor para evitar modulações multiplicativas exageradas.
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=shot.size))

        counts = (shot + read) * scint
        flux = counts / (self.gain_counts_per_flux * self.exposure_time_s)
        return np.clip(flux, 0.0, None)


# =============================================================================
# Simulador principal
# =============================================================================

class SyntheticLightCurveSimulator:
    """
    Simulador de curvas de luz sintéticas para ocultações estelares.

    Parâmetros
    ----------
    mag_star : float
        Magnitude aparente da estrela (escala relativa).
    distance_km : float
        Distância observador–corpo (km), usada na escala de Fresnel.
    diameter_km : float
        Diâmetro projetado do corpo (km) ao longo da corda.
    velocity_kms : float
        Velocidade relativa do evento (km/s).
    exposure_time_s : float
        Tempo de exposição por amostra (s).
    total_duration_s : Optional[float]
        Duração total da simulação (s). Se None, é inferida com margem.
    wavelength_nm : float
        Comprimento de onda efetivo (nm), p.ex. 550 nm ~ banda V.
    seeing_arcsec : float
        Seeing (arcsec), controla a cintilação.
    rings : Optional[List[Tuple[float, float, float]]]
        Lista de anéis como (offset_km, width_km, opacity). Opacity em [0,1].
    satellites : Optional[List[Tuple[float, float]]]
        Lista de satélites como (offset_km, diameter_km).
    normalize_method : str
        "top_quartiles" (default) ou "median".
    random_seed : Optional[int]
        Semente para reprodutibilidade dos ruídos.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4_000.0,
        diameter_km: float = 1_200.0,
        velocity_kms: float = 20.0,
        exposure_time_s: float = 0.1,
        total_duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        satellites: Optional[List[Tuple[float, float]]] = None,
        normalize_method: str = "top_quartiles",
        random_seed: Optional[int] = None,
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time_s = float(exposure_time_s)
        self.total_duration_s = float(total_duration_s) if total_duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.rings = rings if rings is not None else []
        self.satellites = satellites if satellites is not None else []
        self.normalize_method = normalize_method

        self.rng = np.random.default_rng(random_seed)
        self.noise = NoiseModel(
            seeing_arcsec=self.seeing_arcsec,
            exposure_time_s=self.exposure_time_s,
            rng=self.rng,
        )

        # Saídas
        self.time_s: Optional[np.ndarray] = None
        self.flux: Optional[np.ndarray] = None
        self.flux_norm: Optional[np.ndarray] = None

        # Diretórios de saída
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_dirs()

    def simulate(self) -> pd.DataFrame:
        """
        Executa a simulação completa:
        - Constrói tempo e coordenada ao longo da corda
        - Calcula transmitância difrativa: corpo × anéis × satélites
        - Converte magnitude em fluxo relativo e aplica transmitância
        - Aplica ruídos (Poisson, leitura, cintilação)
        - Normaliza o fluxo
        """
        t, x = self._build_time_and_chord()

        # Corpo principal (faixa opaca)
        T_body = FresnelPhysics.opaque_strip_transmission(
            x, center_km=0.0, width_km=self.diameter_km,
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )

        # Anéis (faixas parcialmente opacas)
        T_rings = np.ones_like(T_body)
        for (offset_km, width_km, opacity) in self.rings:
            T_rings *= FresnelPhysics.partial_strip_transmission(
                x, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Satélites (faixas opacas deslocadas)
        T_sats = np.ones_like(T_body)
        for (offset_km, diameter_km) in self.satellites:
            T_sats *= FresnelPhysics.opaque_strip_transmission(
                x, center_km=float(offset_km), width_km=float(diameter_km),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Transmitância total
        T_total = np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

        # Fluxo relativo esperado (sem ruído)
        base_flux = magnitude_to_relative_flux(self.mag_star)
        expected_rel_flux = base_flux * T_total

        # Ruído
        noisy_flux = self.noise.apply(expected_rel_flux)

        # Normalização
        if self.normalize_method == "median":
            baseline = float(np.median(noisy_flux[np.isfinite(noisy_flux)]))
            baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
            flux_norm = noisy_flux / baseline
        else:
            flux_norm = normalize_flux_top_quartiles(noisy_flux)

        # Armazena e retorna
        self.time_s = t
        self.flux = noisy_flux
        self.flux_norm = flux_norm
        return pd.DataFrame({"time_s": t, "flux": noisy_flux, "flux_norm": flux_norm})

    def plot_curve(self, save: bool = True, show: bool = False, title: Optional[str] = None) -> str:
        """
        Plota a curva normalizada. Retorna o caminho do PNG salvo (string)
        se `save=True`, caso contrário retorna string vazia.
        """
        self._require_simulation()
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(self.time_s, self.flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adim.]")
        band = f"{int(round(self.wavelength_nm))} nm"
        ttl = title if title else f"Curva sintética com difração e seeing — {band}"
        ax.set_title(ttl)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        png_path = ""
        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)
        return png_path

    def export_data(self, save: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Exporta os dados simulados para um .dat numerado em output/.
        Retorna (DataFrame, caminho_do_arquivo_ou_string_vazia).
        """
        self._require_simulation()
        df = pd.DataFrame({"time_s": self.time_s, "flux": self.flux, "flux_norm": self.flux_norm})
        dat_path = ""
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df, dat_path

    # -------------------------- helpers internos -----------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.total_duration_s is None:
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time * 3.0  # margem: 1x antes e 1x depois
        else:
            total_time = self.total_duration_s
        n_steps = max(2, int(math.ceil(total_time / self.exposure_time_s)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _ensure_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                n = int(name.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulation(self) -> None:
        if self.time_s is None or self.flux is None or self.flux_norm is None:
            raise RuntimeError("Simulação ainda não executada. Chame simulate() antes.")


# =============================================================================
# Testes extras com corpos pequenos (Umbriel e Chariklo)
# =============================================================================

def testes_extras() -> None:
    """
    Executa dois cenários de teste:
    1) Umbriel (satélite de Urano) — sem anéis
    2) Chariklo (Centauro) — com anéis C1R e C2R (parâmetros aproximados)

    Observações:
    - Valores aproximados (ordem de grandeza) para fins didáticos.
    - Distâncias geocêntricas típicas: Urano ~ 2.9e9 km, Chariklo ~ 2.1e9 km.
    - Velocidades típicas de sombra ~ 20–25 km/s.
    - Parâmetros dos anéis de Chariklo (Braga-Ribas+2014):
        - Raios ~ 391 km e 405 km; larguras ~ 7 km e 3 km;
          profundidades óticas τ ~ 0.4 e 0.06 → opacidade ~ 1 - e^{-τ}.
      Para uma ocultação equatorial idealizada, modelamos cada anel por duas faixas
      simétricas (+/- raio) com a mesma largura e opacidade.
    """
    # ------------------------------- Umbriel ---------------------------------
    umbriel = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,        # ~ distância de Urano à Terra (aprox.)
        diameter_km=1169.0,       # diâmetro de Umbriel ~ 1169 km
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        normalize_method="top_quartiles",
        random_seed=123,
    )
    df_u = umbriel.simulate()
    umbriel.plot_curve(save=True, show=False, title="Umbriel — V~550 nm")
    umbriel.export_data(save=True)

    # ------------------------------ Chariklo ---------------------------------
    # Parâmetros aproximados dos anéis (C1R e C2R)
    r1_km, w1_km, tau1 = 391.0, 7.0, 0.4
    r2_km, w2_km, tau2 = 405.0, 3.0, 0.06
    op1 = 1.0 - math.exp(-tau1)
    op2 = 1.0 - math.exp(-tau2)

    rings_chariklo: List[Tuple[float, float, float]] = [
        (+r1_km, w1_km, op1),
        (-r1_km, w1_km, op1),
        (+r2_km, w2_km, op2),
        (-r2_km, w2_km, op2),
    ]

    chariklo = SyntheticLightCurveSimulator(
        mag_star=13.0,
        distance_km=2.1e9,        # Chariklo típico ~ 15 AU (aprox.)
        diameter_km=250.0,        # diâmetro efetivo do corpo (aprox. esfera equiv.)
        velocity_kms=25.0,
        exposure_time_s=0.1,
        wavelength_nm=650.0,      # banda R aproximada
        seeing_arcsec=1.2,
        rings=rings_chariklo,
        satellites=[],            # sem satélites aqui
        normalize_method="top_quartiles",
        random_seed=321,
    )
    df_c = chariklo.simulate()
    chariklo.plot_curve(save=True, show=False, title="Chariklo com anéis — R~650 nm")
    chariklo.export_data(save=True)

    # Prints simples para feedback (como um "junior" faria)
    print("Umbriel: amostras =", len(df_u), " min/max flux_norm =", float(df_u.flux_norm.min()),
          float(df_u.flux_norm.max()))
    print("Chariklo: amostras =", len(df_c), " min/max flux_norm =", float(df_c.flux_norm.min()),
          float(df_c.flux_norm.max()))


# =============================================================================
# Execução direta (exemplo mínimo)
# =============================================================================

if __name__ == "__main__":
    # Exemplo mínimo de uso "out of the box"
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4_000.0,
        diameter_km=1_200.0,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        random_seed=42,
    )
    df = sim.simulate()
    png = sim.plot_curve(save=True, show=False)
    dat_df, dat_path = sim.export_data(save=True)
    print("Arquivo de dados:", dat_path)
    print("Arquivo da figura:", png)

    # Rodar os testes extras com Umbriel e Chariklo
    testes_extras()
```

- Ajustei `NoiseModel` em `model_training/synthetic_curve/simulate_curve.py`:
  - Aumentei `gain_counts_per_flux` de 4e5 para 1e9.
  - Reduzi a cintilação e coloquei dependência t^(-1/2):
    - Antes: sigma_ln ≈ 0.02 * seeing * (0.1 / texp)
    - Agora: sigma_ln ≈ 0.005 * seeing * (0.1 / texp)^(1/2)

- Efeito esperado: muito mais fótons por amostra e cintilação mais suave → curva normalizada com S/N alto e formato contínuo, próximo ao visual da 2ª imagem.

---

**User**

Me explique o motivo da curva resultado de @model_training/synthetic_curve/simulate_curve.py ter ficado de cabeça para baixo como mostra a imagem. 

---

**Cursor**

- Motivo: o modelo da faixa opaca (corpo) combinou as duas bordas de difração no “sentido” errado. A função de borda usada cresce de 0 (à esquerda da borda, “escuro”) para 1 (à direita, “claro”). Ao multiplicar as duas bordas com um espelhamento de sinal, o produto ficou ≈0 fora do corpo e ≈1 dentro – invertendo a transmitância. A normalização então tomou o trecho “dentro” como baseline alto e o “fora” como quase zero, deixando a curva “de cabeça para baixo”.

- Conserto conceitual: para uma faixa opaca, a transmitância ideal é 1 fora e ~0 entre as bordas. Usando uma função de borda tipo H(x − x_edge) (0 à esquerda, 1 à direita), a transmitância do corpo é:
  T_body ≈ 1 − H(x − x1) + H(x − x2)
  que, com difração, fica bem aproximada por:
  T_body ≈ (1 − T_edge(x, x1)) + T_edge(x, x2)
  e depois “clip” para o intervalo físico.

Aplique esta edição em `FresnelPhysics.opaque_strip_transmission` de `model_training/synthetic_curve/simulate_curve.py`:

```python
@staticmethod
def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                              distance_km: float, wavelength_nm: float) -> np.ndarray:
    """
    Faixa opaca: combinação correta de duas bordas.
    A função de borda cresce de 0 (à esquerda) para 1 (à direita).
    Para uma faixa opaca, a transmitância desejada é ≈ (1 - T1) + T2,
    que equivale ao complemento do “slit” entre as bordas.
    """
    half = 0.5 * float(width_km)
    x1 = float(center_km) - half  # borda de imersão
    x2 = float(center_km) + half  # borda de emersão

    T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
    T2 = FresnelPhysics.knife_edge_transmission(x_km, x2, distance_km, wavelength_nm)

    # 1 - T1 + T2: fora da faixa → ≈1; entre as bordas → ≈0 (com franjas de difração)
    T = (1.0 - T1) + T2

    # Permita pequeno overshoot de difração; ajuste o limite se preferir.
    T = np.clip(T, 0.0, 1.2)
    return T
```

- Efeito esperado: o nível fora da ocultação volta a ~1; entre as bordas a curva cai (com franjas), ficando com o “sinal” correto.

```python
@staticmethod
def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                              distance_km: float, wavelength_nm: float) -> np.ndarray:
    """
    Faixa opaca: combinação correta de duas bordas.
    A função de borda cresce de 0 (à esquerda) para 1 (à direita).
    Para uma faixa opaca, a transmitância desejada é ≈ (1 - T1) + T2,
    que equivale ao complemento do “slit” entre as bordas.
    """
    half = 0.5 * float(width_km)
    x1 = float(center_km) - half  # borda de imersão
    x2 = float(center_km) + half  # borda de emersão

    T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
    T2 = FresnelPhysics.knife_edge_transmission(x_km, x2, distance_km, wavelength_nm)

    # 1 - T1 + T2: fora da faixa → ≈1; entre as bordas → ≈0 (com franjas de difração)
    T = (1.0 - T1) + T2

    # Permita pequeno overshoot de difração; ajuste o limite se preferir.
    T = np.clip(T, 0.0, 1.2)
    return T
```

---

**User**

@model_training/synthetic_curve/simulate_curve.py aplique suas sugestões anteriores

---

**Cursor**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador modular de curvas de luz de ocultações estelares.

Este arquivo reorganiza o antigo script monolítico em classes e funções
coesas, seguindo PEP 8 e boas práticas de programação científica.

Principais componentes:
- Física de Fresnel (difração em bordas "knife-edge" e faixa opaca)
- Geometria do evento (linha do tempo e coordenada ao longo da corda)
- Modelo de ruído (Poisson, leitura, cintilação multiplicativa)
- Normalização "pós-fotometria" (baseline ~ 1)
- Orquestração via uma classe principal de fácil uso

Bibliotecas: numpy, pandas, matplotlib (SciPy é opcional; usado se disponível).

CHANGES (alterações em relação ao código anterior):
- Removidos trechos experimentais, prints soltos e globais redundantes
  (motivo: clareza, reprodutibilidade e manutenibilidade).
- Unidades explicitadas (km, s, nm) e conversões centralizadas
  (motivo: reduzir erros por mistura de unidades).
- Difração de Fresnel isolada em funções puras com fallback sem SciPy
  (motivo: manter acurácia quando disponível e portabilidade quando não).
- Ruídos desacoplados da física (camada separada)
  (motivo: permitir trocar/ligar/desligar ruídos facilmente).
- Normalização robusta por quartis contíguos ou mediana
  (motivo: simular "pós-fotometria" com baseline estável).
- Função `testes_extras()` com cenários aproximados de Umbriel e Chariklo
  (motivo: exemplos práticos com corpos pequenos conhecidos).
"""

from __future__ import annotations

from typing import Optional, Tuple, List
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# Utilidades e constantes
# =============================================================================

SPEED_OF_LIGHT_MS = 299_792_458.0  # m/s (não é usada diretamente, mantida por referência)
NM_TO_KM = 1e-12  # 1 nm = 1e-12 km


def magnitude_to_relative_flux(magnitude: float) -> float:
    """
    Converte magnitude aparente em fluxo relativo (sem calibração absoluta).

    Equação fotométrica padrão:
        F ∝ 10^(-0.4 m)
    """
    return 10.0 ** (-0.4 * float(magnitude))


def normalize_flux_top_quartiles(flux: np.ndarray) -> np.ndarray:
    """
    Normaliza o fluxo dividindo pelo baseline estimado como a média das duas
    maiores médias entre 4 segmentos contíguos (quartis em tempo).

    - Razoável para "pós-fotometria": baseline ~ 1 fora da ocultação.
    - Fallbacks garantem retorno mesmo em séries curtas.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return flux
    if valid.size < 4:
        baseline = float(np.mean(valid))
        baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
        return flux / baseline
    segments = np.array_split(valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
    if len(means) == 0:
        baseline = float(np.median(valid))
    else:
        order = np.argsort(means)
        top = [means[order[-1]]]
        if len(means) >= 2:
            top.append(means[order[-2]])
        baseline = float(np.mean(top))
    if not np.isfinite(baseline) or baseline <= 0:
        baseline = float(np.median(valid))
        if not np.isfinite(baseline) or baseline <= 0:
            return flux
    return flux / baseline


# =============================================================================
# Física de Fresnel (difração)
# =============================================================================

class FresnelPhysics:
    """
    Funções para cálculo de escala de Fresnel e transmitâncias difrativas.
    """

    @staticmethod
    def fresnel_scale_km(distance_km: float, wavelength_nm: float) -> float:
        """
        F = sqrt(lambda * D / 2), com lambda em km e D em km.
        """
        lambda_km = float(wavelength_nm) * NM_TO_KM
        D = float(distance_km)
        return math.sqrt(max(lambda_km * D / 2.0, 1e-30))

    @staticmethod
    def fresnel_CS(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrais de Fresnel (C, S) com SciPy se disponível; caso contrário,
        usa aproximações assintóticas/séries adequadas a fins educacionais.
        """
        try:
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore
            # A escala do argumento varia entre convenções; adotamos um fator
            # para obter bom acordo qualitativo.
            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback aproximado: bom o suficiente didaticamente
        x = np.asarray(u, dtype=float)
        ax = np.abs(x)
        C = np.zeros_like(x)
        S = np.zeros_like(x)

        small = ax <= 1.5
        if np.any(small):
            z = x[small]
            # Séries truncadas (educacional; não metrológico)
            C[small] = (z - (math.pi**2) * (z**5) / 40.0) / math.sqrt(2.0 * math.pi)
            S[small] = ((math.pi) * (z**3) / 6.0 - (math.pi**3) * (z**7) / 336.0) / math.sqrt(
                2.0 * math.pi
            )

        large = ~small
        if np.any(large):
            z = x[large]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[large] = c
            S[large] = s

        return C, S

    @staticmethod
    def knife_edge_transmission(x_km: np.ndarray, edge_pos_km: float,
                                distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Transmitância de difração para uma borda "knife-edge".

        I(u) = 0.5 [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ],
        onde u = (x - x_edge) / F e F é a escala de Fresnel.
        """
        F = FresnelPhysics.fresnel_scale_km(distance_km, wavelength_nm)
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = FresnelPhysics.fresnel_CS(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    @staticmethod
    def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                  distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa opaca: combinação correta de duas bordas (imersão e emersão).

        A transmitância de uma borda "knife-edge" cresce de ~0 (à esquerda) para ~1 (à direita).
        Para representar uma faixa opaca (região central escura), a combinação física
        desejada é:
            T(x) ≈ (1 - T_edge(x, x1)) + T_edge(x, x2)
        Isto produz T ~ 1 fora da faixa e T ~ 0 entre x1 e x2, com as franjas
        de difração aparecendo nas vizinhanças das bordas.
        """
        half = 0.5 * float(width_km)
        x1 = float(center_km) - half
        x2 = float(center_km) + half
        T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
        T2 = FresnelPhysics.knife_edge_transmission(x_km, x2, distance_km, wavelength_nm)
        T = (1.0 - T1) + T2
        # Permite leve overshoot por difração; ajuste se necessário
        return np.clip(T, 0.0, 1.2)

    @staticmethod
    def partial_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                   opacity: float, distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa parcialmente opaca (anéis):
        T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = FresnelPhysics.opaque_strip_transmission(
            x_km, center_km, width_km, distance_km, wavelength_nm
        )
        return 1.0 - float(opacity) * (1.0 - T_opaque)


# =============================================================================
# Modelo de ruído
# =============================================================================

class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.
    """

    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 5.0, gain_counts_per_flux: float = 1e9,
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Aplica Poisson (fótons), ruído de leitura (gaussiano) e cintilação (lognormal).
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 1e-10, None)

        # Converte para contagens (ganho arbitrário para S/N razoável)
        lam = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam = np.clip(lam, 0, 1e12)

        # Poisson (fótons)
        shot = self.rng.poisson(lam)

        # Leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=shot.size)

        # Cintilação (lognormal): pior para seeing ruim e diminui com t^{-1/2}
        # Fator menor para evitar modulações multiplicativas exageradas.
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=shot.size))

        counts = (shot + read) * scint
        flux = counts / (self.gain_counts_per_flux * self.exposure_time_s)
        return np.clip(flux, 0.0, None)


# =============================================================================
# Simulador principal
# =============================================================================

class SyntheticLightCurveSimulator:
    """
    Simulador de curvas de luz sintéticas para ocultações estelares.

    Parâmetros
    ----------
    mag_star : float
        Magnitude aparente da estrela (escala relativa).
    distance_km : float
        Distância observador–corpo (km), usada na escala de Fresnel.
    diameter_km : float
        Diâmetro projetado do corpo (km) ao longo da corda.
    velocity_kms : float
        Velocidade relativa do evento (km/s).
    exposure_time_s : float
        Tempo de exposição por amostra (s).
    total_duration_s : Optional[float]
        Duração total da simulação (s). Se None, é inferida com margem.
    wavelength_nm : float
        Comprimento de onda efetivo (nm), p.ex. 550 nm ~ banda V.
    seeing_arcsec : float
        Seeing (arcsec), controla a cintilação.
    rings : Optional[List[Tuple[float, float, float]]]
        Lista de anéis como (offset_km, width_km, opacity). Opacity em [0,1].
    satellites : Optional[List[Tuple[float, float]]]
        Lista de satélites como (offset_km, diameter_km).
    normalize_method : str
        "top_quartiles" (default) ou "median".
    random_seed : Optional[int]
        Semente para reprodutibilidade dos ruídos.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4_000.0,
        diameter_km: float = 1_200.0,
        velocity_kms: float = 20.0,
        exposure_time_s: float = 0.1,
        total_duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        satellites: Optional[List[Tuple[float, float]]] = None,
        normalize_method: str = "top_quartiles",
        random_seed: Optional[int] = None,
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time_s = float(exposure_time_s)
        self.total_duration_s = float(total_duration_s) if total_duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.rings = rings if rings is not None else []
        self.satellites = satellites if satellites is not None else []
        self.normalize_method = normalize_method

        self.rng = np.random.default_rng(random_seed)
        self.noise = NoiseModel(
            seeing_arcsec=self.seeing_arcsec,
            exposure_time_s=self.exposure_time_s,
            rng=self.rng,
        )

        # Saídas
        self.time_s: Optional[np.ndarray] = None
        self.flux: Optional[np.ndarray] = None
        self.flux_norm: Optional[np.ndarray] = None

        # Diretórios de saída
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_dirs()

    def simulate(self) -> pd.DataFrame:
        """
        Executa a simulação completa:
        - Constrói tempo e coordenada ao longo da corda
        - Calcula transmitância difrativa: corpo × anéis × satélites
        - Converte magnitude em fluxo relativo e aplica transmitância
        - Aplica ruídos (Poisson, leitura, cintilação)
        - Normaliza o fluxo
        """
        t, x = self._build_time_and_chord()

        # Corpo principal (faixa opaca)
        T_body = FresnelPhysics.opaque_strip_transmission(
            x, center_km=0.0, width_km=self.diameter_km,
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )

        # Anéis (faixas parcialmente opacas)
        T_rings = np.ones_like(T_body)
        for (offset_km, width_km, opacity) in self.rings:
            T_rings *= FresnelPhysics.partial_strip_transmission(
                x, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Satélites (faixas opacas deslocadas)
        T_sats = np.ones_like(T_body)
        for (offset_km, diameter_km) in self.satellites:
            T_sats *= FresnelPhysics.opaque_strip_transmission(
                x, center_km=float(offset_km), width_km=float(diameter_km),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Transmitância total
        T_total = np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

        # Fluxo relativo esperado (sem ruído)
        base_flux = magnitude_to_relative_flux(self.mag_star)
        expected_rel_flux = base_flux * T_total

        # Ruído
        noisy_flux = self.noise.apply(expected_rel_flux)

        # Normalização
        if self.normalize_method == "median":
            baseline = float(np.median(noisy_flux[np.isfinite(noisy_flux)]))
            baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
            flux_norm = noisy_flux / baseline
        else:
            flux_norm = normalize_flux_top_quartiles(noisy_flux)

        # Armazena e retorna
        self.time_s = t
        self.flux = noisy_flux
        self.flux_norm = flux_norm
        return pd.DataFrame({"time_s": t, "flux": noisy_flux, "flux_norm": flux_norm})

    def plot_curve(self, save: bool = True, show: bool = False, title: Optional[str] = None) -> str:
        """
        Plota a curva normalizada. Retorna o caminho do PNG salvo (string)
        se `save=True`, caso contrário retorna string vazia.
        """
        self._require_simulation()
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(self.time_s, self.flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adim.]")
        band = f"{int(round(self.wavelength_nm))} nm"
        ttl = title if title else f"Curva sintética com difração e seeing — {band}"
        ax.set_title(ttl)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        png_path = ""
        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)
        return png_path

    def export_data(self, save: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Exporta os dados simulados para um .dat numerado em output/.
        Retorna (DataFrame, caminho_do_arquivo_ou_string_vazia).
        """
        self._require_simulation()
        df = pd.DataFrame({"time_s": self.time_s, "flux": self.flux, "flux_norm": self.flux_norm})
        dat_path = ""
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df, dat_path

    # -------------------------- helpers internos -----------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.total_duration_s is None:
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time * 3.0  # margem: 1x antes e 1x depois
        else:
            total_time = self.total_duration_s
        n_steps = max(2, int(math.ceil(total_time / self.exposure_time_s)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _ensure_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                n = int(name.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulation(self) -> None:
        if self.time_s is None or self.flux is None or self.flux_norm is None:
            raise RuntimeError("Simulação ainda não executada. Chame simulate() antes.")


# =============================================================================
# Testes extras com corpos pequenos (Umbriel e Chariklo)
# =============================================================================

def testes_extras() -> None:
    """
    Executa dois cenários de teste:
    1) Umbriel (satélite de Urano) — sem anéis
    2) Chariklo (Centauro) — com anéis C1R e C2R (parâmetros aproximados)

    Observações:
    - Valores aproximados (ordem de grandeza) para fins didáticos.
    - Distâncias geocêntricas típicas: Urano ~ 2.9e9 km, Chariklo ~ 2.1e9 km.
    - Velocidades típicas de sombra ~ 20–25 km/s.
    - Parâmetros dos anéis de Chariklo (Braga-Ribas+2014):
        - Raios ~ 391 km e 405 km; larguras ~ 7 km e 3 km;
          profundidades óticas τ ~ 0.4 e 0.06 → opacidade ~ 1 - e^{-τ}.
      Para uma ocultação equatorial idealizada, modelamos cada anel por duas faixas
      simétricas (+/- raio) com a mesma largura e opacidade.
    """
    # ------------------------------- Umbriel ---------------------------------
    umbriel = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,        # ~ distância de Urano à Terra (aprox.)
        diameter_km=1169.0,       # diâmetro de Umbriel ~ 1169 km
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        normalize_method="top_quartiles",
        random_seed=123,
    )
    df_u = umbriel.simulate()
    umbriel.plot_curve(save=True, show=False, title="Umbriel — V~550 nm")
    umbriel.export_data(save=True)

    # ------------------------------ Chariklo ---------------------------------
    # Parâmetros aproximados dos anéis (C1R e C2R)
    r1_km, w1_km, tau1 = 391.0, 7.0, 0.4
    r2_km, w2_km, tau2 = 405.0, 3.0, 0.06
    op1 = 1.0 - math.exp(-tau1)
    op2 = 1.0 - math.exp(-tau2)

    rings_chariklo: List[Tuple[float, float, float]] = [
        (+r1_km, w1_km, op1),
        (-r1_km, w1_km, op1),
        (+r2_km, w2_km, op2),
        (-r2_km, w2_km, op2),
    ]

    chariklo = SyntheticLightCurveSimulator(
        mag_star=13.0,
        distance_km=2.1e9,        # Chariklo típico ~ 15 AU (aprox.)
        diameter_km=250.0,        # diâmetro efetivo do corpo (aprox. esfera equiv.)
        velocity_kms=25.0,
        exposure_time_s=0.1,
        wavelength_nm=650.0,      # banda R aproximada
        seeing_arcsec=1.2,
        rings=rings_chariklo,
        satellites=[],            # sem satélites aqui
        normalize_method="top_quartiles",
        random_seed=321,
    )
    df_c = chariklo.simulate()
    chariklo.plot_curve(save=True, show=False, title="Chariklo com anéis — R~650 nm")
    chariklo.export_data(save=True)

    # Prints simples para feedback (como um "junior" faria)
    print("Umbriel: amostras =", len(df_u), " min/max flux_norm =", float(df_u.flux_norm.min()),
          float(df_u.flux_norm.max()))
    print("Chariklo: amostras =", len(df_c), " min/max flux_norm =", float(df_c.flux_norm.min()),
          float(df_c.flux_norm.max()))


# =============================================================================
# Execução direta (exemplo mínimo)
# =============================================================================

if __name__ == "__main__":
    # Exemplo mínimo de uso "out of the box"
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4_000.0,
        diameter_km=1_200.0,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        random_seed=42,
    )
    df = sim.simulate()
    png = sim.plot_curve(save=True, show=False)
    dat_df, dat_path = sim.export_data(save=True)
    print("Arquivo de dados:", dat_path)
    print("Arquivo da figura:", png)

    # Rodar os testes extras com Umbriel e Chariklo
    testes_extras()
```

- Corrigi `FresnelPhysics.opaque_strip_transmission` em `model_training/synthetic_curve/simulate_curve.py` para combinar as duas bordas como faixa opaca física:
  - Antes: produto `T1 * T2` (acabava invertendo o nível fora/dentro).
  - Agora: `T = (1 - T1) + T2`, com `clip(0, 1.2)` para tolerar pequeno overshoot de difração.
- Efeito esperado: fora da ocultação volta a ~1; entre as bordas cai para ~0 com franjas nas transições, eliminando a “curva de cabeça para baixo”.

---

**User**

@model_training/synthetic_curve/simulate_curve.py Por qual motivo não consigo ver as ocultações dos aneis de chariklo nesse outpu (imagem)? 

---

**Cursor**

```python
max_r = max(r1_km, r2_km)
needed_half_span = max_r + 0.5 * diameter_km + 10
total_duration_s = 2 * needed_half_span / velocity_kms
```

- Motivo: a janela temporal não cobre os anéis. No caso de Chariklo que você rodou:
  - r1 ≈ 391 km e r2 ≈ 405 km; v = 25 km/s; diâmetro do corpo = 250 km.
  - O simulador, por padrão, usa duração total ≈ 3 × (diâmetro/v) = 3 × (250/25) = 30 s, centrada em t0.
  - O tempo em que cada anel cruza a estrela é t = t0 ± r/v. Para r ≈ 400 km e v = 25 km/s: Δt ≈ 16 s.
  - Como t0 ≈ 15 s, os anéis ficam perto de t ≈ −1 s e t ≈ 31 s, isto é, fora do intervalo [0, 30] s. Por isso você não os vê no gráfico.

Como resolver
- Aumente a duração total para incluir os raios dos anéis: total_duration_s ≥ 2 × (max_r + diâmetro/2)/v + margem.
- Exemplo para o seu `testes_extras`:

```python
# depois de definir r1_km, r2_km, diameter_km e velocity_kms
max_r = max(r1_km, r2_km)
margin_km = 20.0  # folga
half_span_km = max_r + 0.5 * 250.0 + margin_km  # 250.0 é o diameter_km usado
total_duration_s = 2.0 * half_span_km / 25.0     # 25.0 é velocity_kms

chariklo = SyntheticLightCurveSimulator(
    mag_star=13.0,
    distance_km=2.1e9,
    diameter_km=250.0,
    velocity_kms=25.0,
    exposure_time_s=0.1,
    wavelength_nm=650.0,
    seeing_arcsec=1.2,
    rings=rings_chariklo,
    satellites=[],
    normalize_method="top_quartiles",
    random_seed=321,
    total_duration_s=total_duration_s,  # ← garante que os anéis entrem na janela
)
```

- Alternativas: diminuir a velocidade simulada, ou deslocar o tempo inicial para que t0 ± r/v caia dentro da janela; mas aumentar `total_duration_s` é o mais direto.

```python
# depois de definir r1_km, r2_km, diameter_km e velocity_kms
max_r = max(r1_km, r2_km)
margin_km = 20.0  # folga
half_span_km = max_r + 0.5 * 250.0 + margin_km  # 250.0 é o diameter_km usado
total_duration_s = 2.0 * half_span_km / 25.0     # 25.0 é velocity_kms

chariklo = SyntheticLightCurveSimulator(
    mag_star=13.0,
    distance_km=2.1e9,
    diameter_km=250.0,
    velocity_kms=25.0,
    exposure_time_s=0.1,
    wavelength_nm=650.0,
    seeing_arcsec=1.2,
    rings=rings_chariklo,
    satellites=[],
    normalize_method="top_quartiles",
    random_seed=321,
    total_duration_s=total_duration_s,  # ← garante que os anéis entrem na janela
)
```

---

**User**

Por qual motivo o fundo (durante o evento de ocultação) a curva ficou tão bem comportada (imagem 1)? Poucos desvios bem encostados no zero, eu imaginava um ruído que fizesse inclusive o fundo ficar um pouco acima do zero, ou negativo (como na imagem 2, uma curva real). @model_training/synthetic_curve/simulate_curve.py 

---

**Cursor**

- Por que ficou “colado em zero”: dentro da ocultação o modelo zera a estrela (T_total ≈ 0) e o ruído é principalmente multiplicativo (cintilação) sobre o fluxo da estrela. Como o fluxo-estelar esperado vira ~0, Poisson da estrela ≈ 0, a cintilação não atua e ainda há um clip para não-negativos. Como também não simulamos fundo do céu/bias nem erro de subtração de fundo, o “fundo” fica limpo e encostado no zero. Em dados reais há:
  - fundo do céu (Poisson) que não some na ocultação,
  - bias/offset e ruído de leitura maiores,
  - erro de subtração de fundo (pode levar a valores negativos).

Edits propostos para deixar o fundo realista
- Adicionar fundo de céu (Poisson aditivo), bias (offset), ruído de leitura maior e subtração de fundo com erro. Isso gera valores acima de zero e, às vezes, negativos.

Cole os trechos abaixo em model_training/synthetic_curve/simulate_curve.py (substituem apenas a classe de ruído):

```python
class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.
    Agora inclui:
      - fundo do céu (Poisson aditivo, indep. da estrela)
      - bias/offset do detector
      - erro na subtração de fundo (pode gerar valores negativos)
    """
    def __init__(
        self,
        seeing_arcsec: float = 1.0,
        exposure_time_s: float = 0.1,
        readout_sigma_counts: float = 20.0,         # ↑ ruído de leitura
        gain_counts_per_flux: float = 1e9,
        sky_bg_rate_counts_per_s: float = 300.0,    # taxa média de céu (cont/s)
        bias_offset_counts: float = 100.0,          # offset do detector (cont)
        subtract_background: bool = True,           # simula a subtração de fundo
        bg_subtract_noise_frac: float = 0.05,       # erro relativo da estimativa
        allow_negative: bool = True,                # permite negativos após subtração
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.sky_bg_rate_counts_per_s = float(sky_bg_rate_counts_per_s)
        self.bias_offset_counts = float(bias_offset_counts)
        self.subtract_background = bool(subtract_background)
        self.bg_subtract_noise_frac = float(bg_subtract_noise_frac)
        self.allow_negative = bool(allow_negative)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Poisson estrela + Poisson céu + leitura + cintilação (só na estrela).
        Depois, subtração do fundo com erro → pode deixar negativos.
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 0.0, None)

        # Estrela (contagens esperadas)
        lam_star = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam_star = np.clip(lam_star, 0, 1e12)
        counts_star = self.rng.poisson(lam_star)

        # Céu (não depende de T_total)
        lam_bg = self.sky_bg_rate_counts_per_s * self.exposure_time_s
        counts_bg = self.rng.poisson(lam_bg * np.ones_like(counts_star))

        # Leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=counts_star.size)

        # Cintilação (multiplicativa; atua na estrela, não no céu)
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=counts_star.size))

        # Sinal total em contagens
        total_counts = counts_star * scint + counts_bg + read + self.bias_offset_counts

        # Subtração de fundo com erro (como no pipeline real)
        if self.subtract_background:
            est_bg = (self.sky_bg_rate_counts_per_s * self.exposure_time_s) + self.bias_offset_counts
            est_bg *= (1.0 + self.rng.normal(0.0, self.bg_subtract_noise_frac, size=counts_star.size))
            total_counts = total_counts - est_bg

        # Converte para "fluxo relativo"
        flux = total_counts / (self.gain_counts_per_flux * self.exposure_time_s)

        if not self.allow_negative:
            flux = np.clip(flux, 0.0, None)
        return flux
```

Opcional: se quiser enfatizar ainda mais o fundo “sujo”, aumente:
- `sky_bg_rate_counts_per_s` para 500–1500,
- `bg_subtract_noise_frac` para 0.08–0.15,
- `readout_sigma_counts` para 30–50.

Resumo
- Antes: sem céu/bias e com clip → fundo colado em 0.
- Depois: céu + bias + subtração com erro + leitura → fundo com dispersão realista, inclusive excursões negativas, como nos dados reais.

```python
class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.
    Agora inclui:
      - fundo do céu (Poisson aditivo, indep. da estrela)
      - bias/offset do detector
      - erro na subtração de fundo (pode gerar valores negativos)
    """
    def __init__(
        self,
        seeing_arcsec: float = 1.0,
        exposure_time_s: float = 0.1,
        readout_sigma_counts: float = 20.0,         # ↑ ruído de leitura
        gain_counts_per_flux: float = 1e9,
        sky_bg_rate_counts_per_s: float = 300.0,    # taxa média de céu (cont/s)
        bias_offset_counts: float = 100.0,          # offset do detector (cont)
        subtract_background: bool = True,           # simula a subtração de fundo
        bg_subtract_noise_frac: float = 0.05,       # erro relativo da estimativa
        allow_negative: bool = True,                # permite negativos após subtração
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.sky_bg_rate_counts_per_s = float(sky_bg_rate_counts_per_s)
        self.bias_offset_counts = float(bias_offset_counts)
        self.subtract_background = bool(subtract_background)
        self.bg_subtract_noise_frac = float(bg_subtract_noise_frac)
        self.allow_negative = bool(allow_negative)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Poisson estrela + Poisson céu + leitura + cintilação (só na estrela).
        Depois, subtração do fundo com erro → pode deixar negativos.
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 0.0, None)

        # Estrela (contagens esperadas)
        lam_star = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam_star = np.clip(lam_star, 0, 1e12)
        counts_star = self.rng.poisson(lam_star)

        # Céu (não depende de T_total)
        lam_bg = self.sky_bg_rate_counts_per_s * self.exposure_time_s
        counts_bg = self.rng.poisson(lam_bg * np.ones_like(counts_star))

        # Leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=counts_star.size)

        # Cintilação (multiplicativa; atua na estrela, não no céu)
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=counts_star.size))

        # Sinal total em contagens
        total_counts = counts_star * scint + counts_bg + read + self.bias_offset_counts

        # Subtração de fundo com erro (como no pipeline real)
        if self.subtract_background:
            est_bg = (self.sky_bg_rate_counts_per_s * self.exposure_time_s) + self.bias_offset_counts
            est_bg *= (1.0 + self.rng.normal(0.0, self.bg_subtract_noise_frac, size=counts_star.size))
            total_counts = total_counts - est_bg

        # Converte para "fluxo relativo"
        flux = total_counts / (self.gain_counts_per_flux * self.exposure_time_s)

        if not self.allow_negative:
            flux = np.clip(flux, 0.0, None)
        return flux
```

---

**User**

@model_training/synthetic_curve/simulate_curve.py aplique sua sugestão anterior

---

**Cursor**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador modular de curvas de luz de ocultações estelares.

Este arquivo reorganiza o antigo script monolítico em classes e funções
coesas, seguindo PEP 8 e boas práticas de programação científica.

Principais componentes:
- Física de Fresnel (difração em bordas "knife-edge" e faixa opaca)
- Geometria do evento (linha do tempo e coordenada ao longo da corda)
- Modelo de ruído (Poisson, leitura, cintilação multiplicativa)
- Normalização "pós-fotometria" (baseline ~ 1)
- Orquestração via uma classe principal de fácil uso

Bibliotecas: numpy, pandas, matplotlib (SciPy é opcional; usado se disponível).

CHANGES (alterações em relação ao código anterior):
- Removidos trechos experimentais, prints soltos e globais redundantes
  (motivo: clareza, reprodutibilidade e manutenibilidade).
- Unidades explicitadas (km, s, nm) e conversões centralizadas
  (motivo: reduzir erros por mistura de unidades).
- Difração de Fresnel isolada em funções puras com fallback sem SciPy
  (motivo: manter acurácia quando disponível e portabilidade quando não).
- Ruídos desacoplados da física (camada separada)
  (motivo: permitir trocar/ligar/desligar ruídos facilmente).
- Normalização robusta por quartis contíguos ou mediana
  (motivo: simular "pós-fotometria" com baseline estável).
- Função `testes_extras()` com cenários aproximados de Umbriel e Chariklo
  (motivo: exemplos práticos com corpos pequenos conhecidos).
"""

from __future__ import annotations

from typing import Optional, Tuple, List
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# Utilidades e constantes
# =============================================================================

SPEED_OF_LIGHT_MS = 299_792_458.0  # m/s (não é usada diretamente, mantida por referência)
NM_TO_KM = 1e-12  # 1 nm = 1e-12 km


def magnitude_to_relative_flux(magnitude: float) -> float:
    """
    Converte magnitude aparente em fluxo relativo (sem calibração absoluta).

    Equação fotométrica padrão:
        F ∝ 10^(-0.4 m)
    """
    return 10.0 ** (-0.4 * float(magnitude))


def normalize_flux_top_quartiles(flux: np.ndarray) -> np.ndarray:
    """
    Normaliza o fluxo dividindo pelo baseline estimado como a média das duas
    maiores médias entre 4 segmentos contíguos (quartis em tempo).

    - Razoável para "pós-fotometria": baseline ~ 1 fora da ocultação.
    - Fallbacks garantem retorno mesmo em séries curtas.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return flux
    if valid.size < 4:
        baseline = float(np.mean(valid))
        baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
        return flux / baseline
    segments = np.array_split(valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
    if len(means) == 0:
        baseline = float(np.median(valid))
    else:
        order = np.argsort(means)
        top = [means[order[-1]]]
        if len(means) >= 2:
            top.append(means[order[-2]])
        baseline = float(np.mean(top))
    if not np.isfinite(baseline) or baseline <= 0:
        baseline = float(np.median(valid))
        if not np.isfinite(baseline) or baseline <= 0:
            return flux
    return flux / baseline


# =============================================================================
# Física de Fresnel (difração)
# =============================================================================

class FresnelPhysics:
    """
    Funções para cálculo de escala de Fresnel e transmitâncias difrativas.
    """

    @staticmethod
    def fresnel_scale_km(distance_km: float, wavelength_nm: float) -> float:
        """
        F = sqrt(lambda * D / 2), com lambda em km e D em km.
        """
        lambda_km = float(wavelength_nm) * NM_TO_KM
        D = float(distance_km)
        return math.sqrt(max(lambda_km * D / 2.0, 1e-30))

    @staticmethod
    def fresnel_CS(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrais de Fresnel (C, S) com SciPy se disponível; caso contrário,
        usa aproximações assintóticas/séries adequadas a fins educacionais.
        """
        try:
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore
            # A escala do argumento varia entre convenções; adotamos um fator
            # para obter bom acordo qualitativo.
            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback aproximado: bom o suficiente didaticamente
        x = np.asarray(u, dtype=float)
        ax = np.abs(x)
        C = np.zeros_like(x)
        S = np.zeros_like(x)

        small = ax <= 1.5
        if np.any(small):
            z = x[small]
            # Séries truncadas (educacional; não metrológico)
            C[small] = (z - (math.pi**2) * (z**5) / 40.0) / math.sqrt(2.0 * math.pi)
            S[small] = ((math.pi) * (z**3) / 6.0 - (math.pi**3) * (z**7) / 336.0) / math.sqrt(
                2.0 * math.pi
            )

        large = ~small
        if np.any(large):
            z = x[large]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[large] = c
            S[large] = s

        return C, S

    @staticmethod
    def knife_edge_transmission(x_km: np.ndarray, edge_pos_km: float,
                                distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Transmitância de difração para uma borda "knife-edge".

        I(u) = 0.5 [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ],
        onde u = (x - x_edge) / F e F é a escala de Fresnel.
        """
        F = FresnelPhysics.fresnel_scale_km(distance_km, wavelength_nm)
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = FresnelPhysics.fresnel_CS(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    @staticmethod
    def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                  distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa opaca: combinação correta de duas bordas (imersão e emersão).

        A transmitância de uma borda "knife-edge" cresce de ~0 (à esquerda) para ~1 (à direita).
        Para representar uma faixa opaca (região central escura), a combinação física
        desejada é:
            T(x) ≈ (1 - T_edge(x, x1)) + T_edge(x, x2)
        Isto produz T ~ 1 fora da faixa e T ~ 0 entre x1 e x2, com as franjas
        de difração aparecendo nas vizinhanças das bordas.
        """
        half = 0.5 * float(width_km)
        x1 = float(center_km) - half
        x2 = float(center_km) + half
        T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
        T2 = FresnelPhysics.knife_edge_transmission(x_km, x2, distance_km, wavelength_nm)
        T = (1.0 - T1) + T2
        # Permite leve overshoot por difração; ajuste se necessário
        return np.clip(T, 0.0, 1.2)

    @staticmethod
    def partial_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                   opacity: float, distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa parcialmente opaca (anéis):
        T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = FresnelPhysics.opaque_strip_transmission(
            x_km, center_km, width_km, distance_km, wavelength_nm
        )
        return 1.0 - float(opacity) * (1.0 - T_opaque)


# =============================================================================
# Modelo de ruído
# =============================================================================

class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.

    Esta versão inclui:
    - Céu de fundo (Poisson aditivo, independente da estrela)
    - Offset/bias do detector
    - Subtração de fundo com erro (pode gerar valores negativos)
    - Cintilação multiplicativa atuando apenas no termo da estrela
    """

    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 20.0, gain_counts_per_flux: float = 1e9,
                 sky_bg_rate_counts_per_s: float = 300.0, bias_offset_counts: float = 100.0,
                 subtract_background: bool = True, bg_subtract_noise_frac: float = 0.05,
                 allow_negative: bool = True,
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.sky_bg_rate_counts_per_s = float(sky_bg_rate_counts_per_s)
        self.bias_offset_counts = float(bias_offset_counts)
        self.subtract_background = bool(subtract_background)
        self.bg_subtract_noise_frac = float(bg_subtract_noise_frac)
        self.allow_negative = bool(allow_negative)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Aplica:
        - Poisson da estrela (após ganho)
        - Poisson do céu de fundo
        - Ruído de leitura gaussiano
        - Cintilação (lognormal) atuando na estrela
        - Subtração de fundo com erro relativo controlado
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 0.0, None)

        # Contagens esperadas da estrela
        lam_star = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam_star = np.clip(lam_star, 0, 1e12)

        # Poisson da estrela
        counts_star = self.rng.poisson(lam_star)

        # Céu de fundo (Poisson) — independente da estrela
        lam_bg = self.sky_bg_rate_counts_per_s * self.exposure_time_s
        counts_bg = self.rng.poisson(lam_bg * np.ones_like(counts_star))

        # Ruído de leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=counts_star.size)

        # Cintilação (lognormal): pior para seeing ruim e diminui com t^{-1/2}
        # Fator menor para evitar modulações multiplicativas exageradas.
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=counts_star.size))

        # Sinal total (contagens)
        total_counts = counts_star * scint + counts_bg + read + self.bias_offset_counts

        # Subtração de fundo estimado (com erro relativo)
        if self.subtract_background:
            est_bg = lam_bg + self.bias_offset_counts
            est_bg_vec = est_bg * (1.0 + self.rng.normal(0.0, self.bg_subtract_noise_frac, size=counts_star.size))
            total_counts = total_counts - est_bg_vec

        # Converte para "fluxo relativo"
        flux = total_counts / (self.gain_counts_per_flux * self.exposure_time_s)

        if not self.allow_negative:
            flux = np.clip(flux, 0.0, None)
        return flux


# =============================================================================
# Simulador principal
# =============================================================================

class SyntheticLightCurveSimulator:
    """
    Simulador de curvas de luz sintéticas para ocultações estelares.

    Parâmetros
    ----------
    mag_star : float
        Magnitude aparente da estrela (escala relativa).
    distance_km : float
        Distância observador–corpo (km), usada na escala de Fresnel.
    diameter_km : float
        Diâmetro projetado do corpo (km) ao longo da corda.
    velocity_kms : float
        Velocidade relativa do evento (km/s).
    exposure_time_s : float
        Tempo de exposição por amostra (s).
    total_duration_s : Optional[float]
        Duração total da simulação (s). Se None, é inferida com margem.
    wavelength_nm : float
        Comprimento de onda efetivo (nm), p.ex. 550 nm ~ banda V.
    seeing_arcsec : float
        Seeing (arcsec), controla a cintilação.
    rings : Optional[List[Tuple[float, float, float]]]
        Lista de anéis como (offset_km, width_km, opacity). Opacity em [0,1].
    satellites : Optional[List[Tuple[float, float]]]
        Lista de satélites como (offset_km, diameter_km).
    normalize_method : str
        "top_quartiles" (default) ou "median".
    random_seed : Optional[int]
        Semente para reprodutibilidade dos ruídos.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4_000.0,
        diameter_km: float = 1_200.0,
        velocity_kms: float = 20.0,
        exposure_time_s: float = 0.1,
        total_duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        satellites: Optional[List[Tuple[float, float]]] = None,
        normalize_method: str = "top_quartiles",
        random_seed: Optional[int] = None,
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time_s = float(exposure_time_s)
        self.total_duration_s = float(total_duration_s) if total_duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.rings = rings if rings is not None else []
        self.satellites = satellites if satellites is not None else []
        self.normalize_method = normalize_method

        self.rng = np.random.default_rng(random_seed)
        self.noise = NoiseModel(
            seeing_arcsec=self.seeing_arcsec,
            exposure_time_s=self.exposure_time_s,
            rng=self.rng,
        )

        # Saídas
        self.time_s: Optional[np.ndarray] = None
        self.flux: Optional[np.ndarray] = None
        self.flux_norm: Optional[np.ndarray] = None

        # Diretórios de saída
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_dirs()

    def simulate(self) -> pd.DataFrame:
        """
        Executa a simulação completa:
        - Constrói tempo e coordenada ao longo da corda
        - Calcula transmitância difrativa: corpo × anéis × satélites
        - Converte magnitude em fluxo relativo e aplica transmitância
        - Aplica ruídos (Poisson, leitura, cintilação)
        - Normaliza o fluxo
        """
        t, x = self._build_time_and_chord()

        # Corpo principal (faixa opaca)
        T_body = FresnelPhysics.opaque_strip_transmission(
            x, center_km=0.0, width_km=self.diameter_km,
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )

        # Anéis (faixas parcialmente opacas)
        T_rings = np.ones_like(T_body)
        for (offset_km, width_km, opacity) in self.rings:
            T_rings *= FresnelPhysics.partial_strip_transmission(
                x, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Satélites (faixas opacas deslocadas)
        T_sats = np.ones_like(T_body)
        for (offset_km, diameter_km) in self.satellites:
            T_sats *= FresnelPhysics.opaque_strip_transmission(
                x, center_km=float(offset_km), width_km=float(diameter_km),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Transmitância total
        T_total = np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

        # Fluxo relativo esperado (sem ruído)
        base_flux = magnitude_to_relative_flux(self.mag_star)
        expected_rel_flux = base_flux * T_total

        # Ruído
        noisy_flux = self.noise.apply(expected_rel_flux)

        # Normalização
        if self.normalize_method == "median":
            baseline = float(np.median(noisy_flux[np.isfinite(noisy_flux)]))
            baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
            flux_norm = noisy_flux / baseline
        else:
            flux_norm = normalize_flux_top_quartiles(noisy_flux)

        # Armazena e retorna
        self.time_s = t
        self.flux = noisy_flux
        self.flux_norm = flux_norm
        return pd.DataFrame({"time_s": t, "flux": noisy_flux, "flux_norm": flux_norm})

    def plot_curve(self, save: bool = True, show: bool = False, title: Optional[str] = None) -> str:
        """
        Plota a curva normalizada. Retorna o caminho do PNG salvo (string)
        se `save=True`, caso contrário retorna string vazia.
        """
        self._require_simulation()
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(self.time_s, self.flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adim.]")
        band = f"{int(round(self.wavelength_nm))} nm"
        ttl = title if title else f"Curva sintética com difração e seeing — {band}"
        ax.set_title(ttl)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        png_path = ""
        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)
        return png_path

    def export_data(self, save: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Exporta os dados simulados para um .dat numerado em output/.
        Retorna (DataFrame, caminho_do_arquivo_ou_string_vazia).
        """
        self._require_simulation()
        df = pd.DataFrame({"time_s": self.time_s, "flux": self.flux, "flux_norm": self.flux_norm})
        dat_path = ""
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df, dat_path

    # -------------------------- helpers internos -----------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.total_duration_s is None:
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time * 3.0  # margem: 1x antes e 1x depois
        else:
            total_time = self.total_duration_s
        n_steps = max(2, int(math.ceil(total_time / self.exposure_time_s)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _ensure_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                n = int(name.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulation(self) -> None:
        if self.time_s is None or self.flux is None or self.flux_norm is None:
            raise RuntimeError("Simulação ainda não executada. Chame simulate() antes.")


# =============================================================================
# Testes extras com corpos pequenos (Umbriel e Chariklo)
# =============================================================================

def testes_extras() -> None:
    """
    Executa dois cenários de teste:
    1) Umbriel (satélite de Urano) — sem anéis
    2) Chariklo (Centauro) — com anéis C1R e C2R (parâmetros aproximados)

    Observações:
    - Valores aproximados (ordem de grandeza) para fins didáticos.
    - Distâncias geocêntricas típicas: Urano ~ 2.9e9 km, Chariklo ~ 2.1e9 km.
    - Velocidades típicas de sombra ~ 20–25 km/s.
    - Parâmetros dos anéis de Chariklo (Braga-Ribas+2014):
        - Raios ~ 391 km e 405 km; larguras ~ 7 km e 3 km;
          profundidades óticas τ ~ 0.4 e 0.06 → opacidade ~ 1 - e^{-τ}.
      Para uma ocultação equatorial idealizada, modelamos cada anel por duas faixas
      simétricas (+/- raio) com a mesma largura e opacidade.
    """
    # ------------------------------- Umbriel ---------------------------------
    umbriel = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,        # ~ distância de Urano à Terra (aprox.)
        diameter_km=1169.0,       # diâmetro de Umbriel ~ 1169 km
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        normalize_method="top_quartiles",
        random_seed=123,
    )
    df_u = umbriel.simulate()
    umbriel.plot_curve(save=True, show=False, title="Umbriel — V~550 nm")
    umbriel.export_data(save=True)

    # ------------------------------ Chariklo ---------------------------------
    # Parâmetros aproximados dos anéis (C1R e C2R)
    r1_km, w1_km, tau1 = 391.0, 7.0, 0.4
    r2_km, w2_km, tau2 = 405.0, 3.0, 0.06
    op1 = 1.0 - math.exp(-tau1)
    op2 = 1.0 - math.exp(-tau2)

    rings_chariklo: List[Tuple[float, float, float]] = [
        (+r1_km, w1_km, op1),
        (-r1_km, w1_km, op1),
        (+r2_km, w2_km, op2),
        (-r2_km, w2_km, op2),
    ]

    max_r = max(r1_km, r2_km)
    margin_km = 20.0  # folga
    half_span_km = max_r + 0.5 * 250.0 + margin_km  # 250.0 é o diameter_km usado
    total_duration_s = 2.0 * half_span_km / 25.0 

    chariklo = SyntheticLightCurveSimulator(
        mag_star=13.0,
        distance_km=2.1e9,        # Chariklo típico ~ 15 AU (aprox.)
        diameter_km=250.0,        # diâmetro efetivo do corpo (aprox. esfera equiv.)
        velocity_kms=25.0,
        exposure_time_s=0.1,
        wavelength_nm=650.0,      # banda R aproximada
        seeing_arcsec=1.2,
        rings=rings_chariklo,
        satellites=[],            # sem satélites aqui
        normalize_method="top_quartiles",
        total_duration_s=1000,
        random_seed=321,
    )
    df_c = chariklo.simulate()
    chariklo.plot_curve(save=True, show=False, title="Chariklo com anéis — R~650 nm")
    chariklo.export_data(save=True)

    # Prints simples para feedback (como um "junior" faria)
    print("Umbriel: amostras =", len(df_u), " min/max flux_norm =", float(df_u.flux_norm.min()),
          float(df_u.flux_norm.max()))
    print("Chariklo: amostras =", len(df_c), " min/max flux_norm =", float(df_c.flux_norm.min()),
          float(df_c.flux_norm.max()))


# =============================================================================
# Execução direta (exemplo mínimo)
# =============================================================================

if __name__ == "__main__":
    # Exemplo mínimo de uso "out of the box"
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4_000.0,
        diameter_km=1_200.0,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        random_seed=42,
    )
    df = sim.simulate()
    png = sim.plot_curve(save=True, show=False)
    dat_df, dat_path = sim.export_data(save=True)
    print("Arquivo de dados:", dat_path)
    print("Arquivo da figura:", png)

    # Rodar os testes extras com Umbriel e Chariklo
    testes_extras()
```

- Apliquei a nova versão do `NoiseModel` em `model_training/synthetic_curve/simulate_curve.py`:
  - Inclui céu de fundo Poisson, bias/offset, subtração de fundo com erro e possibilidade de valores negativos.
  - Mantém cintilação multiplicativa apenas sobre a estrela.
  - Aumentei o ruído de leitura padrão para 20 contagens.
- Efeito esperado: durante a ocultação, o “fundo” deixa de ficar colado em zero; passa a ter dispersão realista e pode ficar levemente acima de zero ou negativo, como em dados reais.

---

**User**

@model_training/synthetic_curve/simulate_curve.py aplique em "testes_extras" um terceiro teste. Crie um corpo fictício com características similares ao de Umbriel, mas com um anel relativamente grande (proporção igual aos aneis de saturno/tamanho de saturno). Quero ver uma curva com quedas bem fortes e características nos aneis.

---

**Cursor**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador modular de curvas de luz de ocultações estelares.

Este arquivo reorganiza o antigo script monolítico em classes e funções
coesas, seguindo PEP 8 e boas práticas de programação científica.

Principais componentes:
- Física de Fresnel (difração em bordas "knife-edge" e faixa opaca)
- Geometria do evento (linha do tempo e coordenada ao longo da corda)
- Modelo de ruído (Poisson, leitura, cintilação multiplicativa)
- Normalização "pós-fotometria" (baseline ~ 1)
- Orquestração via uma classe principal de fácil uso

Bibliotecas: numpy, pandas, matplotlib (SciPy é opcional; usado se disponível).

CHANGES (alterações em relação ao código anterior):
- Removidos trechos experimentais, prints soltos e globais redundantes
  (motivo: clareza, reprodutibilidade e manutenibilidade).
- Unidades explicitadas (km, s, nm) e conversões centralizadas
  (motivo: reduzir erros por mistura de unidades).
- Difração de Fresnel isolada em funções puras com fallback sem SciPy
  (motivo: manter acurácia quando disponível e portabilidade quando não).
- Ruídos desacoplados da física (camada separada)
  (motivo: permitir trocar/ligar/desligar ruídos facilmente).
- Normalização robusta por quartis contíguos ou mediana
  (motivo: simular "pós-fotometria" com baseline estável).
- Função `testes_extras()` com cenários aproximados de Umbriel e Chariklo
  (motivo: exemplos práticos com corpos pequenos conhecidos).
"""

from __future__ import annotations

from typing import Optional, Tuple, List
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# Utilidades e constantes
# =============================================================================

SPEED_OF_LIGHT_MS = 299_792_458.0  # m/s (não é usada diretamente, mantida por referência)
NM_TO_KM = 1e-12  # 1 nm = 1e-12 km


def magnitude_to_relative_flux(magnitude: float) -> float:
    """
    Converte magnitude aparente em fluxo relativo (sem calibração absoluta).

    Equação fotométrica padrão:
        F ∝ 10^(-0.4 m)
    """
    return 10.0 ** (-0.4 * float(magnitude))


def normalize_flux_top_quartiles(flux: np.ndarray) -> np.ndarray:
    """
    Normaliza o fluxo dividindo pelo baseline estimado como a média das duas
    maiores médias entre 4 segmentos contíguos (quartis em tempo).

    - Razoável para "pós-fotometria": baseline ~ 1 fora da ocultação.
    - Fallbacks garantem retorno mesmo em séries curtas.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return flux
    if valid.size < 4:
        baseline = float(np.mean(valid))
        baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
        return flux / baseline
    segments = np.array_split(valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
    if len(means) == 0:
        baseline = float(np.median(valid))
    else:
        order = np.argsort(means)
        top = [means[order[-1]]]
        if len(means) >= 2:
            top.append(means[order[-2]])
        baseline = float(np.mean(top))
    if not np.isfinite(baseline) or baseline <= 0:
        baseline = float(np.median(valid))
        if not np.isfinite(baseline) or baseline <= 0:
            return flux
    return flux / baseline


# =============================================================================
# Física de Fresnel (difração)
# =============================================================================

class FresnelPhysics:
    """
    Funções para cálculo de escala de Fresnel e transmitâncias difrativas.
    """

    @staticmethod
    def fresnel_scale_km(distance_km: float, wavelength_nm: float) -> float:
        """
        F = sqrt(lambda * D / 2), com lambda em km e D em km.
        """
        lambda_km = float(wavelength_nm) * NM_TO_KM
        D = float(distance_km)
        return math.sqrt(max(lambda_km * D / 2.0, 1e-30))

    @staticmethod
    def fresnel_CS(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrais de Fresnel (C, S) com SciPy se disponível; caso contrário,
        usa aproximações assintóticas/séries adequadas a fins educacionais.
        """
        try:
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore
            # A escala do argumento varia entre convenções; adotamos um fator
            # para obter bom acordo qualitativo.
            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback aproximado: bom o suficiente didaticamente
        x = np.asarray(u, dtype=float)
        ax = np.abs(x)
        C = np.zeros_like(x)
        S = np.zeros_like(x)

        small = ax <= 1.5
        if np.any(small):
            z = x[small]
            # Séries truncadas (educacional; não metrológico)
            C[small] = (z - (math.pi**2) * (z**5) / 40.0) / math.sqrt(2.0 * math.pi)
            S[small] = ((math.pi) * (z**3) / 6.0 - (math.pi**3) * (z**7) / 336.0) / math.sqrt(
                2.0 * math.pi
            )

        large = ~small
        if np.any(large):
            z = x[large]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[large] = c
            S[large] = s

        return C, S

    @staticmethod
    def knife_edge_transmission(x_km: np.ndarray, edge_pos_km: float,
                                distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Transmitância de difração para uma borda "knife-edge".

        I(u) = 0.5 [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ],
        onde u = (x - x_edge) / F e F é a escala de Fresnel.
        """
        F = FresnelPhysics.fresnel_scale_km(distance_km, wavelength_nm)
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = FresnelPhysics.fresnel_CS(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    @staticmethod
    def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                  distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa opaca: combinação correta de duas bordas (imersão e emersão).

        A transmitância de uma borda "knife-edge" cresce de ~0 (à esquerda) para ~1 (à direita).
        Para representar uma faixa opaca (região central escura), a combinação física
        desejada é:
            T(x) ≈ (1 - T_edge(x, x1)) + T_edge(x, x2)
        Isto produz T ~ 1 fora da faixa e T ~ 0 entre x1 e x2, com as franjas
        de difração aparecendo nas vizinhanças das bordas.
        """
        half = 0.5 * float(width_km)
        x1 = float(center_km) - half
        x2 = float(center_km) + half
        T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
        T2 = FresnelPhysics.knife_edge_transmission(x_km, x2, distance_km, wavelength_nm)
        T = (1.0 - T1) + T2
        # Permite leve overshoot por difração; ajuste se necessário
        return np.clip(T, 0.0, 1.2)

    @staticmethod
    def partial_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                   opacity: float, distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa parcialmente opaca (anéis):
        T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = FresnelPhysics.opaque_strip_transmission(
            x_km, center_km, width_km, distance_km, wavelength_nm
        )
        return 1.0 - float(opacity) * (1.0 - T_opaque)


# =============================================================================
# Modelo de ruído
# =============================================================================

class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.

    Esta versão inclui:
    - Céu de fundo (Poisson aditivo, independente da estrela)
    - Offset/bias do detector
    - Subtração de fundo com erro (pode gerar valores negativos)
    - Cintilação multiplicativa atuando apenas no termo da estrela
    """

    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 20.0, gain_counts_per_flux: float = 1e9,
                 sky_bg_rate_counts_per_s: float = 300.0, bias_offset_counts: float = 100.0,
                 subtract_background: bool = True, bg_subtract_noise_frac: float = 0.05,
                 allow_negative: bool = True,
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.sky_bg_rate_counts_per_s = float(sky_bg_rate_counts_per_s)
        self.bias_offset_counts = float(bias_offset_counts)
        self.subtract_background = bool(subtract_background)
        self.bg_subtract_noise_frac = float(bg_subtract_noise_frac)
        self.allow_negative = bool(allow_negative)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Aplica:
        - Poisson da estrela (após ganho)
        - Poisson do céu de fundo
        - Ruído de leitura gaussiano
        - Cintilação (lognormal) atuando na estrela
        - Subtração de fundo com erro relativo controlado
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 0.0, None)

        # Contagens esperadas da estrela
        lam_star = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam_star = np.clip(lam_star, 0, 1e12)

        # Poisson da estrela
        counts_star = self.rng.poisson(lam_star)

        # Céu de fundo (Poisson) — independente da estrela
        lam_bg = self.sky_bg_rate_counts_per_s * self.exposure_time_s
        counts_bg = self.rng.poisson(lam_bg * np.ones_like(counts_star))

        # Ruído de leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=counts_star.size)

        # Cintilação (lognormal): pior para seeing ruim e diminui com t^{-1/2}
        # Fator menor para evitar modulações multiplicativas exageradas.
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=counts_star.size))

        # Sinal total (contagens)
        total_counts = counts_star * scint + counts_bg + read + self.bias_offset_counts

        # Subtração de fundo estimado (com erro relativo)
        if self.subtract_background:
            est_bg = lam_bg + self.bias_offset_counts
            est_bg_vec = est_bg * (1.0 + self.rng.normal(0.0, self.bg_subtract_noise_frac, size=counts_star.size))
            total_counts = total_counts - est_bg_vec

        # Converte para "fluxo relativo"
        flux = total_counts / (self.gain_counts_per_flux * self.exposure_time_s)

        if not self.allow_negative:
            flux = np.clip(flux, 0.0, None)
        return flux


# =============================================================================
# Simulador principal
# =============================================================================

class SyntheticLightCurveSimulator:
    """
    Simulador de curvas de luz sintéticas para ocultações estelares.

    Parâmetros
    ----------
    mag_star : float
        Magnitude aparente da estrela (escala relativa).
    distance_km : float
        Distância observador–corpo (km), usada na escala de Fresnel.
    diameter_km : float
        Diâmetro projetado do corpo (km) ao longo da corda.
    velocity_kms : float
        Velocidade relativa do evento (km/s).
    exposure_time_s : float
        Tempo de exposição por amostra (s).
    total_duration_s : Optional[float]
        Duração total da simulação (s). Se None, é inferida com margem.
    wavelength_nm : float
        Comprimento de onda efetivo (nm), p.ex. 550 nm ~ banda V.
    seeing_arcsec : float
        Seeing (arcsec), controla a cintilação.
    rings : Optional[List[Tuple[float, float, float]]]
        Lista de anéis como (offset_km, width_km, opacity). Opacity em [0,1].
    satellites : Optional[List[Tuple[float, float]]]
        Lista de satélites como (offset_km, diameter_km).
    normalize_method : str
        "top_quartiles" (default) ou "median".
    random_seed : Optional[int]
        Semente para reprodutibilidade dos ruídos.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4_000.0,
        diameter_km: float = 1_200.0,
        velocity_kms: float = 20.0,
        exposure_time_s: float = 0.1,
        total_duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        satellites: Optional[List[Tuple[float, float]]] = None,
        normalize_method: str = "top_quartiles",
        random_seed: Optional[int] = None,
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time_s = float(exposure_time_s)
        self.total_duration_s = float(total_duration_s) if total_duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.rings = rings if rings is not None else []
        self.satellites = satellites if satellites is not None else []
        self.normalize_method = normalize_method

        self.rng = np.random.default_rng(random_seed)
        self.noise = NoiseModel(
            seeing_arcsec=self.seeing_arcsec,
            exposure_time_s=self.exposure_time_s,
            rng=self.rng,
        )

        # Saídas
        self.time_s: Optional[np.ndarray] = None
        self.flux: Optional[np.ndarray] = None
        self.flux_norm: Optional[np.ndarray] = None

        # Diretórios de saída
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_dirs()

    def simulate(self) -> pd.DataFrame:
        """
        Executa a simulação completa:
        - Constrói tempo e coordenada ao longo da corda
        - Calcula transmitância difrativa: corpo × anéis × satélites
        - Converte magnitude em fluxo relativo e aplica transmitância
        - Aplica ruídos (Poisson, leitura, cintilação)
        - Normaliza o fluxo
        """
        t, x = self._build_time_and_chord()

        # Corpo principal (faixa opaca)
        T_body = FresnelPhysics.opaque_strip_transmission(
            x, center_km=0.0, width_km=self.diameter_km,
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )

        # Anéis (faixas parcialmente opacas)
        T_rings = np.ones_like(T_body)
        for (offset_km, width_km, opacity) in self.rings:
            T_rings *= FresnelPhysics.partial_strip_transmission(
                x, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Satélites (faixas opacas deslocadas)
        T_sats = np.ones_like(T_body)
        for (offset_km, diameter_km) in self.satellites:
            T_sats *= FresnelPhysics.opaque_strip_transmission(
                x, center_km=float(offset_km), width_km=float(diameter_km),
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )

        # Transmitância total
        T_total = np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

        # Fluxo relativo esperado (sem ruído)
        base_flux = magnitude_to_relative_flux(self.mag_star)
        expected_rel_flux = base_flux * T_total

        # Ruído
        noisy_flux = self.noise.apply(expected_rel_flux)

        # Normalização
        if self.normalize_method == "median":
            baseline = float(np.median(noisy_flux[np.isfinite(noisy_flux)]))
            baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
            flux_norm = noisy_flux / baseline
        else:
            flux_norm = normalize_flux_top_quartiles(noisy_flux)

        # Armazena e retorna
        self.time_s = t
        self.flux = noisy_flux
        self.flux_norm = flux_norm
        return pd.DataFrame({"time_s": t, "flux": noisy_flux, "flux_norm": flux_norm})

    def plot_curve(self, save: bool = True, show: bool = False, title: Optional[str] = None) -> str:
        """
        Plota a curva normalizada. Retorna o caminho do PNG salvo (string)
        se `save=True`, caso contrário retorna string vazia.
        """
        self._require_simulation()
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(self.time_s, self.flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adim.]")
        band = f"{int(round(self.wavelength_nm))} nm"
        ttl = title if title else f"Curva sintética com difração e seeing — {band}"
        ax.set_title(ttl)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        png_path = ""
        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)
        return png_path

    def export_data(self, save: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Exporta os dados simulados para um .dat numerado em output/.
        Retorna (DataFrame, caminho_do_arquivo_ou_string_vazia).
        """
        self._require_simulation()
        df = pd.DataFrame({"time_s": self.time_s, "flux": self.flux, "flux_norm": self.flux_norm})
        dat_path = ""
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df, dat_path

    # -------------------------- helpers internos -----------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.total_duration_s is None:
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time * 3.0  # margem: 1x antes e 1x depois
        else:
            total_time = self.total_duration_s
        n_steps = max(2, int(math.ceil(total_time / self.exposure_time_s)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _ensure_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                n = int(name.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulation(self) -> None:
        if self.time_s is None or self.flux is None or self.flux_norm is None:
            raise RuntimeError("Simulação ainda não executada. Chame simulate() antes.")


# =============================================================================
# Testes extras com corpos pequenos (Umbriel e Chariklo)
# =============================================================================

def testes_extras() -> None:
    """
    Executa dois cenários de teste:
    1) Umbriel (satélite de Urano) — sem anéis
    2) Chariklo (Centauro) — com anéis C1R e C2R (parâmetros aproximados)

    Observações:
    - Valores aproximados (ordem de grandeza) para fins didáticos.
    - Distâncias geocêntricas típicas: Urano ~ 2.9e9 km, Chariklo ~ 2.1e9 km.
    - Velocidades típicas de sombra ~ 20–25 km/s.
    - Parâmetros dos anéis de Chariklo (Braga-Ribas+2014):
        - Raios ~ 391 km e 405 km; larguras ~ 7 km e 3 km;
          profundidades óticas τ ~ 0.4 e 0.06 → opacidade ~ 1 - e^{-τ}.
      Para uma ocultação equatorial idealizada, modelamos cada anel por duas faixas
      simétricas (+/- raio) com a mesma largura e opacidade.
    """
    # ------------------------------- Umbriel ---------------------------------
    umbriel = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,        # ~ distância de Urano à Terra (aprox.)
        diameter_km=1169.0,       # diâmetro de Umbriel ~ 1169 km
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        normalize_method="top_quartiles",
        random_seed=123,
    )
    df_u = umbriel.simulate()
    umbriel.plot_curve(save=True, show=False, title="Umbriel — V~550 nm")
    umbriel.export_data(save=True)

    # ------------------------------ Chariklo ---------------------------------
    # Parâmetros aproximados dos anéis (C1R e C2R)
    r1_km, w1_km, tau1 = 391.0, 7.0, 0.4
    r2_km, w2_km, tau2 = 405.0, 3.0, 0.06
    op1 = 1.0 - math.exp(-tau1)
    op2 = 1.0 - math.exp(-tau2)

    rings_chariklo: List[Tuple[float, float, float]] = [
        (+r1_km, w1_km, op1),
        (-r1_km, w1_km, op1),
        (+r2_km, w2_km, op2),
        (-r2_km, w2_km, op2),
    ]

    max_r = max(r1_km, r2_km)
    margin_km = 20.0  # folga
    half_span_km = max_r + 0.5 * 250.0 + margin_km  # 250.0 é o diameter_km usado
    total_duration_s = 2.0 * half_span_km / 25.0 

    chariklo = SyntheticLightCurveSimulator(
        mag_star=13.0,
        distance_km=2.1e9,        # Chariklo típico ~ 15 AU (aprox.)
        diameter_km=250.0,        # diâmetro efetivo do corpo (aprox. esfera equiv.)
        velocity_kms=25.0,
        exposure_time_s=0.1,
        wavelength_nm=650.0,      # banda R aproximada
        seeing_arcsec=1.2,
        rings=rings_chariklo,
        satellites=[],            # sem satélites aqui
        normalize_method="top_quartiles",
        total_duration_s=1000,
        random_seed=321,
    )
    df_c = chariklo.simulate()
    chariklo.plot_curve(save=True, show=False, title="Chariklo com anéis — R~650 nm")
    chariklo.export_data(save=True)

    # Prints simples para feedback (como um "junior" faria)
    print("Umbriel: amostras =", len(df_u), " min/max flux_norm =", float(df_u.flux_norm.min()),
          float(df_u.flux_norm.max()))
    print("Chariklo: amostras =", len(df_c), " min/max flux_norm =", float(df_c.flux_norm.min()),
          float(df_c.flux_norm.max()))

    # --------------------- Corpo fictício tipo "Umbriel com anéis" ---------------------
    # Ideia: corpo com diâmetro ~Umbriel, porém com um sistema de anéis "grande"
    # escalonado pela proporção típica de Saturno (raios de anéis ~ 1.7–2.4 vezes o raio do planeta,
    # com larguras fracionárias significativas). Usamos três anéis com opacidades relativamente altas,
    # para produzir quedas fortes e estruturas visíveis.
    umb_like_diam_km = 1169.0
    umb_like_rad_km = 0.5 * umb_like_diam_km
    # Raios proporcionais (em múltiplos do raio do corpo)
    rC = 1.30 * umb_like_rad_km   # anel interno (análog. C)
    rB = 1.70 * umb_like_rad_km   # anel intermediário (análog. B)
    rA = 2.30 * umb_like_rad_km   # anel externo (análog. A)
    # Larguras proporcionais ao raio do corpo (valores inspirados nas frações em Saturno)
    wC = 0.25 * umb_like_rad_km
    wB = 0.44 * umb_like_rad_km
    wA = 0.30 * umb_like_rad_km
    # Profundidades óticas aproximadas (mais opacos para quedas fortes)
    tauC, tauB, tauA = 0.3, 0.9, 0.6
    opC = 1.0 - math.exp(-tauC)
    opB = 1.0 - math.exp(-tauB)
    opA = 1.0 - math.exp(-tauA)

    rings_umb_like: List[Tuple[float, float, float]] = [
        (+rC, wC, opC), (-rC, wC, opC),
        (+rB, wB, opB), (-rB, wB, opB),
        (+rA, wA, opA), (-rA, wA, opA),
    ]

    # Janela temporal suficiente para cobrir o anel externo
    outer_r = max(rA, rB, rC)
    margin_km = 100.0
    half_span_km = outer_r + 0.5 * umb_like_diam_km + margin_km
    total_duration_s = 2.0 * half_span_km / 20.0  # vel = 20 km/s

    umbriel_like_with_rings = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,         # mesma ordem de Umbriel/Urano
        diameter_km=umb_like_diam_km,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=rings_umb_like,
        satellites=[],
        normalize_method="top_quartiles",
        total_duration_s=total_duration_s,
        random_seed=777,
    )
    df_ul = umbriel_like_with_rings.simulate()
    umbriel_like_with_rings.plot_curve(save=True, show=False, title="Umbriel-like com anéis — V~550 nm")
    umbriel_like_with_rings.export_data(save=True)
    print("Umbriel-like: amostras =", len(df_ul), " min/max flux_norm =", float(df_ul.flux_norm.min()),
          float(df_ul.flux_norm.max()))


# =============================================================================
# Execução direta (exemplo mínimo)
# =============================================================================

if __name__ == "__main__":
    # Exemplo mínimo de uso "out of the box"
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4_000.0,
        diameter_km=1_200.0,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        random_seed=42,
    )
    df = sim.simulate()
    png = sim.plot_curve(save=True, show=False)
    dat_df, dat_path = sim.export_data(save=True)
    print("Arquivo de dados:", dat_path)
    print("Arquivo da figura:", png)

    # Rodar os testes extras com Umbriel e Chariklo
    testes_extras()
```

- Acrescentei um 3º cenário em `testes_extras()` chamado “Umbriel-like com anéis”, com:
  - Corpo fictício do tamanho de Umbriel (`diameter_km=1169`) e sistema de anéis grandes inspirados nas proporções de Saturno.
  - Três anéis (C, B, A) com raios ~1.30, 1.70 e 2.30 vezes o raio do corpo; larguras fracionárias e opacidades altas para quedas fortes.
  - Janela temporal calculada para cobrir o anel mais externo.
- O script agora gera e salva também a curva desse caso, com estruturas proeminentes nos anéis.

---

**User**

@model_training/synthetic_curve/simulate_curve.py O teste de umbriel-like com aneis foi um sucesso, mas questiono o fato de observar as quedas dos aneis muito 'bonitinhos'. Elas são caixas quase perfeitas, imaginava ver quedas menos bruscas. O que você me sugere para adicionar mais realismo aos testes? 

---

**Cursor**

Para os anéis ficarem menos “caixa perfeita” e mais realistas, sugiro dois suavizadores físicos simples que funcionam bem:

- integração temporal dentro de cada exposição (média em subamostras no intervalo da exposição);
- fonte estendida (estrela com diâmetro angular finito) → convolução tipo boxcar no eixo do tempo (equivalente a alargar a aresta difrativa).

Abaixo estão edições pontuais no seu `simulate_curve.py` para habilitar isso. Elas suavizam tanto corpo quanto anéis, deixando as quedas menos bruscas e com contornos mais naturais.

1) Adicione novos parâmetros na classe para controlar o efeito
- `subsamples_per_exposure`: número de subamostras por exposição (ex.: 5–9).
- `star_angular_mas`: diâmetro angular da estrela em mili-arcseg (ex.: 0.05–0.3 mas).

Cole no `__init__` de `SyntheticLightCurveSimulator` os novos argumentos (mantenha a mesma ordem):

```python
# ... no signature do __init__
subsamples_per_exposure: int = 1,   # 1 = sem integração; >1 média temporal
star_angular_mas: float = 0.0,      # diâmetro angular da estrela em mas
# ...
self.subsamples_per_exposure = int(subsamples_per_exposure)
self.star_angular_mas = float(star_angular_mas)
```

2) Helper para suavizar por “boxcar” (fonte estendida)
Cole estes métodos dentro da classe `SyntheticLightCurveSimulator`:

```python
def _boxcar_smooth(self, y: np.ndarray, window_samples: int) -> np.ndarray:
    if window_samples <= 1:
        return y
    k = np.ones(int(window_samples), dtype=float)
    k /= k.sum()
    return np.convolve(y, k, mode="same")

def _star_window_samples(self, dt_s: float) -> int:
    # estrela em mas → rad
    if self.star_angular_mas <= 0:
        return 1
    theta_rad = self.star_angular_mas * (np.pi / (648000.0 * 1000.0))  # mas → rad
    # tamanho projetado da estrela no plano do evento (km)
    star_proj_km = self.distance_km * theta_rad
    # largura temporal equivalente
    window_km = max(star_proj_km, 0.0)
    dx_km = self.velocity_kms * max(dt_s, 1e-12)
    n = int(round(window_km / max(dx_km, 1e-9)))
    return max(n, 1)
```

3) Integração temporal por subamostras e convolução de estrela
Substitua o bloco onde você calcula `T_total` dentro de `simulate()` por este trecho (mantendo o restante igual):

```python
t, x = self._build_time_and_chord()
t0 = 0.5 * (t[0] + t[-1])
dt_s = t[1] - t[0] if len(t) > 1 else self.exposure_time_s

def compute_T_total_for_x(xx: np.ndarray) -> np.ndarray:
    T_body = FresnelPhysics.opaque_strip_transmission(
        xx, center_km=0.0, width_km=self.diameter_km,
        distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
    )
    T_rings = np.ones_like(T_body)
    for (offset_km, width_km, opacity) in self.rings:
        T_rings *= FresnelPhysics.partial_strip_transmission(
            xx, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )
    T_sats = np.ones_like(T_body)
    for (offset_km, diameter_km) in self.satellites:
        T_sats *= FresnelPhysics.opaque_strip_transmission(
            xx, center_km=float(offset_km), width_km=float(diameter_km),
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )
    return np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

# 3.a) Integração temporal dentro de cada exposição
if self.subsamples_per_exposure > 1:
    shifts = np.linspace(-0.5 * self.exposure_time_s,
                         +0.5 * self.exposure_time_s,
                         self.subsamples_per_exposure)
    acc = 0.0
    for s in shifts:
        x_s = (t + s - t0) * self.velocity_kms
        acc += compute_T_total_for_x(x_s)
    T_total = acc / float(self.subsamples_per_exposure)
else:
    T_total = compute_T_total_for_x(x)

# 3.b) Fonte estendida (estrela finita): convolução tipo boxcar
win = self._star_window_samples(dt_s)
if win > 1:
    T_total = self._boxcar_smooth(T_total, win)
```

4) Recomendações de valores
- `subsamples_per_exposure=5` ou `9`: já dá um bom arredondamento temporal (exposição integra o evento).
- `star_angular_mas` entre 0.05 e 0.2 mas: gera suavização realista das arestas (combine com a integração).
- Para anéis muito “duros”, experimente aumentar ligeiramente `seeing_arcsec` (a cintilação multiplicativa ajuda a “morder” as arestas) e/ou o `readout_sigma_counts` no `NoiseModel`.

Opcional (para ainda mais realismo, se quiser ir além)
- Anéis com bordas difusas: aplicar um desfoque gaussiano fraco apenas sobre o termo de anéis, ou parametrizar uma “largura de borda” (edge_soft_km) baseada em um erro de perfil vertical do anel.
- Opacidade com “clumps”: variar a opacidade dos anéis lentamente no tempo (ruído colorido com escala de correlação em km) para forma não retangular. Posso te passar um snippet para modulação τ(x) suave.

Com essas duas adições (integração temporal e estrela finita) você verá as quedas dos anéis menos bruscas, com transições arredondadas e mais parecidas com observações reais.

```python
# ... no signature do __init__
subsamples_per_exposure: int = 1,   # 1 = sem integração; >1 média temporal
star_angular_mas: float = 0.0,      # diâmetro angular da estrela em mas
# ...
self.subsamples_per_exposure = int(subsamples_per_exposure)
self.star_angular_mas = float(star_angular_mas)
```

```python
def _boxcar_smooth(self, y: np.ndarray, window_samples: int) -> np.ndarray:
    if window_samples <= 1:
        return y
    k = np.ones(int(window_samples), dtype=float)
    k /= k.sum()
    return np.convolve(y, k, mode="same")

def _star_window_samples(self, dt_s: float) -> int:
    # estrela em mas → rad
    if self.star_angular_mas <= 0:
        return 1
    theta_rad = self.star_angular_mas * (np.pi / (648000.0 * 1000.0))  # mas → rad
    # tamanho projetado da estrela no plano do evento (km)
    star_proj_km = self.distance_km * theta_rad
    # largura temporal equivalente
    window_km = max(star_proj_km, 0.0)
    dx_km = self.velocity_kms * max(dt_s, 1e-12)
    n = int(round(window_km / max(dx_km, 1e-9)))
    return max(n, 1)
```

```python
t, x = self._build_time_and_chord()
t0 = 0.5 * (t[0] + t[-1])
dt_s = t[1] - t[0] if len(t) > 1 else self.exposure_time_s

def compute_T_total_for_x(xx: np.ndarray) -> np.ndarray:
    T_body = FresnelPhysics.opaque_strip_transmission(
        xx, center_km=0.0, width_km=self.diameter_km,
        distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
    )
    T_rings = np.ones_like(T_body)
    for (offset_km, width_km, opacity) in self.rings:
        T_rings *= FresnelPhysics.partial_strip_transmission(
            xx, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )
    T_sats = np.ones_like(T_body)
    for (offset_km, diameter_km) in self.satellites:
        T_sats *= FresnelPhysics.opaque_strip_transmission(
            xx, center_km=float(offset_km), width_km=float(diameter_km),
            distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
        )
    return np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

# 3.a) Integração temporal dentro de cada exposição
if self.subsamples_per_exposure > 1:
    shifts = np.linspace(-0.5 * self.exposure_time_s,
                         +0.5 * self.exposure_time_s,
                         self.subsamples_per_exposure)
    acc = 0.0
    for s in shifts:
        x_s = (t + s - t0) * self.velocity_kms
        acc += compute_T_total_for_x(x_s)
    T_total = acc / float(self.subsamples_per_exposure)
else:
    T_total = compute_T_total_for_x(x)

# 3.b) Fonte estendida (estrela finita): convolução tipo boxcar
win = self._star_window_samples(dt_s)
if win > 1:
    T_total = self._boxcar_smooth(T_total, win)
```

---

**User**

@model_training/synthetic_curve/simulate_curve.py aplique sua sugestão anterior 

---

**Cursor**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador modular de curvas de luz de ocultações estelares.

Este arquivo reorganiza o antigo script monolítico em classes e funções
coesas, seguindo PEP 8 e boas práticas de programação científica.

Principais componentes:
- Física de Fresnel (difração em bordas "knife-edge" e faixa opaca)
- Geometria do evento (linha do tempo e coordenada ao longo da corda)
- Modelo de ruído (Poisson, leitura, cintilação multiplicativa)
- Normalização "pós-fotometria" (baseline ~ 1)
- Orquestração via uma classe principal de fácil uso

Bibliotecas: numpy, pandas, matplotlib (SciPy é opcional; usado se disponível).

CHANGES (alterações em relação ao código anterior):
- Removidos trechos experimentais, prints soltos e globais redundantes
  (motivo: clareza, reprodutibilidade e manutenibilidade).
- Unidades explicitadas (km, s, nm) e conversões centralizadas
  (motivo: reduzir erros por mistura de unidades).
- Difração de Fresnel isolada em funções puras com fallback sem SciPy
  (motivo: manter acurácia quando disponível e portabilidade quando não).
- Ruídos desacoplados da física (camada separada)
  (motivo: permitir trocar/ligar/desligar ruídos facilmente).
- Normalização robusta por quartis contíguos ou mediana
  (motivo: simular "pós-fotometria" com baseline estável).
- Função `testes_extras()` com cenários aproximados de Umbriel e Chariklo
  (motivo: exemplos práticos com corpos pequenos conhecidos).
"""

from __future__ import annotations

from typing import Optional, Tuple, List
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# Utilidades e constantes
# =============================================================================

SPEED_OF_LIGHT_MS = 299_792_458.0  # m/s (não é usada diretamente, mantida por referência)
NM_TO_KM = 1e-12  # 1 nm = 1e-12 km


def magnitude_to_relative_flux(magnitude: float) -> float:
    """
    Converte magnitude aparente em fluxo relativo (sem calibração absoluta).

    Equação fotométrica padrão:
        F ∝ 10^(-0.4 m)
    """
    return 10.0 ** (-0.4 * float(magnitude))


def normalize_flux_top_quartiles(flux: np.ndarray) -> np.ndarray:
    """
    Normaliza o fluxo dividindo pelo baseline estimado como a média das duas
    maiores médias entre 4 segmentos contíguos (quartis em tempo).

    - Razoável para "pós-fotometria": baseline ~ 1 fora da ocultação.
    - Fallbacks garantem retorno mesmo em séries curtas.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return flux
    if valid.size < 4:
        baseline = float(np.mean(valid))
        baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
        return flux / baseline
    segments = np.array_split(valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
    if len(means) == 0:
        baseline = float(np.median(valid))
    else:
        order = np.argsort(means)
        top = [means[order[-1]]]
        if len(means) >= 2:
            top.append(means[order[-2]])
        baseline = float(np.mean(top))
    if not np.isfinite(baseline) or baseline <= 0:
        baseline = float(np.median(valid))
        if not np.isfinite(baseline) or baseline <= 0:
            return flux
    return flux / baseline


# =============================================================================
# Física de Fresnel (difração)
# =============================================================================

class FresnelPhysics:
    """
    Funções para cálculo de escala de Fresnel e transmitâncias difrativas.
    """

    @staticmethod
    def fresnel_scale_km(distance_km: float, wavelength_nm: float) -> float:
        """
        F = sqrt(lambda * D / 2), com lambda em km e D em km.
        """
        lambda_km = float(wavelength_nm) * NM_TO_KM
        D = float(distance_km)
        return math.sqrt(max(lambda_km * D / 2.0, 1e-30))

    @staticmethod
    def fresnel_CS(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrais de Fresnel (C, S) com SciPy se disponível; caso contrário,
        usa aproximações assintóticas/séries adequadas a fins educacionais.
        """
        try:
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore
            # A escala do argumento varia entre convenções; adotamos um fator
            # para obter bom acordo qualitativo.
            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback aproximado: bom o suficiente didaticamente
        x = np.asarray(u, dtype=float)
        ax = np.abs(x)
        C = np.zeros_like(x)
        S = np.zeros_like(x)

        small = ax <= 1.5
        if np.any(small):
            z = x[small]
            # Séries truncadas (educacional; não metrológico)
            C[small] = (z - (math.pi**2) * (z**5) / 40.0) / math.sqrt(2.0 * math.pi)
            S[small] = ((math.pi) * (z**3) / 6.0 - (math.pi**3) * (z**7) / 336.0) / math.sqrt(
                2.0 * math.pi
            )

        large = ~small
        if np.any(large):
            z = x[large]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[large] = c
            S[large] = s

        return C, S

    @staticmethod
    def knife_edge_transmission(x_km: np.ndarray, edge_pos_km: float,
                                distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Transmitância de difração para uma borda "knife-edge".

        I(u) = 0.5 [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ],
        onde u = (x - x_edge) / F e F é a escala de Fresnel.
        """
        F = FresnelPhysics.fresnel_scale_km(distance_km, wavelength_nm)
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = FresnelPhysics.fresnel_CS(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    @staticmethod
    def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                  distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa opaca: combinação correta de duas bordas (imersão e emersão).

        A transmitância de uma borda "knife-edge" cresce de ~0 (à esquerda) para ~1 (à direita).
        Para representar uma faixa opaca (região central escura), a combinação física
        desejada é:
            T(x) ≈ (1 - T_edge(x, x1)) + T_edge(x, x2)
        Isto produz T ~ 1 fora da faixa e T ~ 0 entre x1 e x2, com as franjas
        de difração aparecendo nas vizinhanças das bordas.
        """
        half = 0.5 * float(width_km)
        x1 = float(center_km) - half
        x2 = float(center_km) + half
        T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
        T2 = FresnelPhysics.knife_edge_transmission(x_km, x2, distance_km, wavelength_nm)
        T = (1.0 - T1) + T2
        # Permite leve overshoot por difração; ajuste se necessário
        return np.clip(T, 0.0, 1.2)

    @staticmethod
    def partial_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                   opacity: float, distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa parcialmente opaca (anéis):
        T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = FresnelPhysics.opaque_strip_transmission(
            x_km, center_km, width_km, distance_km, wavelength_nm
        )
        return 1.0 - float(opacity) * (1.0 - T_opaque)


# =============================================================================
# Modelo de ruído
# =============================================================================

class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.

    Esta versão inclui:
    - Céu de fundo (Poisson aditivo, independente da estrela)
    - Offset/bias do detector
    - Subtração de fundo com erro (pode gerar valores negativos)
    - Cintilação multiplicativa atuando apenas no termo da estrela
    """

    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 20.0, gain_counts_per_flux: float = 1e9,
                 sky_bg_rate_counts_per_s: float = 300.0, bias_offset_counts: float = 100.0,
                 subtract_background: bool = True, bg_subtract_noise_frac: float = 0.05,
                 allow_negative: bool = True,
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.sky_bg_rate_counts_per_s = float(sky_bg_rate_counts_per_s)
        self.bias_offset_counts = float(bias_offset_counts)
        self.subtract_background = bool(subtract_background)
        self.bg_subtract_noise_frac = float(bg_subtract_noise_frac)
        self.allow_negative = bool(allow_negative)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Aplica:
        - Poisson da estrela (após ganho)
        - Poisson do céu de fundo
        - Ruído de leitura gaussiano
        - Cintilação (lognormal) atuando na estrela
        - Subtração de fundo com erro relativo controlado
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 0.0, None)

        # Contagens esperadas da estrela
        lam_star = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam_star = np.clip(lam_star, 0, 1e12)

        # Poisson da estrela
        counts_star = self.rng.poisson(lam_star)

        # Céu de fundo (Poisson) — independente da estrela
        lam_bg = self.sky_bg_rate_counts_per_s * self.exposure_time_s
        counts_bg = self.rng.poisson(lam_bg * np.ones_like(counts_star))

        # Ruído de leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=counts_star.size)

        # Cintilação (lognormal): pior para seeing ruim e diminui com t^{-1/2}
        # Fator menor para evitar modulações multiplicativas exageradas.
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=counts_star.size))

        # Sinal total (contagens)
        total_counts = counts_star * scint + counts_bg + read + self.bias_offset_counts

        # Subtração de fundo estimado (com erro relativo)
        if self.subtract_background:
            est_bg = lam_bg + self.bias_offset_counts
            est_bg_vec = est_bg * (1.0 + self.rng.normal(0.0, self.bg_subtract_noise_frac, size=counts_star.size))
            total_counts = total_counts - est_bg_vec

        # Converte para "fluxo relativo"
        flux = total_counts / (self.gain_counts_per_flux * self.exposure_time_s)

        if not self.allow_negative:
            flux = np.clip(flux, 0.0, None)
        return flux


# =============================================================================
# Simulador principal
# =============================================================================

class SyntheticLightCurveSimulator:
    """
    Simulador de curvas de luz sintéticas para ocultações estelares.

    Parâmetros
    ----------
    mag_star : float
        Magnitude aparente da estrela (escala relativa).
    distance_km : float
        Distância observador–corpo (km), usada na escala de Fresnel.
    diameter_km : float
        Diâmetro projetado do corpo (km) ao longo da corda.
    velocity_kms : float
        Velocidade relativa do evento (km/s).
    exposure_time_s : float
        Tempo de exposição por amostra (s).
    total_duration_s : Optional[float]
        Duração total da simulação (s). Se None, é inferida com margem.
    wavelength_nm : float
        Comprimento de onda efetivo (nm), p.ex. 550 nm ~ banda V.
    seeing_arcsec : float
        Seeing (arcsec), controla a cintilação.
    rings : Optional[List[Tuple[float, float, float]]]
        Lista de anéis como (offset_km, width_km, opacity). Opacity em [0,1].
    satellites : Optional[List[Tuple[float, float]]]
        Lista de satélites como (offset_km, diameter_km).
    normalize_method : str
        "top_quartiles" (default) ou "median".
    random_seed : Optional[int]
        Semente para reprodutibilidade dos ruídos.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4_000.0,
        diameter_km: float = 1_200.0,
        velocity_kms: float = 20.0,
        exposure_time_s: float = 0.1,
        total_duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        satellites: Optional[List[Tuple[float, float]]] = None,
        normalize_method: str = "top_quartiles",
        random_seed: Optional[int] = None,
        subsamples_per_exposure: int = 1,   # integração temporal intra-exposição
        star_angular_mas: float = 0.0,      # diâmetro angular da estrela (mas)
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time_s = float(exposure_time_s)
        self.total_duration_s = float(total_duration_s) if total_duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.rings = rings if rings is not None else []
        self.satellites = satellites if satellites is not None else []
        self.normalize_method = normalize_method
        self.subsamples_per_exposure = int(subsamples_per_exposure)
        self.star_angular_mas = float(star_angular_mas)

        self.rng = np.random.default_rng(random_seed)
        self.noise = NoiseModel(
            seeing_arcsec=self.seeing_arcsec,
            exposure_time_s=self.exposure_time_s,
            rng=self.rng,
        )

        # Saídas
        self.time_s: Optional[np.ndarray] = None
        self.flux: Optional[np.ndarray] = None
        self.flux_norm: Optional[np.ndarray] = None

        # Diretórios de saída
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_dirs()

    def simulate(self) -> pd.DataFrame:
        """
        Executa a simulação completa:
        - Constrói tempo e coordenada ao longo da corda
        - Calcula transmitância difrativa: corpo × anéis × satélites
        - Converte magnitude em fluxo relativo e aplica transmitância
        - Aplica ruídos (Poisson, leitura, cintilação)
        - Normaliza o fluxo
        """
        t, x = self._build_time_and_chord()
        t0 = 0.5 * (t[0] + t[-1])
        dt_s = t[1] - t[0] if len(t) > 1 else self.exposure_time_s

        def compute_T_total_for_x(xx: np.ndarray) -> np.ndarray:
            T_body = FresnelPhysics.opaque_strip_transmission(
                xx, center_km=0.0, width_km=self.diameter_km,
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )
            T_rings = np.ones_like(T_body)
            for (offset_km, width_km, opacity) in self.rings:
                T_rings *= FresnelPhysics.partial_strip_transmission(
                    xx, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
                    distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
                )
            T_sats = np.ones_like(T_body)
            for (offset_km, diameter_km) in self.satellites:
                T_sats *= FresnelPhysics.opaque_strip_transmission(
                    xx, center_km=float(offset_km), width_km=float(diameter_km),
                    distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
                )
            return np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

        # Integração temporal intra-exposição
        if self.subsamples_per_exposure > 1:
            shifts = np.linspace(-0.5 * self.exposure_time_s,
                                 +0.5 * self.exposure_time_s,
                                 self.subsamples_per_exposure)
            acc = 0.0
            for s in shifts:
                x_s = (t + s - t0) * self.velocity_kms
                acc += compute_T_total_for_x(x_s)
            T_total = acc / float(self.subsamples_per_exposure)
        else:
            T_total = compute_T_total_for_x(x)

        # Suavização por fonte estendida (estrela com diâmetro finito)
        win = self._star_window_samples(dt_s)
        if win > 1:
            T_total = self._boxcar_smooth(T_total, win)

        # Fluxo relativo esperado (sem ruído)
        base_flux = magnitude_to_relative_flux(self.mag_star)
        expected_rel_flux = base_flux * T_total

        # Ruído
        noisy_flux = self.noise.apply(expected_rel_flux)

        # Normalização
        if self.normalize_method == "median":
            baseline = float(np.median(noisy_flux[np.isfinite(noisy_flux)]))
            baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
            flux_norm = noisy_flux / baseline
        else:
            flux_norm = normalize_flux_top_quartiles(noisy_flux)

        # Armazena e retorna
        self.time_s = t
        self.flux = noisy_flux
        self.flux_norm = flux_norm
        return pd.DataFrame({"time_s": t, "flux": noisy_flux, "flux_norm": flux_norm})

    def plot_curve(self, save: bool = True, show: bool = False, title: Optional[str] = None) -> str:
        """
        Plota a curva normalizada. Retorna o caminho do PNG salvo (string)
        se `save=True`, caso contrário retorna string vazia.
        """
        self._require_simulation()
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(self.time_s, self.flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adim.]")
        band = f"{int(round(self.wavelength_nm))} nm"
        ttl = title if title else f"Curva sintética com difração e seeing — {band}"
        ax.set_title(ttl)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        png_path = ""
        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)
        return png_path

    def export_data(self, save: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Exporta os dados simulados para um .dat numerado em output/.
        Retorna (DataFrame, caminho_do_arquivo_ou_string_vazia).
        """
        self._require_simulation()
        df = pd.DataFrame({"time_s": self.time_s, "flux": self.flux, "flux_norm": self.flux_norm})
        dat_path = ""
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df, dat_path

    # -------------------------- helpers internos -----------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.total_duration_s is None:
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time * 3.0  # margem: 1x antes e 1x depois
        else:
            total_time = self.total_duration_s
        n_steps = max(2, int(math.ceil(total_time / self.exposure_time_s)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _ensure_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                n = int(name.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulation(self) -> None:
        if self.time_s is None or self.flux is None or self.flux_norm is None:
            raise RuntimeError("Simulação ainda não executada. Chame simulate() antes.")

    # ---------------------- suavizações físicas opcionais ---------------------
    def _boxcar_smooth(self, y: np.ndarray, window_samples: int) -> np.ndarray:
        """
        Convolução boxcar (média móvel) para simular fonte estendida.
        """
        if window_samples <= 1:
            return y
        k = np.ones(int(window_samples), dtype=float)
        k /= k.sum()
        return np.convolve(y, k, mode="same")

    def _star_window_samples(self, dt_s: float) -> int:
        """
        Converte o diâmetro angular da estrela (mas) em largura temporal (amostras)
        para um kernel boxcar simples.
        """
        if self.star_angular_mas <= 0:
            return 1
        theta_rad = self.star_angular_mas * (np.pi / (648000.0 * 1000.0))  # mas -> rad
        star_proj_km = self.distance_km * theta_rad                         # km
        dx_km = self.velocity_kms * max(dt_s, 1e-12)                       # km por amostra
        n = int(round(star_proj_km / max(dx_km, 1e-9)))
        return max(n, 1)


# =============================================================================
# Testes extras com corpos pequenos (Umbriel e Chariklo)
# =============================================================================

def testes_extras() -> None:
    """
    Executa dois cenários de teste:
    1) Umbriel (satélite de Urano) — sem anéis
    2) Chariklo (Centauro) — com anéis C1R e C2R (parâmetros aproximados)

    Observações:
    - Valores aproximados (ordem de grandeza) para fins didáticos.
    - Distâncias geocêntricas típicas: Urano ~ 2.9e9 km, Chariklo ~ 2.1e9 km.
    - Velocidades típicas de sombra ~ 20–25 km/s.
    - Parâmetros dos anéis de Chariklo (Braga-Ribas+2014):
        - Raios ~ 391 km e 405 km; larguras ~ 7 km e 3 km;
          profundidades óticas τ ~ 0.4 e 0.06 → opacidade ~ 1 - e^{-τ}.
      Para uma ocultação equatorial idealizada, modelamos cada anel por duas faixas
      simétricas (+/- raio) com a mesma largura e opacidade.
    """
    # ------------------------------- Umbriel ---------------------------------
    umbriel = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,        # ~ distância de Urano à Terra (aprox.)
        diameter_km=1169.0,       # diâmetro de Umbriel ~ 1169 km
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        normalize_method="top_quartiles",
        random_seed=123,
    )
    df_u = umbriel.simulate()
    umbriel.plot_curve(save=True, show=False, title="Umbriel — V~550 nm")
    umbriel.export_data(save=True)

    # ------------------------------ Chariklo ---------------------------------
    # Parâmetros aproximados dos anéis (C1R e C2R)
    r1_km, w1_km, tau1 = 391.0, 7.0, 0.4
    r2_km, w2_km, tau2 = 405.0, 3.0, 0.06
    op1 = 1.0 - math.exp(-tau1)
    op2 = 1.0 - math.exp(-tau2)

    rings_chariklo: List[Tuple[float, float, float]] = [
        (+r1_km, w1_km, op1),
        (-r1_km, w1_km, op1),
        (+r2_km, w2_km, op2),
        (-r2_km, w2_km, op2),
    ]

    max_r = max(r1_km, r2_km)
    margin_km = 20.0  # folga
    half_span_km = max_r + 0.5 * 250.0 + margin_km  # 250.0 é o diameter_km usado
    total_duration_s = 2.0 * half_span_km / 25.0 

    chariklo = SyntheticLightCurveSimulator(
        mag_star=13.0,
        distance_km=2.1e9,        # Chariklo típico ~ 15 AU (aprox.)
        diameter_km=250.0,        # diâmetro efetivo do corpo (aprox. esfera equiv.)
        velocity_kms=25.0,
        exposure_time_s=0.1,
        wavelength_nm=650.0,      # banda R aproximada
        seeing_arcsec=1.2,
        rings=rings_chariklo,
        satellites=[],            # sem satélites aqui
        normalize_method="top_quartiles",
        total_duration_s=1000,
        random_seed=321,
    )
    df_c = chariklo.simulate()
    chariklo.plot_curve(save=True, show=False, title="Chariklo com anéis — R~650 nm")
    chariklo.export_data(save=True)

    # Prints simples para feedback (como um "junior" faria)
    print("Umbriel: amostras =", len(df_u), " min/max flux_norm =", float(df_u.flux_norm.min()),
          float(df_u.flux_norm.max()))
    print("Chariklo: amostras =", len(df_c), " min/max flux_norm =", float(df_c.flux_norm.min()),
          float(df_c.flux_norm.max()))

    # --------------------- Corpo fictício tipo "Umbriel com anéis" ---------------------
    # Ideia: corpo com diâmetro ~Umbriel, porém com um sistema de anéis "grande"
    # escalonado pela proporção típica de Saturno (raios de anéis ~ 1.7–2.4 vezes o raio do planeta,
    # com larguras fracionárias significativas). Usamos três anéis com opacidades relativamente altas,
    # para produzir quedas fortes e estruturas visíveis.
    umb_like_diam_km = 1169.0
    umb_like_rad_km = 0.5 * umb_like_diam_km
    # Raios proporcionais (em múltiplos do raio do corpo)
    rC = 1.30 * umb_like_rad_km   # anel interno (análog. C)
    rB = 1.70 * umb_like_rad_km   # anel intermediário (análog. B)
    rA = 2.30 * umb_like_rad_km   # anel externo (análog. A)
    # Larguras proporcionais ao raio do corpo (valores inspirados nas frações em Saturno)
    wC = 0.25 * umb_like_rad_km
    wB = 0.44 * umb_like_rad_km
    wA = 0.30 * umb_like_rad_km
    # Profundidades óticas aproximadas (mais opacos para quedas fortes)
    tauC, tauB, tauA = 0.3, 0.9, 0.6
    opC = 1.0 - math.exp(-tauC)
    opB = 1.0 - math.exp(-tauB)
    opA = 1.0 - math.exp(-tauA)

    rings_umb_like: List[Tuple[float, float, float]] = [
        (+rC, wC, opC), (-rC, wC, opC),
        (+rB, wB, opB), (-rB, wB, opB),
        (+rA, wA, opA), (-rA, wA, opA),
    ]

    # Janela temporal suficiente para cobrir o anel externo
    outer_r = max(rA, rB, rC)
    margin_km = 100.0
    half_span_km = outer_r + 0.5 * umb_like_diam_km + margin_km
    total_duration_s = 2.0 * half_span_km / 20.0  # vel = 20 km/s

    umbriel_like_with_rings = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,         # mesma ordem de Umbriel/Urano
        diameter_km=umb_like_diam_km,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=rings_umb_like,
        satellites=[],
        normalize_method="top_quartiles",
        total_duration_s=total_duration_s,
        random_seed=777,
    )
    df_ul = umbriel_like_with_rings.simulate()
    umbriel_like_with_rings.plot_curve(save=True, show=False, title="Umbriel-like com anéis — V~550 nm")
    umbriel_like_with_rings.export_data(save=True)
    print("Umbriel-like: amostras =", len(df_ul), " min/max flux_norm =", float(df_ul.flux_norm.min()),
          float(df_ul.flux_norm.max()))


# =============================================================================
# Execução direta (exemplo mínimo)
# =============================================================================

if __name__ == "__main__":
    # Exemplo mínimo de uso "out of the box"
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4_000.0,
        diameter_km=1_200.0,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        random_seed=42,
    )
    df = sim.simulate()
    png = sim.plot_curve(save=True, show=False)
    dat_df, dat_path = sim.export_data(save=True)
    print("Arquivo de dados:", dat_path)
    print("Arquivo da figura:", png)

    # Rodar os testes extras com Umbriel e Chariklo
    testes_extras()
```

- Adicionei integração temporal intra-exposição e suavização por fonte estendida:
  - Novos parâmetros em `SyntheticLightCurveSimulator`: `subsamples_per_exposure` e `star_angular_mas`.
  - Integração: média de `T_total` em subamostras dentro da exposição.
  - Estrela finita: convolução boxcar com largura derivada do diâmetro angular e da velocidade.
- Novos métodos: `_boxcar_smooth` e `_star_window_samples`.
- Efeito esperado: transições dos anéis menos bruscas e mais realistas.

Exemplo de uso rápido:
```python
sim = SyntheticLightCurveSimulator(
    # ...
    subsamples_per_exposure=7,
    star_angular_mas=0.1,
)
```

```python
sim = SyntheticLightCurveSimulator(
    # ...
    subsamples_per_exposure=7,
    star_angular_mas=0.1,
)
```

---

**User**

@model_training/synthetic_curve/simulate_curve.py aplique as modificações anteriores no teste de umbriel-like com aneis com valores adequados

---

**Cursor**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simulador modular de curvas de luz de ocultações estelares.

Este arquivo reorganiza o antigo script monolítico em classes e funções
coesas, seguindo PEP 8 e boas práticas de programação científica.

Principais componentes:
- Física de Fresnel (difração em bordas "knife-edge" e faixa opaca)
- Geometria do evento (linha do tempo e coordenada ao longo da corda)
- Modelo de ruído (Poisson, leitura, cintilação multiplicativa)
- Normalização "pós-fotometria" (baseline ~ 1)
- Orquestração via uma classe principal de fácil uso

Bibliotecas: numpy, pandas, matplotlib (SciPy é opcional; usado se disponível).

CHANGES (alterações em relação ao código anterior):
- Removidos trechos experimentais, prints soltos e globais redundantes
  (motivo: clareza, reprodutibilidade e manutenibilidade).
- Unidades explicitadas (km, s, nm) e conversões centralizadas
  (motivo: reduzir erros por mistura de unidades).
- Difração de Fresnel isolada em funções puras com fallback sem SciPy
  (motivo: manter acurácia quando disponível e portabilidade quando não).
- Ruídos desacoplados da física (camada separada)
  (motivo: permitir trocar/ligar/desligar ruídos facilmente).
- Normalização robusta por quartis contíguos ou mediana
  (motivo: simular "pós-fotometria" com baseline estável).
- Função `testes_extras()` com cenários aproximados de Umbriel e Chariklo
  (motivo: exemplos práticos com corpos pequenos conhecidos).
"""

from __future__ import annotations

from typing import Optional, Tuple, List
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
# Utilidades e constantes
# =============================================================================

SPEED_OF_LIGHT_MS = 299_792_458.0  # m/s (não é usada diretamente, mantida por referência)
NM_TO_KM = 1e-12  # 1 nm = 1e-12 km


def magnitude_to_relative_flux(magnitude: float) -> float:
    """
    Converte magnitude aparente em fluxo relativo (sem calibração absoluta).

    Equação fotométrica padrão:
        F ∝ 10^(-0.4 m)
    """
    return 10.0 ** (-0.4 * float(magnitude))


def normalize_flux_top_quartiles(flux: np.ndarray) -> np.ndarray:
    """
    Normaliza o fluxo dividindo pelo baseline estimado como a média das duas
    maiores médias entre 4 segmentos contíguos (quartis em tempo).

    - Razoável para "pós-fotometria": baseline ~ 1 fora da ocultação.
    - Fallbacks garantem retorno mesmo em séries curtas.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return flux
    if valid.size < 4:
        baseline = float(np.mean(valid))
        baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
        return flux / baseline
    segments = np.array_split(valid, 4)
    means = [float(np.mean(s)) for s in segments if s.size > 0 and np.isfinite(np.mean(s))]
    if len(means) == 0:
        baseline = float(np.median(valid))
    else:
        order = np.argsort(means)
        top = [means[order[-1]]]
        if len(means) >= 2:
            top.append(means[order[-2]])
        baseline = float(np.mean(top))
    if not np.isfinite(baseline) or baseline <= 0:
        baseline = float(np.median(valid))
        if not np.isfinite(baseline) or baseline <= 0:
            return flux
    return flux / baseline


# =============================================================================
# Física de Fresnel (difração)
# =============================================================================

class FresnelPhysics:
    """
    Funções para cálculo de escala de Fresnel e transmitâncias difrativas.
    """

    @staticmethod
    def fresnel_scale_km(distance_km: float, wavelength_nm: float) -> float:
        """
        F = sqrt(lambda * D / 2), com lambda em km e D em km.
        """
        lambda_km = float(wavelength_nm) * NM_TO_KM
        D = float(distance_km)
        return math.sqrt(max(lambda_km * D / 2.0, 1e-30))

    @staticmethod
    def fresnel_CS(u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrais de Fresnel (C, S) com SciPy se disponível; caso contrário,
        usa aproximações assintóticas/séries adequadas a fins educacionais.
        """
        try:
            from scipy.special import fresnel as _scipy_fresnel  # type: ignore
            # A escala do argumento varia entre convenções; adotamos um fator
            # para obter bom acordo qualitativo.
            C, S = _scipy_fresnel(u * math.sqrt(2.0 / math.pi))
            return C, S
        except Exception:
            pass

        # Fallback aproximado: bom o suficiente didaticamente
        x = np.asarray(u, dtype=float)
        ax = np.abs(x)
        C = np.zeros_like(x)
        S = np.zeros_like(x)

        small = ax <= 1.5
        if np.any(small):
            z = x[small]
            # Séries truncadas (educacional; não metrológico)
            C[small] = (z - (math.pi**2) * (z**5) / 40.0) / math.sqrt(2.0 * math.pi)
            S[small] = ((math.pi) * (z**3) / 6.0 - (math.pi**3) * (z**7) / 336.0) / math.sqrt(
                2.0 * math.pi
            )

        large = ~small
        if np.any(large):
            z = x[large]
            t = math.pi * z * z / 2.0
            f = 1.0 / (math.pi * np.abs(z))
            c = 0.5 + f * np.sin(t) - (f**2) * np.cos(t)
            s = 0.5 - f * np.cos(t) - (f**2) * np.sin(t)
            c = np.where(z >= 0, c, -c)
            s = np.where(z >= 0, s, -s)
            C[large] = c
            S[large] = s

        return C, S

    @staticmethod
    def knife_edge_transmission(x_km: np.ndarray, edge_pos_km: float,
                                distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Transmitância de difração para uma borda "knife-edge".

        I(u) = 0.5 [ (C(u) + 0.5)^2 + (S(u) + 0.5)^2 ],
        onde u = (x - x_edge) / F e F é a escala de Fresnel.
        """
        F = FresnelPhysics.fresnel_scale_km(distance_km, wavelength_nm)
        u = (x_km - edge_pos_km) / max(F, 1e-12)
        C, S = FresnelPhysics.fresnel_CS(u)
        I = 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)
        return np.clip(I, 0.0, 1.0)

    @staticmethod
    def opaque_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                  distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa opaca: combinação correta de duas bordas (imersão e emersão).

        A transmitância de uma borda "knife-edge" cresce de ~0 (à esquerda) para ~1 (à direita).
        Para representar uma faixa opaca (região central escura), a combinação física
        desejada é:
            T(x) ≈ (1 - T_edge(x, x1)) + T_edge(x, x2)
        Isto produz T ~ 1 fora da faixa e T ~ 0 entre x1 e x2, com as franjas
        de difração aparecendo nas vizinhanças das bordas.
        """
        half = 0.5 * float(width_km)
        x1 = float(center_km) - half
        x2 = float(center_km) + half
        T1 = FresnelPhysics.knife_edge_transmission(x_km, x1, distance_km, wavelength_nm)
        T2 = FresnelPhysics.knife_edge_transmission(x_km, x2, distance_km, wavelength_nm)
        T = (1.0 - T1) + T2
        # Permite leve overshoot por difração; ajuste se necessário
        return np.clip(T, 0.0, 1.2)

    @staticmethod
    def partial_strip_transmission(x_km: np.ndarray, center_km: float, width_km: float,
                                   opacity: float, distance_km: float, wavelength_nm: float) -> np.ndarray:
        """
        Faixa parcialmente opaca (anéis):
        T_partial = 1 - opacity * (1 - T_opaque)
        """
        T_opaque = FresnelPhysics.opaque_strip_transmission(
            x_km, center_km, width_km, distance_km, wavelength_nm
        )
        return 1.0 - float(opacity) * (1.0 - T_opaque)


# =============================================================================
# Modelo de ruído
# =============================================================================

class NoiseModel:
    """
    Aplica ruídos atmosféricos e instrumentais ao fluxo ideal.

    Esta versão inclui:
    - Céu de fundo (Poisson aditivo, independente da estrela)
    - Offset/bias do detector
    - Subtração de fundo com erro (pode gerar valores negativos)
    - Cintilação multiplicativa atuando apenas no termo da estrela
    """

    def __init__(self, seeing_arcsec: float = 1.0, exposure_time_s: float = 0.1,
                 readout_sigma_counts: float = 20.0, gain_counts_per_flux: float = 1e9,
                 sky_bg_rate_counts_per_s: float = 300.0, bias_offset_counts: float = 100.0,
                 subtract_background: bool = True, bg_subtract_noise_frac: float = 0.05,
                 allow_negative: bool = True,
                 rng: Optional[np.random.Generator] = None) -> None:
        self.seeing_arcsec = float(seeing_arcsec)
        self.exposure_time_s = float(exposure_time_s)
        self.readout_sigma_counts = float(readout_sigma_counts)
        self.gain_counts_per_flux = float(gain_counts_per_flux)
        self.sky_bg_rate_counts_per_s = float(sky_bg_rate_counts_per_s)
        self.bias_offset_counts = float(bias_offset_counts)
        self.subtract_background = bool(subtract_background)
        self.bg_subtract_noise_frac = float(bg_subtract_noise_frac)
        self.allow_negative = bool(allow_negative)
        self.rng = rng if rng is not None else np.random.default_rng()

    def apply(self, expected_relative_flux: np.ndarray) -> np.ndarray:
        """
        Aplica:
        - Poisson da estrela (após ganho)
        - Poisson do céu de fundo
        - Ruído de leitura gaussiano
        - Cintilação (lognormal) atuando na estrela
        - Subtração de fundo com erro relativo controlado
        """
        expected = np.clip(np.asarray(expected_relative_flux, dtype=float), 0.0, None)

        # Contagens esperadas da estrela
        lam_star = expected * self.gain_counts_per_flux * self.exposure_time_s
        lam_star = np.clip(lam_star, 0, 1e12)

        # Poisson da estrela
        counts_star = self.rng.poisson(lam_star)

        # Céu de fundo (Poisson) — independente da estrela
        lam_bg = self.sky_bg_rate_counts_per_s * self.exposure_time_s
        counts_bg = self.rng.poisson(lam_bg * np.ones_like(counts_star))

        # Ruído de leitura (gaussiano)
        read = self.rng.normal(0.0, self.readout_sigma_counts, size=counts_star.size)

        # Cintilação (lognormal): pior para seeing ruim e diminui com t^{-1/2}
        # Fator menor para evitar modulações multiplicativas exageradas.
        sigma_ln = max(
            0.001,
            0.005 * (self.seeing_arcsec / 1.0) * (0.1 / max(self.exposure_time_s, 1e-3)) ** 0.5
        )
        scint = np.exp(self.rng.normal(0.0, sigma_ln, size=counts_star.size))

        # Sinal total (contagens)
        total_counts = counts_star * scint + counts_bg + read + self.bias_offset_counts

        # Subtração de fundo estimado (com erro relativo)
        if self.subtract_background:
            est_bg = lam_bg + self.bias_offset_counts
            est_bg_vec = est_bg * (1.0 + self.rng.normal(0.0, self.bg_subtract_noise_frac, size=counts_star.size))
            total_counts = total_counts - est_bg_vec

        # Converte para "fluxo relativo"
        flux = total_counts / (self.gain_counts_per_flux * self.exposure_time_s)

        if not self.allow_negative:
            flux = np.clip(flux, 0.0, None)
        return flux


# =============================================================================
# Simulador principal
# =============================================================================

class SyntheticLightCurveSimulator:
    """
    Simulador de curvas de luz sintéticas para ocultações estelares.

    Parâmetros
    ----------
    mag_star : float
        Magnitude aparente da estrela (escala relativa).
    distance_km : float
        Distância observador–corpo (km), usada na escala de Fresnel.
    diameter_km : float
        Diâmetro projetado do corpo (km) ao longo da corda.
    velocity_kms : float
        Velocidade relativa do evento (km/s).
    exposure_time_s : float
        Tempo de exposição por amostra (s).
    total_duration_s : Optional[float]
        Duração total da simulação (s). Se None, é inferida com margem.
    wavelength_nm : float
        Comprimento de onda efetivo (nm), p.ex. 550 nm ~ banda V.
    seeing_arcsec : float
        Seeing (arcsec), controla a cintilação.
    rings : Optional[List[Tuple[float, float, float]]]
        Lista de anéis como (offset_km, width_km, opacity). Opacity em [0,1].
    satellites : Optional[List[Tuple[float, float]]]
        Lista de satélites como (offset_km, diameter_km).
    normalize_method : str
        "top_quartiles" (default) ou "median".
    random_seed : Optional[int]
        Semente para reprodutibilidade dos ruídos.
    """

    def __init__(
        self,
        mag_star: float = 12.0,
        distance_km: float = 4_000.0,
        diameter_km: float = 1_200.0,
        velocity_kms: float = 20.0,
        exposure_time_s: float = 0.1,
        total_duration_s: Optional[float] = None,
        wavelength_nm: float = 550.0,
        seeing_arcsec: float = 1.0,
        rings: Optional[List[Tuple[float, float, float]]] = None,
        satellites: Optional[List[Tuple[float, float]]] = None,
        normalize_method: str = "top_quartiles",
        random_seed: Optional[int] = None,
        subsamples_per_exposure: int = 1,   # integração temporal intra-exposição
        star_angular_mas: float = 0.0,      # diâmetro angular da estrela (mas)
    ) -> None:
        self.mag_star = float(mag_star)
        self.distance_km = float(distance_km)
        self.diameter_km = float(diameter_km)
        self.velocity_kms = float(velocity_kms)
        self.exposure_time_s = float(exposure_time_s)
        self.total_duration_s = float(total_duration_s) if total_duration_s is not None else None
        self.wavelength_nm = float(wavelength_nm)
        self.seeing_arcsec = float(seeing_arcsec)
        self.rings = rings if rings is not None else []
        self.satellites = satellites if satellites is not None else []
        self.normalize_method = normalize_method
        self.subsamples_per_exposure = int(subsamples_per_exposure)
        self.star_angular_mas = float(star_angular_mas)

        self.rng = np.random.default_rng(random_seed)
        self.noise = NoiseModel(
            seeing_arcsec=self.seeing_arcsec,
            exposure_time_s=self.exposure_time_s,
            rng=self.rng,
        )

        # Saídas
        self.time_s: Optional[np.ndarray] = None
        self.flux: Optional[np.ndarray] = None
        self.flux_norm: Optional[np.ndarray] = None

        # Diretórios de saída
        self.base_out = os.path.join(os.path.dirname(__file__), "output")
        self.curves_out = os.path.join(self.base_out, "curves")
        self._ensure_dirs()

    def simulate(self) -> pd.DataFrame:
        """
        Executa a simulação completa:
        - Constrói tempo e coordenada ao longo da corda
        - Calcula transmitância difrativa: corpo × anéis × satélites
        - Converte magnitude em fluxo relativo e aplica transmitância
        - Aplica ruídos (Poisson, leitura, cintilação)
        - Normaliza o fluxo
        """
        t, x = self._build_time_and_chord()
        t0 = 0.5 * (t[0] + t[-1])
        dt_s = t[1] - t[0] if len(t) > 1 else self.exposure_time_s

        def compute_T_total_for_x(xx: np.ndarray) -> np.ndarray:
            T_body = FresnelPhysics.opaque_strip_transmission(
                xx, center_km=0.0, width_km=self.diameter_km,
                distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
            )
            T_rings = np.ones_like(T_body)
            for (offset_km, width_km, opacity) in self.rings:
                T_rings *= FresnelPhysics.partial_strip_transmission(
                    xx, center_km=float(offset_km), width_km=float(width_km), opacity=float(opacity),
                    distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
                )
            T_sats = np.ones_like(T_body)
            for (offset_km, diameter_km) in self.satellites:
                T_sats *= FresnelPhysics.opaque_strip_transmission(
                    xx, center_km=float(offset_km), width_km=float(diameter_km),
                    distance_km=self.distance_km, wavelength_nm=self.wavelength_nm
                )
            return np.clip(T_body * T_rings * T_sats, 0.0, 1.0)

        # Integração temporal intra-exposição
        if self.subsamples_per_exposure > 1:
            shifts = np.linspace(-0.5 * self.exposure_time_s,
                                 +0.5 * self.exposure_time_s,
                                 self.subsamples_per_exposure)
            acc = 0.0
            for s in shifts:
                x_s = (t + s - t0) * self.velocity_kms
                acc += compute_T_total_for_x(x_s)
            T_total = acc / float(self.subsamples_per_exposure)
        else:
            T_total = compute_T_total_for_x(x)

        # Suavização por fonte estendida (estrela com diâmetro finito)
        win = self._star_window_samples(dt_s)
        if win > 1:
            T_total = self._boxcar_smooth(T_total, win)

        # Fluxo relativo esperado (sem ruído)
        base_flux = magnitude_to_relative_flux(self.mag_star)
        expected_rel_flux = base_flux * T_total

        # Ruído
        noisy_flux = self.noise.apply(expected_rel_flux)

        # Normalização
        if self.normalize_method == "median":
            baseline = float(np.median(noisy_flux[np.isfinite(noisy_flux)]))
            baseline = baseline if np.isfinite(baseline) and baseline > 0 else 1.0
            flux_norm = noisy_flux / baseline
        else:
            flux_norm = normalize_flux_top_quartiles(noisy_flux)

        # Armazena e retorna
        self.time_s = t
        self.flux = noisy_flux
        self.flux_norm = flux_norm
        return pd.DataFrame({"time_s": t, "flux": noisy_flux, "flux_norm": flux_norm})

    def plot_curve(self, save: bool = True, show: bool = False, title: Optional[str] = None) -> str:
        """
        Plota a curva normalizada. Retorna o caminho do PNG salvo (string)
        se `save=True`, caso contrário retorna string vazia.
        """
        self._require_simulation()
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(self.time_s, self.flux_norm, "k.-", ms=3, lw=0.8, label="Fluxo normalizado")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Fluxo normalizado [adim.]")
        band = f"{int(round(self.wavelength_nm))} nm"
        ttl = title if title else f"Curva sintética com difração e seeing — {band}"
        ax.set_title(ttl)
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        png_path = ""
        if save:
            png_path = self._next_curve_png_path()
            fig.savefig(png_path, dpi=180)
        if show:
            plt.show()
        plt.close(fig)
        return png_path

    def export_data(self, save: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Exporta os dados simulados para um .dat numerado em output/.
        Retorna (DataFrame, caminho_do_arquivo_ou_string_vazia).
        """
        self._require_simulation()
        df = pd.DataFrame({"time_s": self.time_s, "flux": self.flux, "flux_norm": self.flux_norm})
        dat_path = ""
        if save:
            dat_path = self._next_dat_path()
            df.to_csv(dat_path, sep=" ", index=False, header=True, float_format="%.8f")
        return df, dat_path

    # -------------------------- helpers internos -----------------------------
    def _build_time_and_chord(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.total_duration_s is None:
            cross_time = self.diameter_km / max(self.velocity_kms, 1e-6)
            total_time = cross_time * 3.0  # margem: 1x antes e 1x depois
        else:
            total_time = self.total_duration_s
        n_steps = max(2, int(math.ceil(total_time / self.exposure_time_s)))
        t = np.linspace(0.0, total_time, n_steps, dtype=float)
        t0 = 0.5 * (t[0] + t[-1])
        x = (t - t0) * self.velocity_kms  # km
        return t, x

    def _ensure_dirs(self) -> None:
        os.makedirs(self.base_out, exist_ok=True)
        os.makedirs(self.curves_out, exist_ok=True)

    def _next_index(self) -> int:
        existing = glob.glob(os.path.join(self.base_out, "curva_sintetica_*.dat"))
        idx = 1
        for path in existing:
            try:
                name = os.path.splitext(os.path.basename(path))[0]
                n = int(name.split("_")[-1])
                idx = max(idx, n + 1)
            except Exception:
                continue
        return idx

    def _next_dat_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.base_out, f"curva_sintetica_{idx}.dat")

    def _next_curve_png_path(self) -> str:
        idx = self._next_index()
        return os.path.join(self.curves_out, f"curva_sintetica_{idx}.png")

    def _require_simulation(self) -> None:
        if self.time_s is None or self.flux is None or self.flux_norm is None:
            raise RuntimeError("Simulação ainda não executada. Chame simulate() antes.")

    # ---------------------- suavizações físicas opcionais ---------------------
    def _boxcar_smooth(self, y: np.ndarray, window_samples: int) -> np.ndarray:
        """
        Convolução boxcar (média móvel) para simular fonte estendida.
        """
        if window_samples <= 1:
            return y
        k = np.ones(int(window_samples), dtype=float)
        k /= k.sum()
        return np.convolve(y, k, mode="same")

    def _star_window_samples(self, dt_s: float) -> int:
        """
        Converte o diâmetro angular da estrela (mas) em largura temporal (amostras)
        para um kernel boxcar simples.
        """
        if self.star_angular_mas <= 0:
            return 1
        theta_rad = self.star_angular_mas * (np.pi / (648000.0 * 1000.0))  # mas -> rad
        star_proj_km = self.distance_km * theta_rad                         # km
        dx_km = self.velocity_kms * max(dt_s, 1e-12)                       # km por amostra
        n = int(round(star_proj_km / max(dx_km, 1e-9)))
        return max(n, 1)


# =============================================================================
# Testes extras com corpos pequenos (Umbriel e Chariklo)
# =============================================================================

def testes_extras() -> None:
    """
    Executa dois cenários de teste:
    1) Umbriel (satélite de Urano) — sem anéis
    2) Chariklo (Centauro) — com anéis C1R e C2R (parâmetros aproximados)

    Observações:
    - Valores aproximados (ordem de grandeza) para fins didáticos.
    - Distâncias geocêntricas típicas: Urano ~ 2.9e9 km, Chariklo ~ 2.1e9 km.
    - Velocidades típicas de sombra ~ 20–25 km/s.
    - Parâmetros dos anéis de Chariklo (Braga-Ribas+2014):
        - Raios ~ 391 km e 405 km; larguras ~ 7 km e 3 km;
          profundidades óticas τ ~ 0.4 e 0.06 → opacidade ~ 1 - e^{-τ}.
      Para uma ocultação equatorial idealizada, modelamos cada anel por duas faixas
      simétricas (+/- raio) com a mesma largura e opacidade.
    """
    # ------------------------------- Umbriel ---------------------------------
    umbriel = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,        # ~ distância de Urano à Terra (aprox.)
        diameter_km=1169.0,       # diâmetro de Umbriel ~ 1169 km
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        normalize_method="top_quartiles",
        random_seed=123,
    )
    df_u = umbriel.simulate()
    umbriel.plot_curve(save=True, show=False, title="Umbriel — V~550 nm")
    umbriel.export_data(save=True)

    # ------------------------------ Chariklo ---------------------------------
    # Parâmetros aproximados dos anéis (C1R e C2R)
    r1_km, w1_km, tau1 = 391.0, 7.0, 0.4
    r2_km, w2_km, tau2 = 405.0, 3.0, 0.06
    op1 = 1.0 - math.exp(-tau1)
    op2 = 1.0 - math.exp(-tau2)

    rings_chariklo: List[Tuple[float, float, float]] = [
        (+r1_km, w1_km, op1),
        (-r1_km, w1_km, op1),
        (+r2_km, w2_km, op2),
        (-r2_km, w2_km, op2),
    ]

    max_r = max(r1_km, r2_km)
    margin_km = 20.0  # folga
    half_span_km = max_r + 0.5 * 250.0 + margin_km  # 250.0 é o diameter_km usado
    total_duration_s = 2.0 * half_span_km / 25.0 

    chariklo = SyntheticLightCurveSimulator(
        mag_star=13.0,
        distance_km=2.1e9,        # Chariklo típico ~ 15 AU (aprox.)
        diameter_km=250.0,        # diâmetro efetivo do corpo (aprox. esfera equiv.)
        velocity_kms=25.0,
        exposure_time_s=0.1,
        wavelength_nm=650.0,      # banda R aproximada
        seeing_arcsec=1.2,
        rings=rings_chariklo,
        satellites=[],            # sem satélites aqui
        normalize_method="top_quartiles",
        total_duration_s=1000,
        random_seed=321,
    )
    df_c = chariklo.simulate()
    chariklo.plot_curve(save=True, show=False, title="Chariklo com anéis — R~650 nm")
    chariklo.export_data(save=True)

    # Prints simples para feedback (como um "junior" faria)
    print("Umbriel: amostras =", len(df_u), " min/max flux_norm =", float(df_u.flux_norm.min()),
          float(df_u.flux_norm.max()))
    print("Chariklo: amostras =", len(df_c), " min/max flux_norm =", float(df_c.flux_norm.min()),
          float(df_c.flux_norm.max()))

    # --------------------- Corpo fictício tipo "Umbriel com anéis" ---------------------
    # Ideia: corpo com diâmetro ~Umbriel, porém com um sistema de anéis "grande"
    # escalonado pela proporção típica de Saturno (raios de anéis ~ 1.7–2.4 vezes o raio do planeta,
    # com larguras fracionárias significativas). Usamos três anéis com opacidades relativamente altas,
    # para produzir quedas fortes e estruturas visíveis.
    umb_like_diam_km = 1169.0
    umb_like_rad_km = 0.5 * umb_like_diam_km
    # Raios proporcionais (em múltiplos do raio do corpo)
    rC = 1.30 * umb_like_rad_km   # anel interno (análog. C)
    rB = 1.70 * umb_like_rad_km   # anel intermediário (análog. B)
    rA = 2.30 * umb_like_rad_km   # anel externo (análog. A)
    # Larguras proporcionais ao raio do corpo (valores inspirados nas frações em Saturno)
    wC = 0.25 * umb_like_rad_km
    wB = 0.44 * umb_like_rad_km
    wA = 0.30 * umb_like_rad_km
    # Profundidades óticas aproximadas (mais opacos para quedas fortes)
    tauC, tauB, tauA = 0.3, 0.9, 0.6
    opC = 1.0 - math.exp(-tauC)
    opB = 1.0 - math.exp(-tauB)
    opA = 1.0 - math.exp(-tauA)

    rings_umb_like: List[Tuple[float, float, float]] = [
        (+rC, wC, opC), (-rC, wC, opC),
        (+rB, wB, opB), (-rB, wB, opB),
        (+rA, wA, opA), (-rA, wA, opA),
    ]

    # Janela temporal suficiente para cobrir o anel externo
    outer_r = max(rA, rB, rC)
    margin_km = 100.0
    half_span_km = outer_r + 0.5 * umb_like_diam_km + margin_km
    total_duration_s = 2.0 * half_span_km / 20.0  # vel = 20 km/s

    umbriel_like_with_rings = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=2.9e9,         # mesma ordem de Umbriel/Urano
        diameter_km=umb_like_diam_km,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.1,         # leve aumento de seeing ajuda a suavizar
        rings=rings_umb_like,
        satellites=[],
        normalize_method="top_quartiles",
        total_duration_s=total_duration_s,
        random_seed=777,
        subsamples_per_exposure=7, # integração temporal intra-exposição
        star_angular_mas=0.12,     # estrela com diâmetro finito (~0.12 mas)
    )
    df_ul = umbriel_like_with_rings.simulate()
    umbriel_like_with_rings.plot_curve(save=True, show=False, title="Umbriel-like com anéis — V~550 nm")
    umbriel_like_with_rings.export_data(save=True)
    print("Umbriel-like: amostras =", len(df_ul), " min/max flux_norm =", float(df_ul.flux_norm.min()),
          float(df_ul.flux_norm.max()))


# =============================================================================
# Execução direta (exemplo mínimo)
# =============================================================================

if __name__ == "__main__":
    # Exemplo mínimo de uso "out of the box"
    sim = SyntheticLightCurveSimulator(
        mag_star=12.5,
        distance_km=4_000.0,
        diameter_km=1_200.0,
        velocity_kms=20.0,
        exposure_time_s=0.1,
        wavelength_nm=550.0,
        seeing_arcsec=1.0,
        rings=[],
        satellites=[],
        random_seed=42,
    )
    df = sim.simulate()
    png = sim.plot_curve(save=True, show=False)
    dat_df, dat_path = sim.export_data(save=True)
    print("Arquivo de dados:", dat_path)
    print("Arquivo da figura:", png)

    # Rodar os testes extras com Umbriel e Chariklo
    testes_extras()
```

- Ajustei o cenário “Umbriel-like com anéis” em `testes_extras()` para usar as novas opções de realismo:
  - `subsamples_per_exposure=7` para integrar dentro da exposição.
  - `star_angular_mas=0.12` para simular estrela finita.
  - `seeing_arcsec=1.1` para dar leve suavização adicional.
- Efeito esperado: transições dos anéis menos retangulares, com bordas arredondadas e mais próximas de um caso observacional.

