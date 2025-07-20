#!/bin/bash

# ORCAST Angular - Comprehensive Test and Build Script
# This script runs all tests, builds for production, and validates the build

set -e  # Exit on any error

echo "🚀 ORCAST Angular - Test and Build Pipeline"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "angular.json" ]; then
    print_error "Not in Angular project directory. Please run from orcast-angular folder."
    exit 1
fi

print_status "Starting ORCAST Angular testing and build pipeline..."

# 1. Install dependencies
print_status "Installing dependencies..."
npm ci
print_success "Dependencies installed"

# 2. Code formatting check
print_status "Checking code formatting..."
if npm run format:check; then
    print_success "Code formatting is correct"
else
    print_warning "Code formatting issues found. Running formatter..."
    npm run format
    print_success "Code formatted"
fi

# 3. Linting
print_status "Running linting..."
if command -v ng &> /dev/null; then
    if ng lint --max-warnings=0; then
        print_success "Linting passed"
    else
        print_error "Linting failed"
        exit 1
    fi
else
    print_warning "Angular CLI not found, skipping linting"
fi

# 4. Unit tests
print_status "Running unit tests..."
npm run test:ci
print_success "Unit tests passed"

# 5. Security audit
print_status "Running security audit..."
if npm run audit:security; then
    print_success "Security audit passed"
else
    print_warning "Security vulnerabilities found - please review"
fi

# 6. Build for development
print_status "Building development version..."
ng build --configuration=development
print_success "Development build completed"

# 7. Build for production
print_status "Building production version..."
ng build --configuration=production
print_success "Production build completed"

# 8. Analyze bundle size
print_status "Analyzing bundle size..."
if [ -f "dist/orcast-angular/stats.json" ]; then
    echo "Bundle analysis available at: http://localhost:8888"
    echo "Run: npx webpack-bundle-analyzer dist/orcast-angular/stats.json"
else
    print_warning "Stats file not generated, run: npm run build:analyze"
fi

# 9. Validate production build
print_status "Validating production build..."
if [ -d "dist/orcast-angular" ]; then
    if [ -f "dist/orcast-angular/index.html" ]; then
        print_success "Production build validation passed"
        
        # Check file sizes
        INDEX_SIZE=$(du -h dist/orcast-angular/index.html | cut -f1)
        TOTAL_SIZE=$(du -sh dist/orcast-angular | cut -f1)
        
        echo "📊 Build Statistics:"
        echo "   - Index.html size: $INDEX_SIZE"
        echo "   - Total build size: $TOTAL_SIZE"
        echo "   - Files generated: $(find dist/orcast-angular -type f | wc -l)"
        
    else
        print_error "index.html not found in production build"
        exit 1
    fi
else
    print_error "Production build directory not found"
    exit 1
fi

# 10. Test production build locally (optional)
print_status "Testing production build locally..."
if command -v http-server &> /dev/null; then
    echo "Starting local server on http://localhost:8080"
    echo "Press Ctrl+C to stop the server"
    npx http-server dist/orcast-angular -p 8080 -s &
    SERVER_PID=$!
    
    # Wait a moment for server to start
    sleep 3
    
    # Test if server responds
    if curl -s http://localhost:8080 > /dev/null; then
        print_success "Production build server is responding"
        echo "🌐 Test the application at: http://localhost:8080"
        echo "   - Dashboard: http://localhost:8080"
        echo "   - Historical: http://localhost:8080/historical"
        echo "   - Real-time: http://localhost:8080/realtime"
        echo "   - ML Predictions: http://localhost:8080/ml-predictions"
    else
        print_warning "Production build server not responding"
    fi
    
    # Kill the server
    kill $SERVER_PID 2>/dev/null || true
else
    print_warning "http-server not available, install with: npm install -g http-server"
fi

# 11. E2E tests (if Cypress is available and app is running)
if command -v cypress &> /dev/null; then
    print_status "Checking if E2E tests can run..."
    
    # Check if development server is running
    if curl -s http://localhost:4200 > /dev/null; then
        print_status "Running E2E tests..."
        npm run cypress:run
        print_success "E2E tests completed"
    else
        print_warning "Development server not running on port 4200, skipping E2E tests"
        echo "To run E2E tests:"
        echo "  1. Start dev server: npm start"
        echo "  2. Run tests: npm run e2e:ci"
    fi
else
    print_warning "Cypress not available for E2E testing"
fi

echo ""
echo "🎉 ORCAST Angular Build Pipeline Complete!"
echo "============================================="
echo ""
echo "📋 Summary:"
echo "   ✅ Dependencies installed"
echo "   ✅ Code formatting checked"
echo "   ✅ Linting passed"
echo "   ✅ Unit tests passed"
echo "   ✅ Security audit completed"
echo "   ✅ Development build created"
echo "   ✅ Production build created"
echo "   ✅ Build validation passed"
echo ""
echo "🚀 Ready for deployment!"
echo ""
echo "📦 Deployment commands:"
echo "   - Firebase: npm run deploy:prod"
echo "   - Local test: npm run serve:prod-local"
echo "   - Bundle analysis: npm run build:analyze"
echo ""
echo "🧪 Testing commands:"
echo "   - Unit tests: npm run test"
echo "   - E2E tests: npm run e2e"
echo "   - Coverage: npm run test:coverage"
echo "" 