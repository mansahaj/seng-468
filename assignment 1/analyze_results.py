import pandas as pd
import matplotlib.pyplot as plt
import sys

# Read the data
try:
    df = pd.read_csv('results/stress_test_stats_history.csv')
except FileNotFoundError:
    print("Error: results/stress_test_stats_history.csv not found.")
    sys.exit(1)

# Inspect the dataframe columns to ensure we have what we need
# Typically: "Timestamp", "User Count", "Type", "Name", "Requests/s", "Failures/s", "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "100%", "Total Request Count", "Total Failure Count", "Total Median Response Time", "Total Average Response Time", "Total Min Response Time", "Total Max Response Time", "Total Average Content Size"
print("Columns:", df.columns)

# Filter out rows where User Count is NaN or 0 if necessary
df = df[df['User Count'] > 0]

# 1. Plot Latency vs User Count
plt.figure(figsize=(10, 6))
plt.plot(df['User Count'], df['Total Average Response Time'], label='Average Response Time')
plt.plot(df['User Count'], df['95%'], label='95th Percentile', linestyle='--')
plt.xlabel('Concurrent Users')
plt.ylabel('Response Time (ms)')
plt.title('Latency vs Concurrent Users')
plt.legend()
plt.grid(True)
plt.savefig('results/latency_vs_users.png')
print("Saved results/latency_vs_users.png")

# 2. Plot Throughput vs User Count
plt.figure(figsize=(10, 6))
plt.plot(df['User Count'], df['Requests/s'], label='Throughput (Req/s)', color='green')
plt.xlabel('Concurrent Users')
plt.ylabel('Requests/s')
plt.title('Throughput vs Concurrent Users')
plt.legend()
plt.grid(True)
plt.savefig('results/throughput_vs_users.png')
print("Saved results/throughput_vs_users.png")

# 3. Identify Knee
# Simple heuristic: excessive latency (e.g. > 1000ms) or drop in throughput
knee_latency = df[df['Total Average Response Time'] > 1000].head(1)
if not knee_latency.empty:
    print(f"Knee identified (Latency > 1s): {knee_latency['User Count'].values[0]} users")
else:
    print("No latency knee > 1s found.")

# Failure analysis
# Check where failures start occurring
failures = df[df['Failures/s'] > 0].head(1)
if not failures.empty:
    print(f"Failures started at: {failures['User Count'].values[0]} users")
else:
    print("No failures recorded in stats history.")
