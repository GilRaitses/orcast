#!/usr/bin/env python3
"""
Create/Update BigQuery table for orca sightings data with enhanced schema
"""

import logging
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_or_update_sightings_table():
    """Create or update the sightings table in BigQuery with enhanced schema"""
    try:
        client = bigquery.Client()
        dataset_id = "orca_production_data"
        table_id = "sightings"
        
        # Define the enhanced table schema
        schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("latitude", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("longitude", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("species", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("common_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("observer", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("quality_grade", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("photos", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("confidence", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("environmental_data", "STRING", mode="NULLABLE"),  # Keep as STRING for compatibility
            bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="NULLABLE"),
            
            # Enhanced orca-specific fields
            bigquery.SchemaField("individual_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("matriline", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ecotype", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("behavior", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("count", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
        ]
        
        # Table reference
        table_ref = client.dataset(dataset_id).table(table_id)
        
        try:
            # Check if table exists
            existing_table = client.get_table(table_ref)
            logger.info(f"Table {table_id} already exists")
            
            # Check if we need to add new fields
            existing_fields = {field.name for field in existing_table.schema}
            new_fields = {field.name for field in schema}
            
            missing_fields = new_fields - existing_fields
            
            if missing_fields:
                logger.info(f"Adding missing fields: {missing_fields}")
                
                # Add only the missing fields to the existing schema
                updated_schema = list(existing_table.schema)
                
                for field in schema:
                    if field.name in missing_fields:
                        updated_schema.append(field)
                
                # Update the table schema
                existing_table.schema = updated_schema
                updated_table = client.update_table(existing_table, ["schema"])
                
                logger.info(f"Successfully updated table schema: {updated_table.table_id}")
            else:
                logger.info("Table schema is already up to date")
                
        except NotFound:
            # Table doesn't exist, create it
            logger.info(f"Creating new table: {table_id}")
            
            # Create table with partitioning
            table = bigquery.Table(table_ref, schema=schema)
            
            # Enable time partitioning by timestamp
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            
            # Create clustered table for better performance
            table.clustering_fields = ["source", "species", "ecotype"]
            
            table = client.create_table(table)
            logger.info(f"Successfully created table: {table.table_id}")
            
    except Exception as e:
        logger.error(f"Error creating/updating table: {e}")
        raise

def main():
    """Main function"""
    logger.info("Creating/updating BigQuery table for enhanced orca sightings data")
    create_or_update_sightings_table()

if __name__ == "__main__":
    main() 