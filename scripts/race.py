import threading
import time
import sys
import csv
import statistics
import os

# Параметри варіанта 26
NT = 4
INC = 720
R = 1000
TOKEN = "LAB3-26-27"
EXPECTED = NT * INC

def step(c):
    return c + 1

def run_experiment(name, worker_func, interval, setup_func=None):
    print(f"--- Запуск {name} (перемикання: {interval} с) ---")
    sys.setswitchinterval(interval)
    
    results = []
    for t_idx in range(R):
        if setup_func:
            setup_func()
            
        barrier = threading.Barrier(NT + 1)
        
        def thread_wrapper():
            barrier.wait()
            worker_func()
            
        threads = [threading.Thread(target=thread_wrapper) for _ in range(NT)]
        for t in threads:
            t.start()
            
        t0 = time.perf_counter_ns()
        barrier.wait() # Одночасний старт
        
        for t in threads:
            t.join()
            
        dt = time.perf_counter_ns() - t0
        actual = counter
        lost = EXPECTED - actual
        results.append((t_idx, EXPECTED, actual, lost, dt))
        
    # Запис у CSV
    os.makedirs("data", exist_ok=True)
    with open(f"data/race_{name}_{TOKEN}.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['t_idx', 'expected', 'actual', 'lost', 'time_ns'])
        writer.writerows(results)
        
    # Статистика (відкидаємо перші 5% на розігрів)
    warmup = int(R * 0.05)
    valid = results[warmup:]
    
    lost_vals = [r[3] for r in valid]
    time_vals = [r[4] / 1000 for r in valid] # переводимо в мікросекунди
    
    lost_count = sum(1 for l in lost_vals if l > 0)
    med_time = statistics.median(time_vals)
    p95_time = sorted(time_vals)[int(len(time_vals) * 0.95)]
    
    print(f"Втрати: {lost_count}/{len(valid)} повторів")
    print(f"Медіана часу: {med_time:.1f} мкс")
    print(f"p95 часу: {p95_time:.1f} мкс\n")
    return med_time

counter = 0
lock = threading.Lock()
sem = threading.Semaphore(1)

# Робочі функції для різних режимів
def worker_none():
    global counter
    for _ in range(INC):
        counter = step(counter)

def worker_lock():
    global counter
    for _ in range(INC):
        with lock:
            counter = step(counter)

def worker_sem():
    global counter
    for _ in range(INC):
        with sem:
            counter = step(counter)

def worker_local():
    global counter
    local_c = 0
    for _ in range(INC):
        local_c += 1
    with lock:
        counter += local_c

def reset():
    global counter
    counter = 0

if __name__ == '__main__':
    base_time = run_experiment("none_0.005", worker_none, 0.005, reset)
    fast_time = run_experiment("none_1e-6", worker_none, 1e-6, reset)
    
    l_time = run_experiment("L", worker_lock, 1e-6, reset)
    print(f"Відносно бази (L): {l_time/fast_time:.2f}")
    
    s_time = run_experiment("S", worker_sem, 1e-6, reset)
    print(f"Відносно бази (S): {s_time/fast_time:.2f}")
    
    g_time = run_experiment("G", worker_local, 1e-6, reset)
    print(f"Відносно бази (G): {g_time/fast_time:.2f}")
