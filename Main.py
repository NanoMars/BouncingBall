import pygame
import sys
import numpy as np
import random

# Initialize Pygame
pygame.init()
screen_width = 720
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Ball Bouncing Simulation")
clock = pygame.time.Clock()
framerate = 60

# Constants
gravity = np.array([0, 500], dtype='float64')  # Gravity vector
ball_size = 50

# Ball class
class Ball:
    def __init__(self, x, y, size, color, velocity):
        self.pos = np.array([x, y], dtype='float64')
        self.size = size
        self.radius = size // 2
        self.color = color
        self.velocity = np.array(velocity, dtype='float64')

    def update(self, dt):
        # Apply gravity
        self.velocity += gravity * dt
        self.pos += self.velocity * dt
        self.check_boundary_collision()

    def check_boundary_collision(self):
        if self.pos[0] - self.radius < 0 or self.pos[0] + self.radius > screen_width:
            self.velocity[0] *= -1
        if self.pos[1] - self.radius < 0 or self.pos[1] + self.radius > screen_height:
            self.velocity[1] *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos.astype(int), self.radius)

def get_random_velocity():
    angle = random.uniform(0, 2 * np.pi)
    speed = random.uniform(100, 400)
    return np.array([speed * np.cos(angle), speed * np.sin(angle)], dtype='float64')

def main():
    center = np.array([screen_width // 2, screen_height // 2], dtype='float64')
    balls = [Ball(center[0], center[1], ball_size, (0, 255, 0), [200, 0])]
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

        for ball in balls:
            ball.update(dt)

        screen.fill((0, 0, 0))
        for ball in balls:
            ball.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
