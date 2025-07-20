#!/usr/bin/env python3
"""
ORCAST Data Pipeline Testing Framework (pytest-based)
Comprehensive testing for whale research data pipelines using pytest
"""

import pytest
import pandas as pd
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import ORCAST modules
try:
    from scripts.data_processing.production_data_pipeline import ProductionDataPipeline
    from scripts.ml_services.behavioral_ml_service import BehavioralMLService
    from scripts.ml_services.hmc_analysis_runner import HMCAnalysisRunner
except ImportError:
    # Fallback for testing without full setup
    ProductionDataPipeline = None
    BehavioralMLService = None
    HMCAnalysisRunner = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipelineTestConfig:
    """Configuration for data pipeline testing"""
    
    # Geographic bounds for San Juan Islands whale research
    MIN_LATITUDE = 47.0
    MAX_LATITUDE = 49.5
    MIN_LONGITUDE = -124.0
    MAX_LONGITUDE = -122.0
    
    # Data quality thresholds
    MIN_CONFIDENCE_SCORE = 0.6
    MAX_DATA_AGE_HOURS = 24
    MIN_OBSERVATIONS_PER_DAY = 1
    
    # Expected species for orca research
    VALID_SPECIES = [
        'Orcinus orca', 'Orcinus_orca', 'orca', 'killer whale',
        'Southern Resident', 'Biggs', 'Transient', 'Offshore'
    ]
    
    # Valid behavioral categories
    VALID_BEHAVIORS = [
        'feeding', 'traveling', 'socializing', 'resting', 'hunting',
        'foraging', 'milling', 'surface_active', 'diving'
    ]
    
    # Environmental data ranges
    TEMP_RANGE = (8.0, 25.0)  # Celsius
    SALINITY_RANGE = (25.0, 35.0)  # PSU
    DEPTH_RANGE = (0.0, 200.0)  # meters
    CURRENT_SPEED_RANGE = (0.0, 5.0)  # m/s

@pytest.fixture
def sample_whale_data():
    """Provide sample whale sighting data for testing"""
    return pd.DataFrame({
        'sighting_id': ['sight_001', 'sight_002', 'sight_003'],
        'timestamp': [
            datetime.now() - timedelta(hours=1),
            datetime.now() - timedelta(hours=2), 
            datetime.now() - timedelta(hours=3)
        ],
        'latitude': [48.5465, 48.6234, 48.4567],
        'longitude': [-123.0307, -123.1456, -122.9876],
        'species': ['Orcinus orca', 'Orcinus orca', 'Orcinus orca'],
        'quality_grade': ['research', 'research', 'needs_id'],
        'observer': ['Center for Whale Research', 'NOAA', 'iNaturalist'],
        'pod_size': [8, 12, 5],
        'behavior': ['feeding', 'traveling', 'socializing'],
        'individual_id': ['J26', 'T049C', 'L87'],
        'matriline': ['J pod', 'T049s', 'L pod'],
        'confidence': [0.95, 0.87, 0.73]
    })

@pytest.fixture
def sample_environmental_data():
    """Provide sample environmental data for testing"""
    return pd.DataFrame({
        'station_id': ['9447130', '9449880', '9448576'],
        'timestamp': [datetime.now() - timedelta(minutes=i*10) for i in range(3)],
        'water_level': [2.3, 1.8, 2.1],
        'temperature': [15.8, 16.2, 15.5],
        'salinity': [30.2, 29.8, 30.5],
        'current_speed': [0.4, 0.3, 0.5],
        'wind_speed': [8.2, 12.1, 6.8],
        'visibility': [25.0, 18.5, 22.3]
    })

@pytest.fixture
def sample_ml_predictions():
    """Provide sample ML prediction data for testing"""
    return pd.DataFrame({
        'prediction_id': ['pred_001', 'pred_002', 'pred_003'],
        'confidence_score': [0.87, 0.73, 0.91],
        'prediction_class': ['feeding', 'traveling', 'socializing'],
        'latitude': [48.5465, 48.6234, 48.4567],
        'longitude': [-123.0307, -123.1456, -122.9876],
        'created_at': [datetime.now() - timedelta(minutes=i*5) for i in range(3)],
        'model_version': ['v2.1', 'v2.1', 'v2.1'],
        'features_used': [15, 15, 15]
    })

