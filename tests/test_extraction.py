"""Tests for the extraction module - EcommerceAPIClient."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from extraction.api_client import EcommerceAPIClient


@pytest.fixture
def sample_customers():
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
def sample_products():
    return [
        {
            "product_id": "PROD-001",
            "product_name": "Wireless Mouse",
            "category_id": "CAT-ELEC",
            "subcategory": "Accessories",
            "brand": "TechBrand",
            "price": "₹1,299",
            "cost_price": "₹800",
            "stock_quantity": 150,
            "rating": 4.5,
        },
        {
            "product_id": "PROD-002",
            "product_name": "USB Keyboard",
            "category_id": "CAT-ELEC",
            "subcategory": "Accessories",
            "brand": "TechBrand",
            "price": "₹2,499",
            "cost_price": "₹1,500",
            "stock_quantity": 80,
            "rating": 4.2,
        },
    ]


@pytest.fixture
def sample_orders():
    return [
        {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "order_date": "2026-09-01",
            "order_status": "completed",
            "payment_status": "paid",
            "payment_method": "UPI",
            "shipping_city": "Mumbai",
            "shipping_state": "Maharashtra",
            "total_amount": 1299.00,
            "discount_amount": 100.00,
            "tax_amount": 215.82,
        },
    ]


@pytest.fixture
def sample_order_items():
    return [
        {
            "order_item_id": "ITEM-001",
            "order_id": "ORD-001",
            "product_id": "PROD-001",
            "quantity": 2,
            "unit_price": 1299.00,
            "discount": 100.00,
            "subtotal": 2498.00,
        },
    ]


@pytest.fixture
def sample_categories():
    return [
        {"category_id": "CAT-ELEC", "category_name": "Electronics"},
    ]


@pytest.fixture
def sample_reviews():
    return [
        {
            "review_id": "REV-001",
            "product_id": "PROD-001",
            "customer_id": "CUST-001",
            "rating": 5,
            "comment": "Great product!",
            "review_date": "2026-09-01",
        },
    ]


@pytest.fixture
def data_dir(
    tmp_path,
    sample_customers,
    sample_products,
    sample_orders,
    sample_order_items,
    sample_categories,
    sample_reviews,
):
    """Create a temporary data directory with sample JSON files."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)

    (raw_dir / "customers.json").write_text(json.dumps(sample_customers))
    (raw_dir / "products.json").write_text(json.dumps(sample_products))
    (raw_dir / "orders.json").write_text(json.dumps(sample_orders))
    (raw_dir / "order_items.json").write_text(json.dumps(sample_order_items))
    (raw_dir / "categories.json").write_text(json.dumps(sample_categories))
    (raw_dir / "reviews.json").write_text(json.dumps(sample_reviews))

    return tmp_path


@pytest.fixture
def client(data_dir):
    """Create an EcommerceAPIClient pointing at the temp data directory."""
    return EcommerceAPIClient(data_dir=str(data_dir))


class TestEcommerceAPIClient:
    """Test suite for EcommerceAPIClient."""

    def test_load_all_domains(self, client):
        """All 6 data types load and return non-empty lists."""
        customers = client.load_customers()
        products = client.load_products()
        orders = client.load_orders()
        order_items = client.load_order_items()
        categories = client.load_categories()
        reviews = client.load_reviews()

        assert len(customers) > 0, "Customers should not be empty"
        assert len(products) > 0, "Products should not be empty"
        assert len(orders) > 0, "Orders should not be empty"
        assert len(order_items) > 0, "Order items should not be empty"
        assert len(categories) > 0, "Categories should not be empty"
        assert len(reviews) > 0, "Reviews should not be empty"

    def test_load_customers_structure(self, client):
        """Customer records contain all expected fields."""
        customers = client.load_customers()
        required_fields = [
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "gender",
            "age",
            "city",
            "state",
            "country",
            "signup_date",
        ]
        for customer in customers:
            for field in required_fields:
                assert field in customer, f"Customer missing field: {field}"

    def test_load_products_has_prices(self, client):
        """Product price fields are present and numeric after loading."""
        products = client.load_products()
        for product in products:
            assert "price" in product, "Product missing 'price' field"
            assert "cost_price" in product, "Product missing 'cost_price' field"
            # After loading, prices should be numeric (float)
            assert isinstance(product["price"], (int, float)), (
                f"Price should be numeric, got {type(product['price'])}"
            )
            assert isinstance(product["cost_price"], (int, float)), (
                f"Cost price should be numeric, got {type(product['cost_price'])}"
            )

    def test_incremental_loading(self, data_dir, sample_orders):
        """The since parameter filters records by date."""
        # Add a newer order
        raw_dir = data_dir / "data" / "raw"
        newer_order = {
            "order_id": "ORD-002",
            "customer_id": "CUST-002",
            "order_date": "2026-09-02",
            "order_status": "pending",
            "payment_status": "unpaid",
            "payment_method": "Credit Card",
            "shipping_city": "Delhi",
            "shipping_state": "Delhi",
            "total_amount": 2499.00,
            "discount_amount": 0.00,
            "tax_amount": 449.82,
        }
        all_orders = sample_orders + [newer_order]
        (raw_dir / "orders.json").write_text(json.dumps(all_orders))

        client = EcommerceAPIClient(data_dir=str(data_dir))

        # Load orders since 2026-09-02 should only return the newer one
        recent = client.load_orders(since="2026-09-02")
        assert len(recent) == 1, f"Expected 1 order since 2026-09-02, got {len(recent)}"
        assert recent[0]["order_id"] == "ORD-002"

    def test_missing_file_handling(self, tmp_path):
        """Missing data files are handled gracefully without crashing."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        # Do NOT create any JSON files

        client = EcommerceAPIClient(data_dir=str(tmp_path))

        # Should return empty lists, not raise exceptions
        assert client.load_customers() == []
        assert client.load_products() == []
        assert client.load_orders() == []
        assert client.load_order_items() == []
        assert client.load_categories() == []
        assert client.load_reviews() == []

    def test_malformed_json(self, tmp_path):
        """Invalid JSON content is handled gracefully."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)

        # Write invalid JSON
        (raw_dir / "customers.json").write_text("{invalid json content!!!")
        (raw_dir / "products.json").write_text("not json at all")

        client = EcommerceAPIClient(data_dir=str(tmp_path))

        # Should return empty lists or handle the error gracefully
        customers = client.load_customers()
        products = client.load_products()
        assert isinstance(customers, list), "Should return a list even on malformed JSON"
        assert isinstance(products, list), "Should return a list even on malformed JSON"
