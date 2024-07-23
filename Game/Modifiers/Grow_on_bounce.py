def modify(event, ball, game):
    if event == "ball_bounce":
        ball.size += 5
        ball.radius = ball.size // 2