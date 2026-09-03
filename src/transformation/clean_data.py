"""
Data Cleaning Module

This module provides the DataCleaner class for cleaning and standardizing e-commerce
data. It handles whitespace stripping, currency normalization, status standardization,
null value handling, and deduplication.

Usage:
    from transformation.clean_data import DataCleaner

    cleaner = DataCleaner()
    cleaned_customers = cleaner.clean_customers(customers_data)
    all_cleaned = cleaner.clean_all(data_dict)
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

# Configure logging
logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Cleaner for e-commerce data standardization.

    This class provides methods to clean and standardize data across different
    e-commerce domains, handling common data quality issues like whitespace,
    inconsistent formats, and null values.

    Default values used for null/missing fields:
        - String fields: empty string ''
        - Numeric fields: 0
        - Status fields: 'UNKNOWN'
        - Date fields: None
    """

    # Default values for different field types
    DEFAULT_VALUES = {
        'str': '',
        'int': 0,
        'float': 0.0,
        'status': 'UNKNOWN',
    }

    # Fields that should be treated as currency
    CURRENCY_FIELDS = ['price', 'cost_price', 'unit_price', 'amount', 'total', 'discount']

    # Fields that should be normalized to uppercase
    STATUS_FIELDS = ['status', 'payment_status', 'order_status']

    # ID fields for deduplication
    ID_FIELDS = {
        'customers': 'customer_id',
        'products': 'product_id',
        'orders': 'order_id',
        'order_items': 'item_id',
        'payments': 'payment_id',
        'inventory': 'inventory_id',
    }

    def __init__(self):
        """Initialize the DataCleaner."""
        logger.info("DataCleaner initialized")

    def _strip_whitespace(self, value: Any) -> Any:
        """
        Strip whitespace from string values.

        Args:
            value: Value to process

        Returns:
            Stripped string or original value if not a string
        """
        if isinstance(value, str):
            return value.strip()
        return value

    def _standardize_currency(self, value: Any) -> Optional[float]:
        """
        Convert currency strings to float values.

        Handles formats like:
        - "₹1,299" -> 1299.00
        - "Rs. 500" -> 500.00
        - "$1,234.56" -> 1234.56
        - "1,299.99" -> 1299.99

        Args:
            value: Currency value to convert

        Returns:
            Float value or None if conversion fails
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return None

        # Remove currency symbols and whitespace
        cleaned = value.strip()
        cleaned = re.sub(r'[₹$€£]', '', cleaned)
        cleaned = re.sub(r'Rs\.?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'INR\s*', '', cleaned, flags=re.IGNORECASE)

        # Remove commas
        cleaned = cleaned.replace(',', '')

        # Remove any remaining whitespace
        cleaned = cleaned.strip()

        if not cleaned:
            return None

        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"Could not convert currency value: {value}")
            return None

    def _normalize_status(self, value: Any) -> str:
        """
        Normalize status values to uppercase.

        Args:
            value: Status value to normalize

        Returns:
            Uppercase status string
        """
        if value is None:
            return 'UNKNOWN'

        if isinstance(value, str):
            return value.strip().upper()

        return str(value).upper()

    def _handle_null_value(self, value: Any, field_name: str) -> Any:
        """
        Handle null/None values by providing appropriate defaults.

        Args:
            value: Value to check
            field_name: Name of the field for context

        Returns:
            Original value or appropriate default
        """
        if value is not None:
            return value

        # Determine appropriate default based on field name
        if field_name in self.STATUS_FIELDS:
            return self.DEFAULT_VALUES['status']
        elif field_name in self.CURRENCY_FIELDS:
            return self.DEFAULT_VALUES['float']
        elif field_name.endswith('_id'):
            return None  # IDs should remain None if missing
        elif field_name in ['quantity', 'stock', 'count']:
            return self.DEFAULT_VALUES['int']
        elif isinstance(value, str):
            return self.DEFAULT_VALUES['str']

        return None

    def _clean_record(self, record: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """
        Clean a single record by applying all cleaning operations.

        Args:
            record: Data record to clean
            domain: Data domain name

        Returns:
            Cleaned record dictionary
        """
        cleaned = {}

        for field, value in record.items():
            # Skip the errors field from validation
            if field == 'errors':
                continue

            # Strip whitespace from strings
            value = self._strip_whitespace(value)

            # Handle null values
            value = self._handle_null_value(value, field)

            # Standardize currency fields
            if field in self.CURRENCY_FIELDS:
                value = self._standardize_currency(value)

            # Normalize status fields
            if field in self.STATUS_FIELDS:
                value = self._normalize_status(value)

            cleaned[field] = value

        return cleaned

    def _deduplicate_records(
        self,
        records: List[Dict[str, Any]],
        domain: str
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate records based on ID field.

        Keeps the last occurrence of each duplicate ID.

        Args:
            records: List of records to deduplicate
            domain: Data domain name

        Returns:
            Deduplicated list of records
        """
        id_field = self.ID_FIELDS.get(domain)
        if not id_field:
            return records

        seen: Dict[str, Dict] = {}
        duplicates = 0

        for record in records:
            record_id = record.get(id_field)
            if record_id:
                if record_id in seen:
                    duplicates += 1
                seen[record_id] = record
            else:
                # Keep records without IDs
                seen[f"_no_id_{id(record)}"] = record

        if duplicates > 0:
            logger.info(f"Removed {duplicates} duplicate {domain} records")

        return list(seen.values())

    def clean_customers(self, customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean customer data.

        Args:
            customers: List of customer dictionaries

        Returns:
            List of cleaned customer dictionaries
        """
        logger.info(f"Cleaning {len(customers)} customer records...")

        cleaned = [self._clean_record(r, 'customers') for r in customers]
        cleaned = self._deduplicate_records(cleaned, 'customers')

        logger.info(f"Cleaned {len(cleaned)} customer records")
        return cleaned

    def clean_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean product data.

        Args:
            products: List of product dictionaries

        Returns:
            List of cleaned product dictionaries
        """
        logger.info(f"Cleaning {len(products)} product records...")

        cleaned = [self._clean_record(r, 'products') for r in products]
        cleaned = self._deduplicate_records(cleaned, 'products')

        logger.info(f"Cleaned {len(cleaned)} product records")
        return cleaned

    def clean_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean order data.

        Args:
            orders: List of order dictionaries

        Returns:
            List of cleaned order dictionaries
        """
        logger.info(f"Cleaning {len(orders)} order records...")

        cleaned = [self._clean_record(r, 'orders') for r in orders]
        cleaned = self._deduplicate_records(cleaned, 'orders')

        logger.info(f"Cleaned {len(cleaned)} order records")
        return cleaned

    def clean_order_items(self, order_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean order item data.

        Args:
            order_items: List of order item dictionaries

        Returns:
            List of cleaned order item dictionaries
        """
        logger.info(f"Cleaning {len(order_items)} order item records...")

        cleaned = [self._clean_record(r, 'order_items') for r in order_items]
        cleaned = self._deduplicate_records(cleaned, 'order_items')

        logger.info(f"Cleaned {len(cleaned)} order item records")
        return cleaned

    def clean_payments(self, payments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean payment data.

        Args:
            payments: List of payment dictionaries

        Returns:
            List of cleaned payment dictionaries
        """
        logger.info(f"Cleaning {len(payments)} payment records...")

        cleaned = [self._clean_record(r, 'payments') for r in payments]
        cleaned = self._deduplicate_records(cleaned, 'payments')

        logger.info(f"Cleaned {len(cleaned)} payment records")
        return cleaned

    def clean_inventory(self, inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean inventory data.

        Args:
            inventory: List of inventory dictionaries

        Returns:
            List of cleaned inventory dictionaries
        """
        logger.info(f"Cleaning {len(inventory)} inventory records...")

        cleaned = [self._clean_record(r, 'inventory') for r in inventory]
        cleaned = self._deduplicate_records(cleaned, 'inventory')

        logger.info(f"Cleaned {len(cleaned)} inventory records")
        return cleaned

    def clean_all(
        self,
        data_dict: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Clean all data domains.

        Args:
            data_dict: Dictionary with domain names as keys and lists of records as values

        Returns:
            Dictionary with cleaned records for each domain
        """
        logger.info("Starting full data cleaning...")

        cleaned_data = {
            'customers': self.clean_customers(data_dict.get('customers', [])),
            'products': self.clean_products(data_dict.get('products', [])),
            'orders': self.clean_orders(data_dict.get('orders', [])),
            'order_items': self.clean_order_items(data_dict.get('order_items', [])),
            'payments': self.clean_payments(data_dict.get('payments', [])),
            'inventory': self.clean_inventory(data_dict.get('inventory', [])),
        }

        total_cleaned = sum(len(records) for records in cleaned_data.values())
        logger.info(f"Data cleaning complete: {total_cleaned} total records cleaned")

        return cleaned_data


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    sample_products = [
        {"product_id": "P001", "name": "  Laptop  ", "price": "₹1,299", "status": "active"},
        {"product_id": "P002", "name": "Phone", "price": "Rs. 500", "status": None},
        {"product_id": "P001", "name": "Duplicate", "price": "$100", "status": "ACTIVE"},
    ]

    cleaner = DataCleaner()
    cleaned = cleaner.clean_products(sample_products)

    for product in cleaned:
        print(product)
