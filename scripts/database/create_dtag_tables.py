#!/usr/bin/env python3
"""
Create BigQuery tables for DTAG data integration

This script creates the necessary tables for storing DTAG deployment data,
behavioral data, and acoustic events in BigQuery.
"""

import logging
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dtag_tables():
    """Create all DTAG-related tables in BigQuery"""
    try:
        client = bigquery.Client()
        dataset_id = "orca_production_data"
        
        # Create DTAG deployments table
        deployments_table_id = "dtag_deployments"
        deployments_schema = [
            bigquery.SchemaField("deployment_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("individual_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("end_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("duration_hours", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("pod", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("matriline", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ecotype", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("location_start_lat", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("location_start_lon", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("location_end_lat", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("location_end_lon", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("deployment_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("research_organization", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("data_source", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        create_table_if_not_exists(client, dataset_id, deployments_table_id, deployments_schema)
        
        # Create DTAG behavioral data table
        behavioral_table_id = "dtag_behavioral_data"
        behavioral_schema = [
            bigquery.SchemaField("deployment_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("depth", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("pitch", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("roll", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("heading", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("acceleration_x", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("acceleration_y", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("acceleration_z", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("speed", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("behavior_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("acoustic_activity", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("dive_phase", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("foraging_indicator", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("prey_capture_event", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("vessel_distance", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("data_quality", "STRING", mode="NULLABLE"),
        ]
        
        create_table_if_not_exists(client, dataset_id, behavioral_table_id, behavioral_schema)
        
        # Create DTAG acoustic events table
        acoustic_table_id = "dtag_acoustic_events"
        acoustic_schema = [
            bigquery.SchemaField("deployment_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("frequency_hz", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("amplitude_db", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("duration_ms", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("call_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("call_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("is_echolocation", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("is_communication", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("pod_specific", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("context", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("confidence", "FLOAT", mode="NULLABLE"),
        ]
        
        create_table_if_not_exists(client, dataset_id, acoustic_table_id, acoustic_schema)
        
        # Create DTAG dive sequences table
        dive_sequences_table_id = "dtag_dive_sequences"
        dive_sequences_schema = [
            bigquery.SchemaField("deployment_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("dive_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("end_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("max_depth", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("dive_duration", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("surface_duration", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("dive_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("foraging_success", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("prey_species", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("echolocation_clicks", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("feeding_buzzes", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("bottom_time", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("descent_rate", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("ascent_rate", "FLOAT", mode="NULLABLE"),
        ]
        
        create_table_if_not_exists(client, dataset_id, dive_sequences_table_id, dive_sequences_schema)
        
        logger.info("✅ All DTAG tables created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error creating DTAG tables: {e}")
        raise

def create_table_if_not_exists(client, dataset_id, table_id, schema):
    """Create a table if it doesn't exist"""
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        
        try:
            # Check if table exists
            existing_table = client.get_table(table_ref)
            logger.info(f"✅ Table {table_id} already exists")
            
        except NotFound:
            # Create table with partitioning and clustering
            table = bigquery.Table(table_ref, schema=schema)
            
            # Enable time partitioning by timestamp
            if table_id in ['dtag_behavioral_data', 'dtag_acoustic_events']:
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="timestamp"
                )
            elif table_id == 'dtag_deployments':
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="start_time"
                )
            elif table_id == 'dtag_dive_sequences':
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="start_time"
                )
            
            # Create clustered table for better performance
            if table_id == 'dtag_deployments':
                table.clustering_fields = ["individual_id", "pod", "ecotype"]
            elif table_id == 'dtag_behavioral_data':
                table.clustering_fields = ["deployment_id", "behavior_type"]
            elif table_id == 'dtag_acoustic_events':
                table.clustering_fields = ["deployment_id", "event_type", "call_type"]
            elif table_id == 'dtag_dive_sequences':
                table.clustering_fields = ["deployment_id", "dive_type"]
            
            table = client.create_table(table)
            logger.info(f"✅ Created table: {table.table_id}")
            
    except Exception as e:
        logger.error(f"❌ Error creating table {table_id}: {e}")
        raise

def main():
    """Main function"""
    logger.info("🚀 Creating DTAG BigQuery tables...")
    create_dtag_tables()
    logger.info("🎉 DTAG database schema deployment complete!")

if __name__ == "__main__":
    main() 