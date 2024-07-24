# Bouncing Ball

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.0.1-green.svg)](https://www.pygame.org/)

Interactive and expandable simulation of a bouncing ball which aims to provide a fun and educational platform for experimenting with physics and programming.

![Demo](Demo.gif)

## Table of Contents
- [Installation](#installation)
- [Controls](#controls)
- [Creating Modifiers](#tutorial-creating-modifiers)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/bouncing-ball.git
    cd bouncing-ball
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the game:
    ```bash
    python main.py
    ```

## Controls

- **Space**: Add a new ball
- **M**: Toggle the modifiers menu
- **1**: Toggle show lines
- **2**: Toggle show trail
- **3**: Toggle change hue
- **4**: Toggle show background growing circle
- **5**: Toggle show collision growing circle

## Creating Modifiers

Modifiers allow you to change the behavior of the ball in the simulation. Here’s how you can create your own modifier:

1. Create a new Python file in the `Modifiers` folder.
2. Define a `modify` function in your file.
3. Add a docstring to describe what your modifier does.

### Example Modifier:
```python
# Modifiers/ExampleModifier.py

"""
This modifier makes the ball grow larger on each bounce.
"""

def modify(event_name, ball, additional_params):
    if event_name == "ball_bounce":
        ball.size += 10
        ball.radius = ball.size // 2
```

### Steps to Add Your Modifier:
1. Create a new file in the `Modifiers` folder, e.g., `Modifiers/MyModifier.py`.
2. Define the `modify` function and implement your logic.
3. Your modifier will be automatically detected and can be selected from the menu in the game.

### Testing Your Modifier:
1. Run the game.
2. Press 'M' to open the modifiers menu.
3. Select your modifier from the list.
4. Interact with the game and see the changes in effect.

## Customizable Variables

Some variables that you can change to modify the behavior of the simulation:

- `screen_width` and `screen_height`: Change the size of the game window.
- `framerate`: Adjust the game's frame rate.
- `gravity`: Modify the gravity vector affecting the balls.
- `air_resistance`: Change the air resistance coefficient.
- `ball_size`: Set the initial size of the balls.
- `boundary_thickness`: Adjust the thickness of the boundary circle.

## Events

The game triggers certain events that can be used in modifiers. Here’s a list of events you can use:

- `ball_bounce`: Triggered when a ball collides with the boundary.
- `ball_created`: Triggered when a new ball is added.
- `modifier_selected`: Triggered when a modifier is selected from the menu.
- `modifier_deselected`: Triggered when a modifier is deselected.

### Example Usage of Events in a Modifier:
```python
# Modifiers/ColorChangeModifier.py

"""
This modifier changes the color of the ball on each bounce.
"""

def modify(event_name, ball, additional_params):
    if event_name == "ball_bounce":
        ball.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

This project was made for [Hack Club Arcade](https://hackclub.com/arcade/). Special thanks to the Hack Club community for their support and inspiration.