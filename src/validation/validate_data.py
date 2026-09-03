"""
Data Validation Module

This module provides the DataValidator class for validating e-commerce data across
all domains. It checks for missing required fields, invalid values, duplicate IDs,
and referential integrity issues.

Usage:
    from validation.validate_data import DataValidator

    validator = DataValidator()
    valid, invalid, metrics = validator.validate_customers(customers_data)
    all_valid, all_invalid, all_metrics = validator.validate_all(data_dict)
"""

import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validator for e-commerce data quality checks.

    This class validates data records across different domains (customers, products,
    orders, etc.) checking for missing fields, invalid values, duplicates, and
    referential integrity issues.

    Attributes:
        valid_customers (Set): Set of valid customer IDs for referential checks
        valid_products (Set): Set of valid product IDs for referential checks
        valid_orders (Set): Set of valid order IDs for referential checks
    """

    # Required fields for each domain
    REQUIRED_FIELDS = {
        'customers': ['customer_id', 'first_name', 'last_name', 'email'],
        'products': ['product_id', 'product_name', 'price', 'category_id'],
        'orders': ['order_id', 'customer_id', 'order_date', 'order_status'],
        'order_items': ['order_item_id', 'order_id', 'product_id', 'quantity', 'unit_price'],
        'payments': ['payment_id', 'order_id', 'amount', 'payment_method'],
        'inventory': ['inventory_id', 'product_id', 'stock_quantity'],
    }

    # Valid status values for each domain
    VALID_STATUSES = {
        'orders': ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED'],
        'payments': ['SUCCESS', 'FAILED', 'PENDING', 'REFUNDED'],
        'order_items': [],  # No status field for order items
    }

    # Numeric fields that must be positive
    POSITIVE_FIELDS = {
        'products': ['price', 'cost_price'],
        'order_items': ['quantity', 'unit_price'],
        'payments': ['amount'],
        'inventory': ['stock_quantity'],
    }

    def __init__(self):
        """Initialize the DataValidator with empty reference sets."""
        self.valid_customers: Set[str] = set()
        self.valid_products: Set[str] = set()
        self.valid_orders: Set[str] = set()
        logger.info("DataValidator initialized")

    def _check_missing_fields(
        self,
        record: Dict[str, Any],
        domain: str
    ) -> List[str]:
        """
        Check for missing required fields in a record.

        Args:
            record: Data record to check
            domain: Data domain name

        Returns:
            List of error messages for missing fields
        """
        errors = []
        required = self.REQUIRED_FIELDS.get(domain, [])

        for field in required:
            if field not in record or record[field] is None or record[field] == "":
                errors.append(f"Missing required field: {field}")

        return errors

    def _check_positive_values(
        self,
        record: Dict[str, Any],
        domain: str
    ) -> List[str]:
        """
        Check that numeric fields have positive values.

        Args:
            record: Data record to check
            domain: Data domain name

        Returns:
            List of error messages for invalid values
        """
        errors = []
        positive_fields = self.POSITIVE_FIELDS.get(domain, [])

        for field in positive_fields:
            if field in record and record[field] is not None:
                try:
                    value = float(record[field])
                    if value < 0:
                        errors.append(f"Negative value for {field}: {value}")
                    elif value == 0 and field in ['price', 'unit_price', 'amount']:
                        errors.append(f"Zero value for {field}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for {field}: {record[field]}")

        return errors

    def _check_status(
        self,
        record: Dict[str, Any],
        domain: str
    ) -> List[str]:
        """
        Check that status fields have valid values.

        Args:
            record: Data record to check
            domain: Data domain name

        Returns:
            List of error messages for invalid statuses
        """
        errors = []
        valid_statuses = self.VALID_STATUSES.get(domain, [])

        if not valid_statuses:
            return errors

        # Check domain-specific status fields
        status_field = None
        if domain == 'orders':
            status_field = 'order_status'
        elif domain == 'payments':
            status_field = 'payment_status'

        if status_field and status_field in record:
            status = str(record[status_field]).upper()
            if status not in valid_statuses:
                errors.append(f"Invalid {status_field}: {record[status_field]}. Valid: {valid_statuses}")

        return errors

    def _check_referential_integrity(
        self,
        record: Dict[str, Any],
        domain: str
    ) -> List[str]:
        """
        Check referential integrity against reference sets.

        Args:
            record: Data record to check
            domain: Data domain name

        Returns:
            List of error messages for referential integrity violations
        """
        errors = []

        if domain == 'orders':
            customer_id = record.get('customer_id')
            if customer_id and self.valid_customers and customer_id not in self.valid_customers:
                errors.append(f"Referential integrity: customer_id {customer_id} not found")

        elif domain == 'order_items':
            order_id = record.get('order_id')
            product_id = record.get('product_id')

            if order_id and self.valid_orders and order_id not in self.valid_orders:
                errors.append(f"Referential integrity: order_id {order_id} not found")

            if product_id and self.valid_products and product_id not in self.valid_products:
                errors.append(f"Referential integrity: product_id {product_id} not found")

        elif domain == 'payments':
            order_id = record.get('order_id')
            if order_id and self.valid_orders and order_id not in self.valid_orders:
                errors.append(f"Referential integrity: order_id {order_id} not found")

        elif domain == 'inventory':
            product_id = record.get('product_id')
            if product_id and self.valid_products and product_id not in self.valid_products:
                errors.append(f"Referential integrity: product_id {product_id} not found")

        return errors

    def _get_record_id(
        self,
        record: Dict[str, Any],
        domain: str
    ) -> Optional[str]:
        """
        Extract the primary ID field from a record.

        Args:
            record: Data record
            domain: Data domain name

        Returns:
            The record's ID value or None
        """
        id_fields = {
            'customers': 'customer_id',
            'products': 'product_id',
            'orders': 'order_id',
            'order_items': 'order_item_id',
            'payments': 'payment_id',
            'inventory': 'inventory_id',
        }

        id_field = id_fields.get(domain)
        return record.get(id_field) if id_field else None

    def validate_customers(
        self,
        customers: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
        """
        Validate customer records.

        Args:
            customers: List of customer dictionaries

        Returns:
            Tuple of (valid_records, invalid_records, quality_metrics)
        """
        return self._validate_domain(customers, 'customers')

    def validate_products(
        self,
        products: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
        """
        Validate product records.

        Args:
            products: List of product dictionaries

        Returns:
            Tuple of (valid_records, invalid_records, quality_metrics)
        """
        return self._validate_domain(products, 'products')

    def validate_orders(
        self,
        orders: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
        """
        Validate order records.

        Args:
            orders: List of order dictionaries

        Returns:
            Tuple of (valid_records, invalid_records, quality_metrics)
        """
        return self._validate_domain(orders, 'orders')

    def validate_order_items(
        self,
        order_items: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
        """
        Validate order item records.

        Args:
            order_items: List of order item dictionaries

        Returns:
            Tuple of (valid_records, invalid_records, quality_metrics)
        """
        return self._validate_domain(order_items, 'order_items')

    def validate_payments(
        self,
        payments: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
        """
        Validate payment records.

        Args:
            payments: List of payment dictionaries

        Returns:
            Tuple of (valid_records, invalid_records, quality_metrics)
        """
        return self._validate_domain(payments, 'payments')

    def validate_inventory(
        self,
        inventory: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
        """
        Validate inventory records.

        Args:
            inventory: List of inventory dictionaries

        Returns:
            Tuple of (valid_records, invalid_records, quality_metrics)
        """
        return self._validate_domain(inventory, 'inventory')

    def _validate_domain(
        self,
        records: List[Dict[str, Any]],
        domain: str
    ) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
        """
        Validate records for a specific domain.

        Args:
            records: List of data records
            domain: Data domain name

        Returns:
            Tuple of (valid_records, invalid_records, quality_metrics)
        """
        if not records:
            logger.warning(f"No {domain} records to validate")
            return [], [], {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'duplicate': 0,
                'missing_fields': 0
            }

        logger.info(f"Validating {len(records)} {domain} records...")

        valid_records = []
        invalid_records = []
        seen_ids: Set[str] = set()
        duplicate_count = 0
        missing_fields_count = 0

        for record in records:
            errors = []

            # Check for duplicate IDs
            record_id = self._get_record_id(record, domain)
            if record_id:
                if record_id in seen_ids:
                    duplicate_count += 1
                    errors.append(f"Duplicate ID: {record_id}")
                else:
                    seen_ids.add(record_id)

            # Run all validation checks
            errors.extend(self._check_missing_fields(record, domain))
            errors.extend(self._check_positive_values(record, domain))
            errors.extend(self._check_status(record, domain))
            errors.extend(self._check_referential_integrity(record, domain))

            # Count missing fields
            missing_fields_count += len([e for e in errors if e.startswith("Missing required field")])

            if errors:
                record['errors'] = errors
                invalid_records.append(record)
            else:
                valid_records.append(record)

        # Update reference sets for referential integrity checks
        if domain == 'customers':
            self.valid_customers = {
                r.get('customer_id') for r in valid_records if r.get('customer_id')
            }
        elif domain == 'products':
            self.valid_products = {
                r.get('product_id') for r in valid_records if r.get('product_id')
            }
        elif domain == 'orders':
            self.valid_orders = {
                r.get('order_id') for r in valid_records if r.get('order_id')
            }

        quality_metrics = {
            'total': len(records),
            'valid': len(valid_records),
            'invalid': len(invalid_records),
            'duplicate': duplicate_count,
            'missing_fields': missing_fields_count
        }

        logger.info(
            f"{domain} validation complete: {quality_metrics['valid']} valid, "
            f"{quality_metrics['invalid']} invalid, {quality_metrics['duplicate']} duplicates"
        )

        return valid_records, invalid_records, quality_metrics

    def validate_all(
        self,
        data_dict: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[Dict[str, List], Dict[str, List], Dict[str, Dict]]:
        """
        Validate all data domains with proper referential integrity ordering.

        Validates domains in dependency order: customers -> products -> orders ->
        order_items -> payments -> inventory

        Args:
            data_dict: Dictionary with domain names as keys and lists of records as values

        Returns:
            Tuple of (valid_data, invalid_data, quality_metrics) where each is a
            dictionary keyed by domain name
        """
        logger.info("Starting full data validation...")

        valid_data = {}
        invalid_data = {}
        quality_metrics = {}

        # Validate in dependency order for referential integrity
        validation_order = [
            'customers',
            'products',
            'orders',
            'order_items',
            'payments',
            'inventory'
        ]

        for domain in validation_order:
            records = data_dict.get(domain, [])
            valid, invalid, metrics = self._validate_domain(records, domain)

            valid_data[domain] = valid
            invalid_data[domain] = invalid
            quality_metrics[domain] = metrics

        # Log summary
        total_valid = sum(m['valid'] for m in quality_metrics.values())
        total_invalid = sum(m['invalid'] for m in quality_metrics.values())
        logger.info(f"Validation complete: {total_valid} valid, {total_invalid} invalid records")

        return valid_data, invalid_data, quality_metrics


# Import for Optional type hint
from typing import Optional


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Sample data
    sample_customers = [
        {"customer_id": "C001", "name": "John Doe", "email": "john@example.com"},
        {"customer_id": "C002", "name": "", "email": "jane@example.com"},  # Missing name
        {"customer_id": "C001", "name": "Duplicate", "email": "dup@example.com"},  # Duplicate
    ]

    validator = DataValidator()
    valid, invalid, metrics = validator.validate_customers(sample_customers)

    print(f"Valid: {len(valid)}")
    print(f"Invalid: {len(invalid)}")
    print(f"Metrics: {metrics}")

    for record in invalid:
        print(f"  Invalid record: {record.get('customer_id')} - Errors: {record.get('errors')}")
