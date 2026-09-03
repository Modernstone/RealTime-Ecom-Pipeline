-- ============================================================
-- Real-Time E-Commerce Data Pipeline - Schema Definition
-- ============================================================

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    category_id     VARCHAR(50)     PRIMARY KEY,
    category_name   VARCHAR(255)    NOT NULL,
    parent_category VARCHAR(50),
    description     TEXT,
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id     VARCHAR(50)     PRIMARY KEY,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    gender          VARCHAR(20),
    age             INT             CHECK (age > 0 AND age < 150),
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(100),
    signup_date     DATE            NOT NULL,
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP       DEFAULT NOW()
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id      VARCHAR(50)     PRIMARY KEY,
    product_name    VARCHAR(255)    NOT NULL,
    category_id     VARCHAR(50)     NOT NULL REFERENCES categories(category_id),
    subcategory     VARCHAR(100),
    brand           VARCHAR(100),
    description     TEXT,
    price           DECIMAL(10,2)   NOT NULL CHECK (price >= 0),
    cost_price      DECIMAL(10,2)   NOT NULL CHECK (cost_price >= 0),
    stock_quantity  INT             NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    rating          DECIMAL(2,1)    CHECK (rating >= 0 AND rating <= 5),
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP       DEFAULT NOW()
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id        VARCHAR(50)     PRIMARY KEY,
    customer_id     VARCHAR(50)     NOT NULL REFERENCES customers(customer_id),
    order_date      DATE            NOT NULL,
    order_status    VARCHAR(30)     NOT NULL CHECK (order_status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned')),
    payment_status  VARCHAR(30)     NOT NULL CHECK (payment_status IN ('pending', 'authorized', 'paid', 'failed', 'refunded', 'partially_refunded')),
    payment_method  VARCHAR(50),
    shipping_city   VARCHAR(100),
    shipping_state  VARCHAR(100),
    total_amount    DECIMAL(12,2)   NOT NULL CHECK (total_amount >= 0),
    discount_amount DECIMAL(10,2)   DEFAULT 0 CHECK (discount_amount >= 0),
    tax_amount      DECIMAL(10,2)   DEFAULT 0 CHECK (tax_amount >= 0),
    created_at      TIMESTAMP       DEFAULT NOW(),
    updated_at      TIMESTAMP       DEFAULT NOW()
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id   VARCHAR(50)     PRIMARY KEY,
    order_id        VARCHAR(50)     NOT NULL REFERENCES orders(order_id),
    product_id      VARCHAR(50)     NOT NULL REFERENCES products(product_id),
    quantity        INT             NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(10,2)   NOT NULL CHECK (unit_price >= 0),
    discount        DECIMAL(10,2)   DEFAULT 0 CHECK (discount >= 0),
    subtotal        DECIMAL(12,2)   NOT NULL CHECK (subtotal >= 0),
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    payment_id              VARCHAR(50)     PRIMARY KEY,
    order_id                VARCHAR(50)     NOT NULL REFERENCES orders(order_id),
    payment_method          VARCHAR(50)     NOT NULL,
    payment_status          VARCHAR(30)     NOT NULL CHECK (payment_status IN ('pending', 'authorized', 'completed', 'failed', 'refunded', 'partially_refunded')),
    amount                  DECIMAL(12,2)   NOT NULL CHECK (amount >= 0),
    transaction_date        TIMESTAMP       NOT NULL,
    transaction_reference   VARCHAR(255)    UNIQUE,
    created_at              TIMESTAMP       DEFAULT NOW()
);

-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id        VARCHAR(50)     PRIMARY KEY,
    product_id          VARCHAR(50)     NOT NULL UNIQUE REFERENCES products(product_id),
    warehouse           VARCHAR(100),
    stock_quantity      INT             NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    reserved_quantity   INT             NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    reorder_level       INT             NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
    last_updated        TIMESTAMP       DEFAULT NOW()
);

-- Pipeline logs table
CREATE TABLE IF NOT EXISTS pipeline_logs (
    log_id              SERIAL          PRIMARY KEY,
    run_id              VARCHAR(50)     NOT NULL,
    pipeline_name       VARCHAR(100)    NOT NULL,
    status              VARCHAR(20)     NOT NULL CHECK (status IN ('started', 'running', 'completed', 'failed', 'cancelled')),
    started_at          TIMESTAMP       NOT NULL,
    completed_at        TIMESTAMP,
    duration_seconds    INT             CHECK (duration_seconds >= 0),
    records_processed   INT             DEFAULT 0 CHECK (records_processed >= 0),
    records_valid       INT             DEFAULT 0 CHECK (records_valid >= 0),
    records_invalid     INT             DEFAULT 0 CHECK (records_invalid >= 0),
    records_duplicate   INT             DEFAULT 0 CHECK (records_duplicate >= 0),
    error_message       TEXT,
    created_at          TIMESTAMP       DEFAULT NOW()
);
