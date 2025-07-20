# ORCAST Data Pipeline Testing Guide

## Overview
This guide provides **Cypress-equivalent testing frameworks** for your ORCAST whale research data pipeline. These tools automatically discover and test broken points in your data infrastructure.

## 🏆 Testing Framework Options

### 1. Great Expectations (Recommended)
**Most Cypress-like experience** - automatically profiles data and creates comprehensive test suites.

### 2. pytest Framework
**Python-native solution** - integrates with your existing Python infrastructure.

### 3. Soda Core (Alternative)
**Open-source data quality** - lightweight alternative to Great Expectations.

## 🚀 Quick Setup

### Install Dependencies
```bash
# Install testing dependencies (already added to requirements.txt)
pip install -r requirements.txt

# Or install individually:
pip install pytest great-expectations psutil pytest-html
```

### Run Tests

#### Option 1: Great Expectations (Comprehensive)
```bash
# Setup and run comprehensive data testing
cd scripts/data_processing
python great_expectations_setup.py

# This will:
# ✅ Auto-discover data quality issues  
# ✅ Test whale sighting data integrity
# ✅ Validate ML prediction pipeline
# ✅ Check environmental data ranges
# ✅ Test API connectivity
# ✅ Generate detailed reports
```

#### Option 2: pytest Framework (Fast)
```bash
# Run Python-native pipeline tests
cd scripts/data_processing  
python pytest_data_pipeline_tests.py

# Or use pytest directly:
pytest pytest_data_pipeline_tests.py -v
```

## 🔍 What Gets Tested

### Data Quality Tests
- **Geographic bounds** - Whale sightings in San Juan Islands region
- **Species validation** - Only valid orca species/ecotypes
- **Data completeness** - No missing critical fields
- **Data freshness** - Recent observations within 24 hours
- **Behavioral classifications** - Valid feeding/traveling/socializing behaviors

### ML Pipeline Tests  
- **Confidence scores** - Predictions between 0-1, mostly high-confidence
- **Prediction classes** - Valid behavioral categories
- **Geographic consistency** - Predictions within research area
- **Model versioning** - Proper ML model tracking

### Environmental Data Tests
- **Temperature ranges** - Salish Sea conditions (8-25°C)
- **Salinity levels** - Marine environment (25-35 PSU)
- **Current speeds** - Realistic tidal flows (0-5 m/s)
- **Station validation** - Real NOAA station IDs

### API Connectivity Tests
- **NOAA Tides API** - Live environmental data
- **OrcaHello AI API** - Hydrophone detections
- **iNaturalist API** - Citizen science observations

### Performance Tests
- **Processing speed** - Data pipeline performance
- **Memory usage** - Resource consumption monitoring

## 🎯 Automated Discovery Features

### Like Cypress, these frameworks automatically:

1. **Profile your data** to understand normal patterns
2. **Generate expectations** based on data characteristics  
3. **Detect anomalies** when data changes unexpectedly
4. **Create visual reports** showing test results
5. **Alert on failures** when data quality degrades
6. **Track changes** over time for trend analysis

## 📊 Test Reports

Both frameworks generate comprehensive reports:

- **HTML reports** with interactive visualizations
- **JSON reports** for integration with CI/CD
- **XML reports** for Jenkins/GitHub Actions
- **CSV exports** for analysis in Excel/R

## 🔧 Customization for Your Pipeline

### Add Custom Tests
```python
# In pytest_data_pipeline_tests.py, add new test classes:

class TestCustomOrcaData:
    def test_individual_orca_tracking(self, whale_data):
        """Test individual orca ID consistency"""
        # Your custom validation logic
        pass
        
    def test_pod_behavior_patterns(self, whale_data):
        """Test pod-level behavioral patterns"""
        # Your domain-specific tests
        pass
```

### Configure Data Sources
```python
# In great_expectations_setup.py, update data sources:
self.data_sources = {
    'your_custom_source': {
        'path': 'data/your_data.csv',
        'bigquery_table': 'your-project.dataset.table',
        'critical': True
    }
}
```

## 🚨 Integration with CI/CD

### GitHub Actions Integration
```yaml
# .github/workflows/data-pipeline-tests.yml
name: Data Pipeline Tests
on: [push, pull_request]

jobs:
  test-data-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run data pipeline tests
        run: |
          cd scripts/data_processing
          python pytest_data_pipeline_tests.py
```

## 🎨 Visual Dashboard

Great Expectations provides a **data docs dashboard** similar to Cypress Test Runner:

```bash
# Generate and view data documentation
great_expectations docs build
great_expectations docs list
```

This creates an interactive web dashboard showing:
- Test results with pass/fail status
- Data profiling and statistics  
- Expectation validation results
- Historical test trends

## 🔄 Continuous Monitoring

Set up **continuous data monitoring**:

```python
# Schedule regular data quality checks
from scripts.data_processing.great_expectations_setup import ORCASTDataPipelineTester

def daily_data_quality_check():
    """Run daily data quality monitoring"""
    tester = ORCASTDataPipelineTester()
    tester.setup_great_expectations()
    results = tester.run_comprehensive_data_tests()
    
    # Alert on failures
    if not all(results.values()):
        send_alert("Data quality issues detected in ORCAST pipeline")

# Run via cron or scheduler
```

## 📈 Performance Comparison

| Framework | Setup Time | Test Speed | Features | Learning Curve |
|-----------|------------|------------|----------|----------------|
| Great Expectations | 10 min | Medium | Comprehensive | Moderate |
| pytest Framework | 5 min | Fast | Flexible | Easy |
| Soda Core | 15 min | Fast | Good | Moderate |

## 🎉 Benefits

### Automatic Issue Detection
- **Data drift detection** - When whale behavior patterns change
- **Schema validation** - Ensure consistent data structure
- **Outlier identification** - Unusual sightings or measurements
- **Missing data alerts** - When expected data doesn't arrive

### Reliability  
- **Prevent bad data** from reaching ML models
- **Catch API failures** before they impact users
- **Validate transformations** ensure data processing accuracy
- **Monitor performance** track pipeline speed and resource usage

## 🆘 Troubleshooting

### Common Issues

1. **ImportError: No module named 'pytest'**
   ```bash
   pip install -r requirements.txt
   ```

2. **Great Expectations context not found**
   ```bash
   cd scripts/data_processing
   python great_expectations_setup.py
   ```

3. **API connection timeouts**
   - Check internet connectivity
   - Verify API endpoints are accessible
   - Consider rate limiting

## 🤝 Getting Help

1. Check the generated test reports for detailed error information
2. Review the logs for specific failure reasons  
3. Customize test thresholds based on your data characteristics
4. Add new tests for domain-specific whale research requirements

---

**Your ORCAST data pipeline now has comprehensive testing coverage like Cypress provides for web applications!** 🐋 