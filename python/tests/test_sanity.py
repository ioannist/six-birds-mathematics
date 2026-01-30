from sbt_math.utils import ping


def test_ping() -> None:
    assert ping() == "ok"


def test_imports() -> None:
    import numpy  # noqa: F401
    import mpmath  # noqa: F401
    import sympy  # noqa: F401
