"""
Chart Components for the E-Commerce Analytics Dashboard.
All charts use Plotly with a consistent dark theme.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd


# Consistent dark theme configuration
DARK_THEME = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#fafafa"},
    "colorway": [
        "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
        "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
        "#FF97FF", "#FECB52",
    ],
}


def render_revenue_trend(df):
    """
    Render a line chart of revenue over time.

    Args:
        df: DataFrame with columns: date, revenue
    """
    if df.empty:
        st.warning("No revenue data available")
        return

    fig = px.line(
        df,
        x="date",
        y="revenue",
        title="Revenue Trend",
        labels={"date": "Date", "revenue": "Revenue (₹)"},
        markers=True,
    )

    fig.update_layout(
        **DARK_THEME,
        xaxis_title="Date",
        yaxis_title="Revenue (₹)",
        hovermode="x unified",
    )

    fig.update_traces(
        line=dict(width=2),
        hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_orders_trend(df):
    """
    Render a bar chart of orders over time.

    Args:
        df: DataFrame with columns: date, orders (or order_count)
    """
    if df.empty:
        st.warning("No orders data available")
        return

    # Handle different column names
    orders_col = "orders" if "orders" in df.columns else "order_count"

    fig = px.bar(
        df,
        x="date",
        y=orders_col,
        title="Orders Trend",
        labels={"date": "Date", orders_col: "Orders"},
    )

    fig.update_layout(
        **DARK_THEME,
        xaxis_title="Date",
        yaxis_title="Orders",
        hovermode="x unified",
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Orders: %{y:,}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_category_breakdown(df):
    """
    Render a horizontal bar chart of revenue by category.

    Args:
        df: DataFrame with columns: category, revenue
    """
    if df.empty:
        st.warning("No category data available")
        return

    # Sort by revenue for better visualization
    df_sorted = df.sort_values("revenue", ascending=True)

    fig = px.bar(
        df_sorted,
        y="category",
        x="revenue",
        title="Revenue by Category",
        labels={"category": "Category", "revenue": "Revenue (₹)"},
        orientation="h",
    )

    fig.update_layout(
        **DARK_THEME,
        xaxis_title="Revenue (₹)",
        yaxis_title="",
        showlegend=False,
    )

    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.2f}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_payment_method_pie(df):
    """
    Render a pie chart of payment methods.

    Args:
        df: DataFrame with columns: payment_method, count
    """
    if df.empty:
        st.warning("No payment data available")
        return

    fig = px.pie(
        df,
        names="payment_method",
        values="count",
        title="Payment Methods Distribution",
        hole=0.3,
    )

    fig.update_layout(
        **DARK_THEME,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )

    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_order_status_donut(df):
    """
    Render a donut chart of order statuses.

    Args:
        df: DataFrame with columns: status, count
    """
    if df.empty:
        st.warning("No order status data available")
        return

    # Color mapping for order statuses
    status_colors = {
        "completed": "#00CC96",
        "processing": "#636EFA",
        "shipped": "#19D3F3",
        "pending": "#FFA15A",
        "cancelled": "#EF553B",
        "refunded": "#AB63FA",
    }

    colors = [status_colors.get(s.lower(), "#888888") for s in df["status"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=df["status"],
                values=df["count"],
                hole=0.5,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        **DARK_THEME,
        title="Order Status Distribution",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )

    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_customer_location_bar(df):
    """
    Render a bar chart of orders by state.

    Args:
        df: DataFrame with columns: state, order_count
    """
    if df.empty:
        st.warning("No regional data available")
        return

    # Sort by order count and take top 15 for readability
    df_sorted = df.sort_values("order_count", ascending=False).head(15)

    fig = px.bar(
        df_sorted,
        x="state",
        y="order_count",
        title="Orders by State (Top 15)",
        labels={"state": "State", "order_count": "Orders"},
    )

    fig.update_layout(
        **DARK_THEME,
        xaxis_title="State",
        yaxis_title="Orders",
        xaxis_tickangle=-45,
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Orders: %{y:,}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_product_performance(df):
    """
    Render a bar chart of top products by revenue.

    Args:
        df: DataFrame with columns: product_name, revenue
    """
    if df.empty:
        st.warning("No product data available")
        return

    # Sort by revenue for better visualization
    df_sorted = df.sort_values("revenue", ascending=True).tail(10)

    fig = px.bar(
        df_sorted,
        y="product_name",
        x="revenue",
        title="Top Products by Revenue",
        labels={"product_name": "Product", "revenue": "Revenue (₹)"},
        orientation="h",
    )

    fig.update_layout(
        **DARK_THEME,
        xaxis_title="Revenue (₹)",
        yaxis_title="",
        showlegend=False,
        height=400,
    )

    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.2f}<extra></extra>",
    )

    st.plotly_chart(fig, use_container_width=True)
