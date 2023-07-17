import os
import random
import requests
import configparser
from timeit import default_timer as timer
import json
import math
from PIL import Image

IMAGES_GENERATED = 0


class Space:
    def __init__(self):
        self.path = "data/space"
        self.config_file = f"{self.path}/space.conf"
        os.makedirs(self.path, exist_ok=True)
        try:
            self.load_config()
        except IOError:
            self.download_default_config()
            self.load_config()

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
            galaxy.generate(
                self.current_size, self.config["MAP CONFIG"].getint(
                    "systems-per-galaxy"),
                self.config["MAP CONFIG"].getint("objects-per-system"))
            self.galaxies.append(galaxy)
        else:
            while self.current_size <= self.max_galaxies:
                galaxy = Galaxy(self.path)
                galaxy.generate(
                    self.current_size, self.config["MAP CONFIG"].getint(
                        "systems-per-galaxy"),
                    self.config["MAP CONFIG"].getint("objects-per-system"))
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

    def generate_picture(self, x, y, z):
        global IMAGES_GENERATED
        os.makedirs("data/space/images", exist_ok=True)
        image_size = self.calculate_map_size()
        image = Image.new("RGBA", image_size, "black")
        bezos_texture = Image.open("data/textures/bezos.png").convert("RGBA")

        for galaxy in self.galaxies:
            for system in galaxy.systems:
                for celestial_object in system.celestial_objects:
                    xpos = celestial_object.xpos
                    ypos = celestial_object.ypos
                    zpos = celestial_object.zpos
                    size = celestial_object.size

                    # Check if the celestial object is within the desired range
                    if -100 <= xpos <= 100 and -100 <= ypos <= 100 and -100 <= zpos <= 100:
                        # Calculate the scaling factor based on distance and size
                        distance = self.calculate_xyz_distance(
                            xpos - x, ypos - y, zpos - z)
                        # Adjust the denominator as needed
                        scaling_factor = 1 - (distance / 50)

                        # Adjust the scaling factor if the size exceeds a certain threshold
                        max_size = 5000  # Adjust the maximum size as needed
                        if size > max_size:
                            scaling_factor *= max_size / size

                        # Calculate the adjusted size based on the scaling factor and object's size
                        adjusted_size = int(size * scaling_factor)

                        # Check if the resized width and height are zero or negative
                        if adjusted_size <= 0:
                            continue  # Skip this celestial object

                        # Resize the texture image based on the adjusted size
                        resized_texture = bezos_texture.resize(
                            (adjusted_size, adjusted_size))

                        # Calculate the adjusted position for the pasted image
                        texture_width, texture_height = resized_texture.size
                        adjusted_xpos = int(
                            (xpos + 100) / 200 * image_size[0]) - texture_width // 2
                        adjusted_ypos = int(
                            (ypos + 100) / 200 * image_size[1]) - texture_height // 2
                        adjusted_paste_coords = (adjusted_xpos, adjusted_ypos)

                        # Paste the resized texture image onto the background image
                        image.paste(resized_texture,
                                    adjusted_paste_coords, resized_texture)

        image.save(f"data/space/images/{x}_{y}_{z}.png")
        IMAGES_GENERATED += 1

    def remove_old_map(self):
        if os.path.exists("data/space/map.json"):
            os.remove("data/space/map.json")

        map_folder = "data/space/images"
        if os.path.exists(map_folder):
            for filename in os.listdir(map_folder):
                if filename.endswith(".png"):
                    os.remove(os.path.join(map_folder, filename))

    def calculate_map_size(self):
        max_galaxies = self.config["MAP CONFIG"].getint("max-galaxies")
        # Adjust the scaling factor as needed
        scaling_factor = 1 + (max_galaxies - 1) * 0.1
        base_size = (320, 240)  # Adjust the base size as needed
        map_size = (int(base_size[0] * scaling_factor),
                    int(base_size[1] * scaling_factor))
        return map_size

    def calculate_xyz_distance_from_origin(self, x, y, z):
        self.map_origin = (self.config["MAP CONFIG"].getint(
            "map-origin-x"), self.config["MAP CONFIG"].getint("map-origin-y"), self.config["MAP CONFIG"].getint("map-origin-z"))
        distance_from_origin = math.sqrt(
            (x - self.map_origin[0])**2 + (y - self.map_origin[1])**2 + (z - self.map_origin[2])**2)
        return distance_from_origin

    def calculate_xyz_distance_from_point(self, x1, y1, z1, x2, y2, z2):
        distance_from_point = math.sqrt(
            (x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
        return distance_from_point


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
        return random.randint(2, 300)

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

    def generate(self, system_id, dist_from_origin, obj_per_sys):
        self.id = system_id

        for i in range(obj_per_sys):
            celestial_object = CelestialObject()
            celestial_object.generate(dist_from_origin)

            celestial_object.xpos = random.uniform(-100, 100)
            celestial_object.ypos = random.uniform(-100, 100)
            celestial_object.zpos = random.uniform(-100, 100)

            # Calculate the distance from origin (0, 0, 0)
            distance = math.sqrt(
                celestial_object.xpos**2 + celestial_object.ypos**2 + celestial_object.zpos**2)

            celestial_object.originDistance = distance
            self.celestial_objects.append(celestial_object)


class Galaxy:
    def __init__(self, path):
        self.path = path
        self.id = None
        self.systems = []

    def generate(self, galaxy_id, systems_per_galaxy, obj_per_sys):
        self.id = galaxy_id
        for i in range(systems_per_galaxy):
            system = System(self.id)
            system.generate(i, galaxy_id, obj_per_sys)
            self.systems.append(system)