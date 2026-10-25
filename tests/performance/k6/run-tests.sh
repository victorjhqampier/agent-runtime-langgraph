#!/bin/bash
# run-tests.sh
# Script para ejecutar tests k6 con parámetros parametrizables
# Uso: ./run-tests.sh [test-type] [--url URL] [--vus N] [--duration Ns]

set -e

# Defaults
BASE_URL="http://127.0.0.1:8000"
VUS=50
DURATION="30s"
TEST_TYPE="${1:-all}"

# Parse arguments
while [[ $# -gt 1 ]]; do
  case $2 in
    --url)
      BASE_URL="$3"
      shift 2
      ;;
    --vus)
      VUS="$3"
      shift 2
      ;;
    --duration)
      DURATION="$3"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

echo "================================"
echo "K6 Performance Test Runner"
echo "================================"
echo "URL: $BASE_URL"
echo "VUs: $VUS"
echo "Duration: $DURATION"
echo ""

# Function to run a test
run_test() {
  local test_file=$1
  local test_name=$2
  
  echo "📊 Running: $test_name"
  echo "   File: $test_file"
  
  k6 run "$test_file" \
    --env BASE_URL="$BASE_URL" \
    --vus "$VUS" \
    --duration "$DURATION"
  
  echo "✅ $test_name completed"
  echo ""
}

# Execute tests based on type
case $TEST_TYPE in
  smoke)
    echo "🔥 SMOKE TESTS"
    run_test "smoke/basic-health-check.smoke.js" "Health Check"
    run_test "smoke/endpoints-validation.smoke.js" "Endpoints Validation"
    ;;
  
  rps)
    echo "📈 RPS TESTS (Requests Per Second)"
    run_test "rps/bian-example.rps.js" "BianExampleController RPS"
    run_test "rps/no-bian-example.rps.js" "NoBianExampleController RPS"
    run_test "rps/no-bian-redis.rps.js" "NoBianExampleRedisController RPS"
    ;;
  
  stress)
    echo "💥 STRESS TEST"
    run_test "stress/concurrent-load.stress.js" "Concurrent Load"
    ;;
  
  soak)
    echo "🧊 SOAK TEST"
    run_test "soak/long-running.soak.js" "Long-running Stability"
    ;;
  
  all)
    echo "🚀 FULL TEST SUITE"
    echo "Running all tests..."
    run_test "smoke/basic-health-check.smoke.js" "Health Check"
    run_test "smoke/endpoints-validation.smoke.js" "Endpoints Validation"
    run_test "rps/bian-example.rps.js" "BianExampleController RPS"
    run_test "rps/no-bian-example.rps.js" "NoBianExampleController RPS"
    run_test "rps/no-bian-redis.rps.js" "NoBianExampleRedisController RPS"
    run_test "stress/concurrent-load.stress.js" "Concurrent Load"
    run_test "soak/long-running.soak.js" "Long-running Stability"
    ;;
  
  *)
    echo "❌ Unknown test type: $TEST_TYPE"
    echo ""
    echo "Usage: ./run-tests.sh [test-type] [--url URL] [--vus N] [--duration Ns]"
    echo ""
    echo "Test types:"
    echo "  smoke      - Quick validation tests (health + endpoints)"
    echo "  rps        - Requests per second tests for all endpoints"
    echo "  stress     - Find system limits with gradual load"
    echo "  soak       - Long-running stability test"
    echo "  all        - Run all tests (default)"
    echo ""
    echo "Options:"
    echo "  --url URL      Base URL (default: http://127.0.0.1:8000)"
    echo "  --vus N        Virtual Users (default: 50)"
    echo "  --duration Ns  Test duration (default: 30s)"
    echo ""
    echo "Examples:"
    echo "  ./run-tests.sh smoke"
    echo "  ./run-tests.sh rps --vus 100 --duration 60s"
    echo "  ./run-tests.sh stress --url http://127.0.0.1:8000 --vus 200"
    exit 1
    ;;
esac

echo "================================"
echo "All tests completed! 🎉"
echo "================================"
