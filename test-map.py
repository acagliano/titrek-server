import tkinter as tk
from PIL import Image, ImageTk
from space import Space
import time

class GameWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="black")
        self.canvas.pack()
        self.current_image = None

        self.fps_label = tk.Label(self.root, text="", fg="white", bg="black")
        self.fps_label.pack()

        self.space = Space()  # Create an instance of the Space class
        self.space.load_config()
        self.space.load()

        # Set the initial player coordinates
        self.player_x = 0
        self.player_y = 0
        self.player_z = 0

        # Generate the initial map image
        self.generate_map_image()

        # Set up keyboard bindings for player movement
        self.root.bind("<Up>", self.move_forward)
        self.root.bind("<Down>", self.move_backward)
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        
        self.last_update_time = time.time()
        self.root.after(1000, self.update_image)  # Start updating the image every 1 second

    def generate_map_image(self):
        # Generate the map image based on player coordinates (e.g., x, y, z)
        image_stream = self.space.generate_picture(self.player_x, self.player_y, self.player_z, "stream")

        # Create a Tkinter-compatible image object from the image stream
        image = Image.open(image_stream)

        # Resize the image to fit the canvas size
        resized_image = image.resize((800, 600))

        # Create a Tkinter-compatible image object
        self.current_image = ImageTk.PhotoImage(resized_image)

    def update_image(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time

        fps = 1 / elapsed_time

        self.generate_map_image()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)

        self.fps_label.config(text=f"FPS: {fps:.2f}")  # Update the text of the FPS label

        self.root.after(1000, self.update_image)

    def move_forward(self, event):
        # Update the player's Z coordinate to move forward
        self.player_z += 1

    def move_backward(self, event):
        # Update the player's Z coordinate to move backward
        self.player_z -= 1
    
    def move_left(self, event):
        # Update the player's X coordinate to move left
        self.player_x -= 1

    def move_right(self, event):
        # Update the player's X coordinate to move right
        self.player_x += 1

    def start(self):
        self.root.mainloop()

# Create an instance of the GameWindow class and start the game
game = GameWindow()
game.start()
