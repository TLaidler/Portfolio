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

