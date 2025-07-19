#!/usr/bin/env python3
"""
OrCast Automated Collection Service

This service runs the production data pipeline on a schedule to collect
real-time orca sighting data continuously.
"""

import os
import time
import logging
import schedule
from datetime import datetime, timedelta
from production_data_pipeline import ProductionDataPipeline
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedCollectionService:
    def __init__(self):
        self.pipeline = ProductionDataPipeline()
        self.stats = {
            'total_runs': 0,
            'total_sightings': 0,
            'last_run': None,
            'last_sighting_count': 0,
            'sources_summary': {},
            'start_time': datetime.now().isoformat()
        }
        
    def run_collection_job(self):
        """Run a single collection job"""
        try:
            logger.info("🔄 Starting automated collection cycle...")
            
            # Run the pipeline
            sightings_count = self.pipeline.run_collection_cycle()
            
            # Update stats
            self.stats['total_runs'] += 1
            self.stats['total_sightings'] += sightings_count
            self.stats['last_run'] = datetime.now().isoformat()
            self.stats['last_sighting_count'] = sightings_count
            
            logger.info(f"✅ Collection cycle completed: {sightings_count} sightings")
            
            # Save stats
            self.save_stats()
            
        except Exception as e:
            logger.error(f"❌ Collection cycle failed: {e}")
            
    def save_stats(self):
        """Save collection statistics"""
        try:
            with open('collection_stats.json', 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
            
    def load_stats(self):
        """Load existing collection statistics"""
        try:
            with open('collection_stats.json', 'r') as f:
                self.stats.update(json.load(f))
        except FileNotFoundError:
            logger.info("No existing stats found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load stats: {e}")
            
    def print_status(self):
        """Print current service status"""
        logger.info("📊 ORCAST AUTOMATED COLLECTION SERVICE STATUS")
        logger.info(f"   Total runs: {self.stats['total_runs']}")
        logger.info(f"   Total sightings: {self.stats['total_sightings']}")
        logger.info(f"   Last run: {self.stats['last_run']}")
        logger.info(f"   Last count: {self.stats['last_sighting_count']}")
        logger.info(f"   Service started: {self.stats['start_time']}")
        
    def start_service(self):
        """Start the automated collection service"""
        logger.info("🚀 Starting OrCast Automated Collection Service")
        
        # Load existing stats
        self.load_stats()
        
        # Schedule collection jobs
        schedule.every(15).minutes.do(self.run_collection_job)  # Every 15 minutes
        schedule.every().hour.do(self.print_status)  # Hourly status
        
        # Run initial collection
        self.run_collection_job()
        
        logger.info("⏰ Scheduled collection every 15 minutes")
        logger.info("📈 Status reports every hour")
        logger.info("🔄 Service running... Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Service stopped by user")
            self.save_stats()
            
def main():
    """Main function for running the automated service"""
    service = AutomatedCollectionService()
    
    # Check if this is a one-time run or continuous service
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        logger.info("Running single collection cycle...")
        service.run_collection_job()
        service.print_status()
    else:
        service.start_service()

if __name__ == "__main__":
    main() 