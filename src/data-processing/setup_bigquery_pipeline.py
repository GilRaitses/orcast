"""
Setup BigQuery Pipeline for ORCAST Whale Detection Processing
Creates necessary datasets, tables, and processing functions
"""

import os
import logging
from google.cloud import bigquery
from google.cloud.exceptions import Conflict, NotFound
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BigQueryPipelineSetup:
    """Setup BigQuery infrastructure for whale detection processing"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT', 'orcast-whale-analytics')
        
        try:
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"🔧 BigQuery client initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            self.client = None
    
    def create_datasets(self):
        """Create required datasets"""
        
        datasets = [
            {
                'id': 'whale_data',
                'description': 'Raw and processed whale detection data from OrcaHello',
                'location': 'US'
            },
            {
                'id': 'ml_analysis',
                'description': 'ML analysis results and behavioral modeling data',
                'location': 'US'
            },
            {
                'id': 'orcast_results',
                'description': 'Final ORCAST analysis results for frontend consumption',
                'location': 'US'
            }
        ]
        
        for dataset_info in datasets:
            try:
                dataset_id = f"{self.project_id}.{dataset_info['id']}"
                dataset = bigquery.Dataset(dataset_id)
                dataset.description = dataset_info['description']
                dataset.location = dataset_info['location']
                
                dataset = self.client.create_dataset(dataset, exists_ok=True)
                logger.info(f"✅ Created/verified dataset: {dataset_info['id']}")
                
            except Exception as e:
                logger.error(f"Failed to create dataset {dataset_info['id']}: {e}")
    
    def create_tables(self):
        """Create required tables with schemas"""
        
        # Raw detections table
        raw_detections_schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("hydrophone_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("hydrophone_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("latitude", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("longitude", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("confidence", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("detection_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("call_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("species", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("validated", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("audio_duration_seconds", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("frequency_range_min_hz", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("frequency_range_max_hz", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("region", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("processed_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("ml_analysis_pending", "BOOLEAN", mode="NULLABLE"),
        ]
        
        # Processed detections table
        processed_detections_schema = raw_detections_schema + [
            bigquery.SchemaField("bigquery_processed_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("ml_status", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("spatial_cluster_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("temporal_cluster_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("behavioral_score", "FLOAT", mode="NULLABLE"),
        ]
        
        # ML analysis results table
        ml_analysis_schema = [
            bigquery.SchemaField("analysis_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("detection_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("hydrophone_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("behavioral_features", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("foraging_probability", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("social_activity_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("movement_pattern", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("environmental_context", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("prediction_confidence", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("model_version", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("processed_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        # Route recommendations table
        route_recommendations_schema = [
            bigquery.SchemaField("recommendation_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("primary_location", "GEOGRAPHY", mode="REQUIRED"),
            bigquery.SchemaField("success_probability", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("optimal_time_window", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("route_waypoints", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("behavioral_insights", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("confidence_level", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("valid_until", "TIMESTAMP", mode="NULLABLE"),
        ]
        
        tables_to_create = [
            ("whale_data", "raw_detections", raw_detections_schema),
            ("whale_data", "processed_detections", processed_detections_schema),
            ("ml_analysis", "behavioral_analysis", ml_analysis_schema),
            ("orcast_results", "route_recommendations", route_recommendations_schema),
        ]
        
        for dataset_name, table_name, schema in tables_to_create:
            try:
                table_id = f"{self.project_id}.{dataset_name}.{table_name}"
                table = bigquery.Table(table_id, schema=schema)
                
                # Set table properties
                table.description = f"ORCAST {table_name.replace('_', ' ').title()} Table"
                
                # Set partitioning on timestamp for better performance
                if any(field.name == "timestamp" for field in schema):
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field="timestamp"
                    )
                
                table = self.client.create_table(table, exists_ok=True)
                logger.info(f"✅ Created/verified table: {dataset_name}.{table_name}")
                
            except Exception as e:
                logger.error(f"Failed to create table {dataset_name}.{table_name}: {e}")
    
    def create_processing_functions(self):
        """Create SQL functions for data processing"""
        
        functions = [
            {
                'name': 'calculate_spatial_clusters',
                'sql': f"""
                CREATE OR REPLACE FUNCTION `{self.project_id}.whale_data.calculate_spatial_clusters`(
                    detections ARRAY<STRUCT<id STRING, latitude FLOAT64, longitude FLOAT64>>
                )
                RETURNS ARRAY<STRUCT<detection_id STRING, cluster_id STRING>>
                LANGUAGE js AS '''
                    // Simple spatial clustering based on distance
                    const clusters = [];
                    const processed = new Set();
                    let clusterId = 0;
                    
                    for (let i = 0; i < detections.length; i++) {{
                        if (processed.has(i)) continue;
                        
                        const currentCluster = `cluster_${{clusterId++}}`;
                        const clusterMembers = [i];
                        processed.add(i);
                        
                        // Find nearby detections (within ~5km)
                        for (let j = i + 1; j < detections.length; j++) {{
                            if (processed.has(j)) continue;
                            
                            const distance = Math.sqrt(
                                Math.pow(detections[i].latitude - detections[j].latitude, 2) +
                                Math.pow(detections[i].longitude - detections[j].longitude, 2)
                            ) * 111; // Rough km conversion
                            
                            if (distance < 5) {{
                                clusterMembers.push(j);
                                processed.add(j);
                            }}
                        }}
                        
                        // Add cluster assignments
                        for (const memberIdx of clusterMembers) {{
                            clusters.push({{
                                detection_id: detections[memberIdx].id,
                                cluster_id: currentCluster
                            }});
                        }}
                    }}
                    
                    return clusters;
                ''';
                """
            },
            {
                'name': 'calculate_behavioral_score',
                'sql': f"""
                CREATE OR REPLACE FUNCTION `{self.project_id}.ml_analysis.calculate_behavioral_score`(
                    confidence FLOAT64,
                    call_type STRING,
                    duration FLOAT64,
                    cluster_size INT64
                )
                RETURNS FLOAT64
                AS (
                    CASE 
                        WHEN call_type = 'foraging_call' THEN confidence * 1.2 * LEAST(duration/5.0, 1.0) * LEAST(cluster_size/3.0, 1.0)
                        WHEN call_type = 'social_call' THEN confidence * 1.1 * LEAST(cluster_size/2.0, 1.0)
                        WHEN call_type = 'echolocation_click' THEN confidence * 1.0 * LEAST(duration/3.0, 1.0)
                        ELSE confidence * 0.8
                    END
                );
                """
            }
        ]
        
        for func in functions:
            try:
                query_job = self.client.query(func['sql'])
                query_job.result()  # Wait for completion
                logger.info(f"✅ Created/updated function: {func['name']}")
                
            except Exception as e:
                logger.error(f"Failed to create function {func['name']}: {e}")
    
    def create_processing_views(self):
        """Create views for easier data access"""
        
        views = [
            {
                'name': 'recent_detections',
                'dataset': 'whale_data',
                'sql': f"""
                CREATE OR REPLACE VIEW `{self.project_id}.whale_data.recent_detections` AS
                SELECT 
                    *,
                    DATETIME_DIFF(CURRENT_DATETIME(), DATETIME(timestamp), HOUR) as hours_ago,
                    ST_GEOGPOINT(longitude, latitude) as location_point
                FROM `{self.project_id}.whale_data.raw_detections`
                WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                ORDER BY timestamp DESC;
                """
            },
            {
                'name': 'active_hotspots',
                'dataset': 'orcast_results', 
                'sql': f"""
                CREATE OR REPLACE VIEW `{self.project_id}.orcast_results.active_hotspots` AS
                SELECT 
                    hydrophone_id,
                    hydrophone_name,
                    region,
                    AVG(latitude) as center_lat,
                    AVG(longitude) as center_lng,
                    COUNT(*) as detection_count,
                    AVG(confidence) as avg_confidence,
                    MAX(timestamp) as latest_detection,
                    STRING_AGG(DISTINCT call_type) as call_types
                FROM `{self.project_id}.whale_data.recent_detections`
                WHERE confidence > 70
                GROUP BY hydrophone_id, hydrophone_name, region
                HAVING detection_count >= 2
                ORDER BY detection_count DESC, avg_confidence DESC;
                """
            }
        ]
        
        for view in views:
            try:
                query_job = self.client.query(view['sql'])
                query_job.result()
                logger.info(f"✅ Created/updated view: {view['dataset']}.{view['name']}")
                
            except Exception as e:
                logger.error(f"Failed to create view {view['name']}: {e}")
    
    def setup_complete_pipeline(self):
        """Setup complete BigQuery pipeline"""
        
        logger.info("🚀 Setting up complete BigQuery pipeline...")
        
        if not self.client:
            logger.error("BigQuery client not available")
            return False
        
        try:
            # Step 1: Create datasets
            logger.info("📁 Creating datasets...")
            self.create_datasets()
            
            # Step 2: Create tables
            logger.info("📊 Creating tables...")
            self.create_tables()
            
            # Step 3: Create processing functions
            logger.info("⚙️ Creating processing functions...")
            self.create_processing_functions()
            
            # Step 4: Create views
            logger.info("👁️ Creating views...")
            self.create_processing_views()
            
            logger.info("✅ BigQuery pipeline setup complete!")
            
            # Create configuration file for easy access
            config = {
                'project_id': self.project_id,
                'datasets': {
                    'whale_data': f"{self.project_id}.whale_data",
                    'ml_analysis': f"{self.project_id}.ml_analysis", 
                    'orcast_results': f"{self.project_id}.orcast_results"
                },
                'tables': {
                    'raw_detections': f"{self.project_id}.whale_data.raw_detections",
                    'processed_detections': f"{self.project_id}.whale_data.processed_detections",
                    'behavioral_analysis': f"{self.project_id}.ml_analysis.behavioral_analysis",
                    'route_recommendations': f"{self.project_id}.orcast_results.route_recommendations"
                },
                'views': {
                    'recent_detections': f"{self.project_id}.whale_data.recent_detections",
                    'active_hotspots': f"{self.project_id}.orcast_results.active_hotspots"
                }
            }
            
            with open('bigquery_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("📋 Saved BigQuery configuration to bigquery_config.json")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline setup failed: {e}")
            return False

def main():
    """Main setup function"""
    print("🔧 BigQuery Pipeline Setup for ORCAST")
    
    # Get project ID
    project_id = input("Enter your Google Cloud Project ID (press Enter for 'orcast-whale-analytics'): ").strip()
    if not project_id:
        project_id = 'orcast-whale-analytics'
    
    print(f"Setting up BigQuery pipeline for project: {project_id}")
    
    setup = BigQueryPipelineSetup(project_id)
    success = setup.setup_complete_pipeline()
    
    if success:
        print("\n🎯 BigQuery pipeline ready for whale detection processing!")
        print("Next steps:")
        print("1. Run detection integration to populate raw_detections table")
        print("2. Execute ML analysis pipeline")
        print("3. Generate route recommendations")
    else:
        print("\n❌ Pipeline setup failed - check logs for details")

if __name__ == "__main__":
    main() 