"""Tests for the transformation module - DataCleaner and DataTransformer."""

import pytest
from transformation.cleaner import DataCleaner
from transformation.transformer import DataTransformer


@pytest.fixture
def cleaner():
    return DataCleaner()


@pytest.fixture
def transformer():
    return DataTransformer()


class TestDataCleaner:
    """Test suite for DataCleaner."""

    def test_currency_parsing_rupee_symbol(self, cleaner):
        """Indian rupee symbol with commas is parsed correctly."""
        assert cleaner.parse_currency("₹1,299") == 1299.00
        assert cleaner.parse_currency("₹10,999") == 10999.00
        assert cleaner.parse_currency("₹999") == 999.00

    def test_currency_parsing_rs_prefix(self, cleaner):
        """Rs. prefix format is parsed correctly."""
        assert cleaner.parse_currency("Rs. 500") == 500.00
        assert cleaner.parse_currency("Rs. 1,500") == 1500.00
        assert cleaner.parse_currency("Rs. 25,000") == 25000.00

    def test_currency_parsing_plain_number(self, cleaner):
        """Plain numeric strings are parsed correctly."""
        assert cleaner.parse_currency("1299") == 1299.00
        assert cleaner.parse_currency("1299.50") == 1299.50

    def test_currency_parsing_already_numeric(self, cleaner):
        """Already-numeric values pass through unchanged."""
        assert cleaner.parse_currency(1299) == 1299.00
        assert cleaner.parse_currency(1299.50) == 1299.50

    def test_status_normalization(self, cleaner):
        """Status strings are normalized to uppercase."""
        assert cleaner.normalize_status("completed") == "COMPLETED"
        assert cleaner.normalize_status("PENDING") == "PENDING"
        assert cleaner.normalize_status("  Shipped  ") == "SHIPPED"
        assert cleaner.normalize_status("cancelled") == "CANCELLED"
        assert cleaner.normalize_status("processing") == "PROCESSING"

    def test_whitespace_stripping(self, cleaner):
        """Leading and trailing whitespace is removed."""
        assert cleaner.strip_whitespace("  hello  ") == "hello"
        assert cleaner.strip_whitespace("world") == "world"
        assert cleaner.strip_whitespace("  spaces  everywhere  ") == "spaces  everywhere"
        assert cleaner.strip_whitespace("\t\ttabs\t\t") == "tabs"
        assert cleaner.strip_whitespace("\n newlines \n") == "newlines"

    def test_deduplication(self, cleaner):
        """Duplicate records are removed, keeping the first occurrence."""
        records = [
            {"id": "A", "value": 1},
            {"id": "B", "value": 2},
            {"id": "A", "value": 1},  # duplicate
            {"id": "C", "value": 3},
            {"id": "B", "value": 2},  # duplicate
        ]
        result = cleaner.deduplicate(records, key="id")
        assert len(result) == 3
        ids = [r["id"] for r in result]
        assert ids == ["A", "B", "C"]

    def test_deduplication_no_duplicates(self, cleaner):
        """Deduplication with no duplicates returns same list."""
        records = [
            {"id": "A", "value": 1},
            {"id": "B", "value": 2},
        ]
        result = cleaner.deduplicate(records, key="id")
        assert len(result) == 2

    def test_deduplication_empty_list(self, cleaner):
        """Deduplication on empty list returns empty list."""
        result = cleaner.deduplicate([], key="id")
        assert result == []


class TestDataTransformer:
    """Test suite for DataTransformer."""

    def test_subtotal_calculation(self, transformer):
        """Subtotal = quantity * unit_price - discount."""
        item = {
            "quantity": 3,
            "unit_price": 500.00,
            "discount": 50.00,
        }
        result = transformer.calculate_subtotal(item)
        # 3 * 500 - 50 = 1450
        assert result == 1450.00

    def test_subtotal_zero_discount(self, transformer):
        """Subtotal with zero discount is just quantity * unit_price."""
        item = {
            "quantity": 2,
            "unit_price": 750.00,
            "discount": 0.00,
        }
        result = transformer.calculate_subtotal(item)
        assert result == 1500.00

    def test_subtotal_single_item(self, transformer):
        """Subtotal for single item with no discount."""
        item = {
            "quantity": 1,
            "unit_price": 999.00,
            "discount": 0.00,
        }
        result = transformer.calculate_subtotal(item)
        assert result == 999.00

    def test_profit_calculation(self, transformer):
        """Profit = price - cost_price."""
        product = {
            "price": 1299.00,
            "cost_price": 800.00,
        }
        result = transformer.calculate_profit(product)
        assert result == 499.00

    def test_profit_calculation_zero_margin(self, transformer):
        """Profit is zero when price equals cost_price."""
        product = {
            "price": 500.00,
            "cost_price": 500.00,
        }
        result = transformer.calculate_profit(product)
        assert result == 0.00

    def test_profit_calculation_loss(self, transformer):
        """Negative profit when cost exceeds price."""
        product = {
            "price": 400.00,
            "cost_price": 500.00,
        }
        result = transformer.calculate_profit(product)
        assert result == -100.00

    def test_null_handling_defaults(self, transformer):
        """None values are replaced with sensible defaults."""
        record = {
            "name": None,
            "age": None,
            "email": None,
            "city": None,
            "rating": None,
        }
        defaults = {
            "name": "Unknown",
            "age": 0,
            "email": "N/A",
            "city": "N/A",
            "rating": 0.0,
        }
        result = transformer.apply_defaults(record, defaults)
        assert result["name"] == "Unknown"
        assert result["age"] == 0
        assert result["email"] == "N/A"
        assert result["city"] == "N/A"
        assert result["rating"] == 0.0

    def test_null_handling_preserves_values(self, transformer):
        """Non-None values are preserved when applying defaults."""
        record = {
            "name": "Alice",
            "age": 30,
            "email": None,
        }
        defaults = {
            "name": "Unknown",
            "age": 0,
            "email": "N/A",
        }
        result = transformer.apply_defaults(record, defaults)
        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["email"] == "N/A"

    def test_null_handling_no_nones(self, transformer):
        """Record with no None values is unchanged."""
        record = {
            "name": "Bob",
            "age": 25,
        }
        defaults = {"name": "Unknown", "age": 0}
        result = transformer.apply_defaults(record, defaults)
        assert result["name"] == "Bob"
        assert result["age"] == 25
