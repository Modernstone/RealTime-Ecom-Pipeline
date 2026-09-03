"""
E-Commerce Analytics Dashboard
Main Streamlit application with tabs, filters, and real-time monitoring.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# Import query functions
from queries import (
    get_revenue_kpis,
    get_revenue_trend,
    get_top_products,
    get_category_breakdown,
    get_order_status_distribution,
    get_payment_method_breakdown,
    get_customer_segmentation,
    get_top_customers,
    get_low_stock_products,
    get_pipeline_health,
    get_daily_orders,
    get_regional_breakdown,
)

# Import component renderers
from components.kpis import render_kpi_cards, render_mini_kpi
from components.charts import (
    render_revenue_trend,
    render_orders_trend,
    render_category_breakdown,
    render_payment_method_pie,
    render_order_status_donut,
    render_customer_location_bar,
    render_product_performance,
)
from components.tables import (
    render_top_products_table,
    render_low_stock_table,
    render_top_customers_table,
    render_pipeline_status_table,
)


# Page configuration
st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_dark_theme():
    """Apply custom dark theme CSS."""
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0e1117;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #1e2130;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #636efa;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render sidebar filters and return selected values."""
    with st.sidebar:
        st.title("🔧 Filters")
        st.divider()

        # Date range filter
        st.subheader("📅 Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=30),
                max_value=datetime.now(),
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                max_value=datetime.now(),
            )

        st.divider()

        # Category filter
        st.subheader("📦 Category")
        categories = [
            "Electronics", "Clothing", "Home & Kitchen",
            "Books", "Sports", "Beauty", "Toys", "Automotive",
        ]
        selected_categories = st.multiselect(
            "Select Categories",
            options=categories,
            default=[],
        )

        st.divider()

        # Region filter
        st.subheader("🌍 Region")
        states = [
            "Maharashtra", "Karnataka", "Tamil Nadu", "Delhi",
            "Gujarat", "Rajasthan", "Uttar Pradesh", "West Bengal",
            "Telangana", "Kerala",
        ]
        selected_regions = st.multiselect(
            "Select States",
            options=states,
            default=[],
        )

        st.divider()

        # Status filter
        st.subheader("📋 Order Status")
        statuses = ["completed", "processing", "shipped", "pending", "cancelled", "refunded"]
        selected_statuses = st.multiselect(
            "Select Statuses",
            options=statuses,
            default=[],
        )

        st.divider()

        # Auto-refresh toggle
        st.subheader("🔄 Auto Refresh")
        auto_refresh = st.toggle("Enable Auto Refresh", value=False)
        refresh_interval = 60  # seconds

        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=30,
                max_value=300,
                value=60,
                step=30,
            )

        st.divider()

        # Manual refresh button
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "categories": selected_categories if selected_categories else None,
        "regions": selected_regions if selected_regions else None,
        "statuses": selected_statuses if selected_statuses else None,
        "auto_refresh": auto_refresh,
        "refresh_interval": refresh_interval,
    }


def render_executive_overview(filters):
    """Render Executive Overview tab."""
    st.header("📊 Executive Overview")

    try:
        # Get KPIs
        kpis_df = get_revenue_kpis(
            filters["start_date"],
            filters["end_date"],
            filters["categories"],
        )

        if not kpis_df.empty:
            kpis = kpis_df.iloc[0].to_dict()
            # Add delta values (would come from previous period comparison in production)
            kpis["revenue_delta"] = 12.5
            kpis["orders_delta"] = 8.3
            kpis["customers_delta"] = 15.2
            kpis["profit_delta"] = 10.8
            kpis["aov_delta"] = -2.1
            kpis["products_delta"] = 5.6

            render_kpi_cards(kpis)
        else:
            st.warning("Unable to fetch KPI data")

        st.divider()

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            # Revenue trend
            revenue_df = get_revenue_trend(
                filters["start_date"],
                filters["end_date"],
                filters["categories"],
            )
            render_revenue_trend(revenue_df)

        with col2:
            # Order status donut
            status_df = get_order_status_distribution(
                filters["start_date"],
                filters["end_date"],
            )
            render_order_status_donut(status_df)

        # Category breakdown
        st.subheader("📦 Revenue by Category")
        category_df = get_category_breakdown(
            filters["start_date"],
            filters["end_date"],
        )
        render_category_breakdown(category_df)

    except Exception as e:
        st.error(f"Error loading Executive Overview: {e}")


