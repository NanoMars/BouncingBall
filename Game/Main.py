import pygame
import sys
import os
import numpy as np
import random
import time
import pygame.gfxdraw
import pygame.sndarray

# Initialize Pygame
pygame.init()
screen_width = 720
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Ball Bouncing Inside a Circle")
clock = pygame.time.Clock()
framerate = 60

# Initialize Pygame mixer
pygame.mixer.init()

# Load sound
sound_folder = os.path.join(os.path.dirname(__file__), 'Sounds')
sound_file = [f for f in os.listdir(sound_folder) if f.endswith('.mp3') or f.endswith('.wav')][0]
sound_path = os.path.join(sound_folder, sound_file)
sound = pygame.mixer.Sound(sound_path)

# Sound slicing variables
sound_array = pygame.sndarray.array(sound)
sound_length = sound.get_length()
slice_length = 0.5  # 0.5 second
num_slices = int(sound_length / slice_length)
current_slice_index = 0
sample_rate = sound_array.shape[0] / sound_length

# Calculate the number of samples per slice
samples_per_slice = int(slice_length * sample_rate)

# Function to play the next sound slice
def play_next_sound_slice():
    global current_slice_index
    start_index = current_slice_index * samples_per_slice
    end_index = start_index + samples_per_slice
    sound_slice = pygame.sndarray.make_sound(sound_array[start_index:end_index])
    sound_slice.play()
    current_slice_index = (current_slice_index + 1) % num_slices

# Constants
gravity = np.array([0, 300], dtype='float64')  # Gravity vector
air_resistance = 0.998  # Air resistance coefficient (1 means no air resistance)
ball_size = 65

growing_circles = []

class GrowingCircle:
    def __init__(self, x, y, initial_radius, growth_rate, color, initial_alpha=255, fade_rate=255):
        self.pos = np.array([x, y], dtype='float64')
        self.radius = initial_radius
        self.growth_rate = growth_rate
        self.color = color
        self.alpha = initial_alpha
        self.fade_rate = fade_rate  # Rate at which the alpha decreases

    def update(self, dt):
        # Increase the radius based on the growth rate
        self.radius += self.growth_rate * dt
        # Decrease the alpha based on the fade rate
        self.alpha -= self.fade_rate * dt
        # Ensure alpha does not go below zero
        self.alpha = max(self.alpha, 0)
        # Return True if still visible, False if fully transparent
        return self.alpha > 0

    def is_transparent(self):
        # Check if the circle is fully transparent
        return self.alpha == 0

    def draw(self, screen):
        # Create a color with the current alpha value
        color_with_alpha = (*self.color, int(self.alpha))
        surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(surface, int(self.radius), int(self.radius), int(self.radius), color_with_alpha)
        pygame.gfxdraw.aacircle(surface, int(self.radius), int(self.radius), int(self.radius), color_with_alpha)
        screen.blit(surface, (self.pos[0] - self.radius, self.pos[1] - self.radius))

# Ball class
class Ball:
    def __init__(self, x, y, size, color, velocity):
        self.pos = np.array([x, y], dtype='float64')
        self.size = size
        self.radius = size // 2
        self.color = color
        self.velocity = np.array(velocity, dtype='float64')

    def update(self, dt, center, circle_radius):
        self.velocity += gravity * dt
        self.velocity *= air_resistance
        self.pos += self.velocity * dt
        self.check_collision_with_boundary(center, circle_radius)

    def check_collision_with_boundary(self, center, circle_radius):
        to_center = self.pos - center
        distance_to_center = np.linalg.norm(to_center)
        if distance_to_center + self.radius > circle_radius:
            normal = to_center / distance_to_center
            self.velocity -= 2 * np.dot(self.velocity, normal) * normal
            self.pos = center + normal * (circle_radius - self.radius)
            self.on_collision()

    def on_collision(self):
        new_circle = GrowingCircle(self.pos[0], self.pos[1], self.radius, 10, self.color)
        growing_circles.append(new_circle)
        play_next_sound_slice()

    def draw(self, screen):
        pygame.gfxdraw.filled_circle(screen, int(self.pos[0]), int(self.pos[1]), self.radius, self.color)
        pygame.gfxdraw.aacircle(screen, int(self.pos[0]), int(self.pos[1]), self.radius, self.color)

def get_random_velocity():
    angle = random.uniform(0, 2 * np.pi)
    speed = random.uniform(100, 1000)
    return np.array([speed * np.cos(angle), speed * np.sin(angle)], dtype='float64')

center = np.array([screen_width // 2, screen_height // 2], dtype='float64')
circle_radius = 300
balls = []  # Initialize an empty list for balls

initial_ball = Ball(center[0], center[1], ball_size, (0, 255, 0), [200, 0])
balls.append(initial_ball)

running = True
while running:
    
    dt = clock.tick(framerate) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
            new_ball = Ball(center[0], center[1], ball_size, 
                            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), 
                            get_random_velocity())
            balls.append(new_ball)

    # Update all balls
    for ball in balls:
        ball.update(dt, center, circle_radius)

    # Update all growing circles and filter out the transparent ones
    growing_circles = [circle for circle in growing_circles if circle.update(dt)]
    
    # Clear screen
    screen.fill((0, 0, 0))
    pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius, (255, 255, 255))
    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius, (0, 0, 0, 0))

    # Draw all balls
    for ball in balls:
        ball.draw(screen)

    # Draw all growing circles
    for circle in growing_circles:
        circle.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()