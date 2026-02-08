import pstats
import os

print("=== CPU Profiling Analysis ===")
try:
    p = pstats.Stats('results/profiling/cpu_stats.prof')
    p.strip_dirs().sort_stats('cumulative').print_stats(20)
except Exception as e:
    print(f"Error analyzing CPU stats: {e}")

print("\n=== Memory Profiling Analysis ===")
try:
    if os.path.exists('results/profiling/mprof_data.dat'):
        with open('results/profiling/mprof_data.dat', 'r') as f:
            lines = f.readlines()
            print(f"Lines in mprof data: {len(lines)}")
            if len(lines) > 0:
                print("First 5 lines:")
                print("".join(lines[:5]))
                print("Last 5 lines:")
                print("".join(lines[-5:]))
    else:
        print("mprof_data.dat not found")
except Exception as e:
    print(f"Error analyzing memory stats: {e}")

print("\n=== DB Slow Query Analysis ===")
try:
    if os.path.exists('results/profiling/db_slow_queries.log'):
        with open('results/profiling/db_slow_queries.log', 'r') as f:
            lines = f.readlines()
            slow_queries = [l for l in lines if 'duration:' in l]
            print(f"Found {len(slow_queries)} slow queries.")
            for q in slow_queries[:10]:
                print(q.strip())
    else:
        print("db_slow_queries.log not found")
except Exception as e:
    print(f"Error analyzing DB logs: {e}")
