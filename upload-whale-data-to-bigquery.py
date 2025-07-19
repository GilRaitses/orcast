#!/usr/bin/env python3
"""
Upload Whale Data from Firestore to BigQuery
Transfers the 726 whale records from orca-904de Firestore to orca-466204 BigQuery for ML training
"""

import logging
import json
from datetime import datetime
from google.cloud import bigquery, firestore
import firebase_admin
from firebase_admin import credentials

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirestoreToBigQueryUploader:
    def __init__(self):
        self.firestore_client = None
        self.bigquery_client = None
        self.dataset_id = "orca_production_data"
        self.table_id = "sightings"
        
    def initialize_clients(self):
        """Initialize Firestore and BigQuery clients"""
        try:
            # Initialize Firestore (orca-904de project)
            logger.info("🔥 Initializing Firestore client (orca-904de)...")
            cred = credentials.Certificate('./config/orca-904de-firebase-adminsdk-fbsvc-19b853cc6d.json')
            firebase_admin.initialize_app(cred, {
                'projectId': 'orca-904de'
            })
            self.firestore_client = firestore.Client()
            
            # Initialize BigQuery (orca-466204 project)
            logger.info("📊 Initializing BigQuery client (orca-466204)...")
            self.bigquery_client = bigquery.Client(project='orca-466204')
            
            logger.info("✅ Both clients initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize clients: {e}")
            raise
    
    def fetch_whale_data_from_firestore(self):
        """Fetch all whale sightings from Firestore"""
        try:
            logger.info("🐋 Fetching whale data from Firestore...")
            
            # Query whale_sightings collection
            docs = self.firestore_client.collection('whale_sightings').get()
            
            whale_data = []
            for doc in docs:
                data = doc.to_dict()
                whale_data.append({
                    'doc_id': doc.id,
                    'data': data
                })
            
            logger.info(f"📦 Fetched {len(whale_data)} whale records from Firestore")
            return whale_data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Firestore data: {e}")
            raise
    
    def transform_data_for_bigquery(self, firestore_data):
        """Transform Firestore data to BigQuery schema format"""
        try:
            logger.info("🔄 Transforming data for BigQuery schema...")
            
            bigquery_rows = []
            
            for record in firestore_data:
                doc_id = record['doc_id']
                data = record['data']
                
                # Extract location data
                location = data.get('location', {})
                if hasattr(location, 'latitude'):  # GeoPoint object
                    latitude = location.latitude
                    longitude = location.longitude
                else:  # Dict with lat/lng
                    latitude = location.get('lat', 0.0)
                    longitude = location.get('lng', 0.0)
                
                # Handle timestamp
                timestamp = data.get('timestamp')
                if hasattr(timestamp, 'timestamp'):  # Firestore timestamp
                    timestamp_str = timestamp.timestamp()
                    timestamp_dt = datetime.fromtimestamp(timestamp_str)
                elif isinstance(timestamp, str):
                    timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    timestamp_dt = datetime.now()
                
                # Create BigQuery row
                row = {
                    'id': doc_id,
                    'timestamp': timestamp_dt.isoformat(),
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'species': 'Orcinus orca',
                    'common_name': 'Killer Whale',
                    'observer': data.get('researcher', data.get('source', 'Unknown')),
                    'quality_grade': data.get('confidence', 'medium'),
                    'photos': None,  # Not available in our dataset
                    'source': data.get('source', 'unknown'),
                    'confidence': self.confidence_to_float(data.get('confidence', 'medium')),
                    'environmental_data': None,  # Could be added later
                    'ingested_at': datetime.now().isoformat(),
                    
                    # Enhanced orca-specific fields
                    'individual_id': None,  # Not available in our dataset
                    'matriline': None,      # Not available in our dataset
                    'ecotype': 'Unknown',   # Could be inferred
                    'behavior': data.get('behavior', 'observed'),
                    'count': data.get('orcaCount', 1),
                    'notes': data.get('remarks', '')
                }
                
                bigquery_rows.append(row)
            
            logger.info(f"✅ Transformed {len(bigquery_rows)} records for BigQuery")
            return bigquery_rows
            
        except Exception as e:
            logger.error(f"❌ Failed to transform data: {e}")
            raise
    
    def confidence_to_float(self, confidence):
        """Convert confidence string to float value"""
        confidence_map = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }
        return confidence_map.get(confidence.lower() if isinstance(confidence, str) else 'medium', 0.7)
    
    def upload_to_bigquery(self, rows):
        """Upload transformed data to BigQuery"""
        try:
            logger.info("📊 Uploading data to BigQuery...")
            
            # Get table reference
            table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.table_id)
            table = self.bigquery_client.get_table(table_ref)
            
            # Upload in batches
            batch_size = 100
            total_uploaded = 0
            
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                
                logger.info(f"📦 Uploading batch {i//batch_size + 1}: {len(batch)} records")
                
                errors = self.bigquery_client.insert_rows_json(table, batch)
                
                if errors:
                    logger.error(f"❌ BigQuery insert errors: {errors}")
                    # Continue with next batch
                else:
                    total_uploaded += len(batch)
                    logger.info(f"✅ Batch uploaded successfully")
            
            logger.info(f"🎉 Successfully uploaded {total_uploaded} whale records to BigQuery!")
            return total_uploaded
            
        except Exception as e:
            logger.error(f"❌ Failed to upload to BigQuery: {e}")
            raise
    
    def verify_upload(self):
        """Verify the upload by querying BigQuery"""
        try:
            logger.info("🔍 Verifying BigQuery upload...")
            
            query = f"""
            SELECT 
                source,
                COUNT(*) as count,
                MIN(timestamp) as earliest_sighting,
                MAX(timestamp) as latest_sighting
            FROM `{self.bigquery_client.project}.{self.dataset_id}.{self.table_id}`
            GROUP BY source
            ORDER BY count DESC
            """
            
            results = self.bigquery_client.query(query).to_dataframe()
            
            logger.info("📊 BigQuery upload verification:")
            for _, row in results.iterrows():
                logger.info(f"  {row['source'].upper()}: {row['count']} records ({row['earliest_sighting']} to {row['latest_sighting']})")
            
            total_count = results['count'].sum()
            logger.info(f"✅ Total records in BigQuery: {total_count}")
            
            return total_count
            
        except Exception as e:
            logger.error(f"❌ Failed to verify upload: {e}")
            return 0
    
    def run_upload_pipeline(self):
        """Run the complete upload pipeline"""
        try:
            logger.info("🚀 Starting Firestore → BigQuery upload pipeline...")
            
            # Initialize clients
            self.initialize_clients()
            
            # Fetch data from Firestore
            firestore_data = self.fetch_whale_data_from_firestore()
            
            if not firestore_data:
                logger.warning("⚠️ No data found in Firestore")
                return
            
            # Transform data
            bigquery_rows = self.transform_data_for_bigquery(firestore_data)
            
            # Upload to BigQuery
            uploaded_count = self.upload_to_bigquery(bigquery_rows)
            
            # Verify upload
            verified_count = self.verify_upload()
            
            logger.info(f"🎉 Pipeline completed! {verified_count} whale records now available for ML training")
            logger.info(f"🔗 View data: https://console.cloud.google.com/bigquery?project=orca-466204")
            
        except Exception as e:
            logger.error(f"💥 Pipeline failed: {e}")
            raise

def main():
    """Main function to run the upload pipeline"""
    uploader = FirestoreToBigQueryUploader()
    uploader.run_upload_pipeline()

if __name__ == "__main__":
    main() 