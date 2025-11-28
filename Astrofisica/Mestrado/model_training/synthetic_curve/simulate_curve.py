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