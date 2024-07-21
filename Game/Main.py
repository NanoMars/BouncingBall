import pygame
import sys
import os
import numpy as np
import random
import time
import pygame.gfxdraw
import pygame.midi
import mido


# Initialize Pygame
pygame.midi.init()
pygame.init()
screen_width = 720
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Ball Bouncing Inside a Circle")
clock = pygame.time.Clock()
framerate = 60

# Initialize Pygame MIDI
pygame.midi.init()

# Load MIDI file
midi_folder = os.path.join(os.path.dirname(__file__), 'MIDI')
midi_file = [f for f in os.listdir(midi_folder) if f.endswith('.mid')][0]
midi_path = os.path.join(midi_folder, midi_file)
midi = mido.MidiFile(midi_path)

# MIDI playback variables
current_note_index = 0
midi_notes = []

# Extract notes from the MIDI file
for track in midi.tracks:
    for msg in track:
        if msg.type == 'note_on':
            midi_notes.append((msg.note, msg.velocity))

# Function to play the next MIDI notes
def play_next_midi_notes():
    global current_note_index
    if current_note_index < len(midi_notes):
        note, velocity = midi_notes[current_note_index]
        midi_out.note_on(note, velocity)
        current_note_index += 1
    else:
        current_note_index = 0

# Constants
gravity = np.array([0, 300], dtype='float64')  # Gravity vector
air_resistance = 1.000  # Air resistance coefficient (1 means no air resistance)
ball_size = 100
boundary_thickness = 10

growing_circles = []

class GrowingCircle:
    def __init__(self, x, y, initial_radius, growth_rate, color, initial_alpha=255, fade_rate=255):
        self.pos = np.array([x, y], dtype='float64')
        self.radius = initial_radius
        self.growth_rate = growth_rate
        self.color = color
        self.alpha = initial_alpha
        self.fade_rate = fade_rate  # Rate at which the alpha decreases
        
        # Debugging: print the initial color values to verify
        print("Initial color:", self.color)
        
    def update(self, dt):
        # Increase the radius based on the growth rate
        self.radius += self.growth_rate * dt
        # Decrease the alpha based on the fade rate
        self.alpha -= self.fade_rate * dt
        # Ensure alpha does not go below zero
        self.alpha = max(self.alpha, 0)
        
        self.radius = max(self.radius, 0)
        # Return True if still visible, False if fully transparent
        return self.alpha > 0

    def draw(self, screen):
        # Create a surface with alpha
        surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        surface = surface.convert_alpha()
        
        # Ensure the color is a tuple with three values (RGB)
        color_without_alpha = self.color[:3]
        
        # Draw the filled circle with the color (without alpha)
        pygame.gfxdraw.filled_circle(surface, int(self.radius), int(self.radius), int(self.radius), color_without_alpha)
        
        # Apply alpha value
        surface.set_alpha(int(self.alpha))
        
        # Blit the surface onto the screen
        screen.blit(surface, (self.pos[0] - self.radius, self.pos[1] - self.radius))

class Ball:
    def __init__(self, x, y, size, color, velocity):
        self.pos = np.array([x, y], dtype='float64')
        self.size = size
        self.radius = size // 2
        self.color = color
        self.velocity = np.array(velocity, dtype='float64')
        self.invulnerable = True
        self.invulnerable_timer = 999999999  # 0.25 seconds of invulnerability
        self.has_bounced = False
        self.collision_points = []  # Track collision points
        self.line_opacities = []  # Track opacities of lines from collision points

    def update(self, dt, center, circle_radius):
        self.velocity += gravity * dt
        self.velocity *= air_resistance
        self.pos += self.velocity * dt
        self.check_collision_with_boundary(center, circle_radius)
        
        if self.invulnerable:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                
        new_circle = GrowingCircle(self.pos[0], self.pos[1], self.radius, -100, self.color, 170, 250)
        growing_circles.append(new_circle)
        
        # Reduce opacity over time
        for i in range(len(self.line_opacities)):
            self.line_opacities[i] = max(self.line_opacities[i] - dt * 255, 90)  # Reduce opacity

    def check_collision_with_boundary(self, center, circle_radius):
        to_center = self.pos - center
        distance_to_center = np.linalg.norm(to_center)
        if distance_to_center + self.radius > circle_radius - boundary_thickness / 2:
            normal = to_center / distance_to_center
            collision_point = center + normal * (circle_radius - boundary_thickness / 2)
            self.velocity -= 2 * np.dot(self.velocity, normal) * normal
            self.pos = center + normal * (circle_radius - boundary_thickness / 2 - self.radius)
            self.on_collision(collision_point)

    def on_collision(self, collision_point):
        self.collision_points.append(collision_point)  # Store exact collision point
        self.line_opacities.append(255)  # Set initial opacity to 100%

        # Set all lines' transparency to 100%
        for i in range(len(self.line_opacities)):
            self.line_opacities[i] = 255

        new_circle = GrowingCircle(collision_point[0], collision_point[1], self.radius, 10, self.color)
        growing_circles.append(new_circle)
        play_next_midi_notes()

    def draw(self, screen):
        # Create a surface for drawing with alpha channel
        surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Draw lines from all collision points to the current position using anti-aliased lines
        for idx, point in enumerate(self.collision_points):
            color_with_opacity = (*self.color[:3], int(self.line_opacities[idx]))  # Ensure it's an RGBA tuple
            pygame.draw.line(surface, color_with_opacity, (int(point[0]), int(point[1])), (int(self.pos[0]), int(self.pos[1])), 1)
        
        # Draw the ball on the surface
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius, 1)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.pos[0]), int(self.pos[1])), int((4 * self.radius) / 5))
        
        # Blit the surface onto the main screen
        screen.blit(surface, (0, 0))




