import pytest

from pypika_tortoise.utils import validate


class TestValidate:
    def test_type_none_skips_validation(self):
        assert validate("anything", type=None) is None

    def test_type_match_passes(self):
        assert validate(1, type=int) is None

    def test_custom_exception_raised(self):
        with pytest.raises(TypeError, match="as is"):
            validate(1, exc=TypeError("as is"), type=str)

    def test_default_exception_raised(self):
        with pytest.raises(ValueError, match="Expected 1 to be <class 'str'>"):
            validate(1, type=str)
