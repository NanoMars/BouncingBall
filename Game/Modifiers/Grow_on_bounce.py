"ball grows when it bounces"

def modify(event, ball, game):
    if event == "ball_bounce":
        ball.size += 100
        ball.radius = ball.size // 2