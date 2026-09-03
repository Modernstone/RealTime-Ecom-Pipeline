"""
Database query functions for the E-Commerce Analytics Dashboard.
All functions return pandas DataFrames and handle connection errors gracefully.
"""

import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime, timedelta


def get_connection():
    """Create a PostgreSQL database connection from environment variables."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "ecommerce"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        )
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(f"Failed to connect to database: {e}")


@contextmanager
def get_db_cursor():
    """Context manager for database cursor with automatic cleanup."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_revenue_kpis(start_date, end_date, category=None):
    """
    Get revenue KPIs for the specified date range.

    Returns:
        DataFrame with columns: total_revenue, total_orders, total_customers,
        total_profit, avg_order_value
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    COALESCE(SUM(o.total_amount), 0) as total_revenue,
                    COUNT(DISTINCT o.order_id) as total_orders,
                    COUNT(DISTINCT o.customer_id) as total_customers,
                    COALESCE(SUM(o.total_amount - o.cost_amount), 0) as total_profit,
                    COALESCE(AVG(o.total_amount), 0) as avg_order_value
                FROM orders o
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                LEFT JOIN products p ON oi.product_id = p.product_id
                WHERE o.order_date >= %s AND o.order_date <= %s
                AND o.status != 'cancelled'
            """
            params = [start_date, end_date]

            if category:
                query += " AND p.category = ANY(%s)"
                params.append(category)

            cursor.execute(query, params)
            result = cursor.fetchone()
            return pd.DataFrame([result])
    except Exception as e:
        print(f"Error fetching revenue KPIs: {e}")
        return pd.DataFrame()


def get_revenue_trend(start_date, end_date, category=None, granularity='daily'):
    """
    Get revenue trend over time.

    Args:
        granularity: 'daily', 'weekly', or 'monthly'

    Returns:
        DataFrame with columns: date, revenue, orders
    """
    try:
        with get_db_cursor() as cursor:
            if granularity == 'daily':
                date_trunc = "DATE(o.order_date)"
            elif granularity == 'weekly':
                date_trunc = "DATE_TRUNC('week', o.order_date)"
            elif granularity == 'monthly':
                date_trunc = "DATE_TRUNC('month', o.order_date)"
            else:
                date_trunc = "DATE(o.order_date)"

            query = f"""
                SELECT
                    {date_trunc} as date,
                    COALESCE(SUM(o.total_amount), 0) as revenue,
                    COUNT(DISTINCT o.order_id) as orders
                FROM orders o
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                LEFT JOIN products p ON oi.product_id = p.product_id
                WHERE o.order_date >= %s AND o.order_date <= %s
                AND o.status != 'cancelled'
            """
            params = [start_date, end_date]

            if category:
                query += " AND p.category = ANY(%s)"
                params.append(category)

            query += f" GROUP BY {date_trunc} ORDER BY date"

            cursor.execute(query, params)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching revenue trend: {e}")
        return pd.DataFrame()


def get_top_products(limit=10, start_date=None, end_date=None, category=None):
    """
    Get top products by revenue.

    Returns:
        DataFrame with columns: product_id, product_name, category, units_sold, revenue
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    p.product_id,
                    p.product_name,
                    p.category,
                    SUM(oi.quantity) as units_sold,
                    COALESCE(SUM(oi.quantity * oi.unit_price), 0) as revenue
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN orders o ON oi.order_id = o.order_id
                WHERE o.status != 'cancelled'
            """
            params = []

            if start_date:
                query += " AND o.order_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND o.order_date <= %s"
                params.append(end_date)
            if category:
                query += " AND p.category = ANY(%s)"
                params.append(category)

            query += """
                GROUP BY p.product_id, p.product_name, p.category
                ORDER BY revenue DESC
                LIMIT %s
            """
            params.append(limit)

            cursor.execute(query, params)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching top products: {e}")
        return pd.DataFrame()


def get_category_breakdown(start_date=None, end_date=None):
    """
    Get revenue breakdown by product category.

    Returns:
        DataFrame with columns: category, revenue, orders, units_sold
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    p.category,
                    COALESCE(SUM(oi.quantity * oi.unit_price), 0) as revenue,
                    COUNT(DISTINCT o.order_id) as orders,
                    SUM(oi.quantity) as units_sold
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN orders o ON oi.order_id = o.order_id
                WHERE o.status != 'cancelled'
            """
            params = []

            if start_date:
                query += " AND o.order_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND o.order_date <= %s"
                params.append(end_date)

            query += """
                GROUP BY p.category
                ORDER BY revenue DESC
            """

            cursor.execute(query, params)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching category breakdown: {e}")
        return pd.DataFrame()


def get_order_status_distribution(start_date=None, end_date=None):
    """
    Get order count distribution by status.

    Returns:
        DataFrame with columns: status, count
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    status,
                    COUNT(*) as count
                FROM orders
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND order_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND order_date <= %s"
                params.append(end_date)

            query += " GROUP BY status ORDER BY count DESC"

            cursor.execute(query, params)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching order status distribution: {e}")
        return pd.DataFrame()


def get_payment_method_breakdown(start_date=None, end_date=None):
    """
    Get payment count breakdown by payment method.

    Returns:
        DataFrame with columns: payment_method, count, total_amount
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    payment_method,
                    COUNT(*) as count,
                    COALESCE(SUM(amount), 0) as total_amount
                FROM payments
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND payment_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND payment_date <= %s"
                params.append(end_date)

            query += " GROUP BY payment_method ORDER BY count DESC"

            cursor.execute(query, params)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching payment method breakdown: {e}")
        return pd.DataFrame()


