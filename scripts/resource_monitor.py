import os
import sys
import time
import csv

def get_process_metrics(pid):
    stat_path = f"/proc/{pid}/stat"
    status_path = f"/proc/{pid}/status"
    io_path = f"/proc/{pid}/io"
    
    if not os.path.exists(stat_path):
        return None
        
    try:
        with open(stat_path, "r") as pf:
            stat_content = pf.read().split()
        threads = int(stat_content[19])
        
        vsz_kb = 0
        rss_kb = 0
        if os.path.exists(status_path):
            with open(status_path, "r") as pf:
                for line in pf:
                    if line.startswith("VmSize:"):
                        vsz_kb = int(line.split()[1])
                    elif line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                    elif line.startswith("Threads:"):
                        threads = int(line.split()[1])
                        
        min_faults = int(stat_content[9])
        maj_faults = int(stat_content[11])
        page_faults = min_faults + maj_faults

        read_bytes = "NA"
        write_bytes = "NA"
        if os.path.exists(io_path):
            with open(io_path, "r") as pf:
                for line in pf:
                    if line.startswith("read_bytes:"):
                        read_bytes = int(line.split()[1])
                    elif line.startswith("write_bytes:"):
                        write_bytes = int(line.split()[1])
                        
        return rss_kb, vsz_kb, threads, page_faults, read_bytes, write_bytes
    except Exception:
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 resource_monitor.py <PID> <DELTA>", file=sys.stderr)
        sys.exit(1)
        
    try:
        target_pid = int(sys.argv[1])
        delta = float(sys.argv[2])
    except ValueError:
        print("Error: PID must be integer and DELTA must be a number.", file=sys.stderr)
        sys.exit(1)
        
    if not os.path.exists(f"/proc/{target_pid}"):
        print(f"Error: Process with PID {target_pid} does not exist.", file=sys.stderr)
        sys.exit(2)
        
    token = "LAB3-26-27"
    os.makedirs("data", exist_ok=True)
    csv_filename = f"data/monitor_{target_pid}_{token}.csv"
    
    print(f"Starting resource monitor for PID {target_pid} with interval {delta}s...")
    max_points = 600
    
    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t_idx", "ts_ms", "rss_kb", "vsz_kb", "threads", "page_faults", "read_bytes", "write_bytes"])
        
        t_idx = 0
        while t_idx < max_points:
            loop_start = time.time()
            
            if not os.path.exists(f"/proc/{target_pid}"):
                print(f"Process {target_pid} terminated during monitoring.")
                break
                
            metrics = get_process_metrics(target_pid)
            if metrics is None:
                print(f"Process {target_pid} disappeared or unreadable.")
                break
                
            rss_kb, vsz_kb, threads, page_faults, read_bytes, write_bytes = metrics
            ts_ms = int(time.time() * 1000)
            
            writer.writerow([t_idx, ts_ms, rss_kb, vsz_kb, threads, page_faults, read_bytes, write_bytes])
            f.flush()
            
            t_idx += 1
            
            elapsed = time.time() - loop_start
            sleep_time = delta - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    print(f"Monitoring finished. Saved to {csv_filename}")
