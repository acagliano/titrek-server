import argparse
import time
import space
import tqdm
import threading

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", action="store_true",
                        help="Generate a new map")
    parser.add_argument("--image", nargs=3, type=int, metavar=("x", "y", "z"),
                        help="Generate an image based on the provided coordinates")
    parser.add_argument("--galaxies", action="store_true",
                        help="See how many galaxies there are in current map")
    parser.add_argument("--fullrender", action="store_true",
                        help="Render all map images")
    args = parser.parse_args()

    print("Loading space..")
    space = space.Space()
    space.load_config()
    space.load()
    print("Loaded space!")

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

    if args.image:
        x, y, z = args.image
        space.generate_picture(x, y, z)

    if args.fullrender:
        print("FULLRENDER - high CPU usage!")
        image_count_estimated = 0
        for x in range(-100, 101):
            for y in range(-100, 101):
                for z in range(-100, 101):
                    image_count_estimated += 1

        progress_bar = tqdm(total=image_count_estimated, desc="Generating Images")

        for x in range(-100, 101):
            for y in range(-100, 101):
                for z in range(-100, 101):
                    thread = threading.Thread(target=space.generate_picture, args=(x, y, z))
                    thread.name = f"picture-{x}_{y}_{z}-Thread"
                    thread.start()
                    time.sleep(0.1)

                    progress_bar.update(1)

                    if progress_bar.n >= progress_bar.total:
                        break

        progress_bar.close()

    if args.galaxies:
        print(f"Amount of galaxies in current map: {len(space.galaxies)}")
