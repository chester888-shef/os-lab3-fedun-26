import mmap
import os
import resource
import time
import ctypes
import sys
import csv

# Параметри варіанта 26
MEM_MB = 272
PAGE_SIZE = mmap.PAGESIZE
MEM_BYTES = MEM_MB * 1024 * 1024
TOKEN = "LAB3-26-27"

def print_stats(phase_name):
    pid = os.getpid()
    with open(f'/proc/{pid}/statm', 'r') as f:
        statm = f.read().split()
        vsz_kb = int(statm[0]) * PAGE_SIZE // 1024
        rss_kb = int(statm[1]) * PAGE_SIZE // 1024
    
    usage = resource.getrusage(resource.RUSAGE_SELF)
    minflt = usage.ru_minflt
    
    print(f"[{phase_name}] VSZ: {vsz_kb} KB | RSS: {rss_kb} KB | Minor Page Faults: {minflt}")
    return minflt

if __name__ == '__main__':
    pid = os.getpid()
    print(f"PID програми: {pid}")
    print(f"Розмір сторінки (PAGESIZE): {PAGE_SIZE} байт")
    
    # Фаза A
    pf_A = print_stats("Фаза A")
    input("Натисніть Enter для переходу до Фази B (mmap)...")
    
    # Фаза B
    mem = mmap.mmap(-1, MEM_BYTES, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    addr = ctypes.addressof(ctypes.c_char.from_buffer(mem))
    print(f"Адреса початку відображення: {hex(addr)}")
    
    pf_B = print_stats("Фаза B")
    input(f"Натисніть Enter для переходу до Фази C (Перший прохід)...\nПОКИ ЧЕКАЄТЕ: Відкрийте інший термінал і виконайте команду 'cat /proc/{pid}/maps'")
    
    # Фаза C (перший дотик)
    pass1_ns = []
    print("Виконується перший прохід (pass1)...")
    for off in range(0, MEM_BYTES, PAGE_SIZE):
        t0 = time.perf_counter_ns()
        mem[off] = 1  # Записуємо 1 байт
        pass1_ns.append(time.perf_counter_ns() - t0)
        
    pf_C = print_stats("Фаза C")
    print(f"Приріст page faults за фазу C: {pf_C - pf_B}")
    input("Натисніть Enter для переходу до Фази D (Другий прохід)...")
    
    # Фаза D (другий дотик)
    pass2_ns = []
    print("Виконується другий прохід (pass2)...")
    for off in range(0, MEM_BYTES, PAGE_SIZE):
        t0 = time.perf_counter_ns()
        mem[off] = 2  # Записуємо ще 1 байт
        pass2_ns.append(time.perf_counter_ns() - t0)
        
    pf_D = print_stats("Фаза D")
    print(f"Приріст page faults за фазу D: {pf_D - pf_C}")
    
    # Запис CSV
    os.makedirs("data", exist_ok=True)
    with open(f"data/pages_{TOKEN}.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['t_idx', 'pass1_ns', 'pass2_ns'])
        for i in range(len(pass1_ns)):
            writer.writerow([i, pass1_ns[i], pass2_ns[i]])
            
    mem.close()
    print("Завершено. Дані збережено.")
