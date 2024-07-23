"""
ball grows when it bounces
"""
def modify(event, ball, game):
    print(f"Inside modify function for event: {event}")  # Debug print
    if event == "ball_bounce":
        print("Modifier triggered: ball_bounce")  # Debug print
        initial_size = ball.size
        ball.size += 10
        ball.radius = ball.size // 2
        print(f"Modified ball size from {initial_size} to {ball.size}, radius: {ball.radius}")  # Debug print