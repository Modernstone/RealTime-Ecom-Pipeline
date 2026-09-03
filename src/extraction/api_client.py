"""
E-Commerce API Client Module

This module provides the EcommerceAPIClient class for loading raw e-commerce data
from JSON files in the data/raw/ directory. It supports incremental loading and
handles various error conditions gracefully.

Usage:
    from extraction.api_client import EcommerceAPIClient

    client = EcommerceAPIClient()
    all_data = client.load_all()
    customers = client.load_customers()
    recent_orders = client.load_orders(since="2024-01-01T00:00:00")
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class EcommerceAPIClient:
    """
    Client for loading e-commerce data from JSON files.

    This class reads JSON data files from the data/raw/ directory and provides
    methods to load each data domain (customers, products, orders, etc.) with
    support for incremental loading via timestamp filtering.

    Attributes:
        data_dir (Path): Path to the raw data directory
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the EcommerceAPIClient.

        Args:
            data_dir: Path to the data directory. If None, uses 'data/raw/' relative
                     to the project root (two levels up from this file).
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to data/raw/ relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / "data" / "raw"

        logger.info(f"EcommerceAPIClient initialized with data directory: {self.data_dir}")

    def _load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load and parse a JSON file from the data directory.

        Args:
            filename: Name of the JSON file to load

        Returns:
            List of dictionaries from the JSON file, or empty list if file
            doesn't exist or contains malformed JSON.
        """
        filepath = self.data_dir / filename

        if not filepath.exists():
            logger.warning(f"Data file not found: {filepath}")
            return []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning(f"Expected list in {filename}, got {type(data).__name__}")
                return []

            logger.info(f"Successfully loaded {len(data)} records from {filename}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON in {filename}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []

    def _filter_by_timestamp(
        self,
        records: List[Dict[str, Any]],
        since: Optional[str] = None,
        timestamp_field: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """
        Filter records by timestamp for incremental loading.

        Args:
            records: List of record dictionaries
            since: ISO format timestamp string. Only records created/updated after
                  this time will be returned.
            timestamp_field: Field name to check for timestamp ('created_at' or 'updated_at')

        Returns:
            Filtered list of records
        """
        if not since:
            return records

        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(f"Invalid timestamp format '{since}': {e}")
            return records

        filtered = []
        for record in records:
            timestamp_str = record.get(timestamp_field) or record.get("updated_at")
            if timestamp_str:
                try:
                    record_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if record_dt >= since_dt:
                        filtered.append(record)
                except (ValueError, TypeError):
                    # Include records with unparseable timestamps
                    filtered.append(record)
            else:
                # Include records without timestamps
                filtered.append(record)

        logger.info(f"Filtered {len(records)} records to {len(filtered)} since {since}")
        return filtered

    def load_customers(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load customer data from JSON file.

        Args:
            since: Optional ISO timestamp for incremental loading

        Returns:
            List of customer dictionaries
        """
        records = self._load_json_file("customers.json")
        return self._filter_by_timestamp(records, since, "created_at")

    def load_products(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load product data from JSON file.

        Args:
            since: Optional ISO timestamp for incremental loading

        Returns:
            List of product dictionaries
        """
        records = self._load_json_file("products.json")
        return self._filter_by_timestamp(records, since, "created_at")

    def load_orders(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load order data from JSON file.

        Args:
            since: Optional ISO timestamp for incremental loading

        Returns:
            List of order dictionaries
        """
        records = self._load_json_file("orders.json")
        return self._filter_by_timestamp(records, since, "created_at")

    def load_order_items(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load order items data from JSON file.

        Args:
            since: Optional ISO timestamp for incremental loading

        Returns:
            List of order item dictionaries
        """
        records = self._load_json_file("order_items.json")
        return self._filter_by_timestamp(records, since, "created_at")

    def load_payments(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load payment data from JSON file.

        Args:
            since: Optional ISO timestamp for incremental loading

        Returns:
            List of payment dictionaries
        """
        records = self._load_json_file("payments.json")
        return self._filter_by_timestamp(records, since, "created_at")

    def load_inventory(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load inventory data from JSON file.

        Args:
            since: Optional ISO timestamp for incremental loading

        Returns:
            List of inventory dictionaries
        """
        records = self._load_json_file("inventory.json")
        return self._filter_by_timestamp(records, since, "updated_at")

    def load_all(self, since: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load all e-commerce data domains.

        Args:
            since: Optional ISO timestamp for incremental loading

        Returns:
            Dictionary with domain names as keys and lists of records as values:
            {
                'customers': [...],
                'products': [...],
                'orders': [...],
                'order_items': [...],
                'payments': [...],
                'inventory': [...]
            }
        """
        logger.info("Loading all data domains...")

        data = {
            'customers': self.load_customers(since),
            'products': self.load_products(since),
            'orders': self.load_orders(since),
            'order_items': self.load_order_items(since),
            'payments': self.load_payments(since),
            'inventory': self.load_inventory(since),
        }

        total_records = sum(len(records) for records in data.values())
        logger.info(f"Loaded {total_records} total records across all domains")

        return data


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    client = EcommerceAPIClient()
    all_data = client.load_all()

    for domain, records in all_data.items():
        print(f"{domain}: {len(records)} records")
