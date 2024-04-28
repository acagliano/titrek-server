import numpy as np
import random
from scipy.spatial import cKDTree
import json
import time
import os
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

DEFAULT_MAP_SIZE = 50000

STAR_COLORS = ['Yellow', 'Red', 'Blue']
ATMOSPHERE_COLORS = ['Blue', 'Red', 'Green']
PLANET_TYPES = ['Earth-like', 'Gas giant', 'Ice planet']

def generate_space_map_worker(args):
    map_size, min_star_distance, min_planet_distance, star_prob, seed, core_id = args
    random.seed(seed)
    np.random.seed(seed)

    space_map = []
    star_positions = []
    planet_positions = []

    star_count = 0
    planet_count = 0

    progress_bar = tqdm(total=map_size, desc=f"Core {core_id}", position=core_id, dynamic_ncols=False)
    for _ in range(map_size):
        position = np.random.uniform(0, map_size * 10, size=3)

        if star_positions:
            star_tree = cKDTree(star_positions)
            nearest_star_dist, _ = star_tree.query(position)
            if nearest_star_dist > min_star_distance:
                if planet_positions:
                    planet_tree = cKDTree(planet_positions)
                    nearest_planet_dist, _ = planet_tree.query(position)
                    if nearest_planet_dist < min_planet_distance:
                        continue
                celestial_body = 'Planet' if random.random() > star_prob else 'Star'
            else:
                celestial_body = 'Star'
        else:
            celestial_body = 'Star'

        if celestial_body == 'Star':
            star_color = random.choice(STAR_COLORS)
            size = random.uniform(10, 20)
            star_name = f'Star_{star_count}'
            space_map.append({'type': 'Star', 'name': star_name, 'color': star_color, 'position': position.tolist(), 'size': size})
            star_positions.append(position)
            star_count += 1
        elif celestial_body == 'Planet':
            planet_type = random.choice(PLANET_TYPES)
            atmosphere_color = random.choice(ATMOSPHERE_COLORS)
            size = random.uniform(20, 100)
            planet_name = f'Planet_{planet_count}'
            space_map.append({'type': 'Planet', 'name': planet_name, 'planet_type': planet_type, 'atmosphere_color': atmosphere_color, 'position': position.tolist(), 'size': size})
            planet_positions.append(position)
            planet_count += 1

        progress_bar.update(1)

    progress_bar.close()

    return space_map

def generate_space_map(seed=None, map_size=20, min_star_distance=200, min_planet_distance=780, star_prob=0.5):
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

    map_size_input = input("Enter max map size (default is 50000): ")
    map_size = DEFAULT_MAP_SIZE if map_size_input == "" else int(map_size_input)
    
    star_prob_input = input("Enter probability of generating a star (default is 0.5): ")
    star_prob = 0.5 if star_prob_input == "" else float(star_prob_input)

    print("Generating map with the following settings:")
    print("Seed:", seed)
    start_time = time.time()
    space_map, used_seed = generate_space_map(
        seed=seed,
        map_size=map_size,
        star_prob=star_prob
    )
    print("\n" * 10)

    print("Used seed:", used_seed)
    print("Amount of objects:", len(space_map))

    final_json = {
        "metadata": {
            "seed": used_seed,
            "map_size": map_size,
            "star_prob": star_prob,
            "created_at": int(time.time()),
            "object_count": len(space_map),
        },
        "objects": space_map
    }

    print("Saving...")
    with open('space_map.json', 'w') as f:
        json.dump(final_json, f)
        print("Size on disk: ", os.path.getsize('space_map.json'))
        print("Saved!")
    end_time = time.time()

    print("Time taken:", end_time - start_time, "seconds")

    print("Done.")
