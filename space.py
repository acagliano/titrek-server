import os
import random
import requests
import configparser
from timeit import default_timer as timer
import json
import math


def calculate_distance(x, y):
    distance = math.sqrt(x**2 + y**2)
    return distance


class Space:
    def __init__(self):
        self.path = "data/space"
        self.config_file = f"{self.path}/space.conf"
        os.makedirs(self.path, exist_ok=True)
        try:
            self.load_config()
            self.load()
            self.generate()
        except IOError:
            self.download_default_config()
            self.load_config()
            self.load()
            self.generate()

    def load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

    def download_default_config(self):
        get_url = "https://raw.githubusercontent.com/acagliano/titrek-server/rewrite/space.conf"
        r = requests.get(get_url, allow_redirects=True)
        with open(self.config_file, 'wb') as f:
            f.write(r.content)

    def load(self):
        try:
            with open(f"{self.path}/map.json", "r") as f:
                map_data = json.load(f)
        except FileNotFoundError:
            return

        self.galaxies = []
        for galaxy_data in map_data["Galaxies"]:
            galaxy = Galaxy(self.path)
            galaxy.id = galaxy_data["Galaxy"]
            galaxy.systems = []
            for system_data in galaxy_data["Systems"]:
                system = System(galaxy.id)
                system.id = system_data["System"]
                system.celestial_objects = []
                for celestial_object_data in system_data["Celestial Objects"]:
                    celestial_object = CelestialObject()
                    celestial_object.xpos = celestial_object_data["Xpos"]
                    celestial_object.ypos = celestial_object_data["Ypos"]
                    celestial_object.zpos = celestial_object_data["Zpos"]
                    celestial_object.name = celestial_object_data["Name"]
                    celestial_object.originDistance = celestial_object_data[
                        "originDistance"]
                    celestial_object.size = celestial_object_data["Size"]
                    celestial_object.composition = celestial_object_data["Composition"]
                    celestial_object.atmosphere = celestial_object_data["Atmosphere"]
                    system.celestial_objects.append(celestial_object)
                galaxy.systems.append(system)
            self.galaxies.append(galaxy)

    def generate(self):
        self.max_galaxies = self.config["MAP CONFIG"].getint("max-galaxies")
        self.current_size = 0
        self.galaxies = []
        self.galaxy_gen_preset = self.config["GENERATION RATES"]["galaxies"]
        self.system_gen_preset = self.config["GENERATION RATES"]["systems"]
        galaxy_idx = 0

        if self.galaxy_gen_preset == "fast":
            self.galaxy_rates = (1, 3)
        else:
            self.galaxy_rates = (5, 9)

        if self.max_galaxies == 0:
            galaxy = Galaxy(self.path)
            galaxy.generate(self.current_size, self.config["MAP CONFIG"].getint("systems-per-galaxy"))
            self.galaxies.append(galaxy)
        else:
            while self.current_size <= self.max_galaxies:
                galaxy = Galaxy(self.path)
                galaxy.generate(self.current_size, self.config["MAP CONFIG"].getint("systems-per-galaxy"))
                self.galaxies.append(galaxy)
                galaxy_idx += 1
                self.current_size += 1

        self.map_time = {}
        self.map_time["start"] = self.map_time["last"] = timer()
        self.map_time["current"] = None

    def save(self):
        map_data = {"Galaxies": []}
        for galaxy in self.galaxies:
            galaxy_data = {"Galaxy": galaxy.id, "Systems": []}
            for system in galaxy.systems:
                system_data = {"System": system.id, "Celestial Objects": []}
                for celestial_object in system.celestial_objects:
                    celestial_object_data = {
                        "Xpos": celestial_object.xpos,
                        "Ypos": celestial_object.ypos,
                        "Zpos": celestial_object.zpos,
                        "Name": celestial_object.name,
                        "originDistance": celestial_object.originDistance,
                        "Size": celestial_object.size,
                        "Composition": celestial_object.composition,
                        "Atmosphere": celestial_object.atmosphere
                    }
                    system_data["Celestial Objects"].append(
                        celestial_object_data)
                galaxy_data["Systems"].append(system_data)
            map_data["Galaxies"].append(galaxy_data)

        with open(f"{self.path}/map.json", "w") as f:
            json.dump(map_data, f)

    def tick(self):
        self.map_time["current"] = timer()
        # Implement the logic to update the map based on game ticks
        # You can add any additional functionality here


class CelestialObject:
    def __init__(self):
        self.xpos = None
        self.ypos = None
        self.zpos = None

    def generate(self, dist_from_origin):
        self.name = "Planet"
        self.originDistance = dist_from_origin
        self.size = self.generate_size()
        self.composition = self.generate_composition()
        self.atmosphere = self.generate_atmosphere()

    def generate_size(self):
        return random.randint(1000, 10000)

    def generate_composition(self):
        compositions = ["Rocky", "Gaseous", "Icy"]
        return random.choice(compositions)

    def generate_atmosphere(self):
        atmospheres = ["None", "Thin", "Thick"]
        return random.choice(atmospheres)


class System:
    def __init__(self, galaxy_id):
        self.galaxy_id = galaxy_id
        self.id = None
        self.celestial_objects = []

    def generate(self, system_id, dist_from_origin):
        self.id = system_id
        num_objects = random.randint(1, 5)

        for i in range(num_objects):
            celestial_object = CelestialObject()
            celestial_object.generate(dist_from_origin)

            celestial_object.xpos = random.uniform(-100, 100)
            celestial_object.ypos = random.uniform(-100, 100)
            celestial_object.zpos = random.uniform(-100, 100)

            # Calculate the distance from the origin (0, 0)
            distance = math.sqrt(celestial_object.xpos**2 + celestial_object.ypos**2 + celestial_object.zpos**2)

            celestial_object.originDistance = distance
            self.celestial_objects.append(celestial_object)


class Galaxy:
    def __init__(self, path):
        self.path = path
        self.id = None
        self.systems = []

    def generate(self, galaxy_id, systems_per_galaxy):
        self.id = galaxy_id
        # Generate a random number of systems
        for i in range(systems_per_galaxy):
            system = System(self.id)
            system.generate(i, galaxy_id)
            self.systems.append(system)


# Usage example
space = Space()
space.generate()
space.save()

for galaxy in space.galaxies:
    print(f"Galaxy ID: {galaxy.id}")
    for system in galaxy.systems:
        print(f"System ID: {system.id}")
        for celestial_object in system.celestial_objects:
            print(f"--- Celestial Object ---")
            print(f"Name: {celestial_object.name}")
            print(f"X Position: {celestial_object.xpos}")
            print(f"Y Position: {celestial_object.ypos}")
            print(f"Z Position: {celestial_object.zpos}")
            print(f"Origin Distance: {celestial_object.originDistance}")
            print(f"Size: {celestial_object.size}")
            print(f"Composition: {celestial_object.composition}")
            print(f"Atmosphere: {celestial_object.atmosphere}")
