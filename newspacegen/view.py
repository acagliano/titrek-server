from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import pickle
import os

app = Ursina()

player = FirstPersonController(
    gravity=False,
    jump_height=1,
    speed=20,
    jump_duration=0.25,
    cursor_visible=True,
    cursor_locked=False,
)

map_file = 'map-123.dat'

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


class FindClosestPlanetEntity(Entity):
    def update(self):
        closest_planet, min_distance = find_closest_planet(space_map, player.world_position)

        if closest_planet:
            planet_type = closest_planet['planet_type']
            atmosphere_color = closest_planet['atmosphere_color']
            print(f"Approaching {planet_type} | Distance: {min_distance:.2f} meters")


class Projectile(Entity):
    def __init__(self):
        super().__init__(
            model='sphere',
            color=color.red,
            scale=0.1,
            collider='box',
            origin_y=-0.5
        )

    def update(self):
        if self.x > 500 or self.x < -500 or self.z > 500 or self.z < -500:
            destroy(self)


projectiles = []


def input(key):
    global projectiles
    if key == 'left mouse down':
        projectile = Projectile()
        projectile.position = player.position + (0, 1, 0)
        projectile.rotation = player.rotation
        projectile.world_parent = scene
        projectiles.append(projectile)


def view_space_map(stars_texture, planets_texture, atmospheres_texture):
    global player, projectiles
    for row in space_map:
        for cell in row:
            if cell['type'] == 'Star':
                star_position = Vec3(cell['x'], cell['y'], cell['z'])
                distance_to_player = distance(star_position, player.world_position)
                if distance_to_player < 10000:
                    star = Entity(model='sphere', color=color.white, texture=stars_texture, scale=cell['size'])
                    star.position = star_position

    Sky(texture='textures/space_background.jpg')

    FindClosestPlanetEntity()

    app.run()


def update():
    global player, projectiles
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


if __name__ == "__main__":
    if not os.path.isfile(map_file):
        print(f"Error: File '{map_file}' not found.")
    else:
        app.clear_color = color.black
        app.ambient_light = color.black
        app.time_of_day = 24
        stars_texture, planets_texture, atmospheres_texture = load_space_textures()
        view_space_map(stars_texture, planets_texture, atmospheres_texture)