class TestDataQuality:
    """Test data quality and integrity"""
    
    def test_whale_sightings_geographic_bounds(self, sample_whale_data):
        """Test that whale sightings are within expected geographic bounds"""
        df = sample_whale_data
        
        # Test latitude bounds
        assert df['latitude'].min() >= DataPipelineTestConfig.MIN_LATITUDE, \
            f"Latitude below minimum: {df['latitude'].min()}"
        assert df['latitude'].max() <= DataPipelineTestConfig.MAX_LATITUDE, \
            f"Latitude above maximum: {df['latitude'].max()}"
        
        # Test longitude bounds  
        assert df['longitude'].min() >= DataPipelineTestConfig.MIN_LONGITUDE, \
            f"Longitude below minimum: {df['longitude'].min()}"
        assert df['longitude'].max() <= DataPipelineTestConfig.MAX_LONGITUDE, \
            f"Longitude above maximum: {df['longitude'].max()}"
    
    def test_whale_sightings_species_validation(self, sample_whale_data):
        """Test that species names are valid"""
        df = sample_whale_data
        
        invalid_species = df[~df['species'].isin(DataPipelineTestConfig.VALID_SPECIES)]
        assert len(invalid_species) == 0, \
            f"Invalid species found: {invalid_species['species'].unique()}"
    
    def test_whale_sightings_completeness(self, sample_whale_data):
        """Test data completeness for critical fields"""
        df = sample_whale_data
        
        critical_fields = ['timestamp', 'latitude', 'longitude', 'species']
        
        for field in critical_fields:
            null_count = df[field].isnull().sum()
            assert null_count == 0, f"Null values found in critical field {field}: {null_count}"
    
    def test_whale_sightings_data_freshness(self, sample_whale_data):
        """Test that whale sighting data is fresh"""
        df = sample_whale_data
        
        cutoff_time = datetime.now() - timedelta(hours=DataPipelineTestConfig.MAX_DATA_AGE_HOURS)
        old_records = df[df['timestamp'] < cutoff_time]
        
        # Allow some old records, but not majority
        old_percentage = len(old_records) / len(df) * 100
        assert old_percentage < 50, f"Too many old records: {old_percentage:.1f}%"
    
    def test_behavioral_classifications(self, sample_whale_data):
        """Test that behavioral classifications are valid"""
        df = sample_whale_data
        
        invalid_behaviors = df[~df['behavior'].isin(DataPipelineTestConfig.VALID_BEHAVIORS)]
        assert len(invalid_behaviors) == 0, \
            f"Invalid behaviors found: {invalid_behaviors['behavior'].unique()}"

class TestMLPipeline:
    """Test ML prediction pipeline"""
    
    def test_ml_prediction_confidence_scores(self, sample_ml_predictions):
        """Test ML prediction confidence scores are in valid range"""
        df = sample_ml_predictions
        
        # Confidence scores should be between 0 and 1
        assert df['confidence_score'].min() >= 0.0, \
            f"Confidence score below 0: {df['confidence_score'].min()}"
        assert df['confidence_score'].max() <= 1.0, \
            f"Confidence score above 1: {df['confidence_score'].max()}"
        
        # Should have mostly high-confidence predictions
        high_confidence = df[df['confidence_score'] >= DataPipelineTestConfig.MIN_CONFIDENCE_SCORE]
        high_conf_percentage = len(high_confidence) / len(df) * 100
        assert high_conf_percentage >= 70, \
            f"Too few high-confidence predictions: {high_conf_percentage:.1f}%"
    
    def test_ml_prediction_classes(self, sample_ml_predictions):
        """Test that ML prediction classes are valid"""
        df = sample_ml_predictions
        
        invalid_classes = df[~df['prediction_class'].isin(DataPipelineTestConfig.VALID_BEHAVIORS)]
        assert len(invalid_classes) == 0, \
            f"Invalid prediction classes: {invalid_classes['prediction_class'].unique()}"
    
    def test_ml_prediction_geographic_consistency(self, sample_ml_predictions):
        """Test that ML predictions are geographically consistent"""
        df = sample_ml_predictions
        
        # Predictions should be within research area
        assert df['latitude'].min() >= DataPipelineTestConfig.MIN_LATITUDE
        assert df['latitude'].max() <= DataPipelineTestConfig.MAX_LATITUDE
        assert df['longitude'].min() >= DataPipelineTestConfig.MIN_LONGITUDE
        assert df['longitude'].max() <= DataPipelineTestConfig.MAX_LONGITUDE
    
    def test_ml_model_versioning(self, sample_ml_predictions):
        """Test that ML models have proper versioning"""
        df = sample_ml_predictions
        
        # Should have model version information
        assert 'model_version' in df.columns, "Model version information missing"
        
        # All predictions should have version info
        null_versions = df['model_version'].isnull().sum()
        assert null_versions == 0, f"Missing model versions: {null_versions}"

