"""
PostgreSQL Data Loading Module

This module provides the PostgresLoader class for loading transformed e-commerce
data into a PostgreSQL database. It supports upserts, batch inserts, incremental
loading, and pipeline logging.

Usage:
    from loading.load_postgres import PostgresLoader

    loader = PostgresLoader()
    loader.create_tables()
    loader.load_all(transformed_data)
    loader.close()
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
import yaml

# Configure logging
logger = logging.getLogger(__name__)


class PostgresLoader:
    """
    Loader for e-commerce data into PostgreSQL.

    This class handles database connections, table creation, data loading with
    upserts, batch operations, and pipeline run logging.

    Attributes:
        conn: psycopg2 database connection
        cursor: Database cursor
        config (dict): Database configuration
        batch_size (int): Number of records per batch insert
    """

    # Default configuration
    DEFAULT_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ecommerce',
        'user': 'postgres',
        'password': 'postgres',
    }

    def __init__(
        self,
        config_path: Optional[str] = None,
        batch_size: int = 1000
    ):
        """
        Initialize the PostgresLoader.

        Configuration is loaded from (in order of priority):
        1. Environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
        2. config.yaml file
        3. Default values

        Args:
            config_path: Path to config.yaml file. If None, looks in project root.
            batch_size: Number of records per batch insert
        """
        self.batch_size = batch_size
        self.conn = None
        self.cursor = None

        # Load configuration
        self.config = self._load_config(config_path)

        # Connect to database
        self._connect()

        logger.info(f"PostgresLoader initialized with batch size {batch_size}")

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load database configuration from environment variables or config file.

        Args:
            config_path: Path to config.yaml file

        Returns:
            Configuration dictionary
        """
        config = self.DEFAULT_CONFIG.copy()

        # Try to load from config file
        if config_path:
            yaml_path = Path(config_path)
        else:
            project_root = Path(__file__).parent.parent.parent
            yaml_path = project_root / "config.yaml"

        if yaml_path.exists():
            try:
                with open(yaml_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config and 'database' in yaml_config:
                        db_config = yaml_config['database']
                        config.update({
                            'host': db_config.get('host', config['host']),
                            'port': db_config.get('port', config['port']),
                            'database': db_config.get('name', config['database']),
                            'user': db_config.get('user', config['user']),
                            'password': db_config.get('password', config['password']),
                        })
                        logger.info(f"Loaded database config from {yaml_path}")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}")

        # Override with environment variables
        config['host'] = os.environ.get('DB_HOST', config['host'])
        config['port'] = int(os.environ.get('DB_PORT', config['port']))
        config['database'] = os.environ.get('DB_NAME', config['database'])
        config['user'] = os.environ.get('DB_USER', config['user'])
        config['password'] = os.environ.get('DB_PASSWORD', config['password'])

        return config

    def _connect(self) -> None:
        """
        Establish database connection.

        Raises:
            psycopg2.Error: If connection fails
        """
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to PostgreSQL: {self.config['host']}:{self.config['port']}/{self.config['database']}")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def close(self) -> None:
        """
        Close database connection and cursor.
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("Database connection closed")
        except psycopg2.Error as e:
            logger.error(f"Error closing database connection: {e}")

    def create_tables(self, schema_path: Optional[str] = None) -> None:
        """
        Create database tables by executing schema.sql.

        Args:
            schema_path: Path to schema.sql file. If None, looks in project root.
        """
        if schema_path:
            sql_path = Path(schema_path)
        else:
            project_root = Path(__file__).parent.parent.parent
            sql_path = project_root / "sql" / "schema.sql"

        if not sql_path.exists():
            logger.error(f"Schema file not found: {sql_path}")
            raise FileNotFoundError(f"Schema file not found: {sql_path}")

        try:
            with open(sql_path, 'r') as f:
                schema_sql = f.read()

            self.cursor.execute(schema_sql)
            self.conn.commit()
            logger.info(f"Database tables created from {sql_path}")

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error creating tables: {e}")
            raise

    def _batch_insert(
        self,
        table: str,
        records: List[Dict[str, Any]],
        conflict_field: str,
        update_fields: Optional[List[str]] = None
    ) -> int:
        """
        Insert records in batches using ON CONFLICT for upserts.

        Args:
            table: Target table name
            records: List of record dictionaries
            conflict_field: Field to check for conflicts (primary key)
            update_fields: Fields to update on conflict. If None, updates all fields.

        Returns:
            Number of records inserted/updated
        """
        if not records:
            logger.info(f"No records to insert into {table}")
            return 0

        total_inserted = 0

        # Get field names from first record
        fields = list(records[0].keys())
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join(fields)

        # Build ON CONFLICT clause
        if update_fields:
            update_clause = ', '.join([f"{f} = EXCLUDED.{f}" for f in update_fields])
        else:
            update_clause = ', '.join([f"{f} = EXCLUDED.{f}" for f in fields if f != conflict_field])

        query = f"""
            INSERT INTO {table} ({field_names})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_field})
            DO UPDATE SET {update_clause}
        """

        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]

            try:
                # Prepare batch data
                batch_data = []
                for record in batch:
                    row = tuple(record.get(f) for f in fields)
                    batch_data.append(row)

                # Execute batch
                psycopg2.extras.execute_batch(self.cursor, query, batch_data)
                self.conn.commit()

                total_inserted += len(batch)
                logger.debug(f"Inserted batch of {len(batch)} records into {table}")

            except psycopg2.Error as e:
                self.conn.rollback()
                logger.error(f"Error inserting batch into {table}: {e}")
                raise

        logger.info(f"Inserted/updated {total_inserted} records into {table}")
        return total_inserted

    def load_customers(self, customers: List[Dict[str, Any]]) -> int:
        """
        Load customer data into PostgreSQL.

        Args:
            customers: List of customer dictionaries

        Returns:
            Number of records loaded
        """
        return self._batch_insert(
            table='customers',
            records=customers,
            conflict_field='customer_id'
        )

    def load_products(self, products: List[Dict[str, Any]]) -> int:
        """
        Load product data into PostgreSQL.

        Args:
            products: List of product dictionaries

        Returns:
            Number of records loaded
        """
        return self._batch_insert(
            table='products',
            records=products,
            conflict_field='product_id'
        )

    def load_orders(self, orders: List[Dict[str, Any]]) -> int:
        """
        Load order data into PostgreSQL.

        Args:
            orders: List of order dictionaries

        Returns:
            Number of records loaded
        """
        return self._batch_insert(
            table='orders',
            records=orders,
            conflict_field='order_id'
        )

    def load_order_items(self, order_items: List[Dict[str, Any]]) -> int:
        """
        Load order item data into PostgreSQL.

        Args:
            order_items: List of order item dictionaries

        Returns:
            Number of records loaded
        """
        return self._batch_insert(
            table='order_items',
            records=order_items,
            conflict_field='item_id'
        )

    def load_payments(self, payments: List[Dict[str, Any]]) -> int:
        """
        Load payment data into PostgreSQL.

        Args:
            payments: List of payment dictionaries

        Returns:
            Number of records loaded
        """
        return self._batch_insert(
            table='payments',
            records=payments,
            conflict_field='payment_id'
        )

    def load_inventory(self, inventory: List[Dict[str, Any]]) -> int:
        """
        Load inventory data into PostgreSQL.

        Args:
            inventory: List of inventory dictionaries

        Returns:
            Number of records loaded
        """
        return self._batch_insert(
            table='inventory',
            records=inventory,
            conflict_field='inventory_id'
        )

    def log_pipeline_run(
        self,
        run_id: str,
        status: str,
        records_processed: int,
        records_valid: int,
        records_invalid: int,
        duration_seconds: float,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a pipeline run to the pipeline_logs table.

        Args:
            run_id: Unique identifier for the pipeline run
            status: Run status ('STARTED', 'COMPLETED', 'FAILED')
            records_processed: Total records processed
            records_valid: Number of valid records
            records_invalid: Number of invalid records
            duration_seconds: Run duration in seconds
            error_message: Optional error message if run failed
        """
        query = """
            INSERT INTO pipeline_logs (
                run_id, status, records_processed, records_valid,
                records_invalid, duration_seconds, error_message,
                started_at, completed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id) DO UPDATE SET
                status = EXCLUDED.status,
                records_processed = EXCLUDED.records_processed,
                records_valid = EXCLUDED.records_valid,
                records_invalid = EXCLUDED.records_invalid,
                duration_seconds = EXCLUDED.duration_seconds,
                error_message = EXCLUDED.error_message,
                completed_at = EXCLUDED.completed_at
        """

        now = datetime.now()
        started_at = now
        completed_at = now if status in ('COMPLETED', 'FAILED') else None

        try:
            self.cursor.execute(query, (
                run_id,
                status,
                records_processed,
                records_valid,
                records_invalid,
                duration_seconds,
                error_message,
                started_at,
                completed_at
            ))
            self.conn.commit()
            logger.info(f"Pipeline run {run_id} logged with status {status}")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error logging pipeline run: {e}")

    def load_all(
        self,
        data_dict: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, int]:
        """
        Load all data domains into PostgreSQL.

        Args:
            data_dict: Dictionary with domain names as keys and lists of records as values

        Returns:
            Dictionary with domain names and number of records loaded
        """
        logger.info("Starting full data load...")

        load_counts = {}

        try:
            load_counts['customers'] = self.load_customers(data_dict.get('customers', []))
            load_counts['products'] = self.load_products(data_dict.get('products', []))
            load_counts['orders'] = self.load_orders(data_dict.get('orders', []))
            load_counts['order_items'] = self.load_order_items(data_dict.get('order_items', []))
            load_counts['payments'] = self.load_payments(data_dict.get('payments', []))
            load_counts['inventory'] = self.load_inventory(data_dict.get('inventory', []))

            total_loaded = sum(load_counts.values())
            logger.info(f"Data load complete: {total_loaded} total records loaded")

        except Exception as e:
            logger.error(f"Error during data load: {e}")
            raise

        return load_counts


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Note: This requires a running PostgreSQL instance and proper configuration
    try:
        loader = PostgresLoader()
        loader.create_tables()

        # Sample data
        sample_data = {
            'customers': [
                {'customer_id': 'C001', 'name': 'John Doe', 'email': 'john@example.com'}
            ]
        }

        counts = loader.load_all(sample_data)
        print(f"Loaded: {counts}")

        loader.close()
    except Exception as e:
        print(f"Error: {e}")
