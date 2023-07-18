import tkinter as tk
from PIL import Image, ImageTk
from space import Space

class GameWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()
        self.current_image = None

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

        self.root.after(1000, self.update_image)  # Start updating the image every 1 second

    def generate_map_image(self):
        # Generate the map image based on player coordinates (e.g., x, y, z)
        self.space.generate_picture(self.player_x, self.player_y, self.player_z)

        # Load the generated image using PIL
        image = Image.open(f"data/space/images/{self.player_x}_{self.player_y}_{self.player_z}.png")

        # Resize the image to fit the canvas size
        resized_image = image.resize((800, 600))

        # Create a Tkinter-compatible image object
        self.current_image = ImageTk.PhotoImage(resized_image)

    def update_image(self):
        # Generate a new map image based on the updated player coordinates
        self.generate_map_image()

        # Update the canvas with the new image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)

        # Schedule the next image update after 1 second
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
