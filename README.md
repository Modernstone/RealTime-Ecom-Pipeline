# Real-Time E-Commerce Data Pipeline & Analytics Platform

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-2.7-017CEE?logo=apache-airflow&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A production-grade data pipeline that extracts e-commerce data from multiple sources, transforms and validates it, loads it into PostgreSQL, and surfaces insights through an interactive Streamlit dashboard. Orchestrated with Apache Airflow for scheduled and incremental runs.

---

## Architecture

```
+------------------+     +-------------------+     +------------------+
|   Data Sources   |     |   Extraction      |     |  Transformation  |
|                  |     |                   |     |                  |
| customers.json   +---->| EcommerceAPIClient+---->| DataCleaner      |
| products.json    |     |                   |     | DataTransformer  |
| orders.json      |     | - Load JSON       |     |                  |
| order_items.json |     | - Parse dates     |     | - Parse currency |
| categories.json  |     | - Incremental     |     | - Normalize      |
| reviews.json     |     |   loading         |     | - Deduplicate    |
+------------------+     +-------------------+     | - Calculate      |
                                                   +--------+---------+
                                                            |
                                                            v
+------------------+     +-------------------+     +------------------+
|   PostgreSQL     |     |   Loading         |     |  Validation      |
|                  |     |                   |     |                  |
| customers        <----+ PostgresLoader     <----+ DataValidator     |
| products         |     |                   |     |                  |
| orders           |     | - Upsert (ON      |     | - Schema checks  |
| order_items      |     |   CONFLICT)       |     | - Referential    |
| categories       |     | - Pipeline logs   |     |   integrity      |
| reviews          |     | - CSV export      |     | - Quality score  |
| pipeline_logs    |     +-------------------+     +------------------+
+--------+---------+
         |
         v
+------------------+     +-------------------+
|   Dashboard      |     |   Orchestration   |
|                  |     |                   |
| Streamlit App    |     | Apache Airflow    |
| - 6 Tabs         |     | - DAG scheduling  |
| - Real-time      |     | - Incremental     |
|   charts         |     |   runs            |
| - KPI metrics    |     | - Monitoring      |
+------------------+     +-------------------+
```

---

## Tech Stack

| Layer            | Technology           | Purpose                              |
|------------------|----------------------|--------------------------------------|
| Language         | Python 3.11          | Core pipeline logic                  |
| Database         | PostgreSQL 15        | Analytical data warehouse            |
| Orchestration    | Apache Airflow 2.7   | DAG scheduling and monitoring        |
| Dashboard        | Streamlit            | Interactive analytics UI             |
| Data Validation  | Custom validators    | Schema and integrity checks          |
| Containerization | Docker & Compose     | Reproducible deployments             |
| Testing          | pytest               | Unit and integration tests           |
| CI/CD            | GitHub Actions       | Automated testing and deployment     |

---

## Prerequisites

- **Python 3.11+**
- **PostgreSQL 15+**
- **Docker & Docker Compose** (optional, for containerized deployment)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/org/ecommerce-pipeline.git
cd ecommerce-pipeline
```

### 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

### 4. Set Up PostgreSQL

```bash
# Create the database
createdb ecommerce_db

# Run schema migrations
psql -d ecommerce_db -f database/schema.sql

# Seed initial data
psql -d ecommerce_db -f database/seed_data.sql

# Create indexes for performance
psql -d ecommerce_db -f database/indexes.sql
```

### 5. Run the Pipeline

```bash
python src/pipeline.py
```

The pipeline will:
1. Extract data from JSON files in `data/raw/`
2. Clean and transform records
3. Validate data quality
4. Load into PostgreSQL
5. Export processed CSVs to `data/processed/`

### 6. Start the Dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 7. Start Airflow (Optional)

```bash
# Initialize the Airflow database
airflow db init

# Create an admin user
airflow users create --username admin --password admin \
  --firstname Admin --lastname User --role Admin --email admin@example.com

# Start the webserver and scheduler
airflow webserver --port 8080 &
airflow scheduler &
```

Open [http://localhost:8080](http://localhost:8080) to access the Airflow UI.

---

## Docker Quick Start

```bash
# Copy and configure environment variables
cp .env.example .env

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f pipeline

