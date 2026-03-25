import hashlib
import multiprocessing as mp
import os
import time

CNET_ID = "sareneac"

def good_hash(digest: bytes) -> bool:
    return digest[0] == 0 and digest[1] == 0 and digest[2] == 0 and digest[3] < 16

def worker(start: int, step: int, stop: mp.Event, q: mp.Queue) -> None:
    i = start
    cnet = CNET_ID.encode("utf-8")

    while not stop.is_set():
        digest = hashlib.sha256(cnet + str(i).encode("utf-8")).digest()

        if good_hash(digest):
            q.put((i, digest.hex()))
            stop.set()
            return

        if (i - start) % 5_000_000 == 0:
            q.put(("progress", start, i))

        i += step

if __name__ == "__main__":
    nproc = os.cpu_count() or 4
    stop = mp.Event()
    q = mp.Queue()
    procs = []

    print(f"Starting with {nproc} workers")
    t0 = time.time()

    for start in range(nproc):
        p = mp.Process(target=worker, args=(start, nproc, stop, q))
        p.start()
        procs.append(p)

    nonce = None
    digest = None

    while True:
        msg = q.get()
        if isinstance(msg, tuple) and len(msg) == 2 and isinstance(msg[0], int):
            nonce, digest = msg
            print("FOUND")
            print("nonce =", nonce)
            print("hash  =", digest)
            break
        elif isinstance(msg, tuple) and msg[0] == "progress":
            _, worker_id, checked = msg
            elapsed = time.time() - t0
            print(f"worker {worker_id}: checked {checked} after {elapsed:.1f}s", flush=True)

    stop.set()
    for p in procs:
        p.terminate()
        p.join()

    if nonce is not None:
        print(f'\nPut this in puzzle.py:')
        print(f'nonce = "{nonce}"')