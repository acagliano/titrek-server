import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def load_space_map(file_path):
    with open(file_path, 'r') as f:
        space_map = json.load(f)
    return space_map

def plot_space_map_3d(space_map):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    star_positions = []
    planet_positions = []
    planet_names = []
    planet_sizes = []

    for body in space_map:
        if body['type'] == 'Star':
            star_positions.append(body['position'])
        elif body['type'] == 'Planet':
            planet_positions.append(body['position'])
            planet_names.append(body['name'])
            planet_sizes.append(body['size'])

    star_positions = list(zip(*star_positions))
    planet_positions = list(zip(*planet_positions))

    ax.scatter(star_positions[0], star_positions[1], star_positions[2], color='yellow', label='Stars', marker='*')
    if planet_positions:
        ax.scatter(planet_positions[0], planet_positions[1], planet_positions[2], s=planet_sizes, color='blue', label='Planets', marker='o')
    
    for i, name in enumerate(planet_names):
        ax.text(planet_positions[0][i], planet_positions[1][i], planet_positions[2][i], name, color='black', ha='center')

    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_zlabel('Z Position')
    ax.set_title('Space Map')
    ax.legend()
    ax.grid(True)

    plt.show()

if __name__ == "__main__":
    space_map = load_space_map('space_map.json')
    metadata = space_map['metadata']
    print("Map metadata:")
    print("Seed:", metadata['seed'])
    print("Map size:", metadata['map_size'])
    print("Star probability:", metadata['star_prob'])
    print("Created at:", metadata['created_at'])
    print("Object count:", metadata['object_count'])
    plot_space_map_3d(space_map['objects'])
