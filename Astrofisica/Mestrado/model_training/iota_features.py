#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Feature engineering inspirado nos critérios da IOTA para ocultações estelares.

Este módulo calcula métricas físicas utilizadas pela International Occultation
Timing Association (IOTA) para validação de eventos de ocultação, usando
apenas as séries temporais de tempo e fluxo (ou flux_normalized) da curva de luz.

Features produzidas:
  - IOTA_depth: profundidade do dip (baseline - flux_min)
  - IOTA_SNR_dip: signal-to-noise ratio da queda (depth / baseline_std)
  - IOTA_duration_s: duração da queda em segundos (maior run abaixo do baseline)
  - IOTA_n_frames_below_baseline: maior número de frames consecutivos abaixo do baseline
  - IOTA_baseline_std: desvio padrão do baseline (pontos >= baseline)
  - IOTA_flux_min: fluxo mínimo observado
  - IOTA_flux_min_over_baseline: razão flux_min / baseline
  - IOTA_chi2_constant: chi² do modelo constante (sem evento)
  - IOTA_chi2_square_well: chi² do modelo square well (poço retangular)
  - IOTA_chi2_ratio: chi2_constant / chi2_square_well ( > 1 indica que o dip explica melhor)

Decisões de engenharia:
  - Baseline = mediana(flux) para robustez a outliers.
  - baseline_std usando apenas pontos >= baseline (fora do dip).
  - Runs "abaixo do baseline" sem threshold agressivo para capturar dips rasos.
  - chi2 com sigma = max(MAD, eps); chi2_ratio limitada entre 0.1 e 10.
  - Curvas sem dip: depth=0, n_frames=0, duration_s=0, chi2_ratio ≈ 1.