def render_sales_analytics(filters):
    """Render Sales Analytics tab."""
    st.header("💰 Sales Analytics")

    try:
        # Revenue and orders metrics
        kpis_df = get_revenue_kpis(
            filters["start_date"],
            filters["end_date"],
            filters["categories"],
        )

        if not kpis_df.empty:
            kpis = kpis_df.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                render_mini_kpi("Revenue", f"₹{kpis['total_revenue']:,.2f}", "+12.5%")
            with col2:
                render_mini_kpi("Orders", f"{kpis['total_orders']:,}", "+8.3%")
            with col3:
                render_mini_kpi("Profit", f"₹{kpis['total_profit']:,.2f}", "+10.8%")
            with col4:
                render_mini_kpi("AOV", f"₹{kpis['avg_order_value']:,.2f}", "-2.1%")

        st.divider()

        # Revenue trend
        st.subheader("📈 Revenue Trend")
        revenue_df = get_revenue_trend(
            filters["start_date"],
            filters["end_date"],
            filters["categories"],
        )
        render_revenue_trend(revenue_df)

        # Orders trend
        st.subheader("📊 Orders Trend")
        orders_df = get_daily_orders(
            filters["start_date"],
            filters["end_date"],
        )
        render_orders_trend(orders_df)

        # Category breakdown
        st.subheader("📦 Category Performance")
        category_df = get_category_breakdown(
            filters["start_date"],
            filters["end_date"],
        )
        render_category_breakdown(category_df)

    except Exception as e:
        st.error(f"Error loading Sales Analytics: {e}")


def render_product_analytics(filters):
    """Render Product Analytics tab."""
    st.header("📦 Product Analytics")

    try:
        # Top products table
        st.subheader("🏆 Top Products")
        top_products_df = get_top_products(
            limit=10,
            start_date=filters["start_date"],
            end_date=filters["end_date"],
            category=filters["categories"],
        )
        render_top_products_table(top_products_df)

        st.divider()

        # Product performance chart
        st.subheader("📊 Product Performance")
        render_product_performance(top_products_df)

        st.divider()

        # Low stock alerts
        st.subheader("⚠️ Low Stock Alerts")
        low_stock_df = get_low_stock_products()
        render_low_stock_table(low_stock_df)

    except Exception as e:
        st.error(f"Error loading Product Analytics: {e}")


