"""
MLB Data Pipeline Airflow DAGs

Airflow DAGs for orchestration:
- Daily data refresh pipeline
- Backfill capabilities for historical data
- Data quality checks and alerting
- Dependencies between extraction, transformation, loading
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.functions import CloudFunctionInvokeFunctionOperator

# Import our custom modules
import sys
sys.path.append('/opt/airflow/dags')

from mlb_data_pipeline.extractors import MLBAPIExtractor, DataExtractionOrchestrator
from mlb_data_pipeline.loaders import BigQueryDataLoader
from mlb_data_pipeline.validators import DataValidator
from mlb_data_pipeline.models import BigQueryDataWarehouse


# Default arguments for DAGs
default_args = {
    'owner': 'mlb-analytics',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

# Environment variables
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
DATASET_ID = os.getenv('BIGQUERY_DATASET', 'mlb_analytics')
BUCKET_NAME = os.getenv('GCS_BUCKET', 'mlb-analytics-data')


def extract_daily_data(**context):
    """Extract daily MLB data."""
    execution_date = context['execution_date']
    
    async def _extract():
        async with MLBAPIExtractor() as extractor:
            orchestrator = DataExtractionOrchestrator(extractor)
            result = await orchestrator.extract_daily_data(execution_date)
            return result
    
    # Run async function
    import asyncio
    return asyncio.run(_extract())


def load_data_to_bigquery(**context):
    """Load extracted data to BigQuery."""
    ti = context['ti']
    extraction_data = ti.xcom_pull(task_ids='extract_daily_data')
    
    loader = BigQueryDataLoader(PROJECT_ID, DATASET_ID)
    result = loader.load_daily_extraction_data(extraction_data)
    
    return result


def validate_data_quality(**context):
    """Validate data quality after loading."""
    execution_date = context['execution_date']
    
    validator = DataValidator(PROJECT_ID, DATASET_ID)
    validation_report = validator.generate_validation_report(execution_date)
    
    # Store validation results in XCom
    context['ti'].xcom_push(key='validation_report', value=validation_report)
    
    return validation_report


def check_data_freshness(**context):
    """Check data freshness and alert if needed."""
    validator = DataValidator(PROJECT_ID, DATASET_ID)
    freshness_results = validator.check_data_freshness()
    
    # Alert if data is stale
    if freshness_results['overall_freshness'] in ['stale', 'no_data']:
        raise Exception(f"Data is {freshness_results['overall_freshness']}")
    
    return freshness_results


def generate_alerts(**context):
    """Generate alerts based on validation results."""
    ti = context['ti']
    validation_report = ti.xcom_pull(task_ids='validate_data_quality', key='validation_report')
    
    validator = DataValidator(PROJECT_ID, DATASET_ID)
    alerts = validator.alert_on_anomalies(validation_report)
    
    # Log alerts
    for alert in alerts:
        print(f"ALERT [{alert['level'].upper()}]: {alert['message']}")
    
    return alerts


def cleanup_old_data(**context):
    """Clean up old data from BigQuery tables."""
    loader = BigQueryDataLoader(PROJECT_ID, DATASET_ID)
    
    cleanup_results = {}
    for table_name in ['games', 'game_events']:
        try:
            result = loader.cleanup_old_data(table_name, days_to_keep=90)
            cleanup_results[table_name] = result
        except Exception as e:
            print(f"Failed to cleanup {table_name}: {e}")
            cleanup_results[table_name] = {"status": "failed", "error": str(e)}
    
    return cleanup_results


# Daily Data Pipeline DAG
daily_pipeline_dag = DAG(
    'mlb_daily_data_pipeline',
    default_args=default_args,
    description='Daily MLB data extraction and loading pipeline',
    schedule_interval='0 6 * * *',  # Run daily at 6 AM
    max_active_runs=1,
    tags=['mlb', 'analytics', 'data-pipeline'],
)

# Tasks
extract_task = PythonOperator(
    task_id='extract_daily_data',
    python_callable=extract_daily_data,
    dag=daily_pipeline_dag,
)

load_task = PythonOperator(
    task_id='load_data_to_bigquery',
    python_callable=load_data_to_bigquery,
    dag=daily_pipeline_dag,
)

validate_task = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=daily_pipeline_dag,
)

freshness_task = PythonOperator(
    task_id='check_data_freshness',
    python_callable=check_data_freshness,
    dag=daily_pipeline_dag,
)

alerts_task = PythonOperator(
    task_id='generate_alerts',
    python_callable=generate_alerts,
    dag=daily_pipeline_dag,
)

# Task dependencies
extract_task >> load_task >> validate_task >> alerts_task
load_task >> freshness_task


# Live Data Pipeline DAG (for in-progress games)
live_pipeline_dag = DAG(
    'mlb_live_data_pipeline',
    default_args=default_args,
    description='Live MLB data extraction for in-progress games',
    schedule_interval='*/15 * * * *',  # Run every 15 minutes
    max_active_runs=1,
    tags=['mlb', 'analytics', 'live-data'],
)

# Live data extraction using Cloud Function
live_extract_task = CloudFunctionInvokeFunctionOperator(
    task_id='extract_live_game_data',
    function_name='extract-live-game-data',
    data={'game_id': '{{ dag_run.conf.game_id }}'},
    location='us-central1',
    dag=live_pipeline_dag,
)

live_load_task = PythonOperator(
    task_id='load_live_data',
    python_callable=load_data_to_bigquery,
    dag=live_pipeline_dag,
)

live_extract_task >> live_load_task


# Backfill Pipeline DAG
backfill_pipeline_dag = DAG(
    'mlb_backfill_pipeline',
    default_args=default_args,
    description='Backfill historical MLB data',
    schedule_interval=None,  # Manual trigger only
    max_active_runs=1,
    tags=['mlb', 'analytics', 'backfill'],
)

def backfill_historical_data(**context):
    """Backfill historical data for a date range."""
    start_date = context['dag_run'].conf.get('start_date')
    end_date = context['dag_run'].conf.get('end_date')
    
    if not start_date or not end_date:
        raise ValueError("start_date and end_date must be provided in dag_run.conf")
    
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    results = []
    current_date = start_dt
    
    while current_date <= end_dt:
        try:
            # Extract data for current date
            async def _extract():
                async with MLBAPIExtractor() as extractor:
                    orchestrator = DataExtractionOrchestrator(extractor)
                    return await orchestrator.extract_daily_data(current_date)
            
            import asyncio
            extraction_data = asyncio.run(_extract())
            
            # Load data
            loader = BigQueryDataLoader(PROJECT_ID, DATASET_ID)
            load_result = loader.load_daily_extraction_data(extraction_data)
            
            results.append({
                'date': current_date.isoformat(),
                'status': 'success',
                'load_result': load_result
            })
            
        except Exception as e:
            results.append({
                'date': current_date.isoformat(),
                'status': 'failed',
                'error': str(e)
            })
        
        current_date += timedelta(days=1)
    
    return results

backfill_task = PythonOperator(
    task_id='backfill_historical_data',
    python_callable=backfill_historical_data,
    dag=backfill_pipeline_dag,
)


# Data Quality Monitoring DAG
quality_monitoring_dag = DAG(
    'mlb_data_quality_monitoring',
    default_args=default_args,
    description='Data quality monitoring and alerting',
    schedule_interval='0 */4 * * *',  # Run every 4 hours
    max_active_runs=1,
    tags=['mlb', 'analytics', 'quality-monitoring'],
)

# Data quality checks
quality_check_task = PythonOperator(
    task_id='run_quality_checks',
    python_callable=validate_data_quality,
    dag=quality_monitoring_dag,
)

freshness_check_task = PythonOperator(
    task_id='check_data_freshness',
    python_callable=check_data_freshness,
    dag=quality_monitoring_dag,
)

quality_alerts_task = PythonOperator(
    task_id='generate_quality_alerts',
    python_callable=generate_alerts,
    dag=quality_monitoring_dag,
)

# Email notification for quality issues
email_alert_task = EmailOperator(
    task_id='send_quality_alert_email',
    to=['mlb-analytics-team@company.com'],
    subject='MLB Data Quality Alert - {{ ds }}',
    html_content="""
    <h2>MLB Data Quality Alert</h2>
    <p>Data quality issues detected on {{ ds }}.</p>
    <p>Please check the Airflow logs for details.</p>
    """,
    dag=quality_monitoring_dag,
)

quality_check_task >> quality_alerts_task >> email_alert_task
freshness_check_task >> quality_alerts_task


# Data Warehouse Maintenance DAG
maintenance_dag = DAG(
    'mlb_data_warehouse_maintenance',
    default_args=default_args,
    description='Data warehouse maintenance tasks',
    schedule_interval='0 2 * * 0',  # Run weekly on Sunday at 2 AM
    max_active_runs=1,
    tags=['mlb', 'analytics', 'maintenance'],
)

# Cleanup old data
cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=maintenance_dag,
)

# Optimize BigQuery tables
optimize_tables_task = BigQueryExecuteQueryOperator(
    task_id='optimize_bigquery_tables',
    sql="""
    -- Optimize tables by clustering
    OPTIMIZE TABLE `{{ params.project_id }}.{{ params.dataset_id }}.games`
    WHERE partition_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
    
    OPTIMIZE TABLE `{{ params.project_id }}.{{ params.dataset_id }}.game_events`
    WHERE partition_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
    """,
    params={
        'project_id': PROJECT_ID,
        'dataset_id': DATASET_ID
    },
    dag=maintenance_dag,
)

# Update analytics views
update_views_task = BashOperator(
    task_id='update_analytics_views',
    bash_command="""
    python -c "
    from mlb_data_pipeline.models import BigQueryDataWarehouse
    warehouse = BigQueryDataWarehouse('{{ params.project_id }}', '{{ params.dataset_id }}')
    warehouse.create_analytics_views()
    "
    """,
    params={
        'project_id': PROJECT_ID,
        'dataset_id': DATASET_ID
    },
    dag=maintenance_dag,
)

cleanup_task >> optimize_tables_task >> update_views_task


# Export DAGs
__all__ = [
    'daily_pipeline_dag',
    'live_pipeline_dag', 
    'backfill_pipeline_dag',
    'quality_monitoring_dag',
    'maintenance_dag'
]