# Stop all services
docker-compose down
```

**Services exposed:**

| Service          | URL                          |
|------------------|------------------------------|
| Dashboard        | http://localhost:8501         |
| Airflow UI       | http://localhost:8080         |
| PostgreSQL       | localhost:5432               |

---

## Project Structure

```
ecommerce-pipeline/
|-- src/
|   |-- pipeline.py                 # Main pipeline orchestrator
|   |-- extraction/
|   |   |-- __init__.py
|   |   |-- api_client.py           # EcommerceAPIClient
|   |-- transformation/
|   |   |-- __init__.py
|   |   |-- cleaner.py              # DataCleaner
|   |   |-- transformer.py          # DataTransformer
|   |-- validation/
|   |   |-- __init__.py
|   |   |-- validator.py            # DataValidator
|   |-- database/
|       |-- __init__.py
|       |-- loader.py               # PostgresLoader
|-- dashboard/
|   |-- app.py                      # Streamlit dashboard
|-- database/
|   |-- schema.sql                  # Table definitions
|   |-- seed_data.sql               # Initial seed data
|   |-- indexes.sql                 # Performance indexes
|-- dags/
|   |-- ecommerce_pipeline_dag.py   # Airflow DAG definition
|-- data/
|   |-- raw/                        # Source JSON files
|   |-- processed/                  # Output CSV files
|       |-- customers.csv
|       |-- products.csv
|       |-- orders.csv
|       |-- order_items.csv
|-- tests/
|   |-- test_extraction.py
|   |-- test_transformation.py
|   |-- test_validation.py
|   |-- test_database.py
|-- config/
|   |-- settings.py                 # Application configuration
|-- logs/
|   |-- pipeline.log                # Pipeline execution logs
|-- Dockerfile                      # Multi-stage Docker build
|-- Dockerfile.airflow              # Airflow-specific image
|-- docker-compose.yml              # Service orchestration
|-- requirements.txt                # Python dependencies
|-- .env.example                    # Environment template
|-- README.md
|-- LICENSE
```

---

## Database Schema

The PostgreSQL database contains the following tables:

| Table           | Description                          | Key Columns                                          |
|-----------------|--------------------------------------|------------------------------------------------------|
| `customers`     | Customer profiles                    | customer_id (PK), email, city, signup_date           |
| `products`      | Product catalog with pricing         | product_id (PK), price, cost_price, stock_quantity   |
| `categories`    | Product category hierarchy           | category_id (PK), category_name                      |
| `orders`        | Order headers                        | order_id (PK), customer_id (FK), total_amount        |
| `order_items`   | Individual line items per order      | order_item_id (PK), order_id (FK), product_id (FK)   |
| `reviews`       | Customer product reviews             | review_id (PK), product_id (FK), customer_id (FK)    |
| `pipeline_logs` | Pipeline execution audit trail       | run_id (PK), status, records_processed, duration     |

All tables use `ON CONFLICT` upsert logic for idempotent loads.

---

## Dashboard Features

The Streamlit dashboard provides **6 interactive tabs**:

1. **Overview** -- High-level KPIs: total revenue, order count, average order value, active customers
2. **Sales Trends** -- Time-series charts for daily/weekly/monthly revenue and order volume
3. **Product Analytics** -- Top products by revenue, category breakdown, stock levels, profit margins
4. **Customer Insights** -- Customer segmentation, geographic distribution, signup trends, lifetime value
5. **Order Analysis** -- Order status distribution, payment method breakdown, fulfillment metrics
6. **Data Quality** -- Validation results, quality scores, completeness metrics, pipeline run history

---

## Testing

Run the full test suite:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_extraction.py

# Run with coverage
pytest --cov=src --cov-report=html
```

**Test coverage includes:**

- **Extraction**: Data loading, incremental loading, missing files, malformed JSON
- **Transformation**: Currency parsing, status normalization, deduplication, calculations
- **Validation**: Schema validation, referential integrity, quality metrics
- **Database**: Table creation, data loading, upsert behavior, pipeline logging

---

## CI/CD

The project uses GitHub Actions for continuous integration:

- **On push to `main`/`develop`**: Run full test suite, lint with flake8, type-check with mypy
- **On pull request**: Run tests, generate coverage report, build Docker image
- **On release tag**: Build and push Docker image to container registry, deploy to staging

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- All tests pass (`pytest`)
- Code follows PEP 8 style guidelines
- New features include corresponding tests
- Update documentation as needed

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
