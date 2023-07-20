import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import numpy as np
from PIL import Image

# Callback function for window resize


def framebuffer_size_callback(window, width, height):
    glViewport(0, 0, width, height)


# Initialize GLFW
glfw.init()

# Create a window
window = glfw.create_window(800, 800, "OpenGL Window", None, None)
glfw.make_context_current(window)
glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)

# Vertex shader source code
vertex_shader_source = """
#version 330 core
layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 a_texture;

out vec2 texture_coords;

void main()
{
    gl_Position = vec4(a_position, 1.0);
    texture_coords = vec2(a_texture.x, 1.0 - a_texture.y);  // Flip texture coordinates
}
"""

fragment_shader_source = """
#version 330 core
in vec2 texture_coords;
out vec4 FragColor;

uniform sampler2D texture_sampler;

void main()
{
    FragColor = texture(texture_sampler, texture_coords);
}
"""

# Compile and link shaders
vertex_shader = compileShader(vertex_shader_source, GL_VERTEX_SHADER)
fragment_shader = compileShader(fragment_shader_source, GL_FRAGMENT_SHADER)
shader_program = compileProgram(vertex_shader, fragment_shader)

# Define vertex and texture coordinates
vertices = np.array([
    # Position    # Texture
    -0.5, -0.5, 0.0, 0.0, 0.0,
    0.5, -0.5, 0.0, 1.0, 0.0,
    0.5, 0.5, 0.0, 1.0, 1.0,
    -0.5, 0.5, 0.0, 0.0, 1.0
], dtype=np.float32)

indices = np.array([
    0, 1, 2,
    2, 3, 0
], dtype=np.uint32)

# Create and bind vertex array object (VAO)
vao = glGenVertexArrays(1)
glBindVertexArray(vao)

# Create and bind vertex buffer object (VBO)
vbo = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

# Create and bind element buffer object (EBO)
ebo = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

# Set vertex attribute pointers
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 *
                      vertices.itemsize, ctypes.c_void_p(0))
glEnableVertexAttribArray(0)
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 *
                      vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
glEnableVertexAttribArray(1)

# Load texture image
image = Image.open("data/textures/bezos.jpg")
image_data = np.array(list(image.getdata()), np.uint8)

# Generate and bind texture
texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)

# Set texture parameters
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# Load texture data
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.width, image.height,
             0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
glGenerateMipmap(GL_TEXTURE_2D)

# Use shader program
glUseProgram(shader_program)

# Render loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    glClearColor(0.2, 0.3, 0.3, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    # Draw textured quad
    glBindVertexArray(vao)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    glfw.swap_buffers(window)

# Clean up
glfw.terminate()
