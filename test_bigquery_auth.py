#!/usr/bin/env python3
"""
Simple test script to verify BigQuery authentication and access
"""

import logging
from google.cloud import bigquery

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bigquery_access():
    """Test BigQuery authentication and basic operations"""
    try:
        # Initialize BigQuery client
        client = bigquery.Client()
        logger.info(f"BigQuery client initialized successfully")
        logger.info(f"Using project: {client.project}")
        
        # Test listing datasets
        datasets = list(client.list_datasets())
        logger.info(f"Found {len(datasets)} datasets in project")
        
        for dataset in datasets:
            logger.info(f"  - {dataset.dataset_id}")
        
        # Test creating a dataset if it doesn't exist
        dataset_id = "orca_production_data"
        dataset = bigquery.Dataset(f"{client.project}.{dataset_id}")
        dataset.location = "US"
        
        try:
            dataset = client.create_dataset(dataset)
            logger.info(f"Created dataset {dataset.dataset_id}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Dataset {dataset_id} already exists")
            else:
                logger.error(f"Error creating dataset: {e}")
        
        # Test listing tables in the dataset
        try:
            tables = list(client.list_tables(dataset_id))
            logger.info(f"Found {len(tables)} tables in dataset {dataset_id}")
            for table in tables:
                logger.info(f"  - {table.table_id}")
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
        
        logger.info("BigQuery access test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"BigQuery access test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_bigquery_access()
    exit(0 if success else 1) 