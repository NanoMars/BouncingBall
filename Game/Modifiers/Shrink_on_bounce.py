def modify(event, ball, game):
    if event == "ball_bounce":
        previous_size = ball.size
        ball.size *= 0.95
        ball.radius = ball.size // 2
        size_ratio = ball.size / previous_size
        velocity_multiplier = 1 / size_ratio
        ball.velocity *= velocity_multiplier