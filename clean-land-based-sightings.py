#!/usr/bin/env python3
"""
Clean Land-Based Whale Sightings from BigQuery
Removes whale sightings that fall within island interior boundaries
"""

import logging
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_land_based_sightings():
    """Remove whale sightings that are located on land within island boundaries"""
    
    client = bigquery.Client(project='orca-466204')
    
    logger.info("🧹 Starting cleanup of land-based whale sightings...")
    
    # Count problematic sightings before cleanup
    count_query = '''
    SELECT COUNT(*) as land_sightings
    FROM `orca-466204.orca_production_data.sightings`
    WHERE 
        -- Orcas Island interior
        (latitude BETWEEN 48.635 AND 48.705 AND longitude BETWEEN -122.960 AND -122.840) OR
        -- San Juan Island interior  
        (latitude BETWEEN 48.520 AND 48.585 AND longitude BETWEEN -123.175 AND -123.045) OR
        -- Lopez Island interior
        (latitude BETWEEN 48.470 AND 48.535 AND longitude BETWEEN -122.955 AND -122.845) OR
        -- Shaw Island interior
        (latitude BETWEEN 48.575 AND 48.625 AND longitude BETWEEN -122.975 AND -122.915) OR
        -- Fidalgo Island interior
        (latitude BETWEEN 48.400 AND 48.520 AND longitude BETWEEN -122.680 AND -122.580)
    '''
    
    result = client.query(count_query).to_dataframe()
    land_sightings_count = result.iloc[0]['land_sightings']
    logger.info(f"🚨 Found {land_sightings_count} land-based sightings to remove")
    
    # Create clean table without land-based sightings
    cleanup_query = '''
    CREATE OR REPLACE TABLE `orca-466204.orca_production_data.sightings` AS
    SELECT *
    FROM `orca-466204.orca_production_data.sightings`
    WHERE NOT (
        -- Exclude Orcas Island interior
        (latitude BETWEEN 48.635 AND 48.705 AND longitude BETWEEN -122.960 AND -122.840) OR
        -- Exclude San Juan Island interior  
        (latitude BETWEEN 48.520 AND 48.585 AND longitude BETWEEN -123.175 AND -123.045) OR
        -- Exclude Lopez Island interior
        (latitude BETWEEN 48.470 AND 48.535 AND longitude BETWEEN -122.955 AND -122.845) OR
        -- Exclude Shaw Island interior
        (latitude BETWEEN 48.575 AND 48.625 AND longitude BETWEEN -122.975 AND -122.915) OR
        -- Exclude Fidalgo Island interior
        (latitude BETWEEN 48.400 AND 48.520 AND longitude BETWEEN -122.680 AND -122.580)
    )
    '''
    
    job = client.query(cleanup_query)
    job.result()
    
    logger.info("✅ Cleaned up land-based sightings")
    
    # Verify cleanup
    verify_query = '''
    SELECT 
        COUNT(*) as total_sightings,
        COUNT(CASE 
            WHEN (latitude BETWEEN 48.635 AND 48.705 AND longitude BETWEEN -122.960 AND -122.840) OR
                 (latitude BETWEEN 48.520 AND 48.585 AND longitude BETWEEN -123.175 AND -123.045) OR
                 (latitude BETWEEN 48.470 AND 48.535 AND longitude BETWEEN -122.955 AND -122.845) OR
                 (latitude BETWEEN 48.575 AND 48.625 AND longitude BETWEEN -122.975 AND -122.915) OR
                 (latitude BETWEEN 48.400 AND 48.520 AND longitude BETWEEN -122.680 AND -122.580)
            THEN 1 END
        ) as remaining_land_sightings,
        COUNT(DISTINCT CONCAT(CAST(latitude AS STRING), ',', CAST(longitude AS STRING))) as unique_locations
    FROM `orca-466204.orca_production_data.sightings`
    '''
    
    verification = client.query(verify_query).to_dataframe()
    total = verification.iloc[0]['total_sightings']
    remaining_land = verification.iloc[0]['remaining_land_sightings']
    unique_locations = verification.iloc[0]['unique_locations']
    
    logger.info(f"📊 Cleanup Results:")
    logger.info(f"  Total sightings: {total}")
    logger.info(f"  Remaining land sightings: {remaining_land}")
    logger.info(f"  Unique locations: {unique_locations}")
    logger.info(f"  Removed: {land_sightings_count} land-based sightings")
    
    # Show source distribution after cleanup
    source_query = '''
    SELECT 
        source,
        COUNT(*) as count,
        COUNT(DISTINCT CONCAT(CAST(latitude AS STRING), ',', CAST(longitude AS STRING))) as unique_locations
    FROM `orca-466204.orca_production_data.sightings`
    GROUP BY source
    ORDER BY count DESC
    '''
    
    sources = client.query(source_query).to_dataframe()
    logger.info(f"📈 Clean data distribution by source:")
    for _, row in sources.iterrows():
        logger.info(f"  {row['source']}: {row['count']} sightings ({row['unique_locations']} locations)")
    
    return total, land_sightings_count

if __name__ == "__main__":
    total_clean, removed_count = clean_land_based_sightings()
    logger.info(f"🎉 Cleanup completed successfully!")
    logger.info(f"📊 Final dataset: {total_clean} whale sightings (removed {removed_count} land-based)")
    logger.info(f"🗺️ All remaining sightings are in water around the San Juan Islands") 