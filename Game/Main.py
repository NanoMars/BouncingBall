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
air_resistance = 1.001  # Air resistance coefficient (1 means no air resistance)
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
        # Create a color with the current alpha value
        color_with_alpha = (*self.color, int(self.alpha))
        surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(surface, int(self.radius), int(self.radius), int(self.radius), color_with_alpha)
        # pygame.gfxdraw.aacircle(surface, int(self.radius), int(self.radius), int(self.radius), color_with_alpha)
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
        new_circle = GrowingCircle(collision_point[0], collision_point[1], self.radius, 10, self.color)
        growing_circles.append(new_circle)
        play_next_sound_slice()

    def draw(self, screen):
        # Draw lines from all collision points to the current position
        for point in self.collision_points:
            pygame.draw.line(screen, self.color, (int(point[0]), int(point[1])), (int(self.pos[0]), int(self.pos[1])), 2)
        pygame.gfxdraw.filled_circle(screen, int(self.pos[0]), int(self.pos[1]), self.radius, self.color)
        pygame.gfxdraw.aacircle(screen, int(self.pos[0]), int(self.pos[1]), self.radius, self.color)
        pygame.gfxdraw.filled_circle(screen, int(self.pos[0]), int(self.pos[1]), int((4 * self.radius) / 5), (0, 0, 0))

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

center = np.array([screen_width // 2, screen_height // 2], dtype='float64')
circle_radius = 300
balls = []  # Initialize an empty list for balls

initial_ball = Ball(center[0], center[1], ball_size, (0, 255, 0), [200, 0])
balls.append(initial_ball)

hue = 0
running = True
while running:
    
    dt = clock.tick(framerate) / 1000.0
    hue = (hue + dt * 10) % 360
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

    check_ball_collisions()

    # Update all growing circles and filter out the transparent ones
    growing_circles = [circle for circle in growing_circles if circle.update(dt) and circle.radius > 0]
    
    # Clear screen
    screen.fill((0, 0, 0))
    color = pygame.Color(0)
    color.hsva = (hue, 100, 100, 100)
    inner_radius = circle_radius - boundary_thickness
    
    # Draw the outer boundary with anti-aliasing
    for i in range(boundary_thickness):
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)
        pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - i, color)
    
    # Fill the inner part to create a solid boundary effect
    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), inner_radius, (0, 0, 0))
    
    # Draw all growing circles
    for circle in growing_circles:
        circle.draw(screen)
    # Draw all balls
    for ball in balls:
        ball.draw(screen)

    

    pygame.display.flip()

pygame.quit()
sys.exit()