# List available MIDI devices
def list_midi_devices():
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        print(i, info)

# List available MIDI devices
def list_midi_devices():
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        print(i, info)

# Print available MIDI devices to the console
print("Available MIDI devices:")
list_midi_devices()

# Attempt to get the default MIDI output ID
try:
    default_output_id = pygame.midi.get_default_output_id()
    if default_output_id == -1:
        raise pygame.midi.MidiException("No default MIDI output device found.")
    midi_out = pygame.midi.Output(default_output_id)
except pygame.midi.MidiException as e:
    print(f"Error initializing default MIDI output: {e}")
    # Fall back to manual selection
    available_devices = [i for i in range(pygame.midi.get_count()) if pygame.midi.get_device_info(i)[3] == 1]
    if not available_devices:
        print("No MIDI output devices available.")
        sys.exit(1)
    # Select the first available MIDI output device
    selected_device = available_devices[0]
    print(f"Using available MIDI device: {pygame.midi.get_device_info(selected_device)}")
    midi_out = pygame.midi.Output(selected_device)

def get_random_velocity():
    angle = random.uniform(0, 2 * np.pi)
    speed = random.uniform(100, 1000)
    return np.array([speed * np.cos(angle), speed * np.sin(angle)], dtype='float64')

def check_ball_collisions():
    global balls
    new_balls = []
    while balls:
        ball = balls.pop(0)
        if not ball.invulnerable:
            collided = False
            for other_ball in balls:
                if np.linalg.norm(ball.pos - other_ball.pos) < ball.radius + other_ball.radius:
                    collided = True
                    balls.remove(other_ball)
                    break
            if not collided:
                new_balls.append(ball)
        else:
            new_balls.append(ball)
    balls = new_balls

def get_random_color():
    hue = random.randint(0, 360)
    color = pygame.Color(0)
    color.hsva = (hue, 100, 100, 100)
    return color

center = np.array([screen_width // 2, screen_height // 2], dtype='float64')
circle_radius = 300
balls = []  # Initialize an empty list for balls

running = True
while running:
    dt = clock.tick(framerate) / 1000.0
    hue = (hue + dt * 10) % 360
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
            new_ball = Ball(center[0], center[1], ball_size,
            get_random_color(),
            get_random_velocity())
            balls.append(new_ball)
        # Update all balls
    for ball in balls:
        ball.update(dt, center, circle_radius)

    check_ball_collisions()

    # Update all growing circles and filter out the transparent ones
    growing_circles = [circle for circle in growing_circles if circle.update(dt) and circle.radius > 0]

    # Clear screen
    screen.fill((0, 0, 0))
    color = pygame.Color(0)
    color.hsva = (hue, 100, 100, 100)
    inner_radius = circle_radius - boundary_thickness

    # Draw all growing circles
    for circle in growing_circles:
        circle.draw(screen)
    # Draw all balls
    for ball in balls:
        ball.draw(screen)

    # Draw the outer boundary with anti-aliasing
    for i in range(boundary_thickness):
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)

    pygame.display.flip()
midi_out.close()
pygame.midi.quit()
pygame.quit()
sys.exit()