#!/bin/bash
# ORCAST Data Pipeline Testing Runner
# Run comprehensive data pipeline tests like Cypress for web apps

echo "🐋 ORCAST Data Pipeline Testing Suite"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "great_expectations_setup.py" ]; then
    echo "❌ Error: Must run from scripts/data_processing directory"
    echo "   cd scripts/data_processing && ./run_pipeline_tests.sh"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import pytest, great_expectations, pandas, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing missing dependencies..."
    pip install -r ../../requirements.txt
fi

echo ""
echo "🔍 Running Data Pipeline Tests..."
echo "================================="

# Option 1: Run pytest framework (fast)
echo ""
echo "1️⃣ Running pytest framework tests..."
python3 pytest_data_pipeline_tests.py
pytest_exit_code=$?

# Option 2: Run Great Expectations (comprehensive)
echo ""
echo "2️⃣ Running Great Expectations tests..."
python3 great_expectations_setup.py
ge_exit_code=$?

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="

if [ $pytest_exit_code -eq 0 ]; then
    echo "✅ pytest framework: PASSED"
else
    echo "❌ pytest framework: FAILED"
fi

if [ $ge_exit_code -eq 0 ]; then
    echo "✅ Great Expectations: PASSED"
else
    echo "❌ Great Expectations: FAILED"
fi

# Overall result
if [ $pytest_exit_code -eq 0 ] && [ $ge_exit_code -eq 0 ]; then
    echo ""
    echo "🎉 ALL DATA PIPELINE TESTS PASSED!"
    echo "Your ORCAST whale research pipeline is healthy!"
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed. Check output above for details."
    exit 1
fi 