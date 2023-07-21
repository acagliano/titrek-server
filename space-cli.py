import argparse
import time
from space import Space
from concurrent.futures import ThreadPoolExecutor
import sys

def noConf():
    print("No space.conf file!")
    print("Downloading default config..")
    space.download_default_config()
    space.load_config()
    try:
        mapconf = space.config["MAP CONFIG"]
    except KeyError:
        print("Could not load freshly-downloaded default config!")
        sys.exit(1)
    
    print("Successfully downloaded default config!")

def loadMap():
        print("Loading map..")
        space.load()
        print("Loaded map!")

def loadTextures():
    print("Loading textures..")
    space.load_textures()
    print("Loaded textures!")

def generate_picture_thread(thread_id, x, y, z, yaw, pitch, image_count):
    start_time = time.time()
    space.generate_picture(x, y, z, yaw, pitch, "stream")
    end_time = time.time()
    took_time = round((end_time - start_time), 2)
    print(f"[T{thread_id}] GENERATED image {image_count} in {took_time}s")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", action="store_true",
                        help="Generate a new map")
    parser.add_argument("--genimg", nargs=5, type=int, metavar=("x", "y", "z", "yaw", "pitch"),
                        help="Generate an image based on the provided coordinates, yaw and pitch)")
    parser.add_argument("--galaxies", action="store_true",
                        help="See how many galaxies there are in current map")
    parser.add_argument("--dlconf", action="store_true",
                        help="Download latest default configuration file")
    parser.add_argument("--benchmark", nargs=7, type=int, metavar=("x_range", "y_range", "z_range", "yaw_range", "pitch_range", "max_samples", "threads"),
                        help="Benchmark image generation with streaming and display average FPS \nSet max_samples to -1 for unlimited generation.")
    
    args = parser.parse_args()

    space = Space()

    try:
        mapconf = space.config["MAP CONFIG"]
    except KeyError:
        noConf()

    if args.gen:
        print("Generating...")
        start_time = time.time()
        space.remove_old_map()
        space.generate()
        space.save()
        space.load()
        end_time = time.time()
        took_time = round((end_time - start_time), 2)
        print(f"Generated map in {took_time}s!")

    if args.genimg:
        loadMap()
        x, y, z, yaw, pitch = args.genimg
        loadTextures()
        start_time = time.time()
        space.generate_picture(x, y, z, yaw, pitch, "save")
        end_time = time.time()
        took_time = round((end_time - start_time), 2)
        print(f"Generated image in {took_time}s!")

    if args.dlconf:
        print("Downloading default config..")
        space.download_default_config()
        space.load_config()
        if space.config is None:
            print("Could not load freshly-downloaded default config!")
            sys.exit(1)
        else:
            print("Successfully downloaded default config!")

    if args.galaxies:
        print(f"Amount of galaxies in current map: {len(space.galaxies)}")

    if args.benchmark:
        x_range, y_range, z_range, yaw_range, pitch_range, max_samples, threads_amount = args.benchmark

        loadMap()
        loadTextures()

        total_images = x_range * y_range * z_range * yaw_range * pitch_range
        if max_samples == -1:
            max_samples = total_images
        else:
            max_samples = min(max_samples, total_images)

        start_time = time.time()

        thread_pool = []
        image_count = 1

        with ThreadPoolExecutor(max_workers=threads_amount) as executor:
            for x in range(-x_range, x_range + 1):
                for y in range(-y_range, y_range + 1):
                    for z in range(-z_range, z_range + 1):
                        for yaw in range(-yaw_range, yaw_range + 1):
                            for pitch in range(-pitch_range, pitch_range + 1):
                                executor.submit(generate_picture_thread, len(thread_pool) + 1, x, y, z, yaw, pitch, image_count)
                                image_count += 1

        end_time = time.time()

        total_time = end_time - start_time
        avg_fps = max_samples / total_time
        print(f"\nAverage FPS: {avg_fps:.2f}")