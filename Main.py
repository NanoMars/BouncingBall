import pygame
import sys
import numpy as np
import random
import time
import pygame.gfxdraw

# Initialize Pygame
pygame.init()
screen_width = 720
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Ball Bouncing Inside a Circle")
clock = pygame.time.Clock()
framerate = 60

# Constants
gravity = np.array([0, 300], dtype='float64')  # Gravity vector
air_resistance = 0.998  # Air resistance coefficient (1 means no air resistance)
ball_size = 65

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

    # Clear screen
    screen.fill((0, 0, 0))
    pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius, (255, 255, 255))
    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius, (0, 0, 0, 0))

    # Draw all balls
    for ball in balls:
        ball.draw(screen)

    pygame.display.flip()