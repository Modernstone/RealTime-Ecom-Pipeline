"""
E-Commerce Data Pipeline DAG
Airflow 2.x DAG for processing e-commerce data from source to analytics.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

# Import functions from src modules
from src.extract import extract_customers_data, extract_products_data, extract_orders_data
from src.validate import validate_data
from src.transform import transform_data
from src.load import (
    load_customers,
    load_products,
    load_orders,
    load_order_items,
    load_payments,
    load_inventory,
)
from src.analytics import run_analytics


# Default arguments for the DAG
default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
}


def create_dag():
    """Create and return the e-commerce pipeline DAG."""

    with DAG(
        dag_id="ecommerce_pipeline_dag",
        default_args=default_args,
        description="Real-time E-Commerce Data Pipeline - Extract, Transform, Load, and Analyze",
        schedule_interval="*/15 * * * *",  # Every 15 minutes
        start_date=datetime(2024, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["ecommerce", "etl", "analytics"],
    ) as dag:

        # Start task
        start = EmptyOperator(
            task_id="start",
            doc="Pipeline start marker",
        )

        # Extract tasks (parallel)
        extract_customers = PythonOperator(
            task_id="extract_customers",
            python_callable=extract_customers_data,
            doc="Extract customer data from source system",
        )

        extract_products = PythonOperator(
            task_id="extract_products",
            python_callable=extract_products_data,
            doc="Extract product catalog from source system",
        )

        extract_orders = PythonOperator(
            task_id="extract_orders",
            python_callable=extract_orders_data,
            doc="Extract orders and related data from source system",
        )

        # Validate task
        validate = PythonOperator(
            task_id="validate_data",
            python_callable=validate_data,
            doc="Validate extracted data for quality and completeness",
        )

        # Transform task
        transform = PythonOperator(
            task_id="transform_data",
            python_callable=transform_data,
            doc="Transform and enrich data for loading",
        )

        # Load tasks (sequential groups)
        load_customers_task = PythonOperator(
            task_id="load_customers",
            python_callable=load_customers,
            doc="Load customer dimension table",
        )

        load_products_task = PythonOperator(
            task_id="load_products",
            python_callable=load_products,
            doc="Load product dimension table",
        )

        load_orders_task = PythonOperator(
            task_id="load_orders",
            python_callable=load_orders,
            doc="Load orders fact table",
        )

        load_order_items_task = PythonOperator(
            task_id="load_order_items",
            python_callable=load_order_items,
            doc="Load order line items",
        )

        load_payments_task = PythonOperator(
            task_id="load_payments",
            python_callable=load_payments,
            doc="Load payment transactions",
        )

        load_inventory_task = PythonOperator(
            task_id="load_inventory",
            python_callable=load_inventory,
            doc="Load inventory levels",
        )

        # Analytics task
        run_analytics = PythonOperator(
            task_id="run_analytics",
            python_callable=run_analytics,
            doc="Run analytics aggregations and update materialized views",
        )

        # End task
        end = EmptyOperator(
            task_id="end",
            doc="Pipeline end marker",
        )

        # Task dependencies
        # Start -> Extract (parallel)
        start >> [extract_customers, extract_products, extract_orders]

        # Extract -> Validate -> Transform
        [extract_customers, extract_products, extract_orders] >> validate >> transform

        # Transform -> Load dimensions (parallel)
        transform >> [load_customers_task, load_products_task]

        # Load dimensions -> Load facts (parallel)
        [load_customers_task, load_products_task] >> [load_orders_task, load_order_items_task]

        # Load facts -> Load transactions (parallel)
        [load_orders_task, load_order_items_task] >> [load_payments_task, load_inventory_task]

        # Load transactions -> Analytics -> End
        [load_payments_task, load_inventory_task] >> run_analytics >> end

    return dag


# Create the DAG
dag = create_dag()