def render_customer_analytics(filters):
    """Render Customer Analytics tab."""
    st.header("👥 Customer Analytics")

    try:
        # Customer KPIs
        kpis_df = get_revenue_kpis(
            filters["start_date"],
            filters["end_date"],
            filters["categories"],
        )

        if not kpis_df.empty:
            kpis = kpis_df.iloc[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                render_mini_kpi("Total Customers", f"{kpis['total_customers']:,}", "+15.2%")
            with col2:
                render_mini_kpi("Avg Order Value", f"₹{kpis['avg_order_value']:,.2f}", "-2.1%")
            with col3:
                render_mini_kpi("Revenue per Customer", f"₹{kpis['total_revenue']/max(kpis['total_customers'],1):,.2f}", "+5.3%")

        st.divider()

        # Customer segmentation
        st.subheader("🎯 Customer Segmentation")
        segmentation_df = get_customer_segmentation()
        if not segmentation_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(
                    segmentation_df,
                    use_container_width=True,
                    hide_index=True,
                )
            with col2:
                import plotly.express as px
                fig = px.pie(
                    segmentation_df,
                    names="segment",
                    values="customer_count",
                    title="Customer Distribution by Segment",
                    hole=0.4,
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Top customers
        st.subheader("🏆 Top Customers")
        top_customers_df = get_top_customers(limit=10)
        render_top_customers_table(top_customers_df)

        st.divider()

        # Regional breakdown
        st.subheader("🌍 Regional Breakdown")
        regional_df = get_regional_breakdown(
            filters["start_date"],
            filters["end_date"],
        )
        render_customer_location_bar(regional_df)

    except Exception as e:
        st.error(f"Error loading Customer Analytics: {e}")


def render_orders_operations(filters):
    """Render Orders & Operations tab."""
    st.header("📋 Orders & Operations")

    try:
        # Order status distribution
        st.subheader("📊 Order Status Distribution")
        status_df = get_order_status_distribution(
            filters["start_date"],
            filters["end_date"],
        )
        render_order_status_donut(status_df)

        st.divider()

        # Payment methods
        st.subheader("💳 Payment Methods")
        payment_df = get_payment_method_breakdown(
            filters["start_date"],
            filters["end_date"],
        )
        render_payment_method_pie(payment_df)

        st.divider()

        # Delivery metrics
        st.subheader("🚚 Delivery Metrics")
        if not status_df.empty:
            total_orders = status_df["count"].sum()
            completed = status_df[status_df["status"] == "completed"]["count"].sum() if "completed" in status_df["status"].values else 0
            cancelled = status_df[status_df["status"] == "cancelled"]["count"].sum() if "cancelled" in status_df["status"].values else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                render_mini_kpi("Total Orders", f"{total_orders:,}")
            with col2:
                completion_rate = (completed / total_orders * 100) if total_orders > 0 else 0
                render_mini_kpi("Completion Rate", f"{completion_rate:.1f}", suffix="%")
            with col3:
                cancellation_rate = (cancelled / total_orders * 100) if total_orders > 0 else 0
                render_mini_kpi("Cancellation Rate", f"{cancellation_rate:.1f}", suffix="%")

    except Exception as e:
        st.error(f"Error loading Orders & Operations: {e}")


def render_pipeline_monitoring(filters):
    """Render Pipeline Monitoring tab."""
    st.header("🔧 Pipeline Monitoring")

    try:
        # Pipeline health KPIs
        st.subheader("📊 Pipeline Health")
        pipeline_df = get_pipeline_health()

        if not pipeline_df.empty:
            total_tasks = len(pipeline_df)
            successful = len(pipeline_df[pipeline_df["status"] == "success"])
            failed = len(pipeline_df[pipeline_df["status"] == "failed"])
            running = len(pipeline_df[pipeline_df["status"] == "running"])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                render_mini_kpi("Total Tasks", f"{total_tasks}")
            with col2:
                render_mini_kpi("Successful", f"{successful}", delta_color="normal")
            with col3:
                render_mini_kpi("Failed", f"{failed}", delta_color="inverse")
            with col4:
                render_mini_kpi("Running", f"{running}")

            # Success rate
            success_rate = (successful / total_tasks * 100) if total_tasks > 0 else 0
            st.progress(success_rate / 100)
            st.caption(f"Success Rate: {success_rate:.1f}%")

        st.divider()

        # Pipeline task status table
        st.subheader("📋 Task Status")
        render_pipeline_status_table(pipeline_df)

        # Auto-refresh indicator
        if filters.get("auto_refresh"):
            st.divider()
            st.info(f"🔄 Auto-refreshing every {filters['refresh_interval']} seconds")

    except Exception as e:
        st.error(f"Error loading Pipeline Monitoring: {e}")


def main():
    """Main application entry point."""
    apply_dark_theme()

    # Render sidebar and get filters
    filters = render_sidebar()

    # Main content area
    st.title("🛒 E-Commerce Analytics Dashboard")
    st.caption(f"Data from {filters['start_date']} to {filters['end_date']}")

    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Executive Overview",
        "💰 Sales Analytics",
        "📦 Product Analytics",
        "👥 Customer Analytics",
        "📋 Orders & Operations",
        "🔧 Pipeline Monitoring",
    ])

    # Render each tab
    with tab1:
        render_executive_overview(filters)

    with tab2:
        render_sales_analytics(filters)

    with tab3:
        render_product_analytics(filters)

    with tab4:
        render_customer_analytics(filters)

    with tab5:
        render_orders_operations(filters)

    with tab6:
        render_pipeline_monitoring(filters)

    # Auto-refresh logic
    if filters.get("auto_refresh"):
        time.sleep(filters["refresh_interval"])
        st.rerun()


if __name__ == "__main__":
    main()
