"""
Data Transformation Module

This module provides the DataTransformer class for transforming e-commerce data.
It handles type conversions, derived field calculations, timestamp formatting,
category normalization, and CSV export.

Usage:
    from transformation.transform_data import DataTransformer

    transformer = DataTransformer()
    transformed_customers = transformer.transform_customers(customers_data)
    all_transformed = transformer.transform_all(data_dict)
"""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class DataTransformer:
    """
    Transformer for e-commerce data processing.

    This class transforms cleaned data by converting types, calculating derived
    fields, formatting timestamps, normalizing categories, and exporting to CSV.

    Attributes:
        output_dir (Path): Directory for CSV output files
    """

    # Category normalization mapping
    CATEGORY_MAPPING = {
        'electronics': 'Electronics',
        'electronic': 'Electronics',
        'tech': 'Electronics',
        'technology': 'Electronics',
        'clothing': 'Clothing & Apparel',
        'apparel': 'Clothing & Apparel',
        'fashion': 'Clothing & Apparel',
        'home': 'Home & Kitchen',
        'kitchen': 'Home & Kitchen',
        'household': 'Home & Kitchen',
        'sports': 'Sports & Outdoors',
        'outdoors': 'Sports & Outdoors',
        'fitness': 'Sports & Outdoors',
        'books': 'Books & Media',
        'media': 'Books & Media',
        'toys': 'Toys & Games',
        'games': 'Toys & Games',
        'beauty': 'Beauty & Personal Care',
        'personal care': 'Beauty & Personal Care',
        'health': 'Health & Wellness',
        'wellness': 'Health & Wellness',
        'automotive': 'Automotive',
        'auto': 'Automotive',
        'grocery': 'Grocery & Gourmet',
        'gourmet': 'Grocery & Gourmet',
        'food': 'Grocery & Gourmet',
    }

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the DataTransformer.

        Args:
            output_dir: Path to output directory for CSV files. If None, uses
                       'data/processed/' relative to the project root.
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.output_dir = project_root / "data" / "processed"

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataTransformer initialized with output directory: {self.output_dir}")

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """
        Convert a value to the specified type.

        Args:
            value: Value to convert
            target_type: Target type ('int', 'float', 'str', 'bool')

        Returns:
            Converted value or None if conversion fails
        """
        if value is None:
            return None

        try:
            if target_type == 'int':
                return int(float(value))
            elif target_type == 'float':
                return float(value)
            elif target_type == 'str':
                return str(value)
            elif target_type == 'bool':
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes')
                return bool(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Type conversion failed for {value} to {target_type}: {e}")
            return None

        return value

    def _format_timestamp(self, value: Any) -> Optional[str]:
        """
        Format a timestamp to ISO 8601 format.

        Args:
            value: Timestamp value (string, datetime, or other)

        Returns:
            ISO formatted timestamp string or None
        """
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, str):
            # Try common formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%m/%d/%Y %H:%M:%S',
                '%d-%m-%Y',
                '%d/%m/%Y',
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(value.strip(), fmt)
                    return dt.isoformat()
                except ValueError:
                    continue

            # If already ISO format, return as-is
            if 'T' in value:
                return value

        logger.warning(f"Could not format timestamp: {value}")
        return str(value) if value else None

    def _normalize_category(self, category: Optional[str]) -> str:
        """
        Normalize category names to standard format.

        Args:
            category: Category name to normalize

        Returns:
            Normalized category name
        """
        if not category:
            return 'Uncategorized'

        # Convert to lowercase for mapping lookup
        lower_category = category.strip().lower()

        # Check mapping
        if lower_category in self.CATEGORY_MAPPING:
            return self.CATEGORY_MAPPING[lower_category]

        # If not in mapping, capitalize first letter of each word
        return category.strip().title()

    def _calculate_subtotal(
        self,
        quantity: Any,
        unit_price: Any,
        discount: Any = 0
    ) -> Optional[float]:
        """
        Calculate order item subtotal.

        Formula: subtotal = quantity * unit_price - discount

        Args:
            quantity: Item quantity
            unit_price: Price per unit
            discount: Discount amount (default 0)

        Returns:
            Calculated subtotal or None if inputs are invalid
        """
        try:
            qty = float(quantity) if quantity else 0
            price = float(unit_price) if unit_price else 0
            disc = float(discount) if discount else 0

            subtotal = (qty * price) - disc
            return round(subtotal, 2)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not calculate subtotal: {e}")
            return None

    def _calculate_profit(self, price: Any, cost_price: Any) -> Optional[float]:
        """
        Calculate profit from price and cost price.

        Formula: profit = price - cost_price

        Args:
            price: Selling price
            cost_price: Cost price

        Returns:
            Calculated profit or None if inputs are invalid
        """
        try:
            p = float(price) if price else 0
            cp = float(cost_price) if cost_price else 0
            return round(p - cp, 2)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not calculate profit: {e}")
            return None

    def _calculate_profit_margin(self, profit: Any, price: Any) -> Optional[float]:
        """
        Calculate profit margin percentage.

        Formula: profit_margin = (profit / price) * 100

        Args:
            profit: Profit amount
            price: Selling price

        Returns:
            Profit margin percentage or None if inputs are invalid
        """
        try:
            p = float(profit) if profit else 0
            pr = float(price) if price else 0

            if pr == 0:
                return 0.0

            margin = (p / pr) * 100
            return round(margin, 2)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not calculate profit margin: {e}")
            return None

    def _write_csv(self, records: List[Dict[str, Any]], filename: str) -> None:
        """
        Write records to a CSV file.

        Args:
            records: List of dictionaries to write
            filename: Output filename
        """
        if not records:
            logger.warning(f"No records to write for {filename}")
            return

        filepath = self.output_dir / filename

        try:
            # Get all unique fieldnames from all records
            fieldnames = []
            seen = set()
            for record in records:
                for key in record.keys():
                    if key not in seen:
                        fieldnames.append(key)
                        seen.add(key)

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)

            logger.info(f"Wrote {len(records)} records to {filepath}")

        except Exception as e:
            logger.error(f"Error writing CSV {filename}: {e}")
            raise

    def transform_customers(self, customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform customer data.

        Converts types, formats timestamps, and normalizes fields.

        Args:
            customers: List of customer dictionaries

        Returns:
            List of transformed customer dictionaries
        """
        logger.info(f"Transforming {len(customers)} customer records...")

        transformed = []
        for customer in customers:
            record = {
                'customer_id': self._convert_type(customer.get('customer_id'), 'str'),
                'name': self._convert_type(customer.get('name'), 'str'),
                'email': self._convert_type(customer.get('email'), 'str'),
                'phone': self._convert_type(customer.get('phone'), 'str'),
                'city': self._convert_type(customer.get('city'), 'str'),
                'state': self._convert_type(customer.get('state'), 'str'),
                'country': self._convert_type(customer.get('country'), 'str'),
                'registration_date': self._format_timestamp(customer.get('registration_date')),
                'created_at': self._format_timestamp(customer.get('created_at')),
                'updated_at': self._format_timestamp(customer.get('updated_at')),
            }
            transformed.append(record)

        self._write_csv(transformed, 'customers.csv')
        logger.info(f"Transformed {len(transformed)} customer records")
        return transformed

    def transform_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform product data.

        Converts types, calculates profit and margin, normalizes categories.

        Args:
            products: List of product dictionaries

        Returns:
            List of transformed product dictionaries
        """
        logger.info(f"Transforming {len(products)} product records...")

        transformed = []
        for product in products:
            price = self._convert_type(product.get('price'), 'float')
            cost_price = self._convert_type(product.get('cost_price'), 'float')
            profit = self._calculate_profit(price, cost_price)
            profit_margin = self._calculate_profit_margin(profit, price)

            record = {
                'product_id': self._convert_type(product.get('product_id'), 'str'),
                'name': self._convert_type(product.get('name'), 'str'),
                'description': self._convert_type(product.get('description'), 'str'),
                'category': self._normalize_category(product.get('category')),
                'price': price,
                'cost_price': cost_price,
                'profit': profit,
                'profit_margin': profit_margin,
                'brand': self._convert_type(product.get('brand'), 'str'),
                'sku': self._convert_type(product.get('sku'), 'str'),
                'created_at': self._format_timestamp(product.get('created_at')),
                'updated_at': self._format_timestamp(product.get('updated_at')),
            }
            transformed.append(record)

        self._write_csv(transformed, 'products.csv')
        logger.info(f"Transformed {len(transformed)} product records")
        return transformed

    def transform_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform order data.

        Converts types, formats timestamps, normalizes statuses.

        Args:
            orders: List of order dictionaries

        Returns:
            List of transformed order dictionaries
        """
        logger.info(f"Transforming {len(orders)} order records...")

        transformed = []
        for order in orders:
            record = {
                'order_id': self._convert_type(order.get('order_id'), 'str'),
                'customer_id': self._convert_type(order.get('customer_id'), 'str'),
                'order_date': self._format_timestamp(order.get('order_date')),
                'status': self._convert_type(order.get('status'), 'str').upper() if order.get('status') else 'UNKNOWN',
                'total_amount': self._convert_type(order.get('total_amount'), 'float'),
                'shipping_address': self._convert_type(order.get('shipping_address'), 'str'),
                'created_at': self._format_timestamp(order.get('created_at')),
                'updated_at': self._format_timestamp(order.get('updated_at')),
            }
            transformed.append(record)

        self._write_csv(transformed, 'orders.csv')
        logger.info(f"Transformed {len(transformed)} order records")
        return transformed

    def transform_order_items(self, order_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform order item data.

        Converts types and calculates subtotals.

        Args:
            order_items: List of order item dictionaries

        Returns:
            List of transformed order item dictionaries
        """
        logger.info(f"Transforming {len(order_items)} order item records...")

        transformed = []
        for item in order_items:
            quantity = self._convert_type(item.get('quantity'), 'int')
            unit_price = self._convert_type(item.get('unit_price'), 'float')
            discount = self._convert_type(item.get('discount'), 'float') or 0
            subtotal = self._calculate_subtotal(quantity, unit_price, discount)

            record = {
                'item_id': self._convert_type(item.get('item_id'), 'str'),
                'order_id': self._convert_type(item.get('order_id'), 'str'),
                'product_id': self._convert_type(item.get('product_id'), 'str'),
                'quantity': quantity,
                'unit_price': unit_price,
                'discount': discount,
                'subtotal': subtotal,
                'created_at': self._format_timestamp(item.get('created_at')),
            }
            transformed.append(record)

        self._write_csv(transformed, 'order_items.csv')
        logger.info(f"Transformed {len(transformed)} order item records")
        return transformed

    def transform_payments(self, payments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform payment data.

        Converts types, formats timestamps, normalizes statuses.

        Args:
            payments: List of payment dictionaries

        Returns:
            List of transformed payment dictionaries
        """
        logger.info(f"Transforming {len(payments)} payment records...")

        transformed = []
        for payment in payments:
            record = {
                'payment_id': self._convert_type(payment.get('payment_id'), 'str'),
                'order_id': self._convert_type(payment.get('order_id'), 'str'),
                'amount': self._convert_type(payment.get('amount'), 'float'),
                'payment_method': self._convert_type(payment.get('payment_method'), 'str'),
                'status': self._convert_type(payment.get('status'), 'str').upper() if payment.get('status') else 'UNKNOWN',
                'transaction_id': self._convert_type(payment.get('transaction_id'), 'str'),
                'payment_date': self._format_timestamp(payment.get('payment_date')),
                'created_at': self._format_timestamp(payment.get('created_at')),
            }
            transformed.append(record)

        self._write_csv(transformed, 'payments.csv')
        logger.info(f"Transformed {len(transformed)} payment records")
        return transformed

    def transform_inventory(self, inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform inventory data.

        Converts types, normalizes statuses.

        Args:
            inventory: List of inventory dictionaries

        Returns:
            List of transformed inventory dictionaries
        """
        logger.info(f"Transforming {len(inventory)} inventory records...")

        transformed = []
        for inv in inventory:
            quantity = self._convert_type(inv.get('quantity'), 'int')
            reorder_level = self._convert_type(inv.get('reorder_level'), 'int') or 0

            # Determine stock status based on quantity
            status = inv.get('status')
            if not status or status == 'UNKNOWN':
                if quantity is not None:
                    if quantity <= 0:
                        status = 'OUT_OF_STOCK'
                    elif quantity <= reorder_level:
                        status = 'LOW_STOCK'
                    else:
                        status = 'IN_STOCK'

            record = {
                'inventory_id': self._convert_type(inv.get('inventory_id'), 'str'),
                'product_id': self._convert_type(inv.get('product_id'), 'str'),
                'quantity': quantity,
                'warehouse': self._convert_type(inv.get('warehouse'), 'str'),
                'reorder_level': reorder_level,
                'status': status.upper() if status else 'UNKNOWN',
                'last_restock_date': self._format_timestamp(inv.get('last_restock_date')),
                'updated_at': self._format_timestamp(inv.get('updated_at')),
            }
            transformed.append(record)

        self._write_csv(transformed, 'inventory.csv')
        logger.info(f"Transformed {len(transformed)} inventory records")
        return transformed

    def transform_all(
        self,
        data_dict: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform all data domains and write CSV files.

        Args:
            data_dict: Dictionary with domain names as keys and lists of records as values

        Returns:
            Dictionary with transformed records for each domain
        """
        logger.info("Starting full data transformation...")

        transformed_data = {
            'customers': self.transform_customers(data_dict.get('customers', [])),
            'products': self.transform_products(data_dict.get('products', [])),
            'orders': self.transform_orders(data_dict.get('orders', [])),
            'order_items': self.transform_order_items(data_dict.get('order_items', [])),
            'payments': self.transform_payments(data_dict.get('payments', [])),
            'inventory': self.transform_inventory(data_dict.get('inventory', [])),
        }

        total_transformed = sum(len(records) for records in transformed_data.values())
        logger.info(f"Data transformation complete: {total_transformed} total records transformed")

        return transformed_data


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    sample_products = [
        {
            "product_id": "P001",
            "name": "Laptop",
            "category": "electronics",
            "price": "1299.99",
            "cost_price": "899.99",
            "created_at": "2024-01-15 10:30:00"
        }
    ]

    transformer = DataTransformer()
    transformed = transformer.transform_products(sample_products)

    for product in transformed:
        print(product)
