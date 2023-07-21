import os
import random
import requests
import configparser
from timeit import default_timer as timer
import json
import math
from PIL import Image, ImageDraw
import io
import numpy as np
import concurrent.futures


class Space:
    def __init__(self):
        self.path = "data/space"
        self.textures_dir = "data/assets/space/"
        self.config_file = f"{self.path}/space.conf"
        os.makedirs(self.path, exist_ok=True)
        try:
            self.load_config()
        except IOError:
            self.download_default_config()
            self.load_config()

        self.map_size = self.calculate_map_size()
        self.render_distance = self.config['RENDERING'].getint(
            'render-distance')
        self.enable_atmosphere_render = self.config['RENDERING'].getboolean(
            'enable-atmosphere-render')

        self.planet_compositions = [filename.replace(
            ".png", "") for filename in os.listdir(self.textures_dir)]

        self.planet_atmospheres = self.config["CELESTIAL OBJECTS"].get(
            "atmospheres").split(",")

        self.load_textures()

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
                    celestial_object.id = celestial_object_data["id"]
                    celestial_object.xpos = celestial_object_data["Xpos"]
                    celestial_object.ypos = celestial_object_data["Ypos"]
                    celestial_object.zpos = celestial_object_data["Zpos"]
                    celestial_object.name = celestial_object_data["name"]
                    celestial_object.type = celestial_object_data["type"]
                    celestial_object.originDistance = celestial_object_data[
                        "originDistance"]
                    celestial_object.radius = celestial_object_data["radius"]
                    celestial_object.composition = celestial_object_data["composition"]
                    celestial_object.atmosphere = celestial_object_data["atmosphere"]
                    system.celestial_objects.append(celestial_object)
                galaxy.systems.append(system)
            self.galaxies.append(galaxy)

    def load_textures(self):
        self.cached_textures = {}
        self.cached_textures["Default"] = Image.open(
            "data/assets/space/Default.png").convert("RGBA").resize((500, 500))
        for planet_composition in self.planet_compositions:
            texture_path = f"{self.textures_dir}{planet_composition}.png"
            try:
                texture = Image.open(texture_path).convert(
                    "RGBA").resize((500, 500))
                self.cached_textures[planet_composition] = texture
            except FileNotFoundError:
                print(
                    f"Warning: Texture file '{texture_path}' not found. Using default texture.")
                self.cached_textures[planet_composition] = self.cached_textures["Default"]

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
                        "id": celestial_object.id,
                        "Xpos": celestial_object.xpos,
                        "Ypos": celestial_object.ypos,
                        "Zpos": celestial_object.zpos,
                        "name": celestial_object.name,
                        "type": celestial_object.type,
                        "originDistance": celestial_object.originDistance,
                        "radius": celestial_object.radius,
                        "composition": celestial_object.composition,
                        "atmosphere": celestial_object.atmosphere
                    }
                    system_data["Celestial Objects"].append(
                        celestial_object_data)
                galaxy_data["Systems"].append(system_data)
            map_data["Galaxies"].append(galaxy_data)

        with open(f"{self.path}/map.json", "w") as f:
            json.dump(map_data, f)

    def tick(self):
        self.map_time["current"] = timer()

    def generate_picture(self, x, y, z, yaw, pitch, returnType):
        player_screen = Image.new("RGBA", (320, 240))

        player_position = np.array([x, y, z])
        player_facing_direction = np.array([
            math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)),
            math.sin(math.radians(pitch)),
            math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
        ])

        for galaxy in self.galaxies:
            for system in galaxy.systems:
                for celestial_object in system.celestial_objects:
                    celestial_object_position = np.array([
                        celestial_object.xpos, celestial_object.ypos, celestial_object.zpos
                    ])

                    object_direction = celestial_object_position - player_position
                    distance = np.linalg.norm(object_direction)
                    object_direction /= distance

                    if distance > self.render_distance:
                        continue

                    dot_product = np.dot(player_facing_direction, object_direction)

                    if dot_product < 0:
                        continue

                    screen_x = np.dot(object_direction, np.array([1, 0, 0]))
                    screen_y = np.dot(object_direction, np.array([0, 1, 0]))

                    adjusted_xpos = int((screen_x + 1) * player_screen.width / 2)
                    adjusted_ypos = int((1 - screen_y) * player_screen.height / 2)

                    size = celestial_object.radius
                    scaling_factor = max(1 - (distance / 50), size / 5000)
                    adjusted_size = int(max(size * scaling_factor, 1))

                    if celestial_object.type == "Planet":
                        composition_texture = self.cached_textures[celestial_object.composition].copy()
                        adjusted_size = int(max(celestial_object.radius * scaling_factor, 1))
                        composition_texture = composition_texture.resize((adjusted_size * 2, adjusted_size * 2))

                        if self.enable_atmosphere_render:
                            atmosphere_size = adjusted_size
                            atmosphere = Image.new(
                                "RGBA", (atmosphere_size, atmosphere_size), (0, 0, 0, 0))
                            draw = ImageDraw.Draw(atmosphere)
                            draw.ellipse(
                                (0, 0, atmosphere_size, atmosphere_size), fill=(0, 0, 0, 100))
                            combined_texture = Image.alpha_composite(
                                composition_texture, atmosphere)
                            player_screen.paste(
                                combined_texture, (adjusted_xpos - composition_texture.width // 2, adjusted_ypos - composition_texture.height // 2), mask=combined_texture)
                        else:
                            player_screen.paste(
                                composition_texture, (adjusted_xpos - composition_texture.width // 2, adjusted_ypos - composition_texture.height // 2), mask=composition_texture)

        if returnType == "save":
            player_screen.save(f"data/space/images/{x}_{y}_{z}_{yaw}_{pitch}.png")
        elif returnType == "stream":
            image_stream = io.BytesIO()
            player_screen.save(image_stream, format='PNG')
            image_stream.seek(0)
            return image_stream

    def is_inside_planet(self, x, y, z):
        player_position = np.array([x, y, z])
        player_facing_direction = np.array([0, 0, 1])

        for galaxy in self.galaxies:
            for system in galaxy.systems:
                for celestial_object in system.celestial_objects:
                    distance = self.calculate_xyz_distance_from_point(
                        celestial_object.xpos, celestial_object.ypos, celestial_object.zpos, x, y, z
                    )

                    if celestial_object.type == "Planet" and distance <= celestial_object.radius:
                        celestial_object_position = np.array(
                            [celestial_object.xpos, celestial_object.ypos, celestial_object.zpos]
                        )
                        object_direction = celestial_object_position - player_position
                        object_direction /= np.linalg.norm(object_direction)
                        angle = np.arccos(np.dot(player_facing_direction, object_direction))

                        angle_degrees = np.degrees(angle)

                        if 0 <= angle_degrees < 45 or 315 <= angle_degrees <= 360:
                            relative_side = "front"
                        elif 45 <= angle_degrees < 135:
                            relative_side = "right"
                        elif 135 <= angle_degrees < 225:
                            relative_side = "back"
                        elif 225 <= angle_degrees < 315:
                            relative_side = "left"
                        else:
                            relative_side = "unknown"

                        return True, celestial_object.name, relative_side

        return False, None, None
    
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
        scaling_factor = 1 + (max_galaxies - 1) * 0.1
        base_size = (320, 240)
        map_size = (int(base_size[0] * scaling_factor),
                    int(base_size[1] * scaling_factor))
        return map_size

    def calculate_xyz_distance_from_origin(self, x, y, z):
        map_origin = (self.config["MAP CONFIG"].getint("map-origin-x"), self.config["MAP CONFIG"].getint(
            "map-origin-y"), self.config["MAP CONFIG"].getint("map-origin-z"))
        distance_from_origin = math.sqrt(
            (x - map_origin[0]) ** 2 + (y - map_origin[1]) ** 2 + (z - map_origin[2]) ** 2)
        return distance_from_origin

    def calculate_xyz_distance_from_point(self, x1, y1, z1, x2, y2, z2):
        position1 = np.array([x1, y1, z1])
        position2 = np.array([x2, y2, z2])
        distance_from_point = np.linalg.norm(position2 - position1)
        return distance_from_point

    def generate_planet_name(self, seed=None):
        if seed is None:
            seed = random.randint(0, 0xFFFF), random.randint(
                0, 0xFFFF), random.randint(0, 0xFFFF)
        pairs = "..LEXEGEZACEBISOUSESARMAINDIREA.ERATENBERALAVETIEDORQUANTEISRION"

        def size16Num(value):
            mask = (1 << 16) - 1
            return value & mask

        def rotate1(x):
            temp = x & 128
            return (2 * (x & 127)) + (temp >> 7)

        def twist(x):
            return (256 * rotate1(x >> 8)) + rotate1(x & 255)

        longnameflag = seed[0] & 64

        pair1 = 2 * (((seed[2]) >> 8) & 31)
        seed = size16Num(twist(seed[0])), size16Num(
            twist(seed[1])), size16Num(twist(seed[2]))
        pair2 = 2 * (((seed[2]) >> 8) & 31)
        seed = size16Num(twist(seed[0])), size16Num(
            twist(seed[1])), size16Num(twist(seed[2]))

        pair3 = 2 * (((seed[2]) >> 8) & 31)
        seed = size16Num(twist(seed[0])), size16Num(
            twist(seed[1])), size16Num(twist(seed[2]))

        pair4 = 2 * (((seed[2]) >> 8) & 31)
        seed = size16Num(twist(seed[0])), size16Num(
            twist(seed[1])), size16Num(twist(seed[2]))

        name = []
        name.append(pairs[pair1])
        name.append(pairs[pair1 + 1])
        name.append(pairs[pair2])
        name.append(pairs[pair2 + 1])
        name.append(pairs[pair3])
        name.append(pairs[pair3 + 1])

        if longnameflag:
            name.append(pairs[pair4])
            name.append(pairs[pair4 + 1])

        planet_name = "".join(name).replace('.', '')
        planet_name = planet_name.capitalize()
        return planet_name


class CelestialObject:
    def __init__(self):
        self.xpos = None
        self.ypos = None
        self.zpos = None

    def generate(self, dist_from_origin, id):
        name = space.generate_planet_name()
        if name == "":
            name = space.generate_planet_name()
        self.id = id
        self.name = name
        self.type = "Planet"
        self.originDistance = dist_from_origin
        self.radius = self.generate_radius()
        self.composition = self.generate_composition()
        self.atmosphere = self.generate_atmosphere()

    def generate_radius(self):
        return random.randint(300, 700)

    def generate_composition(self):
        planet_compositions = [
            composition for composition in space.planet_compositions if composition != "Default"]
        return random.choice(planet_compositions)

    def generate_atmosphere(self):
        return random.choice(space.planet_atmospheres)


class System:
    def __init__(self, galaxy_id):
        self.galaxy_id = galaxy_id
        self.id = None
        self.celestial_objects = []

    def generate(self, system_id, dist_from_origin, obj_per_sys):
        self.id = system_id

        for i in range(obj_per_sys):
            celestial_object = CelestialObject()
            celestial_object.generate(dist_from_origin, i)

            celestial_object.xpos = random.uniform(-5000, 5000)
            celestial_object.ypos = random.uniform(-5000, 5000)
            celestial_object.zpos = random.uniform(-5000, 5000)

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


space = Space()
