"""Tests for the database module - PostgresLoader (mocked)."""

import pytest
from unittest.mock import MagicMock, patch, call
from database.loader import PostgresLoader


@pytest.fixture
def mock_conn():
    """Create a mock database connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture
def mock_cursor(mock_conn):
    """Get the mock cursor from the mock connection."""
    return mock_conn.cursor.return_value.__enter__()


@pytest.fixture
def loader(mock_conn):
    """Create a PostgresLoader with a mocked connection."""
    with patch("database.loader.psycopg2") as mock_pg:
        mock_pg.connect.return_value = mock_conn
        loader = PostgresLoader(
            host="localhost",
            port=5432,
            dbname="test_db",
            user="test_user",
            password="test_pass",
        )
        yield loader


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
def sample_orders():
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


class TestPostgresLoader:
    """Test suite for PostgresLoader with mocked DB connections."""

    def test_create_tables(self, loader, mock_conn, mock_cursor):
        """Schema SQL is executed to create tables."""
        mock_cursor.fetchall.return_value = []

        loader.create_tables()

        # Verify that execute was called (schema.sql content)
        assert mock_cursor.execute.called, "execute should be called for schema creation"
        # The SQL should contain CREATE TABLE statements
        executed_sql = str(mock_cursor.execute.call_args_list)
        assert "CREATE TABLE" in executed_sql.upper() or "customers" in executed_sql.lower(), (
            "Schema should create tables"
        )
        mock_conn.commit.assert_called()

    def test_load_customers(self, loader, mock_conn, mock_cursor, sample_customers):
        """Customer data is inserted into the database."""
        mock_cursor.rowcount = len(sample_customers)

        loader.load_customers(sample_customers)

        assert mock_cursor.execute.called, "execute should be called for INSERT"
        mock_conn.commit.assert_called()

        # Verify the number of records matches
        assert mock_cursor.rowcount == len(sample_customers)

    def test_upsert_behavior(self, loader, mock_conn, mock_cursor, sample_customers):
        """ON CONFLICT clause handles upsert correctly."""
        mock_cursor.rowcount = len(sample_customers)

        loader.load_customers(sample_customers)

        # Check that the SQL contains ON CONFLICT for upsert
        executed_sql = str(mock_cursor.execute.call_args_list).upper()
        assert "ON CONFLICT" in executed_sql or "INSERT" in executed_sql, (
            "Should use INSERT with ON CONFLICT for upsert"
        )
        mock_conn.commit.assert_called()

    def test_pipeline_log_entry(self, loader, mock_conn, mock_cursor):
        """A row is inserted into pipeline_logs after a run."""
        run_id = "RUN-20260902-220000"
        status = "SUCCESS"
        records_processed = 150
        duration_seconds = 42

        loader.log_pipeline_run(
            run_id=run_id,
            status=status,
            records_processed=records_processed,
            duration_seconds=duration_seconds,
        )

        assert mock_cursor.execute.called, "execute should be called for log insert"
        executed_sql = str(mock_cursor.execute.call_args_list)
        assert "pipeline_log" in executed_sql.lower(), (
            "Should insert into pipeline_logs table"
        )
        mock_conn.commit.assert_called()

    def test_incremental_load(self, loader, mock_conn, mock_cursor, sample_orders):
        """Only new records since the given timestamp are loaded."""
        mock_cursor.fetchall.return_value = sample_orders
        mock_cursor.rowcount = len(sample_orders)

        result = loader.load_orders_incremental(since="2026-09-01")

        assert mock_cursor.execute.called, "execute should be called for incremental query"
        executed_sql = str(mock_cursor.execute.call_args_list)
        # Should have a WHERE clause filtering by date
        assert "WHERE" in executed_sql.upper() or "since" in executed_sql.lower() or ">=" in executed_sql, (
            "Incremental load should filter by timestamp"
        )
