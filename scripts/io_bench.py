import os
import time
import csv
import statistics

TOKEN = "LAB3-26-27"
CONFIGS = [
    (512, 2000),
    (4096, 2000),
    (65536, 2000),
    (1048576, 256)
]

def format_size(b):
    if b == 512: return "512 Б"
    elif b == 4096: return "4 КБ"
    elif b == 65536: return "64 КБ"
    elif b == 1048576: return "1 МБ"
    return str(b)

def get_io_stats():
    try:
        with open('/proc/self/io', 'r') as f:
            lines = f.readlines()
            wchar = next((int(l.split(':')[1]) for l in lines if l.startswith('wchar')), 0)
            wbytes = next((int(l.split(':')[1]) for l in lines if l.startswith('write_bytes')), 0)
            return wchar, wbytes
    except:
        return 0, 0

def run_io_bench(block_size, ops, mode):
    filename = f"test_{mode}_{block_size}.dat"
    data = os.urandom(block_size)
    times_ns = []
    
    # Для Завдання 6.2
    capture_io = (block_size == 65536 and mode == 'buffered')
    io_start, io_after_write, io_final = (0,0), (0,0), (0,0)
    
    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    
    if capture_io: io_start = get_io_stats()
    
    total_start = time.perf_counter()
    for i in range(ops):
        t0 = time.perf_counter_ns()
        os.write(fd, data)
        if mode == 'fsync':
            os.fsync(fd)
        t1 = time.perf_counter_ns()
        times_ns.append(t1 - t0)
        
    if capture_io: io_after_write = get_io_stats()
        
    if mode == 'buffered':
        t0 = time.perf_counter_ns()
        os.fsync(fd)
        t1 = time.perf_counter_ns()
        final_fsync_ms = (t1 - t0) / 1e6
    else:
        final_fsync_ms = 0.0
        
    if capture_io: io_final = get_io_stats()
        
    total_time = time.perf_counter() - total_start
    os.close(fd)
    
    times_us = [t / 1000.0 for t in times_ns]
    med = statistics.median(times_us)
    p95 = sorted(times_us)[int(len(times_us) * 0.95)]
    p99 = sorted(times_us)[int(len(times_us) * 0.99)]
    
    iops = ops / total_time
    mbs = (ops * block_size / (1024 * 1024)) / total_time
    
    os.makedirs("data", exist_ok=True)
    csv_path = f"data/io_{mode}_{block_size}_{TOKEN}.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['t_idx', 'time_ns'])
        for idx, t in enumerate(times_ns):
            writer.writerow([idx, t])
            
    os.remove(filename)
    
    if capture_io:
        print("\n--- Завдання 6.2 Лічильники I/O (Блок 64 КБ, buffered) ---")
        print(f"До запису:          wchar={io_start[0]}, write_bytes={io_start[1]}")
        print(f"Після os.write():   wchar={io_after_write[0]}, write_bytes={io_after_write[1]}")
        print(f"Після os.fsync():   wchar={io_final[0]}, write_bytes={io_final[1]}")
        print("-" * 60)
    
    return med, p95, p99, iops, mbs, final_fsync_ms

def test_read_cache():
    filename = "test_read.dat"
    block_size = 1048576
    ops = 256
    data = os.urandom(block_size)
    
    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    for _ in range(ops): os.write(fd, data)
    os.fsync(fd)
    os.close(fd)
    
    fd = os.open(filename, os.O_RDONLY)
    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED) # Скидаємо кеш
    
    t0 = time.perf_counter()
    while os.read(fd, block_size): pass
    t1 = time.perf_counter()
    mbs1 = (ops * block_size / (1024 * 1024)) / (t1 - t0)
    
    os.lseek(fd, 0, os.SEEK_SET) # Повертаємося на початок
    
    t0 = time.perf_counter()
    while os.read(fd, block_size): pass
    t1 = time.perf_counter()
    mbs2 = (ops * block_size / (1024 * 1024)) / (t1 - t0)
    
    os.close(fd)
    os.remove(filename)
    
    print("\n--- Завдання 6.1 Читання: page cache ---")
    print(f"Холодне читання (з диска, після fadvise): {mbs1:.2f} МБ/с")
    print(f"Гаряче читання  (з RAM, через page cache): {mbs2:.2f} МБ/с\n")

if __name__ == '__main__':
    print(f"{'Розмір':<6} | {'Режим':<8} | {'Медіана(мкс)':<12} | {'p95(мкс)':<10} | {'IOPS':<8} | {'МБ/с':<8} | {'Final fsync'}")
    print("-" * 85)
    
    for size, ops in CONFIGS:
        for mode in ['buffered', 'fsync']:
            med, p95, p99, iops, mbs, final = run_io_bench(size, ops, mode)
            sz_str = format_size(size)
            final_str = f"{final:.2f} ms" if mode == 'buffered' else "-"
            print(f"{sz_str:<6} | {mode:<8} | {med:<12.1f} | {p95:<10.1f} | {iops:<8.0f} | {mbs:<8.2f} | {final_str}")
            
    test_read_cache()
