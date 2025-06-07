import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
from PIL import Image
import math
import time
import os

from spiffmodel import SpiffModel

import spiffPhysicsEngine as SPE

os.environ["SDL_VIDEO_X11_FORCE_EGL"] = "1"
# Window dimensions
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600


WINDOW_WIDTH = 400
WINDOW_HEIGHT = 300
#WINDOW_WIDTH = 1920
#WINDOW_HEIGHT = 1080
# Vertex shader (passes through vertex positions)
VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec3 position;
void main() {
    gl_Position = vec4(position, 1.0);
}
"""

# Fragment shader (performs ray tracing)
FRAGMENT_SHADER = """
#version 330 core
out vec4 fragColor;
uniform vec2 resolution;
uniform vec3 camera_pos;
uniform vec3 camera_dir;
uniform vec4 metaballs[10];
uniform int metaballcount;
bool isObjectAt(vec3 point) {
    if (point.y < -2){
        return true;
    }
    float TotalDistance = 0;
    for (int i = 0; i < metaballcount; i++) {
        vec3 center = metaballs[i].xyz;
        float radius = metaballs[i].w;
        if (distance(point,center) > 0){
            TotalDistance += radius/(distance(point,center));
        }
        if (distance(point, center) <= radius) {
            //return true;
        }
    if (TotalDistance > metaballcount){
    return true;
    }
    }
    return false;

}
void main() {
    vec2 uv = gl_FragCoord.xy / resolution * 2.0 - 1.0;
    uv.y *= resolution.y / resolution.x;
    vec3 ray_origin = camera_pos;
    vec3 ray_dir = normalize(vec3(uv.x, uv.y, -1.0)); // Ray direction in view space
    //ray_dir = vec3();
    float Cam_XAngle = camera_dir.x;
    ray_dir = vec3((sin(Cam_XAngle)*uv.x)-(cos(Cam_XAngle)*uv.z),uv.y,(cos(Cam_XAngle)*uv.x)+(sin(Cam_XAngle)*uv.z));
    ray_dir = normalize(ray_dir);
    float max_distance = 100.0;
    float step_size = 0.1;
    vec3 current_pos = ray_origin;
    bool hit = false;
    float b = 0;
    for (float t = 0.0; t < max_distance; t += step_size) {
        current_pos += ray_dir * step_size;
        b += 1/(max_distance+step_size);
        if (isObjectAt(current_pos)) {
            hit = true;
            break;
        }
    }
    if (hit) {
        fragColor = vec4(1-b, 0.0, 0.0, 1.0); // Red for hit
    } else {
        fragColor = vec4(0.0, 0.0, 1.0, 1.0); // Blue for miss
    }
}
"""



for fragment_shader_file_path in ["Fragment-Shader.c","_internals/Fragment-Shader.c","_internal/Fragment-Shader.c"]:
    try:
        with open(fragment_shader_file_path) as file:
            FRAGMENT_SHADER = file.read()
            break
    except FileNotFoundError as e:
        print(e) 
        continue
print(FRAGMENT_SHADER)

for post_fragment_shader_file_path in ["Post-Fragment.c","_internals/Post-Fragment.c","_internal/Post-Fragment.c"]:
    try:
        with open(post_fragment_shader_file_path) as file:
            POST_FRAGMENT_SHADER = file.read()
            break
    except FileNotFoundError as e:
        print(e) 
        continue


for post_vertex_shader_file_path in ["Post-Vertex.c","_internals/Post-Vertex.c","_internal/Post-Vertex.c"]:
    try:
        with open(post_vertex_shader_file_path) as file:
            POST_VERTEX_SHADER = file.read()
            break
    except FileNotFoundError as e:
        print(e) 
        continue


def load_shader_file(name):
    shader = ""
    for shader_file_path in [f"{name}",f"_internals/{name}",f"_internal/{name}"]:
        try:
            with open(shader_file_path) as file:
                shader = file.read()
                break
        except FileNotFoundError as e:
            print(e) 
            continue
    return shader



UI_Vertex = load_shader_file("UI-Vertex.c")
UI_Fragment = load_shader_file("UI-Fragment.c")


COMP_Vertex = load_shader_file("COMP-Vertex.c")
COMP_Fragment = load_shader_file("COMP-Fragment.c")

SKY_Vertex = load_shader_file("SKY-Vertex.c")
SKY_Fragment = load_shader_file("SKY-Fragment.c")

PAUSE_Vertex = load_shader_file("PAUSE-Vertex.c")
PAUSE_Fragment = load_shader_file("PAUSE-Fragment.c")


def create_shader_program():
    return compileProgram(
        compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
        compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    )

def create_post_shader_program():
    return compileProgram(
        compileShader(POST_VERTEX_SHADER, GL_VERTEX_SHADER),
        compileShader(POST_FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    )

def create_new_shader_program(vertex_shader,fragment_shader):
    return compileProgram(
        compileShader(vertex_shader, GL_VERTEX_SHADER),
        compileShader(fragment_shader, GL_FRAGMENT_SHADER)
    )

def rotate_camera(camera_dir, yaw, pitch):
    # Rotate around Y-axis (yaw)
    rotation_matrix_yaw = np.array([
        [np.cos(yaw), 0, np.sin(yaw)],
        [0, 1, 0],
        [-np.sin(yaw), 0, np.cos(yaw)]
    ])

    # Rotate around X-axis (pitch)
    rotation_matrix_pitch = np.array([
        [1, 0, 0],
        [0, np.cos(pitch), -np.sin(pitch)],
        [0, np.sin(pitch), np.cos(pitch)]
    ])

    # Apply yaw and pitch rotations to the camera direction
    rotated_dir = np.dot(rotation_matrix_yaw, camera_dir)
    rotated_dir = np.dot(rotation_matrix_pitch, rotated_dir)

    return rotated_dir

def load_3d_texture(folder_path):
    """
    Loads a 3D texture from a folder of images.

    :param folder_path: Path to the folder containing images.
    :return: OpenGL texture ID
    """
    # Get sorted list of image files
    image_files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))])
    
    if not image_files:
        raise ValueError("No images found in the specified folder.")

    # Load images
    slices = []
    for filename in image_files:
        img_path = os.path.join(folder_path, filename)
        img = Image.open(img_path).convert("RGB")  # Ensure 3 channels (RGB)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)  # Flip vertically for OpenGL
        slices.append(np.array(img, dtype=np.uint8))

    # Convert list to 3D NumPy array
    data = np.stack(slices, axis=0)  # Shape: (depth, height, width, 3)
    depth, height, width, channels = data.shape

    # Generate OpenGL texture
    textureID = glGenTextures(1)
    glBindTexture(GL_TEXTURE_3D, textureID)
    glTexImage3D(GL_TEXTURE_3D, 0, GL_RGB8, width, height, depth, 0, GL_RGB, GL_UNSIGNED_BYTE, data)

    # Set texture parameters
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

    glBindTexture(GL_TEXTURE_3D, 0)  # Unbind

    return textureID





def main(FRAGMENT_SHADER=""):


    ##LoadConfig

    config = {}

    with open("config.txt") as file:
        for line in file.read().split('\n'):
            config[line.split(":")[0]] = line.split(":")[1]
    FRAGMENT_SHADER
    for config_target in config:
        if config_target == "width":
            WINDOW_WIDTH = int(config[config_target])
        if config_target == "height":
            WINDOW_HEIGHT = int(config[config_target])
        FRAGMENT_SHADER = (config_target + "="+config[config_target] + ";").join(FRAGMENT_SHADER.split(f"//config.{config_target}"))
        print(config_target)
        print(FRAGMENT_SHADER)
        

    
    pygame.init()
    print("OpenGL Major Version",pygame.display.gl_get_attribute(pygame.GL_CONTEXT_MAJOR_VERSION))
    print("OpenGL Major Version",pygame.display.gl_get_attribute(pygame.GL_CONTEXT_MINOR_VERSION))
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,4)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,2)
    print("OpenGL Major Version",pygame.display.gl_get_attribute(pygame.GL_CONTEXT_MAJOR_VERSION))
    print("OpenGL Major Version",pygame.display.gl_get_attribute(pygame.GL_CONTEXT_MINOR_VERSION))
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    


    # Create a shader program
    #shader = create_shader_program()
    shader = create_new_shader_program(VERTEX_SHADER,FRAGMENT_SHADER)

    
    blur_shader = create_post_shader_program()


    ui_shader = create_new_shader_program(UI_Vertex,UI_Fragment)

    
    comp_shader = create_new_shader_program(COMP_Vertex,COMP_Fragment)

    sky_shader = create_new_shader_program(SKY_Vertex,SKY_Fragment)

    pause_shader = create_new_shader_program(PAUSE_Vertex,PAUSE_Fragment)

    # Create FBO
    fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)

    # Create texture to render to
    render_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, render_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Attach the texture to the FBO
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                           GL_TEXTURE_2D, render_texture, 0)

    # (Optional) Create a renderbuffer for depth if needed
    rbo = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, WINDOW_WIDTH, WINDOW_HEIGHT)
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    # Check for completeness
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        print("ERROR: Framebuffer is not complete!")
    glBindFramebuffer(GL_FRAMEBUFFER, 0)





    # Create Sky FBO
    sky_buffer = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, sky_buffer)

    # Create texture to render to
    sky_render_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, sky_render_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Attach the texture to the FBO
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                           GL_TEXTURE_2D, sky_render_texture, 0)

    # (Optional) Create a renderbuffer for depth if needed
    #rbo = glGenRenderbuffers(1)
    #glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    #glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, WINDOW_WIDTH, WINDOW_HEIGHT)
    #glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    # Check for completeness
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        print("ERROR: Framebuffer is not complete!")
    glBindFramebuffer(GL_FRAMEBUFFER, 0)



    # Create Pause FBO
    pause_buffer = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, pause_buffer)

    # Create texture to render to
    pause_render_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, pause_render_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Attach the texture to the FBO
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                           GL_TEXTURE_2D, pause_render_texture, 0)

    # (Optional) Create a renderbuffer for depth if needed
    #rbo = glGenRenderbuffers(1)
    #glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    #glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, WINDOW_WIDTH, WINDOW_HEIGHT)
    #glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    # Check for completeness
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        print("ERROR: Framebuffer is not complete!")
    glBindFramebuffer(GL_FRAMEBUFFER, 0)





    # Create FBO
    ui_buffer = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, ui_buffer)

    # Create texture to render to
    ui_render_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, ui_render_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Attach the texture to the FBO
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                           GL_TEXTURE_2D, ui_render_texture, 0)

    # (Optional) Create a renderbuffer for depth if needed
    #rbo = glGenRenderbuffers(1)
    #glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    #glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, WINDOW_WIDTH, WINDOW_HEIGHT)
    #glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    # Check for completeness
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        print("ERROR: Framebuffer is not complete!")
    glBindFramebuffer(GL_FRAMEBUFFER, 0)





    
    # Define a fullscreen quad
    quad_vertices = np.array([
        -1.0, -1.0, 0.0,
         1.0, -1.0, 0.0,
        -1.0,  1.0, 0.0,
         1.0,  1.0, 0.0,
    ], dtype=np.float32)

    # Create a Vertex Buffer Object and Vertex Array Object
    VBO = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)

    VAO = glGenVertexArrays(1)
    glBindVertexArray(VAO)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
    glEnableVertexAttribArray(0)

    #glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * quad_vertices.itemsize, ctypes.c_void_p(3 * quad_vertices.itemsize))
    #glEnableVertexAttribArray(1)

    #texture = glGenTextures(1)
    #Texdepth = 16
    #Texwidth, Texheight = 16, 16
    #data = np.random.rand(16, 16, 16, 3).astype(np.float32)  # Random RGB values

    #print(data)

    
    try:
        textureID = load_3d_texture("images")
    except Exception as e:
        print(e)
        textureID = load_3d_texture("_internal/images")



    #glBindTexture(GL_TEXTURE_3D, textureID)
    #glTexImage3D(GL_TEXTURE_3D, 0, GL_RGB32F, Texwidth, Texheight, Texdepth, 0, GL_RGB, GL_FLOAT, data)






    # Set the shader program and uniforms
    glUseProgram(shader)
    resolution_location = glGetUniformLocation(shader, "resolution")
    glUniform2f(resolution_location, WINDOW_WIDTH, WINDOW_HEIGHT)

    camera_pos_location = glGetUniformLocation(shader, "camera_pos")
    camera_dir_location = glGetUniformLocation(shader, "camera_dir")

    metaball_location = glGetUniformLocation(shader, "metaballs")
    metaball_count_location = glGetUniformLocation(shader, "metaballcount")

    portal_location = glGetUniformLocation(shader, "Portals")
    portal_count_location = glGetUniformLocation(shader, "PortalCount")
    other_portal_location = glGetUniformLocation(shader, "OtherPortalIndex")

    lights_location = glGetUniformLocation(shader, "light_positions")
    lights_color_location = glGetUniformLocation(shader, "light_colors")
    lights_amount_location = glGetUniformLocation(shader, "light_count")

    object_meshes_location = glGetUniformLocation(shader, "ObjectsMeshes")
    object_id_location = glGetUniformLocation(shader, "ObjectID")
    object_id_list_location = glGetUniformLocation(shader, "ObjectIDList")
    object_count_location = glGetUniformLocation(shader, "ObjectCount")
    object_mesh_count_location = glGetUniformLocation(shader, "ObjectMeshCount")

    time_location = glGetUniformLocation(shader, "time")
    
    camera_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    camera_dir = np.array([0.0, 0.0, -1.0], dtype=np.float32)

    clock = pygame.time.Clock()

    sphere_data = np.array([
        [0.0, 0.0, -5.0, 2.0],  # Sphere 1: center (0,0,-5), radius 2
        [2, 0.0, -5.0, 1.0],  # Sphere 2: center (2,0,-5), radius 1
    ], dtype=np.float32)

    portal_data = np.array([[0,3,-7,2.0],[0,3,-2,2.0]])
    other_portal_data = np.array([[1,0]])

    light_positions = np.array([[3.0,2.0,-5.0],[5.0,2.0,-5.0],[0.0,2.0,-5.0]], dtype=np.float32)
    lights_colors = np.array([[0.0,1.0,0.0],[0.0,0.0,1.0],[1.0,1.0,1.0]], dtype=np.float32)

    ObjectMeshes = np.array([[0.0, 0.0, -3.0, 1.0],[2, 0.0, -3.0, 1.0]], dtype=np.float32)
    ObjectIDList = np.array([0], dtype=np.float32)
    ObjectIDS = np.array([0,0],dtype=np.float32)


    
    with SpiffModel.open("TestModel.spiffmodel") as file:
        ObjectMeshes = []
        ObjectIDS = []
        for Object in file.getModelObjects():
            x,y,z = [Object["position"][x] for x in ["x","y","z"]]
            r = Object["radius"]
            objectId = Object["objectID"]
            ObjectMeshes.append([x,y,z,r])
            ObjectIDS.append(objectId)

        light_positions = []
        lights_colors = []
        for Light in file.getLightObjects():
            x,y,z = [Light["position"][x] for x in ["x","y","z"]]
            r,g,b = [Light["color"][x] for x in ["r","g","b"]]
            r = Light["radius"]
            light_positions.append([x,y,z,r])
            lights_colors.append([r,g,b])

    light_positions = np.array(light_positions,dtype=np.float32)
    lights_colors = np.array(lights_colors,dtype=np.float32)
    
            
    ObjectIDList = np.array(list(set(ObjectIDS)),dtype=np.float32)
    ObjectIDS = np.array(ObjectIDS,dtype=np.float32)
    ObjectMeshes = np.array(ObjectMeshes,dtype=np.float32)

    PlayerVel = np.array([0.0,0.0,0.0],dtype=np.float32)

    gravity_strength = -9
    jump_strength = 400+9



    last_mouse_x, last_mouse_y = pygame.mouse.get_pos()

    running = True
    i = 0
    MouseGrabbed = False
    yaw = 0
    pitch = 0

    enable_POST = False
    enable_COMP = True
    escape_menu = False


    FrameStart = time.time()
    EnablePhysics = True
    while running:
        DeltaTime = time.time()-FrameStart
        if DeltaTime != 0:
            pass
            #print(round(1/DeltaTime))
        
        #print(DeltaTime)
        FrameStart = time.time()
        i += 1
        sphere_data = np.array([
            [0.0, 0.0, -5.0, 1.0],  # Sphere 1: center (0,0,-5), radius 2
            [math.sin(math.radians(i)) * 10, 0.0, -5, 1.0],  # Sphere 2: center (2,0,-5), radius 1
        ], dtype=np.float32)

        #ObjectMeshes = np.array([
        #    [0.0, 0.0, -3.0, 1.0],  # Sphere 1: center (0,0,-5), radius 2
        #    [math.sin(math.radians(i)) * 10, 0.0, -3, 1.0],  # Sphere 2: center (2,0,-5), radius 1
        #    [0.0, 0.0, -2.0, 1.0],
        #    [0.0, 2.0, -3.0, 1.0]
        #], dtype=np.float32)
        #ObjectIDS = np.array([0,0,1,2],dtype=np.float32)
        #ObjectIDList = np.array([0,1,2], dtype=np.float32)
        """
        sphere_data = []
        for x in range(1):
            for y in range(-2,2):
                sphere_data.append([0,0.0,y+-5,1.0])
        sphere_data = np.array(sphere_data)
        """
        pygame.event.set_grab(MouseGrabbed)
        #if MouseGrabbed:
            #pygame.mouse.set_pos((WINDOW_WIDTH/2,WINDOW_HEIGHT/2))
        #print(MouseGrabbed)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        key_mouse_dx,key_mouse_dy = 0,0
        arrows_pressed = [False,False,False,False]
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    escape_menu = not escape_menu
                if event.key == pygame.K_ESCAPE:
                    MouseGrabbed = not MouseGrabbed
                if event.key == pygame.K_b:
                    enable_POST = not enable_POST
                if event.key == pygame.K_c:
                    enable_COMP = not enable_COMP
                if event.key == pygame.K_v:
                    EnablePhysics = not EnablePhysics
                if event.key == K_SPACE:
                    onGround = camera_pos[1]-1 <= -2
                    if onGround:
                        PlayerVel[1] += jump_strength*DeltaTime
            if event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                mouse_dx,mouse_dy = event.rel
                #if MouseGrabbed:
                 #   pygame.mouse.set_pos((WINDOW_WIDTH/2,WINDOW_HEIGHT/2))
        if MouseGrabbed:
            pygame.mouse.set_pos((WINDOW_WIDTH/2,WINDOW_HEIGHT/2))
        #pygame.mouse.set_pos((0,0))
        # Get mouse movement
        
        #print(mouse_x,mouse_y)
        if MouseGrabbed:
            pass
            #mouse_x = mouse_x - WINDOW_WIDTH/2
            #mouse_dy = mouse_y - WINDOW_HEIGHT/2
        else:
            mouse_dx = mouse_x - last_mouse_x
            mouse_dy = mouse_y - last_mouse_y
        last_mouse_x, last_mouse_y = mouse_x, mouse_y

        # Sensitivity for camera rotation
        sensitivity = 0.002

        # Update yaw and pitch
        mouse_dy += key_mouse_dy
        #print(key_mouse_dy)
        yaw += mouse_dx * sensitivity*-1
        pitch += mouse_dy * sensitivity

        #print(camera_dir)

        # Apply the camera rotation
        camera_dir = np.array([pitch, yaw, 0], dtype=np.float32)

        # Movement controls
        keys = pygame.key.get_pressed()
        #print(yaw)
        #print(keys[])
        accel_dir = ([0.0,0.0,0.0])
        if keys[K_w]:
            #camera_pos += camera_dir * 0.1
            if EnablePhysics:
                accel_dir[2]+= -math.sin(yaw)*0.1
                accel_dir[0] += math.cos(yaw)*0.1
            else:   
                camera_pos[2]+= -math.sin(yaw)*0.1
                camera_pos[0]+= math.cos(yaw)*0.1
        if keys[K_s]:
            if EnablePhysics:
                accel_dir[2]+= -math.sin(yaw)*-0.1
                accel_dir[0]+= math.cos(yaw)*-0.1
            else:
                #camera_pos -= camera_dir * 0.1
                camera_pos[2]+= -math.sin(yaw)*-0.1
                camera_pos[0]+= math.cos(yaw)*-0.1
            #camera_pos[2]-= 0.1
        if keys[K_a]:
            if EnablePhysics:
            #camera_pos[0] -= 0.1
                accel_dir[2]+= -math.sin(yaw+math.radians(90))*0.1
                accel_dir[0]+= math.cos(yaw+math.radians(90))*0.1
            else:
                camera_pos[2]+= -math.sin(yaw+math.radians(90))*0.1
                camera_pos[0]+= math.cos(yaw+math.radians(90))*0.1
        if keys[K_d]:
            if EnablePhysics:
                accel_dir[2]+= -math.sin(yaw-math.radians(90))*0.1
                accel_dir[0]+= math.cos(yaw-math.radians(90))*0.1
            else:
                camera_pos[2]+= -math.sin(yaw-math.radians(90))*0.1
                camera_pos[0]+= math.cos(yaw-math.radians(90))*0.1
        if keys[K_q]:
            camera_pos[1] -= 0.1
        if keys[K_e]:
            camera_pos[1] += 0.1
        if keys[K_z]:
            pitch += 0.1
        if keys[K_UP]:
            pitch -= 0.1
        if keys[K_DOWN]:
            pitch += 0.1
        if keys[K_LEFT]:
            yaw += 0.1
        if keys[K_RIGHT]:
            yaw -= 0.1
        camera_pos = camera_pos[:3]
        camera_dir = camera_dir[:3]


        if EnablePhysics:

            onGround = camera_pos[1]-1 <= -2
            #print(onGround)
            if onGround:
                speed = np.linalg.norm(PlayerVel)
                friction = 10
                if speed != 0:
                    drop = speed*friction*DeltaTime
                    PlayerVel *= max(speed-drop,0)/speed


            
            max_velocity = 1000

            accelerate = 300

            accel_dir = np.array(accel_dir,dtype=np.float32)



            projVel = np.dot(PlayerVel,accel_dir)
            accelVel = accelerate*DeltaTime
            if projVel+accelVel > max_velocity:
                accelVel = max_velocity-projVel
            PlayerVel += accel_dir*accelVel


            PlayerVel[1] += gravity_strength*DeltaTime
            #camera_pos[1] += PlayerVel[1]*DeltaTime

            camera_pos[1] -=1

            if SPE.PointIsColliding(camera_pos+PlayerVel*DeltaTime):
                velocityLength = math.sqrt(sum((PlayerVel*DeltaTime)**2))
                if velocityLength > 0:
                    
                    velocitySegments = int(velocityLength)
                    velocityParts = (PlayerVel*DeltaTime)/velocitySegments
                    for vPart in range(velocitySegments):
                        if SPE.PointIsColliding(camera_pos+(velocityParts*vPart)):
                            camera_pos += (velocityParts*vPart)
                            
                print("Collision")
            else:
                camera_pos += PlayerVel*DeltaTime

            camera_pos[1] += 1
            #print(projVel)

            
            if camera_pos[1]-1 < -2:
                camera_pos[1] = -1
                if PlayerVel[1] < 0:
                    PlayerVel[1] = 0



        


        # First pass: render scene to FBO
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Use your existing shader for raytracing and render the fullscreen quad
        glUseProgram(shader)

        

        #print(sphere_data)
        glUniform1f(time_location, time.time())
        try:
            #print(*camera_pos)
            #print("glUniform3f(camera_pos_location, *camera_pos)")
            glUniform3f(camera_pos_location, *camera_pos)
            #print("glUniform3f(camera_dir_location, *camera_dir)")
            glUniform3f(camera_dir_location, *camera_dir)
            glUniform1i(metaball_count_location, len(sphere_data))
            glUniform1i(lights_amount_location, len(light_positions))
            glUniform3fv(lights_location, len(light_positions),light_positions.flatten())
            glUniform3fv(lights_color_location, len(light_positions),lights_colors.flatten())
            glUniform4fv(metaball_location, len(sphere_data), sphere_data.flatten())


            glUniform1i(portal_count_location, len(portal_data))
            glUniform4fv(portal_location, len(portal_data), portal_data.flatten())
            glUniform1iv(other_portal_location, len(portal_data), other_portal_data.flatten())

            glUniform4fv(object_meshes_location, len(ObjectMeshes), ObjectMeshes.flatten())
            glUniform1fv(object_id_location, len(ObjectIDS), ObjectIDS.flatten())
            glUniform1fv(object_id_list_location, len(ObjectIDList), ObjectIDList.flatten())

            glUniform1i(object_count_location, len(ObjectIDList))
            glUniform1i(object_mesh_count_location, len(ObjectIDS))

            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_3D, textureID)
            glUniform1i(glGetUniformLocation(shader, "texture3D"), 0)
        except Exception as e:
            print(e)


        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        

        glBindFramebuffer(GL_FRAMEBUFFER, 0)



        #Sky Code
        #"""
        #

        glClear(GL_COLOR_BUFFER_BIT)
        glBindFramebuffer(GL_FRAMEBUFFER, sky_buffer)
        glUseProgram(sky_shader)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, sky_render_texture)

        glUniform3f(glGetUniformLocation(sky_shader, "camera_dir"), *camera_dir)


        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        #"""


        #Pause Code
        #"""
        #
        #glBindFramebuffer(GL_FRAMEBUFFER, pause_buffer)
        glClear(GL_COLOR_BUFFER_BIT)
        glBindFramebuffer(GL_FRAMEBUFFER, pause_buffer)
        glUseProgram(pause_shader)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, pause_render_texture)

        glUniform1i(glGetUniformLocation(pause_shader, "Enabled"), escape_menu)

        #glUniform3f(glGetUniformLocation(sky_shader, "camera_dir"), *camera_dir)


        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        #"""

        #UI code

        
        
        glClear(GL_COLOR_BUFFER_BIT)
        glBindFramebuffer(GL_FRAMEBUFFER, ui_buffer)
        glUseProgram(ui_shader)


        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, ui_render_texture)
            
        glUniform1i(glGetUniformLocation(ui_shader, "screenTexture"), 0)



        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        

        glBindFramebuffer(GL_FRAMEBUFFER, 0)




        


        #glBindFramebuffer(GL_FRAMEBUFFER, 1)

        if enable_POST:
            #"""
            #glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            
            glClear(GL_COLOR_BUFFER_BIT)
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            ##Post Start

            

            glUseProgram(blur_shader)
            

            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, render_texture)
            
            glUniform1i(glGetUniformLocation(blur_shader, "screenTexture"), 0)



            glBindVertexArray(VAO)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            
            #"""
            ##Post Enmd
        #print(enable_COMP)
        if enable_COMP:

            
            #glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            
            glClear(GL_COLOR_BUFFER_BIT)

            ##Post Start

            

            glUseProgram(comp_shader)

            glUniform1i(glGetUniformLocation(comp_shader, "screenTexture"), 0)
            #
    

            glUniform1i(glGetUniformLocation(comp_shader, "uiTexture"), 1)
            glUniform1i(glGetUniformLocation(comp_shader, "skyTexture"), 2)

            glUniform1i(glGetUniformLocation(comp_shader, "pauseTexture"), 3)

            glActiveTexture(GL_TEXTURE0+0)
            glBindTexture(GL_TEXTURE_2D, render_texture)
            glActiveTexture(GL_TEXTURE0+1)
            glBindTexture(GL_TEXTURE_2D, ui_render_texture)
            glActiveTexture(GL_TEXTURE0+2)
            glBindTexture(GL_TEXTURE_2D, sky_render_texture)
            glActiveTexture(GL_TEXTURE0+3)
            glBindTexture(GL_TEXTURE_2D, pause_render_texture)
            
            
            
            
        
        # Draw the fullscreen quad
        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main(FRAGMENT_SHADER)
