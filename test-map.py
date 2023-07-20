import tkinter as tk
from PIL import Image, ImageTk
from space import Space
import time

class GameWindow:
    def __init__(self):
        print("Initing..")
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="black")
        self.canvas.pack()
        self.current_image = None
        self.image_stream = None
        self.canvas_image = None  # Add canvas_image attribute

        self.fps_label = tk.Label(self.root, text="", fg="white", bg="black")
        self.fps_label.pack()

        # Entry widgets to input movement values
        self.x_entry = tk.Entry(self.root, width=8)
        self.x_entry.insert(0, "1")
        self.y_entry = tk.Entry(self.root, width=8)
        self.y_entry.insert(0, "1")
        self.z_entry = tk.Entry(self.root, width=8)
        self.z_entry.insert(0, "1")

        self.x_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.y_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.z_entry.pack(side=tk.LEFT, padx=5, pady=5)

        # Label to display messages
        self.message_label = tk.Label(self.root, text="", fg="red", bg="black")
        self.message_label.pack()

        self.space = Space()
        self.space.load()
        self.space.load_textures()

        self.player_x = 0
        self.player_y = 0
        self.player_z = 0
        self.rotation_yaw = 0
        self.rotation_pitch = 0

        self.generate_map_image()

        self.root.bind("<Up>", self.move_forward)
        self.root.bind("<Down>", self.move_backward)
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("<space>", self.move_up)
        self.root.bind("<Shift_L>", self.move_down)
        self.root.bind("<Prior>", self.rotate_left)  # PgUp key
        self.root.bind("<Next>", self.rotate_right)  # PgDn key
        self.root.bind("<KeyPress-w>", self.rotate_up)  # Press 'w' to rotate up
        self.root.bind("<KeyPress-s>", self.rotate_down)  # Press 's' to rotate down

        self.fps_accumulator = 0
        self.frames_counted = 0
        self.last_fps_update_time = time.time()

        self.last_update_time = time.time()
        self.root.after(10, self.update_image)

    def generate_map_image(self):
        if self.image_stream is None:
            self.image_stream = self.space.generate_picture(
                self.player_x, self.player_y, self.player_z, self.rotation_yaw, self.rotation_pitch, "stream")
            self.current_image = ImageTk.PhotoImage(Image.open(self.image_stream))
            self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)  # Update canvas_image
        else:
            self.image_stream = self.space.generate_picture(
                self.player_x, self.player_y, self.player_z, self.rotation_yaw, self.rotation_pitch, "stream")
            image = Image.open(self.image_stream)
            self.current_image = ImageTk.PhotoImage(image)
            self.canvas.itemconfig(self.canvas_image, image=self.current_image)

    def update_image(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time

        fps = 1 / elapsed_time

        self.fps_label.config(
            text=f"FPS: {fps:.2f} | Time since last input: {elapsed_time * 1000:.2f} ms")

        self.generate_map_image()

        self.root.after(1, self.update_image)

    def move_forward(self, event):
        self.player_z += int(self.z_entry.get())
        print(f"Move forward; Z = {self.player_z}")

    def move_backward(self, event):
        self.player_z -= int(self.y_entry.get())
        print(f"Move back; Z = {self.player_z}")

    def move_left(self, event):
        self.player_x -= int(self.x_entry.get())
        print(f"Move left; X = {self.player_x}")

    def move_right(self, event):
        self.player_x += int(self.z_entry.get())
        print(f"Move right; X = {self.player_x}")

    def move_up(self, event):
        self.player_y += int(self.y_entry.get())
        print(f"Move up; Y = {self.player_y}")

    def move_down(self, event):
        self.player_y -= int(self.y_entry.get())
        print(f"Move down; Y = {self.player_y}")

    def rotate_left(self, event):
        self.rotation_yaw += int(self.x_entry.get())
        self.generate_map_image()
        print(f"Rotate left; Yaw = {self.rotation_yaw} degrees")

    def rotate_right(self, event):
        self.rotation_yaw -= int(self.x_entry.get())
        self.generate_map_image()
        print(f"Rotate right; Yaw = {self.rotation_yaw} degrees")

    def rotate_up(self, event):
        self.rotation_pitch += int(self.y_entry.get())
        self.generate_map_image()
        print(f"Rotate up; Pitch = {self.rotation_pitch} degrees")

    def rotate_down(self, event):
        self.rotation_pitch -= int(self.y_entry.get())
        self.generate_map_image()
        print(f"Rotate down; Pitch = {self.rotation_pitch} degrees")

    def start(self):
        self.root.mainloop()


if __name__ == '__main__':
    game = GameWindow()
    game.start()
