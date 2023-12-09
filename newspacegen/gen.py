import random
import pickle
import time
from tqdm import tqdm

def generate_space_map(seed=None, map_size=20, min_distance=50):
    if seed is None:
        seed = int(time.time())

    random.seed(seed)
    space_map = []

    star_positions = []
    planet_positions = []

    for i in tqdm(range(map_size), desc="Generating Space Map"):
        row = []
        for j in range(map_size):
            celestial_body = random.random()
            x = random.uniform(0, map_size * 10)  # Increase the scale for larger distances
            y = random.uniform(0, map_size * 10)
            z = random.uniform(0, map_size * 10)

            # Check distances within the existing positions
            while any(((x - pos[0]) ** 2 + (y - pos[1]) ** 2 + (z - pos[2]) ** 2) ** 0.5 < min_distance
                      for pos in star_positions + planet_positions):
                x = random.uniform(0, map_size * 10)
                y = random.uniform(0, map_size * 10)
                z = random.uniform(0, map_size * 10)

            if celestial_body < 0.05:
                # Star
                star_color = random.choice(['Yellow', 'Red', 'Blue'])
                size = random.uniform(10, 20)
                star_name = f'Star_{i}_{j}'
                row.append({'type': 'Star', 'star_name': star_name, 'star_color': star_color, 'x': x, 'y': y, 'z': z, 'size': size})
                star_positions.append((x, y, z))

            elif celestial_body < 0.2:
                # Planet
                planet_type = random.choice(['Earth-like', 'Gas giant', 'Ice planet'])
                atmosphere_color = random.choice(['Blue', 'Red', 'Green'])
                size = random.uniform(20, 100)
                planet_name = f'Planet_{i}_{j}'
                row.append({'type': 'Planet', 'planet_name': planet_name, 'planet_type': planet_type, 'atmosphere_color': atmosphere_color,
                            'x': x, 'y': y, 'z': z, 'size': size})
                planet_positions.append((x, y, z))

        space_map.append(row)

    with open(f'map-{seed}.dat', 'wb') as f:
        pickle.dump(space_map, f)

if __name__ == "__main__":
    seed_input = input("Enter seed (press Enter for a random seed): ")

    if seed_input:
        seed = int(seed_input)
    else:
        seed = None

    generate_space_map(seed, map_size=200, min_distance=50)