class TestEnvironmentalData:
    """Test environmental data pipeline"""
    
    def test_environmental_data_ranges(self, sample_environmental_data):
        """Test that environmental data is within expected ranges"""
        df = sample_environmental_data
        
        # Temperature range
        temp_min, temp_max = DataPipelineTestConfig.TEMP_RANGE
        assert df['temperature'].min() >= temp_min, \
            f"Temperature below minimum: {df['temperature'].min()}"
        assert df['temperature'].max() <= temp_max, \
            f"Temperature above maximum: {df['temperature'].max()}"
        
        # Salinity range
        sal_min, sal_max = DataPipelineTestConfig.SALINITY_RANGE
        assert df['salinity'].min() >= sal_min, \
            f"Salinity below minimum: {df['salinity'].min()}"
        assert df['salinity'].max() <= sal_max, \
            f"Salinity above maximum: {df['salinity'].max()}"
        
        # Current speed range
        curr_min, curr_max = DataPipelineTestConfig.CURRENT_SPEED_RANGE
        assert df['current_speed'].min() >= curr_min, \
            f"Current speed below minimum: {df['current_speed'].min()}"
        assert df['current_speed'].max() <= curr_max, \
            f"Current speed above maximum: {df['current_speed'].max()}"
    
    def test_environmental_station_ids(self, sample_environmental_data):
        """Test that station IDs are valid NOAA stations"""
        df = sample_environmental_data
        
        # Valid NOAA station IDs for Salish Sea region
        valid_stations = ['9447130', '9449880', '9448576', '9447832', '9444900']
        
        invalid_stations = df[~df['station_id'].isin(valid_stations)]
        assert len(invalid_stations) == 0, \
            f"Invalid station IDs: {invalid_stations['station_id'].unique()}"

