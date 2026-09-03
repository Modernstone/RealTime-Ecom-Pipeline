"""
E-Commerce Data Pipeline Module

This module provides the EcommercePipeline class for orchestrating the complete
data pipeline: extraction, validation, transformation, loading, and analytics.

Usage:
    from pipeline import EcommercePipeline

    # Full pipeline run
    pipeline = EcommercePipeline()
    summary = pipeline.run()

    # Incremental run
    summary = pipeline.run_incremental(since="2024-01-01T00:00:00")

CLI Usage:
    python pipeline.py                    # Full pipeline run
    python pipeline.py --incremental      # Incremental run
    python pipeline.py --since 2024-01-01 # Run since specific date
"""

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from extraction.api_client import EcommerceAPIClient
from validation.validate_data import DataValidator
from transformation.clean_data import DataCleaner
from transformation.transform_data import DataTransformer
from loading.load_postgres import PostgresLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)
logger = logging.getLogger(__name__)


class EcommercePipeline:
    """
    Orchestrator for the e-commerce data pipeline.

    This class coordinates the complete ETL pipeline: extraction from JSON files,
    data validation, cleaning, transformation, and loading into PostgreSQL.

    Attributes:
        api_client (EcommerceAPIClient): Data extraction client
        validator (DataValidator): Data validation engine
        cleaner (DataCleaner): Data cleaning processor
        transformer (DataTransformer): Data transformation engine
        loader (PostgresLoader): Database loader
        run_id (str): Unique identifier for the current pipeline run
    """

    def __init__(self, enable_db: bool = True):
        """
        Initialize the EcommercePipeline.

        Args:
            enable_db: Whether to initialize database connection. Set to False
                      for testing without a database.
        """
        self.run_id = str(uuid.uuid4())
        self.api_client = EcommerceAPIClient()
        self.validator = DataValidator()
        self.cleaner = DataCleaner()
        self.transformer = DataTransformer()

        self.loader = None
        if enable_db:
            try:
                self.loader = PostgresLoader()
                logger.info("Database loader initialized")
            except Exception as e:
                logger.warning(f"Database loader initialization failed: {e}")
                logger.info("Pipeline will run without database loading")

        logger.info(f"EcommercePipeline initialized with run_id: {self.run_id}")

    def _log_step(
        self,
        step: str,
        records_processed: int,
        duration: float,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log metrics for a pipeline step.

        Args:
            step: Step name
            records_processed: Number of records processed
            duration: Step duration in seconds
            additional_metrics: Optional additional metrics

        Returns:
            Step metrics dictionary
        """
        metrics = {
            'step': step,
            'records_processed': records_processed,
            'duration_seconds': round(duration, 2),
            'timestamp': datetime.now().isoformat()
        }

        if additional_metrics:
            metrics.update(additional_metrics)

        logger.info(
            f"Step '{step}': {records_processed} records processed in {duration:.2f}s"
        )

        return metrics

    def _handle_record_error(
        self,
        record: Dict[str, Any],
        error: Exception,
        step: str
    ) -> None:
        """
        Handle errors for individual records without stopping the pipeline.

        Args:
            record: The record that caused the error
            error: The exception that occurred
            step: The pipeline step where the error occurred
        """
        record_id = (
            record.get('customer_id') or
            record.get('product_id') or
            record.get('order_id') or
            record.get('item_id') or
            record.get('payment_id') or
            record.get('inventory_id') or
            'unknown'
        )
        logger.warning(f"Error processing record {record_id} in {step}: {error}")

    def run(self) -> Dict[str, Any]:
        """
        Execute the complete data pipeline.

        Returns:
            Pipeline run summary dictionary with metrics for each step
        """
        start_time = time.time()
        logger.info(f"Starting pipeline run {self.run_id}")

        summary = {
            'run_id': self.run_id,
            'start_time': datetime.now().isoformat(),
            'status': 'RUNNING',
            'steps': {},
            'total_records': {},
            'errors': []
        }

        try:
            # Step 1: Extract
            step_start = time.time()
            logger.info("Step 1: Extracting data...")

            raw_data = self.api_client.load_all()
            total_extracted = sum(len(records) for records in raw_data.values())

            summary['steps']['extraction'] = self._log_step(
                'extraction',
                total_extracted,
                time.time() - step_start
            )
            summary['total_records']['extracted'] = total_extracted

            # Step 2: Validate
            step_start = time.time()
            logger.info("Step 2: Validating data...")

            valid_data, invalid_data, quality_metrics = self.validator.validate_all(raw_data)

            total_valid = sum(len(records) for records in valid_data.values())
            total_invalid = sum(len(records) for records in invalid_data.values())

            summary['steps']['validation'] = self._log_step(
                'validation',
                total_extracted,
                time.time() - step_start,
                {
                    'valid_records': total_valid,
                    'invalid_records': total_invalid,
                    'quality_metrics': quality_metrics
                }
            )
            summary['total_records']['valid'] = total_valid
            summary['total_records']['invalid'] = total_invalid

            # Step 3: Clean
            step_start = time.time()
            logger.info("Step 3: Cleaning data...")

            cleaned_data = self.cleaner.clean_all(valid_data)
            total_cleaned = sum(len(records) for records in cleaned_data.values())

            summary['steps']['cleaning'] = self._log_step(
                'cleaning',
                total_cleaned,
                time.time() - step_start
            )
            summary['total_records']['cleaned'] = total_cleaned

            # Step 4: Transform
            step_start = time.time()
            logger.info("Step 4: Transforming data...")

            transformed_data = self.transformer.transform_all(cleaned_data)
            total_transformed = sum(len(records) for records in transformed_data.values())

            summary['steps']['transformation'] = self._log_step(
                'transformation',
                total_transformed,
                time.time() - step_start
            )
            summary['total_records']['transformed'] = total_transformed

            # Step 5: Load
            if self.loader:
                step_start = time.time()
                logger.info("Step 5: Loading data to PostgreSQL...")

                load_counts = self.loader.load_all(transformed_data)
                total_loaded = sum(load_counts.values())

                summary['steps']['loading'] = self._log_step(
                    'loading',
                    total_loaded,
                    time.time() - step_start,
                    {'load_counts': load_counts}
                )
                summary['total_records']['loaded'] = total_loaded

                # Log pipeline run
                self.loader.log_pipeline_run(
                    run_id=self.run_id,
                    status='COMPLETED',
                    records_processed=total_extracted,
                    records_valid=total_valid,
                    records_invalid=total_invalid,
                    duration_seconds=time.time() - start_time
                )
            else:
                logger.info("Step 5: Skipping database load (no database connection)")
                summary['steps']['loading'] = {'status': 'SKIPPED', 'reason': 'No database connection'}

            # Pipeline complete
            summary['status'] = 'COMPLETED'
            summary['end_time'] = datetime.now().isoformat()
            summary['total_duration_seconds'] = round(time.time() - start_time, 2)

            logger.info(
                f"Pipeline run {self.run_id} completed in "
                f"{summary['total_duration_seconds']}s"
            )

        except Exception as e:
            summary['status'] = 'FAILED'
            summary['end_time'] = datetime.now().isoformat()
            summary['total_duration_seconds'] = round(time.time() - start_time, 2)
            summary['errors'].append(str(e))

            logger.error(f"Pipeline run {self.run_id} failed: {e}")

            # Log failed run
            if self.loader:
                try:
                    self.loader.log_pipeline_run(
                        run_id=self.run_id,
                        status='FAILED',
                        records_processed=summary.get('total_records', {}).get('extracted', 0),
                        records_valid=summary.get('total_records', {}).get('valid', 0),
                        records_invalid=summary.get('total_records', {}).get('invalid', 0),
                        duration_seconds=summary['total_duration_seconds'],
                        error_message=str(e)
                    )
                except Exception as log_error:
                    logger.error(f"Failed to log pipeline error: {log_error}")

            raise

        finally:
            # Cleanup
            if self.loader:
                self.loader.close()

        return summary

    def run_incremental(self, since: str) -> Dict[str, Any]:
        """
        Execute an incremental pipeline run.

        Only processes records created/updated since the specified timestamp.

        Args:
            since: ISO format timestamp string

        Returns:
            Pipeline run summary dictionary
        """
        logger.info(f"Starting incremental pipeline run since {since}")

        # Store original load methods
        original_load_all = self.api_client.load_all

        # Override to use incremental loading
        def incremental_load_all():
            return self.api_client.load_all(since=since)

        self.api_client.load_all = incremental_load_all

        try:
            summary = self.run()
            summary['mode'] = 'incremental'
            summary['since'] = since
            return summary
        finally:
            # Restore original method
            self.api_client.load_all = original_load_all


def main():
    """
    CLI entry point for the e-commerce pipeline.

    Parses command line arguments and executes the pipeline.
    """
    parser = argparse.ArgumentParser(
        description='E-Commerce Data Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py                    # Full pipeline run
  python pipeline.py --incremental      # Incremental run (last 24 hours)
  python pipeline.py --since 2024-01-01 # Run since specific date
  python pipeline.py --no-db            # Run without database loading
        """
    )

    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Run in incremental mode (process only new/updated records)'
    )

    parser.add_argument(
        '--since',
        type=str,
        help='ISO timestamp for incremental loading (e.g., 2024-01-01T00:00:00)'
    )

    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Run without database loading (for testing)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize pipeline
    pipeline = EcommercePipeline(enable_db=not args.no_db)

    try:
        # Run pipeline
        if args.incremental or args.since:
            since = args.since or datetime.now().isoformat()
            summary = pipeline.run_incremental(since=since)
        else:
            summary = pipeline.run()

        # Print summary
        print("\n" + "=" * 60)
        print("PIPELINE RUN SUMMARY")
        print("=" * 60)
        print(f"Run ID: {summary['run_id']}")
        print(f"Status: {summary['status']}")
        print(f"Duration: {summary.get('total_duration_seconds', 'N/A')}s")
        print(f"\nRecords:")
        for key, value in summary.get('total_records', {}).items():
            print(f"  {key}: {value}")
        print("\nSteps:")
        for step, metrics in summary.get('steps', {}).items():
            if isinstance(metrics, dict) and 'duration_seconds' in metrics:
                print(f"  {step}: {metrics['records_processed']} records in {metrics['duration_seconds']}s")
        print("=" * 60)

        # Exit with appropriate code
        sys.exit(0 if summary['status'] == 'COMPLETED' else 1)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"\nPipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
