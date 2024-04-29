import numpy as np
import random
from scipy.spatial import distance
import json
import time
import os
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

DEFAULT_MAP_SIZE = 50000
DEFAULT_MIN_STAR_DISTANCE = 200
DEFAULT_MIN_PLANET_DISTANCE = 780
DEFAULT_STAR_PROB = 0.7
DEFAULT_MAX_OBJECTS_PER_THOUSAND_SIZE = 250

STAR_COLORS = ['Yellow', 'Red', 'Blue']
ATMOSPHERE_COLORS = ['Blue', 'Red', 'Green']
PLANET_TYPES = ['Earth-like', 'Gas giant', 'Ice planet']

DEFAULT_MAX_OBJECTS_PER_THOUSAND_SIZE = DEFAULT_MAX_OBJECTS_PER_THOUSAND_SIZE / 250

def calculate_radius(size):
    return size / 2

def generate_space_map_worker(args):
    map_size, min_star_distance, min_planet_distance, star_prob, seed, core_id = args
    
    worker_logs = []

    random.seed(seed)
    np.random.seed(seed)

    space_map = []
    star_positions = []
    planet_positions = []
    star_radii = []

    star_count = 0
    planet_count = 0

    worker_logs.append(f"Starting core {core_id}...")

    progress_bar = tqdm(total=map_size, desc=f"Core {core_id}", position=core_id, dynamic_ncols=False)
    for _ in range(map_size):
        position = np.random.uniform(0, map_size, size=3)

        if star_positions:
            distances_to_stars = distance.cdist([position], star_positions)[0]
            if np.min(distances_to_stars) > min_star_distance:
                if planet_positions:
                    distances_to_planets = distance.cdist([position], planet_positions)[0]
                    if np.min(distances_to_planets) < min_planet_distance:
                        worker_logs.append("Planet distance is less than minimum planet distance. Skipping...")
                        continue
                celestial_body = 'Planet' if random.random() > star_prob else 'Star'
            else:
                celestial_body = 'Star'
        else:
            celestial_body = 'Star'

        if celestial_body == 'Star':
            star_color = random.choice(STAR_COLORS)
            size = random.uniform(10, 20)
            radius = calculate_radius(size)
            star_name = f'Star_{star_count}'
            space_map.append({'type': 'Star', 'name': star_name, 'color': star_color, 'position': position.tolist(), 'size': size})
            star_positions.append(position)
            star_radii.append(radius)
            star_count += 1
            worker_logs.append(f"Generated Star: Name - {star_name}, Color - {star_color}, Position - {position.tolist()}, Size - {size}")
        elif celestial_body == 'Planet':
            planet_type = random.choice(PLANET_TYPES)
            atmosphere_color = random.choice(ATMOSPHERE_COLORS)
            size = random.uniform(20, 100)
            radius = calculate_radius(size)
            position_valid = True
            for star_pos, star_radius in zip(star_positions, star_radii):
                if np.linalg.norm(star_pos - position) < (star_radius + radius + min_planet_distance):
                    worker_logs.append("Planet is too close to a star. Skipping...")
                    position_valid = False
                    break
            if not position_valid:
                continue
            planet_name = f'Planet_{planet_count}'
            space_map.append({'type': 'Planet', 'name': planet_name, 'planet_type': planet_type, 'atmosphere_color': atmosphere_color, 'position': position.tolist(), 'size': size})
            planet_positions.append(position)
            planet_count += 1
            worker_logs.append(f"Generated Planet: Name - {planet_name}, Type - {planet_type}, Atmosphere Color - {atmosphere_color}, Position - {position.tolist()}, Size - {size}")

        progress_bar.update(1)

    progress_bar.close()

    worker_logs.append(f"Core {core_id} finished.")

    return space_map, worker_logs

def generate_space_map(seed=None, map_size=DEFAULT_MAP_SIZE, min_star_distance=DEFAULT_MIN_STAR_DISTANCE, min_planet_distance=DEFAULT_MIN_PLANET_DISTANCE, star_prob=DEFAULT_STAR_PROB):
    num_cores = cpu_count()
    print(f"Using {num_cores} cores for generation.")

    seed = seed if seed else random.randint(0, 2**32 - 1)

    args = [(map_size // num_cores, min_star_distance, min_planet_distance, star_prob, seed, i) for i in range(num_cores)]

    with Pool(num_cores) as p:
        results = []
        for result in p.imap(generate_space_map_worker, args):
            results.extend(result)
    
    return results, seed

if __name__ == "__main__":
    seed_input = input("Enter seed (leave empty for random seed): ")
    seed = int(seed_input) if seed_input.strip() else random.randint(0, 2**32 - 1)

    map_size_input = input(f"Enter max map size (default is {DEFAULT_MAP_SIZE}): ")
    map_size = DEFAULT_MAP_SIZE if map_size_input == "" else int(map_size_input)
    
    star_prob_input = input(f"Enter probability of generating a star (default is {DEFAULT_STAR_PROB}): ")
    star_prob = DEFAULT_STAR_PROB if star_prob_input == "" else float(star_prob_input)

    print("Generating map with the following settings:")
    print("Seed:", seed)
    start_time = time.time()
    map_results, used_seed = generate_space_map(
        seed=seed,
        map_size=map_size,
        star_prob=star_prob
    )
    map_objects_json = map_results[0]
    logs = map_results[1]
    print("\n" * 10)

    print("Used seed:", used_seed)
    print("Amount of objects:", len(map_objects_json))

    final_json = {
        "metadata": {
            "seed": used_seed,
            "map_size": map_size,
            "star_prob": star_prob,
            "created_at": int(time.time()),
            "object_count": len(map_objects_json),
        },
        "objects": map_objects_json
    }

    print("Saving...")
    with open('space_map.json', 'w') as f:
        json.dump(final_json, f)
        print("Size on disk: ", os.path.getsize('space_map.json'))
        print("Saved!")
    end_time = time.time()

    print("Saving logs..")
    with open('logs.txt', 'w') as f:
        f.write("\n".join(logs))
        print("Saved logs!")

    print("Time taken:", end_time - start_time, "seconds")

    print("Done.")
