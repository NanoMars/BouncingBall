import pygame
import sys
import numpy as np

# Initialize Pygame
pygame.init()
screen_width = 720
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Basic Ball Simulation")
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

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos.astype(int), self.radius)

def main():
    center = np.array([screen_width // 2, screen_height // 2], dtype='float64')
    ball = Ball(center[0], center[1], ball_size, (0, 255, 0), [200, 0])
    running = True

    while running:
        dt = clock.tick(framerate) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ball.update(dt)
        screen.fill((0, 0, 0))
        ball.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
