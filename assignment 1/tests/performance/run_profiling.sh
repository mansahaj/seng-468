#!/bin/bash

# Create results directory
mkdir -p results/profiling
export FLASK_DEBUG=False

# Install py-spy if not present (requires sudo usually, or user installation)
# Assuming py-spy is installed or we can install it via pip

echo "Starting Profiling..."

# 1. CPU Profiling with cProfile
echo "Starting app with cProfile..."
# Run app with cProfile
# We use -m cProfile -o output.pstats
python -m cProfile -o results/profiling/cpu_stats.prof app/app.py > /dev/null 2>&1 &
APP_PID=$!
echo "App PID: $APP_PID"

# Wait for app to start
sleep 5

# Run Load Test
echo "Running Load Test (45s)..."
export STOP_AFTER=45
locust -f tests/performance/locustfile.py --headless --host http://localhost:5000 --users 50 --spawn-rate 10 --csv results/profiling/cpu_load_test

# Kill app - SIGINT to allow it to write stats hopefully, or just kill
# cProfile usually writes on exit.
kill -SIGINT $APP_PID
wait $APP_PID
echo "CPU Profiling complete. Stats saved to results/profiling/cpu_stats.prof"

# 2. Memory Profiling with mprof
echo "Starting app for Memory profiling..."
# Run app with mprof
mprof run --output results/profiling/mprof_data.dat --python app/app.py > /dev/null 2>&1 &
MPROF_PID=$!
# APP_PID_MEM=$(pgrep -P $MPROF_PID -n) 

# Wait for app to start
sleep 5

# Run Load Test
echo "Running Load Test (60s)..."
export STOP_AFTER=60
locust -f tests/performance/locustfile.py --headless --host http://localhost:5000 --users 50 --spawn-rate 10 --csv results/profiling/mem_load_test

# Stop mprof
kill $MPROF_PID
sleep 1
# Plot memory usage
mprof plot --output results/profiling/memory_profile.png results/profiling/mprof_data.dat || echo "mprof plot failed"

echo "Memory Profiling complete."

# 3. I/O Profiling (Database logs)
echo "Fetching Database Logs..."
docker-compose logs --no-log-prefix db > results/profiling/db_slow_queries.log || echo "Docker logs failed"

echo "Profiling Complete. Results in results/profiling/"
