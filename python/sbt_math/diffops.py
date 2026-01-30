"""Finite-difference operators with periodic boundary conditions."""

from __future__ import annotations

import numpy as np


def shift(f: np.ndarray, h: float) -> np.ndarray:
    """Shift by one grid step along the last axis using periodic wrap.

    For samples f(x_i) with spacing h, this applies T_h via np.roll(..., -1, axis=-1).
    """
    _ = float(h)
    return np.roll(np.asarray(f), -1, axis=-1)


def delta(f: np.ndarray, h: float) -> np.ndarray:
    """Forward difference: Δ_h f = T_h f - f."""
    return shift(f, h) - np.asarray(f)


def scaled_delta(f: np.ndarray, h: float) -> np.ndarray:
    """Scaled forward difference: δ_h f = (T_h f - f) / h."""
    h_val = float(h)
    if h_val == 0.0:
        raise ValueError("h must be nonzero")
    return delta(f, h_val) / h_val


def leibniz_identity_residual(f: np.ndarray, g: np.ndarray, h: float) -> np.ndarray:
    """Residual of the discrete Leibniz identity for δ_h.

    δ_h(fg) - (δ_h f) g - f (δ_h g) - h (δ_h f)(δ_h g)
    """
    f_arr = np.asarray(f)
    g_arr = np.asarray(g)
    df = scaled_delta(f_arr, h)
    dg = scaled_delta(g_arr, h)
    return scaled_delta(f_arr * g_arr, h) - df * g_arr - f_arr * dg - float(h) * df * dg
