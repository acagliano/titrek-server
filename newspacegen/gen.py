import numpy as np
import random
import pickle
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import signal
import sys
import time

space_map = []
star_positions = []
planet_positions = []


def generate_space_map(start, end, map_size, min_distance, seed, max_time_per_gen, thread_id):
    random.seed(seed)
    np.random.seed(seed)

    row = []
    for i in tqdm(range(start, end), desc=f"Thread {thread_id}: Generating Space Map", position=thread_id):
        for j in range(map_size):
            gen_start_time = time.time()
            celestial_body = random.random()
            x, y, z = np.random.uniform(0, map_size * 10, size=3)

            while any(((x - pos[0]) ** 2 + (y - pos[1]) ** 2 + (z - pos[2]) ** 2) ** 0.5 < min_distance
                      for pos in star_positions + planet_positions):
                x, y, z = np.random.uniform(0, map_size * 10, size=3)

            if celestial_body < 0.05:
                # Star
                star_color = random.choice(['Yellow', 'Red', 'Blue'])
                size = random.uniform(10, 20)
                star_name = f'Star_{i}_{j}'
                row.append({'type': 'Star', 'star_name': star_name, 'star_color': star_color, 'x': x, 'y': y, 'z': z,
                            'size': size})
                star_positions.append((x, y, z))

            elif celestial_body < 0.2:
                # Planet
                planet_type = random.choice(['Earth-like', 'Gas giant', 'Ice planet'])
                atmosphere_color = random.choice(['Blue', 'Red', 'Green'])
                size = random.uniform(20, 100)
                planet_name = f'Planet_{i}_{j}'
                row.append({'type': 'Planet', 'planet_name': planet_name, 'planet_type': planet_type,
                            'atmosphere_color': atmosphere_color,
                            'x': x, 'y': y, 'z': z, 'size': size})
                planet_positions.append((x, y, z))

            if time.time() - gen_start_time > max_time_per_gen != -1:
                break

    return row


def signal_handler(sig, frame):
    print("\nCTRL-C received. Stopping gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    seed_input = input("Enter seed (press Enter for a random seed): ")

    if seed_input:
        seed = int(seed_input)
    else:
        seed = None

    map_size = 1500
    min_distance = 150
    num_processes = 4  # number of cores

    chunk_size = map_size // num_processes

    start_time = time.time()
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = []
        for i in range(num_processes):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i != num_processes - 1 else map_size
            futures.append(executor.submit(generate_space_map, start, end, map_size, min_distance, seed, 40, i + 1))

        for future in tqdm(futures, desc="Collecting Results"):
            space_map.extend(future.result())

    elapsed_time = time.time() - start_time
    print(f"\nTotal Elapsed Time: {elapsed_time:.2f} seconds")

    with open(f'map-{seed}.dat', 'wb') as f:
        pickle.dump(space_map, f)
