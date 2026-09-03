"""Tests for the validation module - DataValidator."""

import pytest
from validation.validator import DataValidator


@pytest.fixture
def validator():
    return DataValidator()


@pytest.fixture
def valid_customers():
    return [
        {
            "customer_id": "CUST-001",
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice@example.com",
            "gender": "Female",
            "age": 32,
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "signup_date": "2024-01-15",
        },
        {
            "customer_id": "CUST-002",
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob@example.com",
            "gender": "Male",
            "age": 28,
            "city": "Delhi",
            "state": "Delhi",
            "country": "India",
            "signup_date": "2024-02-20",
        },
    ]


@pytest.fixture
def valid_products():
    return [
        {
            "product_id": "PROD-001",
            "product_name": "Wireless Mouse",
            "category_id": "CAT-ELEC",
            "subcategory": "Accessories",
            "brand": "TechBrand",
            "price": 1299.00,
            "cost_price": 800.00,
            "stock_quantity": 150,
            "rating": 4.5,
        },
    ]


@pytest.fixture
def valid_orders():
    return [
        {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "order_date": "2026-09-01",
            "order_status": "COMPLETED",
            "payment_status": "PAID",
            "payment_method": "UPI",
            "shipping_city": "Mumbai",
            "shipping_state": "Maharashtra",
            "total_amount": 1299.00,
            "discount_amount": 100.00,
            "tax_amount": 215.82,
        },
    ]


class TestDataValidator:
    """Test suite for DataValidator."""

    def test_valid_customers(self, validator, valid_customers):
        """Valid customer records pass validation."""
        results = validator.validate_customers(valid_customers)
        invalid = [r for r in results if not r["valid"]]
        assert len(invalid) == 0, f"Valid customers should pass: {invalid}"

    def test_missing_customer_id(self, validator):
        """Records without customer_id are flagged as invalid."""
        customers = [
            {
                "first_name": "Charlie",
                "last_name": "Brown",
                "email": "charlie@example.com",
            },
        ]
        results = validator.validate_customers(customers)
        invalid = [r for r in results if not r["valid"]]
        assert len(invalid) == 1, "Record without customer_id should be invalid"
        assert any("customer_id" in str(e).lower() for e in invalid[0].get("errors", []))

    def test_negative_price(self, validator, valid_products):
        """Negative prices are detected as invalid."""
        products = [
            {
                "product_id": "PROD-BAD",
                "product_name": "Invalid Product",
                "category_id": "CAT-ELEC",
                "subcategory": "Accessories",
                "brand": "TechBrand",
                "price": -500.00,
                "cost_price": 800.00,
                "stock_quantity": 10,
                "rating": 3.0,
            },
        ]
        results = validator.validate_products(products)
        invalid = [r for r in results if not r["valid"]]
        assert len(invalid) == 1, "Negative price should be invalid"
        assert any("price" in str(e).lower() for e in invalid[0].get("errors", []))

    def test_duplicate_order_ids(self, validator):
        """Duplicate order IDs are detected."""
        orders = [
            {
                "order_id": "ORD-001",
                "customer_id": "CUST-001",
                "order_date": "2026-09-01",
                "order_status": "COMPLETED",
                "total_amount": 500.00,
            },
            {
                "order_id": "ORD-001",  # duplicate
                "customer_id": "CUST-002",
                "order_date": "2026-09-02",
                "order_status": "PENDING",
                "total_amount": 750.00,
            },
        ]
        duplicates = validator.find_duplicate_order_ids(orders)
        assert len(duplicates) == 1, "Should detect one duplicate order_id"
        assert "ORD-001" in duplicates

    def test_invalid_order_status(self, validator):
        """Invalid order status values are detected."""
        orders = [
            {
                "order_id": "ORD-003",
                "customer_id": "CUST-001",
                "order_date": "2026-09-01",
                "order_status": "BANANA",
                "total_amount": 100.00,
            },
        ]
        results = validator.validate_orders(orders)
        invalid = [r for r in results if not r["valid"]]
        assert len(invalid) == 1, "BANANA should be an invalid status"
        assert any("status" in str(e).lower() for e in invalid[0].get("errors", []))

    def test_referential_integrity(self, validator, valid_customers, valid_orders):
        """Orders referencing non-existent customer_id fail validation."""
        orders = [
            {
                "order_id": "ORD-ORPHAN",
                "customer_id": "CUST-999",  # does not exist
                "order_date": "2026-09-01",
                "order_status": "COMPLETED",
                "total_amount": 500.00,
            },
        ]
        results = validator.check_referential_integrity(
            orders=orders,
            customers=valid_customers,
        )
        violations = [r for r in results if not r["valid"]]
        assert len(violations) == 1, "Order with non-existent customer_id should fail"
        assert "CUST-999" in str(violations[0].get("errors", []))

    def test_quality_metrics(self, validator, valid_customers, valid_products, valid_orders):
        """Quality metrics dictionary has the correct keys."""
        all_data = {
            "customers": valid_customers,
            "products": valid_products,
            "orders": valid_orders,
        }
        metrics = validator.calculate_quality_metrics(all_data)

        expected_keys = [
            "total_records",
            "valid_records",
            "invalid_records",
            "quality_score",
            "completeness",
        ]
        for key in expected_keys:
            assert key in metrics, f"Metrics missing key: {key}"

        assert isinstance(metrics["total_records"], int)
        assert isinstance(metrics["valid_records"], int)
        assert isinstance(metrics["invalid_records"], int)
        assert isinstance(metrics["quality_score"], (int, float))
        assert isinstance(metrics["completeness"], (int, float))
        assert 0 <= metrics["quality_score"] <= 100
        assert 0 <= metrics["completeness"] <= 100