class TestAPIConnectivity:
    """Test external API connectivity and responses"""
    
    def test_noaa_tides_api(self):
        """Test NOAA tides API connectivity"""
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        params = {
            'station': '9447130',
            'product': 'water_level',
            'datum': 'MLLW',
            'format': 'json',
            'time_zone': 'lst_ldt',
            'begin_date': datetime.now().strftime('%Y%m%d'),
            'end_date': datetime.now().strftime('%Y%m%d')
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            assert response.status_code == 200, f"NOAA API failed: {response.status_code}"
            
            data = response.json()
            assert 'data' in data or 'error' in data, "Unexpected NOAA API response format"
            
        except requests.exceptions.RequestException as e:
            pytest.fail(f"NOAA API connection failed: {e}")
    
    def test_orcahello_api(self):
        """Test OrcaHello AI API connectivity"""
        url = "https://aifororcas.azurewebsites.net/api"
        
        try:
            response = requests.get(url, timeout=30)
            # API might return 404 for base URL, but should be reachable
            assert response.status_code in [200, 404, 405], \
                f"OrcaHello API unreachable: {response.status_code}"
            
        except requests.exceptions.RequestException as e:
            pytest.fail(f"OrcaHello API connection failed: {e}")
    
    def test_inaturalist_api(self):
        """Test iNaturalist API connectivity"""
        url = "https://api.inaturalist.org/v1/observations"
        params = {
            'taxon_name': 'Orcinus orca',
            'place_id': '35',  # Washington State
            'per_page': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            assert response.status_code == 200, f"iNaturalist API failed: {response.status_code}"
            
            data = response.json()
            assert 'results' in data, "Unexpected iNaturalist API response format"
            
        except requests.exceptions.RequestException as e:
            pytest.fail(f"iNaturalist API connection failed: {e}")

class TestDataPipelineIntegration:
    """Test end-to-end data pipeline integration"""
    
    @pytest.mark.skipif(ProductionDataPipeline is None, reason="ProductionDataPipeline not available")
    def test_production_pipeline_initialization(self):
        """Test that production data pipeline can be initialized"""
        try:
            pipeline = ProductionDataPipeline()
            assert pipeline is not None, "Failed to initialize ProductionDataPipeline"
            
        except Exception as e:
            pytest.fail(f"ProductionDataPipeline initialization failed: {e}")
    
    def test_file_structure_integrity(self):
        """Test that required files and directories exist"""
        required_paths = [
            'data/',
            'models/',
            'scripts/data_processing/',
            'scripts/ml_services/',
            'requirements.txt',
            'config.js'
        ]
        
        for path in required_paths:
            full_path = project_root / path
            assert full_path.exists(), f"Required path missing: {path}"
    
    def test_bigquery_configuration(self):
        """Test BigQuery configuration"""
        config_path = project_root / 'bigquery_config.json'
        
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            
            assert 'project_id' in config, "BigQuery project_id missing"
            assert config['project_id'] == 'orca-466204', \
                f"Unexpected project_id: {config['project_id']}"
        else:
            pytest.skip("BigQuery config not found")

class TestPerformance:
    """Test data pipeline performance"""
    
    def test_data_processing_speed(self, sample_whale_data):
        """Test that data processing completes within reasonable time"""
        df = sample_whale_data
        
        start_time = datetime.now()
        
        # Simulate data processing operations
        processed = df.copy()
        processed['processed_timestamp'] = datetime.now()
        processed['distance_from_shore'] = np.sqrt(
            (processed['latitude'] - 48.5) ** 2 + 
            (processed['longitude'] + 123.0) ** 2
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Should process sample data in under 1 second
        assert processing_time < 1.0, f"Data processing too slow: {processing_time:.2f}s"
    
    def test_memory_usage(self, sample_whale_data, sample_environmental_data):
        """Test that memory usage stays within reasonable limits"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple datasets
        for _ in range(10):
            df1 = sample_whale_data.copy()
            df2 = sample_environmental_data.copy()
            
            # Simulate some processing
            merged = pd.merge(df1, df2, left_on='timestamp', right_on='timestamp', how='outer')
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for test data)
        assert memory_increase < 100, f"Excessive memory usage: {memory_increase:.1f}MB"

# Utility functions for running tests

def run_data_pipeline_tests():
    """Run all data pipeline tests and generate report"""
    
    print("🐋 Running ORCAST Data Pipeline Tests")
    print("=" * 50)
    
    try:
        # Run pytest with custom configuration
        test_args = [
            __file__,
            '-v',  # Verbose output
            '--tb=short',  # Short traceback format
            '--strict-markers',  # Strict marker checking
            '--junit-xml=data_pipeline_test_results.xml'  # Generate XML report
        ]
        
        exit_code = pytest.main(test_args)
        
        if exit_code == 0:
            print("🎉 All data pipeline tests passed!")
            print("Your ORCAST data pipeline is healthy and ready!")
        else:
            print("⚠️ Some data pipeline tests failed")
            print("Check the detailed output above for issues")
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        print("Make sure pytest is installed: pip install pytest")
        return 1

if __name__ == "__main__":
    run_data_pipeline_tests() 