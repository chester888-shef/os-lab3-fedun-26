import threading
import time
import sys
import csv
import os

# Параметри варіанта 26
B = 4
P = 1
C = 3
N = 26
ITEMS = 2000
TOKEN = "LAB3-26-27"

class BoundedBuffer:
    def __init__(self, capacity):
        self.B = capacity
        self.buf = [None] * self.B
        self.inp = 0
        self.out = 0
        self.count = 0
        self.M = threading.Lock()
        self.not_full = threading.Condition(self.M)
        self.not_empty = threading.Condition(self.M)
        self.waits_put = 0
        self.waits_get = 0

    def put(self, item):
        with self.M:
            while self.count == self.B:
                self.waits_put += 1
                self.not_full.wait()
            self.buf[self.inp] = item
            self.inp = (self.inp + 1) % self.B
            self.count += 1
            self.not_empty.notify()

    def get(self):
        with self.M:
            while self.count == 0:
                self.waits_get += 1
                self.not_empty.wait()
            item = self.buf[self.out]
            self.out = (self.out + 1) % self.B
            self.count -= 1
            self.not_full.notify()
            return item

def producer(buf, mode, prod_id):
    print(f"Виробник {prod_id} стартував (TID: {threading.get_native_id()})")
    for i in range(ITEMS):
        val = i * N + 1
        put_time = time.perf_counter_ns()
        buf.put((i, val, put_time))
        if mode == 'c':
            time.sleep(0.005)

def consumer(buf, mode, cons_id, results):
    print(f"Споживач {cons_id} стартував (TID: {threading.get_native_id()})")
    while True:
        item = buf.get()
        if item == "STOP":
            break
        get_time = time.perf_counter_ns()
        num, val, put_time = item
        delay = get_time - put_time
        results.append((num, val, delay))
        if mode == 'b':
            time.sleep(0.001)

def run_mode(mode):
    print(f"\n--- Запуск режиму '{mode}' ---")
    buf = BoundedBuffer(B)
    results = []
    
    producers = [threading.Thread(target=producer, args=(buf, mode, i)) for i in range(P)]
    consumers = [threading.Thread(target=consumer, args=(buf, mode, i, results)) for i in range(C)]
    
    for c in consumers: c.start()
    for p in producers: p.start()
    
    for p in producers: p.join()
    
    for _ in range(C):
        buf.put("STOP")
        
    for c in consumers: c.join()
    
    # Перевірка правильності
    total_received = len(results)
    sum_vals = sum(r[1] for r in results)
    expected_sum = sum(i * N + 1 for i in range(ITEMS))
    
    print(f"Отримано елементів: {total_received} (Очікувано: {ITEMS})")
    print(f"Сума значень: {sum_vals} (Очікувано: {expected_sum})")
    print(f"waits_put (виробник чекав): {buf.waits_put}")
    print(f"waits_get (споживач чекав): {buf.waits_get}")
    
    os.makedirs("data", exist_ok=True)
    with open(f"data/buffer_{mode}_{TOKEN}.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['num', 'val', 'delay_ns'])
        for r in results:
            writer.writerow(r)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_mode(sys.argv[1])
    else:
        run_mode('a')
        run_mode('b')
        run_mode('c')
