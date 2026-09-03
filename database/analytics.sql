-- ============================================================
-- Real-Time E-Commerce Data Pipeline - Analytical Views
-- ============================================================

-- ------------------------------------------------------------
-- Revenue Summary: overall totals
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_revenue_summary AS
SELECT
    COUNT(DISTINCT o.order_id)      AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_revenue,
    COALESCE(AVG(o.total_amount), 0) AS avg_order_value,
    COALESCE(SUM(oi.subtotal) - SUM(oi.quantity * p.cost_price), 0) AS total_profit
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p     ON p.product_id = oi.product_id
WHERE o.order_status NOT IN ('cancelled', 'returned');

-- ------------------------------------------------------------
-- Monthly Revenue: revenue, orders, and profit by month
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_monthly_revenue AS
SELECT
    DATE_TRUNC('month', o.order_date)::DATE             AS month,
    COUNT(DISTINCT o.order_id)                          AS total_orders,
    COALESCE(SUM(o.total_amount), 0)                    AS total_revenue,
    COALESCE(SUM(o.total_amount - o.discount_amount - o.tax_amount), 0) AS estimated_profit
FROM orders o
WHERE o.order_status NOT IN ('cancelled', 'returned')
GROUP BY DATE_TRUNC('month', o.order_date)
ORDER BY month DESC;

-- ------------------------------------------------------------
-- Top 10 Products by Revenue
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_top_products AS
SELECT
    p.product_id,
    p.product_name,
    p.brand,
    c.category_name,
    SUM(oi.quantity)            AS units_sold,
    SUM(oi.subtotal)            AS total_revenue
FROM order_items oi
JOIN products p  ON p.product_id  = oi.product_id
JOIN categories c ON c.category_id = p.category_id
JOIN orders o    ON o.order_id    = oi.order_id
WHERE o.order_status NOT IN ('cancelled', 'returned')
GROUP BY p.product_id, p.product_name, p.brand, c.category_name
ORDER BY total_revenue DESC
LIMIT 10;

-- ------------------------------------------------------------
-- Top Categories by Revenue
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_top_categories AS
SELECT
    c.category_id,
    c.category_name,
    COUNT(DISTINCT o.order_id)  AS total_orders,
    SUM(oi.subtotal)            AS total_revenue
FROM order_items oi
JOIN products p   ON p.product_id  = oi.product_id
JOIN categories c ON c.category_id = p.category_id
JOIN orders o     ON o.order_id    = oi.order_id
WHERE o.order_status NOT IN ('cancelled', 'returned')
GROUP BY c.category_id, c.category_name
ORDER BY total_revenue DESC;

-- ------------------------------------------------------------
-- Customer Segmentation by Order Count
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_customer_segmentation AS
SELECT
    cu.customer_id,
    cu.first_name,
    cu.last_name,
    cu.email,
    COUNT(o.order_id) AS order_count,
    SUM(o.total_amount) AS total_spent,
    CASE
        WHEN COUNT(o.order_id) BETWEEN 1 AND 2   THEN 'New'
        WHEN COUNT(o.order_id) BETWEEN 3 AND 10  THEN 'Returning'
        WHEN COUNT(o.order_id) >= 11             THEN 'High-Value'
        ELSE 'Inactive'
    END AS segment
FROM customers cu
LEFT JOIN orders o ON o.customer_id = cu.customer_id
    AND o.order_status NOT IN ('cancelled', 'returned')
GROUP BY cu.customer_id, cu.first_name, cu.last_name, cu.email;

-- ------------------------------------------------------------
-- Top 10 Customers by Spending
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_top_customers AS
SELECT
    cu.customer_id,
    cu.first_name,
    cu.last_name,
    cu.email,
    cu.city,
    cu.country,
    COUNT(o.order_id)       AS total_orders,
    SUM(o.total_amount)     AS total_spent,
    AVG(o.total_amount)     AS avg_order_value
FROM customers cu
JOIN orders o ON o.customer_id = cu.customer_id
WHERE o.order_status NOT IN ('cancelled', 'returned')
GROUP BY cu.customer_id, cu.first_name, cu.last_name, cu.email, cu.city, cu.country
ORDER BY total_spent DESC
LIMIT 10;

-- ------------------------------------------------------------
-- Order Status Distribution
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_order_status_distribution AS
SELECT
    order_status,
    COUNT(*)                AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM orders
GROUP BY order_status
ORDER BY order_count DESC;

-- ------------------------------------------------------------
-- Payment Method Breakdown
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_payment_method_breakdown AS
SELECT
    payment_method,
    COUNT(*)                AS transaction_count,
    SUM(amount)             AS total_amount,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM payments
WHERE payment_status = 'completed'
GROUP BY payment_method
ORDER BY total_amount DESC;

-- ------------------------------------------------------------
-- Low Stock Products (available stock below reorder level)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_low_stock_products AS
SELECT
    p.product_id,
    p.product_name,
    p.brand,
    c.category_name,
    i.warehouse,
    i.stock_quantity,
    i.reserved_quantity,
    (i.stock_quantity - i.reserved_quantity) AS available_stock,
    i.reorder_level
FROM inventory i
JOIN products p   ON p.product_id  = i.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE (i.stock_quantity - i.reserved_quantity) < i.reorder_level
ORDER BY available_stock ASC;

-- ------------------------------------------------------------
-- Pipeline Health: latest run metrics per pipeline
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_pipeline_health AS
SELECT DISTINCT ON (pipeline_name)
    pipeline_name,
    run_id,
    status,
    started_at,
    completed_at,
    duration_seconds,
    records_processed,
    records_valid,
    records_invalid,
    records_duplicate,
    error_message
FROM pipeline_logs
ORDER BY pipeline_name, started_at DESC;

-- ------------------------------------------------------------
-- Daily Orders: order count by day for the last 30 days
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_daily_orders AS
SELECT
    order_date,
    COUNT(*)                AS order_count,
    SUM(total_amount)       AS total_revenue
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY order_date
ORDER BY order_date DESC;
