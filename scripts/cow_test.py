import os
import mmap
import time
import resource

# Параметри варіанта 26
MEM_MB = 272
PAGE_SIZE = mmap.PAGESIZE
MEM_BYTES = MEM_MB * 1024 * 1024
F_NUM = (1 + 26 % 4)  # 1 + 2 = 3
F_DEN = 8
F_FRACTION = F_NUM / F_DEN  # 3/8

def get_minor_faults():
    return resource.getrusage(resource.RUSAGE_SELF).ru_minflt

if __name__ == '__main__':
    print(f"Батьківський PID: {os.getpid()}")
    print(f"Виділяємо {MEM_MB} МБ пам'яті...")
    
    # Виділяємо пам'ять і заповнюємо її
    mem = bytearray(MEM_BYTES)
    for i in range(0, MEM_BYTES, PAGE_SIZE):
        mem[i] = 1
        
    print(f"Пам'ять заповнена. Поточні page faults батька: {get_minor_faults()}")
    print(f"Нащадок записуватиме у {F_NUM}/{F_DEN} сторінок ({F_FRACTION*100:.1f}%)\n")
    
    # Повторюємо дослід 5 разів, як просять у методичці
    for attempt in range(1, 6):
        print(f"--- Спроба {attempt} ---")
        pid = os.fork()
        
        if pid == 0:
            # ДОЧІРНІЙ ПРОЦЕС
            child_pid = os.getpid()
            pages_to_write = int((MEM_BYTES // PAGE_SIZE) * F_FRACTION)
            bytes_to_write = pages_to_write * PAGE_SIZE
            
            pf_start = get_minor_faults()
            t0 = time.perf_counter_ns()
            
            # Нащадок пише у свою частку
            for i in range(0, bytes_to_write, PAGE_SIZE):
                mem[i] = 2
                
            t_end = time.perf_counter_ns()
            pf_end = get_minor_faults()
            
            faults_diff = pf_end - pf_start
            print(f"[Нащадок {child_pid}] Записано сторінок: {pages_to_write}", flush=True)
            print(f"[Нащадок {child_pid}] Отримано minor page faults: {faults_diff}", flush=True)
            print(f"[Нащадок {child_pid}] Час запису: {(t_end - t0) / 1e6:.2f} мс\n", flush=True)
            
            os._exit(0)
        else:
            # БАТЬКІВСЬКИЙ ПРОЦЕС
            os.waitpid(pid, 0)
