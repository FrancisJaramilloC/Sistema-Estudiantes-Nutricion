"""
Tests for app.database — validates convert_decimals and table creation.
"""

from decimal import Decimal

from app.database import convert_decimals


class TestConvertDecimals:
    def test_decimal_to_int(self):
        result = convert_decimals(Decimal("42"))
        assert result == 42
        assert isinstance(result, int)

    def test_decimal_to_float(self):
        result = convert_decimals(Decimal("3.14"))
        assert result == 3.14
        assert isinstance(result, float)

    def test_list_of_decimals(self):
        result = convert_decimals([Decimal("1"), Decimal("2.5"), Decimal("3")])
        assert result == [1, 2.5, 3]
        assert isinstance(result[0], int)
        assert isinstance(result[1], float)

    def test_dict_with_decimals(self):
        data = {"a": Decimal("10"), "b": Decimal("20.5"), "c": "hola"}
        result = convert_decimals(data)
        assert result == {"a": 10, "b": 20.5, "c": "hola"}
        assert isinstance(result["a"], int)
        assert isinstance(result["b"], float)

    def test_nested_structure(self):
        data = {
            "outer": [
                {"inner_dec": Decimal("99.99")},
                {"inner_int": Decimal("7")},
            ]
        }
        result = convert_decimals(data)
        assert result["outer"][0]["inner_dec"] == 99.99
        assert result["outer"][1]["inner_int"] == 7

    def test_non_decimal_passthrough(self):
        assert convert_decimals("string") == "string"
        assert convert_decimals(42) == 42
        assert convert_decimals(None) is None
        assert convert_decimals(True) is True
