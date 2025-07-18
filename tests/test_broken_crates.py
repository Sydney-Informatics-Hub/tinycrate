import pytest

from tinycrate.tinycrate import TinyCrate, TinyCrateException


def test_invalid_crate(invalid_crates):
    with pytest.raises(TinyCrateException):
        tc = TinyCrate(invalid_crates["missing_types"])
        assert tc