def get_customer_segmentation():
    """
    Get customer segmentation based on spending.

    Returns:
        DataFrame with columns: segment, customer_count, avg_spending
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                WITH customer_spending AS (
                    SELECT
                        c.customer_id,
                        COALESCE(SUM(o.total_amount), 0) as total_spent,
                        COUNT(o.order_id) as order_count
                    FROM customers c
                    LEFT JOIN orders o ON c.customer_id = o.customer_id
                        AND o.status != 'cancelled'
                    GROUP BY c.customer_id
                )
                SELECT
                    CASE
                        WHEN total_spent >= 10000 THEN 'Premium'
                        WHEN total_spent >= 5000 THEN 'Gold'
                        WHEN total_spent >= 1000 THEN 'Silver'
                        ELSE 'Bronze'
                    END as segment,
                    COUNT(*) as customer_count,
                    AVG(total_spent) as avg_spending
                FROM customer_spending
                GROUP BY
                    CASE
                        WHEN total_spent >= 10000 THEN 'Premium'
                        WHEN total_spent >= 5000 THEN 'Gold'
                        WHEN total_spent >= 1000 THEN 'Silver'
                        ELSE 'Bronze'
                    END
                ORDER BY avg_spending DESC
            """
            cursor.execute(query)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching customer segmentation: {e}")
        return pd.DataFrame()


def get_top_customers(limit=10):
    """
    Get top customers by total spending.

    Returns:
        DataFrame with columns: customer_id, customer_name, email, orders, total_spent
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    c.customer_id,
                    c.customer_name,
                    c.email,
                    COUNT(o.order_id) as orders,
                    COALESCE(SUM(o.total_amount), 0) as total_spent
                FROM customers c
                LEFT JOIN orders o ON c.customer_id = o.customer_id
                    AND o.status != 'cancelled'
                GROUP BY c.customer_id, c.customer_name, c.email
                ORDER BY total_spent DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching top customers: {e}")
        return pd.DataFrame()


def get_low_stock_products(threshold=None):
    """
    Get products with low stock levels.

    Args:
        threshold: Stock threshold (default from env or 50)

    Returns:
        DataFrame with columns: product_id, product_name, category, stock_quantity, status
    """
    try:
        if threshold is None:
            threshold = int(os.getenv("LOW_STOCK_THRESHOLD", "50"))

        with get_db_cursor() as cursor:
            query = """
                SELECT
                    p.product_id,
                    p.product_name,
                    p.category,
                    i.stock_quantity,
                    CASE
                        WHEN i.stock_quantity = 0 THEN 'Out of Stock'
                        WHEN i.stock_quantity <= %s / 2 THEN 'Critical'
                        WHEN i.stock_quantity <= %s THEN 'Low Stock'
                        ELSE 'In Stock'
                    END as status
                FROM products p
                JOIN inventory i ON p.product_id = i.product_id
                WHERE i.stock_quantity <= %s
                ORDER BY i.stock_quantity ASC
            """
            cursor.execute(query, (threshold, threshold, threshold))
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching low stock products: {e}")
        return pd.DataFrame()


def get_pipeline_health():
    """
    Get latest pipeline run information.

    Returns:
        DataFrame with columns: run_id, dag_id, task_id, status, start_time, end_time, duration
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    run_id,
                    dag_id,
                    task_id,
                    status,
                    start_time,
                    end_time,
                    EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds
                FROM pipeline_runs
                WHERE run_id = (
                    SELECT run_id
                    FROM pipeline_runs
                    ORDER BY start_time DESC
                    LIMIT 1
                )
                ORDER BY start_time
            """
            cursor.execute(query)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching pipeline health: {e}")
        return pd.DataFrame()


def get_daily_orders(start_date, end_date):
    """
    Get daily order counts.

    Returns:
        DataFrame with columns: date, order_count, revenue
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    DATE(order_date) as date,
                    COUNT(*) as order_count,
                    COALESCE(SUM(total_amount), 0) as revenue
                FROM orders
                WHERE order_date >= %s AND order_date <= %s
                AND status != 'cancelled'
                GROUP BY DATE(order_date)
                ORDER BY date
            """
            cursor.execute(query, (start_date, end_date))
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching daily orders: {e}")
        return pd.DataFrame()


def get_regional_breakdown(start_date=None, end_date=None):
    """
    Get order breakdown by state/region.

    Returns:
        DataFrame with columns: state, order_count, revenue, customer_count
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    c.state,
                    COUNT(DISTINCT o.order_id) as order_count,
                    COALESCE(SUM(o.total_amount), 0) as revenue,
                    COUNT(DISTINCT c.customer_id) as customer_count
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.status != 'cancelled'
            """
            params = []

            if start_date:
                query += " AND o.order_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND o.order_date <= %s"
                params.append(end_date)

            query += """
                GROUP BY c.state
                ORDER BY order_count DESC
            """

            cursor.execute(query, params)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    except Exception as e:
        print(f"Error fetching regional breakdown: {e}")
        return pd.DataFrame()
