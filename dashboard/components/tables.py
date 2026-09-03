"""
Table Components for the E-Commerce Analytics Dashboard.
Renders styled tables using Streamlit's st.dataframe() with column_config.
"""

import streamlit as st
import pandas as pd


def render_top_products_table(df):
    """
    Render a styled table of top products.

    Args:
        df: DataFrame with columns: product_id, product_name, category, units_sold, revenue
    """
    if df.empty:
        st.warning("No product data available")
        return

    # Add rank column
    df = df.copy()
    df.insert(0, "rank", range(1, len(df) + 1))

    # Configure columns
    column_config = {
        "rank": st.column_config.NumberColumn(
            "Rank",
            help="Product ranking by revenue",
            format="%d",
            width="small",
        ),
        "product_id": st.column_config.TextColumn(
            "Product ID",
            help="Unique product identifier",
            width="medium",
        ),
        "product_name": st.column_config.TextColumn(
            "Product Name",
            help="Product name",
            width="large",
        ),
        "category": st.column_config.TextColumn(
            "Category",
            help="Product category",
            width="medium",
        ),
        "units_sold": st.column_config.NumberColumn(
            "Units Sold",
            help="Total units sold",
            format="%d",
            width="small",
        ),
        "revenue": st.column_config.NumberColumn(
            "Revenue",
            help="Total revenue generated",
            format="₹%.2f",
            width="medium",
        ),
    }

    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
    )


def render_low_stock_table(df):
    """
    Render a table with color-coded stock status.

    Args:
        df: DataFrame with columns: product_id, product_name, category, stock_quantity, status
    """
    if df.empty:
        st.info("All products are well-stocked")
        return

    # Configure columns
    column_config = {
        "product_id": st.column_config.TextColumn(
            "Product ID",
            help="Unique product identifier",
            width="medium",
        ),
        "product_name": st.column_config.TextColumn(
            "Product Name",
            help="Product name",
            width="large",
        ),
        "category": st.column_config.TextColumn(
            "Category",
            help="Product category",
            width="medium",
        ),
        "stock_quantity": st.column_config.NumberColumn(
            "Stock",
            help="Current stock quantity",
            format="%d",
            width="small",
        ),
        "status": st.column_config.TextColumn(
            "Status",
            help="Stock status indicator",
            width="medium",
        ),
    }

    # Apply color styling based on status
    def highlight_status(row):
        styles = [""] * len(row)
        if "status" in row.index:
            status = row["status"]
            if status == "Out of Stock":
                styles = ["background-color: #ff4b4b; color: white"] * len(row)
            elif status == "Critical":
                styles = ["background-color: #ff8c00; color: white"] * len(row)
            elif status == "Low Stock":
                styles = ["background-color: #ffd700; color: black"] * len(row)
        return styles

    styled_df = df.style.apply(highlight_status, axis=1)

    st.dataframe(
        styled_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
    )


def render_top_customers_table(df):
    """
    Render a table of top customers.

    Args:
        df: DataFrame with columns: customer_id, customer_name, email, orders, total_spent
    """
    if df.empty:
        st.warning("No customer data available")
        return

    # Add rank column
    df = df.copy()
    df.insert(0, "rank", range(1, len(df) + 1))

    # Configure columns
    column_config = {
        "rank": st.column_config.NumberColumn(
            "Rank",
            help="Customer ranking by spending",
            format="%d",
            width="small",
        ),
        "customer_id": st.column_config.TextColumn(
            "Customer ID",
            help="Unique customer identifier",
            width="medium",
        ),
        "customer_name": st.column_config.TextColumn(
            "Customer Name",
            help="Customer full name",
            width="large",
        ),
        "email": st.column_config.TextColumn(
            "Email",
            help="Customer email address",
            width="large",
        ),
        "orders": st.column_config.NumberColumn(
            "Orders",
            help="Total number of orders",
            format="%d",
            width="small",
        ),
        "total_spent": st.column_config.NumberColumn(
            "Total Spent",
            help="Total amount spent",
            format="₹%.2f",
            width="medium",
        ),
    }

    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
    )


def render_pipeline_status_table(df):
    """
    Render a table showing pipeline task status with color indicators.

    Args:
        df: DataFrame with columns: run_id, dag_id, task_id, status, start_time, end_time, duration_seconds
    """
    if df.empty:
        st.warning("No pipeline data available")
        return

    # Configure columns
    column_config = {
        "run_id": st.column_config.TextColumn(
            "Run ID",
            help="Pipeline run identifier",
            width="medium",
        ),
        "dag_id": st.column_config.TextColumn(
            "DAG",
            help="DAG identifier",
            width="medium",
        ),
        "task_id": st.column_config.TextColumn(
            "Task",
            help="Task identifier",
            width="medium",
        ),
        "status": st.column_config.TextColumn(
            "Status",
            help="Task execution status",
            width="small",
        ),
        "start_time": st.column_config.DatetimeColumn(
            "Start Time",
            help="Task start time",
            format="YYYY-MM-DD HH:mm:ss",
            width="medium",
        ),
        "end_time": st.column_config.DatetimeColumn(
            "End Time",
            help="Task end time",
            format="YYYY-MM-DD HH:mm:ss",
            width="medium",
        ),
        "duration_seconds": st.column_config.NumberColumn(
            "Duration (s)",
            help="Task duration in seconds",
            format="%.1f",
            width="small",
        ),
    }

    # Apply color styling based on status
    def highlight_status(row):
        styles = [""] * len(row)
        if "status" in row.index:
            status = row["status"]
            if status == "success":
                styles = ["background-color: #00cc96; color: white"] * len(row)
            elif status == "running":
                styles = ["background-color: #636efa; color: white"] * len(row)
            elif status == "failed":
                styles = ["background-color: #ef553b; color: white"] * len(row)
            elif status == "pending":
                styles = ["background-color: #ffa15a; color: black"] * len(row)
        return styles

    styled_df = df.style.apply(highlight_status, axis=1)

    st.dataframe(
        styled_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
    )
