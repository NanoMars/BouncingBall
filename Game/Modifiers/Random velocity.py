"""This is an example modifier that showcases a long description.
This modifier applies a random velocity to the ball and changes its color.
The velocity is chosen from a predefined set of possible velocities,
ensuring that the ball moves in a different direction each time the modifier is applied.
"""

import random
import numpy as np

def modify(event_name, ball, *args, **kwargs):
    if event_name == "apply":
        # Set a random velocity
        angle = random.uniform(0, 2 * np.pi)
        speed = random.uniform(100, 300)
        ball.velocity = np.array([speed * np.cos(angle), speed * np.sin(angle)], dtype='float64')

        # Set a random color
        ball.color = pygame.Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))