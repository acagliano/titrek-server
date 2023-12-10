from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import pickle
import os
import random

RENDER_DISTANCE = 300

app = Ursina()

player = FirstPersonController()
player.gravity = False
player.jump_height = 1
player.speed = 10
player.jump_up_duration = 0.25

camera.clip_plane_far = 1000

map_file = 'map-123.pickle'

with open(map_file, 'rb') as f:
    space_map = pickle.load(f)


def load_space_textures():
    texture_path = 'textures/'
    stars_texture = load_texture(texture_path + 'stars.png')
    planets_texture = {
        'Earth-like': load_texture(texture_path + 'earth-like.png'),
        'Gas giant': load_texture(texture_path + 'gas-giant.png'),
        'Ice planet': load_texture(texture_path + 'ice-planet.png'),
    }
    atmospheres_texture = {
        'Blue': load_texture(texture_path + 'atmosphere-blue.png'),
        'Red': load_texture(texture_path + 'atmosphere-red.png'),
        'Green': load_texture(texture_path + 'atmosphere-green.png'),
    }
    return stars_texture, planets_texture, atmospheres_texture


stars_texture, planets_texture, atmospheres_texture = load_space_textures()
rendered_objects = []


def clear_objects():
    for entity in rendered_objects:
        destroy(entity)
    rendered_objects.clear()


def load_space_textures():
    texture_path = 'textures/'
    stars_texture = load_texture(texture_path + 'stars.png')
    planets_texture = {
        'Earth-like': load_texture(texture_path + 'earth-like.png'),
        'Gas giant': load_texture(texture_path + 'gas-giant.png'),
        'Ice planet': load_texture(texture_path + 'ice-planet.png'),
    }
    atmospheres_texture = {
        'Blue': load_texture(texture_path + 'atmosphere-blue.png'),
        'Red': load_texture(texture_path + 'atmosphere-red.png'),
        'Green': load_texture(texture_path + 'atmosphere-green.png'),
    }
    return stars_texture, planets_texture, atmospheres_texture


def find_closest_planet(space_map, player_position):
    closest_planet = None
    min_distance = float('inf')

    for row in space_map:
        for cell in row:
            if cell['type'] == 'Planet':
                planet_position = Vec3(cell['x'], cell['y'], cell['z'])
                distance_to_player = distance(planet_position, player_position)

                if distance_to_player < min_distance:
                    min_distance = distance_to_player
                    closest_planet = cell

    return closest_planet, min_distance


class Planet(Entity):
    def __init__(self, position, planet_type, texture, scale):
        super().__init__(
            model='sphere',
            color=color.white,
            texture=texture,
            scale=scale,
            position=position
        )

    def update(self):
        self.rotation_y += time.dt * 2

    def explode(self):
        # Implement explosion effect code here
        destroy(self)


class FindClosestPlanetEntity(Entity):
    def update(self):
        closest_planet, min_distance = find_closest_planet(space_map, player.world_position)

        if closest_planet:
            planet_type = closest_planet['planet_type']
            print(f"Approaching {planet_type} | Distance: {min_distance:.2f} meters")


def view_space_map():
    global player, rendered_objects

    player_position = player.world_position
    for row in space_map:
        for cell in row:
            if cell['type'] == 'Star':
                star_position = Vec3(cell['x'], cell['y'], cell['z'])
                star = Entity(model='sphere', color=color.white, texture=stars_texture, scale=0.05)
                star.position = star_position
                rendered_objects.append(star)
            elif cell['type'] == 'Planet':
                planet_position = Vec3(cell['x'], cell['y'], cell['z'])
                planet_type = cell['planet_type']
                planet = Planet(position=planet_position, planet_type=planet_type,
                                texture=planets_texture[planet_type], scale=cell['size'])
                rendered_objects.append(planet)


def update_planet_positions():
    for planet in rendered_objects:
        planet.x += random.uniform(-0.1, 0.1)
        planet.y += random.uniform(-0.1, 0.1)
        planet.z += random.uniform(-0.1, 0.1)
        planet.position = (planet.x, planet.y, planet.z)


def check_collisions():
    num_objects = len(rendered_objects)
    for i in range(num_objects):
        for j in range(i + 1, num_objects):
            planet_i = rendered_objects[i]
            planet_j = rendered_objects[j]

            distance_squared = (
                    (planet_i.x - planet_j.x) ** 2 +
                    (planet_i.y - planet_j.y) ** 2 +
                    (planet_i.z - planet_j.z) ** 2
            )

            if distance_squared < 1:
                planet_i.explode()
                planet_j.explode()


def update():
    global player

    speed = player.speed

    if held_keys['space']:
        player.y += speed * time.dt
    if held_keys['left shift']:
        player.y -= speed * time.dt
    if held_keys['w']:
        player.y += speed * time.dt
    if held_keys['s']:
        player.y -= speed * time.dt
    if held_keys['a']:
        player.x -= speed * time.dt
    if held_keys['d']:
        player.x += speed * time.dt

    # update_planet_positions()
    # check_collisions()


if __name__ == "__main__":
    if not os.path.isfile(map_file):
        print(f"Error: File '{map_file}' not found.")
    else:
        app.clear_color = color.black
        app.ambient_light = color.black
        app.time_of_day = 24
        Sky(texture='textures/space_background.jpg')
        view_space_map()
        FindClosestPlanetEntity()
        app.run()
