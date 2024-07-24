"""Ball grows larger on each bounce.
"""

def modify(event_name, ball, additional_params):
    if event_name == "ball_bounce":
        ball.size += 10
        ball.radius = ball.size // 2