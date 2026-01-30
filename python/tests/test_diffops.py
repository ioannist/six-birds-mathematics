import numpy as np

from sbt_math.diffops import delta, leibniz_identity_residual, scaled_delta


def test_scaled_delta_matches_delta_over_h() -> None:
    rng = np.random.default_rng(0)
    f = rng.standard_normal(128)
    h = 0.25
    assert np.allclose(scaled_delta(f, h), delta(f, h) / h)


def test_leibniz_residual_near_zero() -> None:
    seeds = [0, 1, 2]
    shapes = [(128,), (8, 128)]
    hs = [1.0, 0.5, 0.1, 0.01]
    for seed in seeds:
        rng = np.random.default_rng(seed)
        for shape in shapes:
            f = rng.standard_normal(shape)
            g = rng.standard_normal(shape)
            for h in hs:
                res = leibniz_identity_residual(f, g, h)
                max_abs = np.max(np.abs(res))
                assert max_abs <= 1e-12
