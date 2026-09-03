"""
KPI Card Components for the E-Commerce Analytics Dashboard.
Renders metric cards using Streamlit's st.metric().
"""

import streamlit as st


def render_mini_kpi(label, value, delta=None, prefix="", suffix=""):
    """
    Render a single mini KPI card.

    Args:
        label: KPI label text
        value: Current value
        delta: Change value (can be string like "+12.5%")
        prefix: Prefix for value (e.g., "₹")
        suffix: Suffix for value (e.g., "%")
    """
    formatted_value = f"{prefix}{value}{suffix}" if value is not None else "N/A"
    st.metric(label=label, value=formatted_value, delta=delta)


def render_kpi_cards(kpis_dict):
    """
    Render 6 KPI cards in a 3-column layout.

    Args:
        kpis_dict: Dictionary with KPI data containing:
            - total_revenue: Current revenue
            - revenue_delta: Revenue change percentage
            - total_orders: Current orders
            - orders_delta: Orders change percentage
            - total_customers: Current customers
            - customers_delta: Customers change percentage
            - total_profit: Current profit
            - profit_delta: Profit change percentage
            - avg_order_value: Current AOV
            - aov_delta: AOV change percentage
            - products_sold: Current products sold
            - products_delta: Products sold change percentage
    """
    # Row 1: Revenue, Orders, Customers
    col1, col2, col3 = st.columns(3)

    with col1:
        revenue = kpis_dict.get("total_revenue", 0)
        revenue_delta = kpis_dict.get("revenue_delta")
        delta_str = f"{revenue_delta:+.1f}%" if revenue_delta is not None else None
        st.metric(
            label="Total Revenue",
            value=f"₹{revenue:,.2f}",
            delta=delta_str,
            delta_color="normal",
        )

    with col2:
        orders = kpis_dict.get("total_orders", 0)
        orders_delta = kpis_dict.get("orders_delta")
        delta_str = f"{orders_delta:+.1f}%" if orders_delta is not None else None
        st.metric(
            label="Total Orders",
            value=f"{orders:,}",
            delta=delta_str,
            delta_color="normal",
        )

    with col3:
        customers = kpis_dict.get("total_customers", 0)
        customers_delta = kpis_dict.get("customers_delta")
        delta_str = f"{customers_delta:+.1f}%" if customers_delta is not None else None
        st.metric(
            label="Total Customers",
            value=f"{customers:,}",
            delta=delta_str,
            delta_color="normal",
        )

    # Row 2: Profit, AOV, Products Sold
    col4, col5, col6 = st.columns(3)

    with col4:
        profit = kpis_dict.get("total_profit", 0)
        profit_delta = kpis_dict.get("profit_delta")
        delta_str = f"{profit_delta:+.1f}%" if profit_delta is not None else None
        st.metric(
            label="Total Profit",
            value=f"₹{profit:,.2f}",
            delta=delta_str,
            delta_color="normal",
        )

    with col5:
        aov = kpis_dict.get("avg_order_value", 0)
        aov_delta = kpis_dict.get("aov_delta")
        delta_str = f"{aov_delta:+.1f}%" if aov_delta is not None else None
        st.metric(
            label="Avg Order Value",
            value=f"₹{aov:,.2f}",
            delta=delta_str,
            delta_color="normal",
        )

    with col6:
        products = kpis_dict.get("products_sold", 0)
        products_delta = kpis_dict.get("products_delta")
        delta_str = f"{products_delta:+.1f}%" if products_delta is not None else None
        st.metric(
            label="Products Sold",
            value=f"{products:,}",
            delta=delta_str,
            delta_color="normal",
        )
