import os
import random
import requests
import configparser

from timeit import default_timer as timer


class Space:
    def __init__(self):
        self.path = "data/space"
        self.config_file = f"{self.path}/space.conf"
        os.makedirs(self.path, exist_ok=True)
        try:
            self.load_config()
            self.generate()
        except IOError:
            self.download_default_config()
            self.load_config()
            self.generate()

    def load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

    def download_default_config(self):
        get_url = "https://raw.githubusercontent.com/acagliano/titrek-server/rewrite/space.conf"
        r = requests.get(get_url, allow_redirects=True)
        with open(self.config_file, 'wb') as f:
            f.write(r.content)

    def generate(self):
        self.target_size = self.config["MAP CONFIG"].getint("starting-size")
        self.current_size = 0
        self.galaxies = []
        self.galaxy_gen_preset = self.config["GENERATION RATES"]["galaxies"]
        self.system_gen_preset = self.config["GENERATION RATES"]["systems"]
        galaxy_idx = 0

        if self.galaxy_gen_preset == "fast":
            self.galaxy_rates = (1, 3)
        else:
            self.galaxy_rates = (5, 9)

        if self.target_size == 0:
            galaxy = Galaxy(self.path)
            galaxy.generate(self.current_size)
            self.galaxies.append(galaxy)
        else:
            while self.current_size < self.target_size:
                galaxies_to_generate = random.choice(
                    range(self.galaxy_rates[0], self.galaxy_rates[1]))
                for g in range(galaxies_to_generate):
                    galaxy = Galaxy(self.path)
                    galaxy.generate(self.current_size)
                    self.galaxies.append(galaxy)
                    galaxy_idx += 1
                    self.current_size += 1

        self.map_time = {}
        self.map_time["start"] = self.map_time["last"] = timer()
        self.map_time["current"] = None

    def save(self):
        return

    def tick(self):
        self.map_time["current"] = timer()
        return


class CelestialObject:
    def __init__(self):
        pass

    def generate(self, dist_from_origin):
        # Generate the celestial object based on the distance from the origin
        # and other parameters

        # Example implementation:
        # Assume the celestial object is a planet
        self.name = "Planet"
        self.distance_from_origin = dist_from_origin

        # Generate other properties of the celestial object
        # such as size, composition, atmosphere, etc.
        self.size = self.generate_size()
        self.composition = self.generate_composition()
        self.atmosphere = self.generate_atmosphere()

    def generate_size(self):
        # Generate the size of the celestial object
        # Example implementation:
        return random.randint(1000, 10000)  # Random size between 1000 and 10000

    def generate_composition(self):
        # Generate the composition of the celestial object
        # Example implementation:
        compositions = ["Rocky", "Gaseous", "Icy"]
        return random.choice(compositions)  # Random composition from the list

    def generate_atmosphere(self):
        # Generate the atmosphere of the celestial object
        # Example implementation:
        atmospheres = ["Thin", "Thick", "No atmosphere"]
        return random.choice(atmospheres)  # Random atmosphere from the list


class Galaxy(CelestialObject):
    identifier = 0

    def __init__(self, path):
        self.id = Galaxy.identifier
        self.path = f"{path}/galaxy{self.id}"
        Galaxy.identifier += 1


class System(CelestialObject):
    identifier = 0

    def __init__(self, path):
        self.id = System.identifier
        self.path = f"{path}/system{self.id}.dat"
        System.identifier += 1
