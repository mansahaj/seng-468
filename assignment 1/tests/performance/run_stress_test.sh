#!/bin/bash

# Create results directory if it doesn't exist
mkdir -p results

echo "Starting Stress Test..."
echo "Target: http://localhost:5000"
echo "Results will be saved to results/stress_test.csv"
echo "HTML report will be saved to results/report.html"

# Run locust
# -f: locust file
# --headless: no UI
# -u: start users (controlled by LoadShape, but required arg sometimes or ignored if Shape present)
# --host: target host
# --csv: output prefix
# --html: html report
# --run-time: how long to run (optional, maybe 20m to reach ~600 users?)
# Let's run for 20 minutes to see the knee
locust -f tests/performance/locustfile.py \
       --headless \
       --host http://localhost:5000 \
       --csv results/stress_test \
       --html results/report.html \
       --run-time 20m 