"""

from __future__ import annotations

from typing import Optional, List, Tuple
import numpy as np


# -----------------------------------------------------------------------------
# Constantes (parâmetros de robustez)
# -----------------------------------------------------------------------------
# Epsilon para evitar divisão por zero em sigma e chi2_ratio
_EPS_SIGMA = 1e-10
# Limites para chi2_ratio (evitar valores extremos)
_CHI2_RATIO_MIN = 0.1
_CHI2_RATIO_MAX = 10.0
# Mínimo de pontos para considerar curva válida
_MIN_POINTS = 5


def _get_baseline(flux: np.ndarray, method: str = 'median') -> float:
    """
    Estima o fluxo de baseline (fora da ocultação).

    Motivação física: Em curvas normalizadas, o baseline é o nível de fluxo
    quando a estrela não está oculta. A mediana é robusta a dips e outliers.

    Fórmula: baseline = mediana(flux) para method='median'.

    Args:
        flux: Array 1D de fluxo (normalizado).
        method: 'median' (padrão) ou 'mean_above_median'.

    Returns:
        Escalar com o valor do baseline.
    """
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return np.nan
    if method == 'median':
        return float(np.median(valid))
    if method == 'mean_above_median':
        med = np.median(valid)
        above = valid[valid >= med]
        if above.size == 0:
            return float(med)
        return float(np.mean(above))
    return float(np.median(valid))


def _get_baseline_std(flux: np.ndarray, baseline: float) -> float:
    """
    Desvio padrão do baseline (apenas pontos >= baseline).

    Motivação física: Ruído fotométrico e cintilação caracterizam o baseline;
    excluir pontos no dip evita inflar o sigma.

    Fórmula: sigma_baseline = std(flux[flux >= baseline]). Se houver poucos
    pontos, fallback para std(flux).

    Args:
        flux: Array 1D de fluxo.
        baseline: Valor do baseline (ex.: mediana).

    Returns:
        Desvio padrão (escalar). Retorna std(flux) se nenhum ponto >= baseline.
    """
    flux = np.asarray(flux, dtype=float)
    mask = flux >= baseline
    if np.sum(mask) < 2:
        # Fallback: usar toda a série
        if len(flux) < 2:
            return _EPS_SIGMA
        return float(np.std(flux))
    return float(np.std(flux[mask]))


def _runs_below_baseline(flux: np.ndarray, baseline: float) -> List[Tuple[int, int]]:
    """
    Identifica runs consecutivos de índices onde flux[i] < baseline.

    Motivação física: Ocultações produzem um bloco contíguo de pontos abaixo
    do baseline; ruído tende a pontos isolados.

    Args:
        flux: Array 1D de fluxo.
        baseline: Valor do baseline.

    Returns:
        Lista de (start_idx, end_idx) exclusivo (end_idx não incluído no run).
        Ex.: [(2, 5), (10, 12)] significa pontos 2,3,4 e 10,11 abaixo do baseline.
    """
    flux = np.asarray(flux, dtype=float)
    below = flux < baseline
    n = len(below)
    runs: List[Tuple[int, int]] = []
    i = 0
    while i < n:
        if not below[i]:
            i += 1
            continue
        start = i
        while i < n and below[i]:
            i += 1
        runs.append((start, i))
    return runs


def _depth(flux: np.ndarray, baseline: float) -> float:
    """
    Profundidade do dip: baseline - min(flux).

    Motivação física: Em ocultações o fluxo cai; a profundidade é a queda
    em unidades de fluxo. Critério IOTA para magnitude do evento.

    Fórmula: depth = max(0, baseline - min(flux)).

    Args:
        flux: Array 1D de fluxo.
        baseline: Valor do baseline.

    Returns:
        depth >= 0.
    """
    flux_min = float(np.min(np.asarray(flux)[np.isfinite(flux)])) if np.any(np.isfinite(flux)) else np.nan
    if np.isnan(flux_min):
        return 0.0
    return float(max(0.0, baseline - flux_min))


def _snr_dip(depth: float, baseline_std: float) -> float:
    """
    Signal-to-noise ratio da queda: depth / sigma_baseline.

    Motivação física: IOTA exige que a queda seja significativa em relação
    ao ruído; SNR alto sugere evento real.

    Fórmula: SNR_dip = depth / baseline_std. Retorna 0 se baseline_std <= 0.

    Args:
        depth: Profundidade do dip (baseline - flux_min).
        baseline_std: Desvio padrão do baseline.

    Returns:
        SNR (>= 0) ou 0 se baseline_std inválido.
    """
    if baseline_std is None or baseline_std <= 0 or not np.isfinite(baseline_std):
        return 0.0
    if not np.isfinite(depth) or depth < 0:
        return 0.0
    return float(depth / baseline_std)


def _max_run_frames(flux: np.ndarray, baseline: float) -> int:
    """
    Comprimento do maior bloco consecutivo com flux < baseline.

    Motivação física: Ocultações reais têm vários frames consecutivos na queda;
    ruído tende a poucos pontos isolados.

    Args:
        flux: Array 1D de fluxo.
        baseline: Valor do baseline.

    Returns:
        Número de pontos do maior run (0 se não houver pontos abaixo).
    """
    runs = _runs_below_baseline(flux, baseline)
    if not runs:
        return 0
    return max(end - start for start, end in runs)


def _duration_seconds(
    time: np.ndarray,
    flux: np.ndarray,
    baseline: float,
) -> float:
    """
    Duração em segundos do maior run abaixo do baseline.

    Motivação física: Duração da ocultação ligada à geometria (tamanho do
    objeto, velocidade). Critério IOTA para consistência do evento.

    Args:
        time: Array 1D de tempos (mesmo tamanho que flux).
        flux: Array 1D de fluxo.
        baseline: Valor do baseline.

    Returns:
        time[end] - time[start] do run mais longo (0 se não houver dip).
    """
    runs = _runs_below_baseline(flux, baseline)
    if not runs:
        return 0.0
    time = np.asarray(time, dtype=float)
    best = max(runs, key=lambda r: r[1] - r[0])
    start_idx, end_idx = best
    if end_idx <= start_idx or end_idx > len(time):
        return 0.0
    return float(time[end_idx - 1] - time[start_idx])


def _chi2_constant(flux: np.ndarray, mu: float, sigma: float) -> float:
    """
    Chi² do modelo constante: soma (f_i - mu)^2 / sigma^2.

    Motivação física: Modelo "sem evento" (fluxo constante). Usado para
    comparar com o modelo square well.

    Fórmula: chi2_0 = sum_i (f_i - mu)^2 / sigma^2.

    Args:
        flux: Array 1D de fluxo.
        mu: Valor do modelo constante (ex.: mediana).
        sigma: Escala dos resíduos (ex.: MAD ou std); deve ser > 0.

    Returns:
        Chi² (soma dos quadrados dos resíduos normalizados).
    """
    flux = np.asarray(flux, dtype=float)
    sig = max(float(sigma), _EPS_SIGMA)
    resid = flux - mu
    return float(np.nansum(resid ** 2) / (sig ** 2))


def _chi2_square_well(
    flux: np.ndarray,
    baseline: float,
    run_start: int,
    run_end: int,
    sigma: float,
) -> float:
    """
    Chi² do modelo square well: nível baseline fora da janela, nível constante
    dentro da janela (média do flux na janela).

    Motivação física: Ocultação ideal é um "poço" retangular; este modelo
    compara quão bem esse formato explica os dados.

    Fórmula: predição = baseline fora de [run_start, run_end), e média(flux
    na janela) dentro; chi2_sw = sum_i (f_i - pred_i)^2 / sigma^2.

    Args:
        flux: Array 1D de fluxo.
        baseline: Nível fora do dip.
        run_start: Índice inicial do run (inclusivo).
        run_end: Índice final do run (exclusivo).
        sigma: Escala dos resíduos (deve ser > 0).

    Returns:
        Chi² do modelo square well.
    """
    flux = np.asarray(flux, dtype=float)
    n = len(flux)
    sig = max(float(sigma), _EPS_SIGMA)
    pred = np.full_like(flux, baseline)
    if run_start < run_end and run_end <= n:
        level_inside = float(np.nanmean(flux[run_start:run_end]))
        pred[run_start:run_end] = level_inside
    resid = flux - pred
    return float(np.nansum(resid ** 2) / (sig ** 2))


def _chi2_ratio(chi2_const: float, chi2_sw: float) -> float:
    """
    Razão chi2_constant / chi2_square_well. Valores > 1 indicam que o modelo
    com dip explica melhor os dados.

    Clamp entre _CHI2_RATIO_MIN e _CHI2_RATIO_MAX para evitar extremos.

    Args:
        chi2_const: Chi² do modelo constante.
        chi2_sw: Chi² do modelo square well.

    Returns:
        Razão limitada ao intervalo [0.1, 10].
    """
    if not np.isfinite(chi2_const) or not np.isfinite(chi2_sw):
        return 1.0
    if chi2_sw <= 0:
        return _CHI2_RATIO_MAX
    r = chi2_const / chi2_sw
    return float(np.clip(r, _CHI2_RATIO_MIN, _CHI2_RATIO_MAX))


def _mad(flux: np.ndarray) -> float:
    """Median Absolute Deviation: mediana(|flux - mediana(flux)|)."""
    flux = np.asarray(flux, dtype=float)
    valid = flux[np.isfinite(flux)]
    if valid.size == 0:
        return _EPS_SIGMA
    med = np.median(valid)
    return float(np.median(np.abs(valid - med)))


def compute_iota_features(curve: dict) -> Optional[dict]:
    """
    Calcula todas as features IOTA para uma curva de luz.

    Utiliza apenas as chaves 'time', 'flux' e/ou 'flux_normalized' do dicionário
    curve. Preferência por flux_normalized quando existir.

    Curvas inválidas (menos de 5 pontos ou time e flux com tamanhos diferentes)
    retornam None. Curvas sem dip retornam depth=0, n_frames=0, duration_s=0,
    chi2_square_well ≈ chi2_constant e chi2_ratio ≈ 1.

    Args:
        curve: Dicionário com 'time' (array), 'flux' (array) e opcionalmente
               'flux_normalized' (array). Formato típico do pipeline.

    Returns:
        Dicionário com as chaves:
          IOTA_depth, IOTA_SNR_dip, IOTA_duration_s, IOTA_n_frames_below_baseline,
          IOTA_baseline_std, IOTA_flux_min, IOTA_flux_min_over_baseline,
          IOTA_chi2_constant, IOTA_chi2_square_well, IOTA_chi2_ratio.
        Ou None se a curva for inválida.
    """
    flux = np.asarray(curve.get('flux_normalized', curve.get('flux', [])))
    time = np.asarray(curve.get('time', []))
    if len(flux) < _MIN_POINTS or len(time) != len(flux):
        return None
    flux = np.asarray(flux, dtype=float)
    time = np.asarray(time, dtype=float)
    if np.any(~np.isfinite(flux)):
        flux = np.nan_to_num(flux, nan=np.nanmedian(flux), posinf=np.nanmedian(flux), neginf=np.nanmedian(flux))

    baseline = _get_baseline(flux)
    baseline_std = _get_baseline_std(flux, baseline)
    depth = _depth(flux, baseline)
    n_frames = _max_run_frames(flux, baseline)
    duration_s = _duration_seconds(time, flux, baseline)
    flux_min = float(np.min(flux))
    if baseline > 0 and np.isfinite(baseline):
        flux_min_over_baseline = float(flux_min / baseline)
    else:
        flux_min_over_baseline = np.nan

    # Sigma robusto para chi² (MAD; escala ~ desvio padrão para normal)
    sigma = max(_mad(flux), _EPS_SIGMA)
    chi2_constant = _chi2_constant(flux, baseline, sigma)

    runs = _runs_below_baseline(flux, baseline)
    if runs:
        longest = max(runs, key=lambda r: r[1] - r[0])
        run_start, run_end = longest
        chi2_square_well = _chi2_square_well(flux, baseline, run_start, run_end, sigma)
    else:
        # Sem dip: modelo square well = constante
        chi2_square_well = chi2_constant
    chi2_ratio = _chi2_ratio(chi2_constant, chi2_square_well)

    return {
        'IOTA_depth': depth,
        'IOTA_SNR_dip': _snr_dip(depth, baseline_std),
        'IOTA_duration_s': duration_s,
        'IOTA_n_frames_below_baseline': n_frames,
        'IOTA_baseline_std': baseline_std,
        'IOTA_flux_min': flux_min,
        'IOTA_flux_min_over_baseline': flux_min_over_baseline,
        'IOTA_chi2_constant': chi2_constant,
        'IOTA_chi2_square_well': chi2_square_well,
        'IOTA_chi2_ratio': chi2_ratio,
    }


# Ordem fixa das colunas IOTA para consistência no dataset (usado por build_dataset)
IOTA_FEATURE_NAMES = [
    'IOTA_depth',
    'IOTA_SNR_dip',
    'IOTA_duration_s',
    'IOTA_n_frames_below_baseline',
    'IOTA_baseline_std',
    'IOTA_flux_min',
    'IOTA_flux_min_over_baseline',
    'IOTA_chi2_constant',
    'IOTA_chi2_square_well',
    'IOTA_chi2_ratio',
]
