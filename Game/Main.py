import os
import sys
import pygame
import numpy as np
import importlib
import random
import time
import pygame.gfxdraw
import mido

# Initialize Pygame
pygame.init()
screen_width = 720
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height), pygame.SRCALPHA)
pygame.display.set_caption("Ball Bouncing Inside a Circle")
clock = pygame.time.Clock()
framerate = 60

# Initialize font
font = pygame.font.Font(None, 36)

midi_folder = os.path.join(os.path.dirname(__file__), 'MIDI')
midi_files = [f for f in os.listdir(midi_folder) if f.endswith('.mid')]

midi_notes = []
if midi_files:
    midi_path = os.path.join(midi_folder, midi_files[0])
    mid = mido.MidiFile(midi_path)
    for msg in mid:
        if not msg.is_meta and (msg.type == 'note_on' or msg.type == 'note_off'):
            midi_notes.append(msg)

color = (255, 255, 255)
hue = 0

show_lines = True
show_trail = True
change_hue = True
show_background_growing_circle = True
show_collision_growing_circle = True

# Variables for GUI
selected_modifier = None
expanded_modifier = None
click_processed = False  # Initialize click_processed flag


current_midi_index = 0
currently_playing_sounds = []

def sanitize_name(name):
    return ''.join(char for char in name if char.isprintable())

def load_modifiers():
    modifiers = {}
    modifiers_folder = os.path.join(os.path.dirname(__file__), 'Modifiers')
    for filename in os.listdir(modifiers_folder):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            module = importlib.import_module(f'Modifiers.{module_name}')
            if hasattr(module, 'modify'):
                modifiers[module_name] = {
                    "function": module.modify,
                    "description": module.__doc__ or "No description available"
                }
    return modifiers

modifiers = load_modifiers()
selected_modifiers = []  # No initial selection
expanded_modifier = None

def wrap_text(surface, text, x, y, max_width, font):
    words = text.replace('\n', ' ').split(' ')
    space_width, space_height = font.size(' ')
    lines = []
    current_line = []
    current_width = 0

    for word in words:
        word_surface = font.render(word, True, (255, 255, 255))
        word_width, word_height = word_surface.get_size()
        if current_width + word_width <= max_width:
            current_line.append(word_surface)
            current_width += word_width + space_width
        else:
            lines.append(current_line)
            current_line = [word_surface]
            current_width = word_width + space_width

    lines.append(current_line)

    y_initial = y  # Store the initial y position

    for line in lines:
        for word_surface in line:
            surface.blit(word_surface, (x, y))
            x += word_surface.get_width() + space_width
        x = menu_rect.x + 40  # Reset x position relative to the box
        y += space_height

    return y  # Return the new y position without additional spacing

def draw_modifier_menu(screen, font, modifiers, selected_modifiers, expanded_modifier, dragging, drag_offset, minimized):
    global menu_position
    
    title_text = font.render("Modifiers", True, (255, 255, 255))
    title_width = title_text.get_width()
    button_width = 80
    title_and_buttons_width = title_width + button_width + 20
    max_item_width = max(font.size(sanitize_name(name).replace('_', ' '))[0] for name in modifiers.keys()) + 100
    menu_width = max(title_and_buttons_width, max_item_width)
    
    menu_rect = pygame.Rect(menu_position.x, menu_position.y, menu_width, 620)
    header_rect = pygame.Rect(menu_position.x, menu_position.y, menu_width, 40)
    item_rects = []
    triangle_rects = []

    if dragging:
        menu_rect.topleft = pygame.Vector2(pygame.mouse.get_pos()) - drag_offset
        header_rect.topleft = menu_rect.topleft

    if not minimized:
        pygame.draw.rect(screen, (0, 0, 0), menu_rect)
        pygame.draw.rect(screen, (100, 100, 100, 128), menu_rect)

    pygame.draw.rect(screen, (150, 150, 150, 128), header_rect)

    header_text = font.render("Modifiers", True, (255, 255, 255))
    screen.blit(header_text, (header_rect.x + 10, header_rect.y + 10))

    close_button = pygame.Rect(header_rect.right - 30, header_rect.y + 5, 20, 20)
    minimize_button = pygame.Rect(header_rect.right - 60, header_rect.y + 5, 20, 20)
    pygame.draw.rect(screen, (200, 0, 0), close_button)
    pygame.draw.rect(screen, (200, 200, 0), minimize_button)
    close_text = font.render("X", True, (255, 255, 255))
    minimize_text = font.render("-", True, (255, 255, 255))
    screen.blit(close_text, (close_button.x + 5, close_button.y))
    screen.blit(minimize_text, (minimize_button.x + 5, minimize_button.y))

    if minimized:
        return menu_rect, header_rect, close_button, minimize_button, item_rects, triangle_rects

    y_offset = header_rect.height + 10
    buffer = 10

    for i, (name, data) in enumerate(modifiers.items()):
        display_name = sanitize_name(name).replace('_', ' ')
        is_selected = name in selected_modifiers
        background_color = (0, 255, 0, 128) if is_selected else (50, 50, 50, 0)

        text_surface = font.render(display_name, True, (255, 255, 255), (0, 0, 0))
        text_surface.set_colorkey((0, 0, 0))
        text_width, text_height = font.size(display_name)

        text_width += buffer * 2
        item_rect = pygame.Rect(menu_rect.x + 20, menu_rect.y + y_offset, text_width, 30)
        pygame.draw.rect(screen, background_color, item_rect)

        if text_surface:
            screen.blit(text_surface, (menu_rect.x + 20 + buffer, menu_rect.y + y_offset))

        triangle_color = (255, 255, 255)
        triangle_x = menu_rect.x + text_width + 40  # Adjusted value to add gap
        triangle_y = menu_rect.y + y_offset + 10
        triangle_points = [(triangle_x, triangle_y), 
                           (triangle_x + 10, triangle_y + 10), 
                           (triangle_x - 10, triangle_y + 10)]
        if expanded_modifier == name:
            triangle_points = [(triangle_x, triangle_y + 10), 
                               (triangle_x + 10, triangle_y), 
                               (triangle_x - 10, triangle_y)]
        pygame.draw.polygon(screen, triangle_color, triangle_points)
        
        triangle_rect = pygame.Rect(triangle_x - 10, triangle_y - 10, 20, 20)
        triangle_rects.append((triangle_rect, name))
        item_rects.append((item_rect, name))
        y_offset += 40

        if expanded_modifier == name:
            description_y = menu_rect.y + y_offset
            y_offset = wrap_text(screen, data["description"], menu_rect.x + 40, description_y, menu_width - 80, font) - menu_rect.y + 10

    return menu_rect, header_rect, close_button, minimize_button, item_rects, triangle_rects

def toggle_modifier(modifier, selected_modifiers):
    sanitized_modifier = sanitize_name(modifier)
    if sanitized_modifier in selected_modifiers:
        selected_modifiers.remove(sanitized_modifier)
    else:
        selected_modifiers.append(sanitized_modifier)

# Global variables
menu_position = pygame.Vector2(50, 50)  # Initial position of the menu

def handle_mouse_events(event, menu_rect, header_rect, close_button, minimize_button, dragging, drag_offset, click_processed):
    global menu_open, menu_minimized, expanded_modifier, menu_position
    if event.type == pygame.MOUSEBUTTONDOWN:
        if close_button.collidepoint(event.pos):
            menu_open = False
        elif minimize_button.collidepoint(event.pos):
            menu_minimized = not menu_minimized
        elif header_rect.collidepoint(event.pos):
            dragging = True
            drag_offset = pygame.Vector2(event.pos) - pygame.Vector2(header_rect.topleft)
        expanded_modifier, click_processed = handle_triangle_click(event, triangle_rects, expanded_modifier, click_processed)
    elif event.type == pygame.MOUSEBUTTONUP:
        dragging = False
        drag_offset = None
        menu_position = pygame.Vector2(header_rect.topleft)
    elif event.type == pygame.MOUSEMOTION:
        if dragging:
            new_pos = pygame.Vector2(event.pos) - drag_offset
            menu_rect.topleft = (int(new_pos.x), int(new_pos.y))
            header_rect.topleft = menu_rect.topleft
    return dragging, drag_offset, click_processed

def handle_triangle_click(event, triangle_rects, expanded_modifier, click_processed):
    if event.type == pygame.MOUSEBUTTONDOWN and not click_processed:
        for triangle_rect, name in triangle_rects:
            if triangle_rect.collidepoint(event.pos):
                if expanded_modifier == name:
                    expanded_modifier = None
                else:
                    expanded_modifier = name
                click_processed = True
                break
    return expanded_modifier, click_processed

def apply_modifier(event_name, ball):
    global selected_modifiers
    if selected_modifiers:
        for modifier_name in selected_modifiers:
            if modifier_name in modifiers:
                modifier_function = modifiers[modifier_name]["function"]
                modifier_function(event_name, ball, None)

def adsr_envelope(t, attack, decay, sustain, release):
    total_samples = len(t)
    attack_samples = min(int(attack * 44100), total_samples)
    decay_samples = min(int(decay * 44100), total_samples - attack_samples)
    release_samples = min(int(release * 44100), total_samples - attack_samples - decay_samples)
    sustain_samples = total_samples - (attack_samples + decay_samples + release_samples)

    env = np.zeros(total_samples)
    env[:attack_samples] = np.linspace(0, 1, attack_samples)
    env[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain, decay_samples)
    if sustain_samples > 0:
        env[attack_samples + decay_samples:attack_samples + decay_samples + sustain_samples] = sustain
    env[-release_samples:] = np.linspace(sustain, 0, release_samples)

    return env

def play_next_midi_notes():
    global current_midi_index
    global currently_playing_sounds

    if current_midi_index >= len(midi_notes):
        current_midi_index = 0

    notes_to_play = []
    while current_midi_index < len(midi_notes):
        msg = midi_notes[current_midi_index]
        if msg.type == 'note_on':
            freq = 440.0 * (2.0 ** ((msg.note - 69) / 12.0))
            duration = int(44100 * msg.time) if msg.time > 0 else 44100
            t = np.arange(duration) / 44100.0
            samples = np.sin(2 * np.pi * freq * t).astype(np.float32)

            # Apply ADSR envelope
            attack = 0.01
            decay = 0.1
            sustain = 0.7
            release = 0.2
            envelope = adsr_envelope(t, attack, decay, sustain, release)
            samples *= envelope

            samples_stereo = np.column_stack((samples, samples))
            samples_stereo *= 0.0125  # Normalize the amplitude
            sound = pygame.sndarray.make_sound((samples_stereo * 32767).astype(np.int16))
            notes_to_play.append(sound)
        elif msg.type == 'note_off':
            pass
        current_midi_index += 1

        if len(notes_to_play) > 0 and (current_midi_index >= len(midi_notes) or midi_notes[current_midi_index].time > 0):
            break

    for sound in notes_to_play:
        sound.play()
        currently_playing_sounds.append(sound)

# Constants
gravity = np.array([0, 300], dtype='float64')  # Gravity vector
air_resistance = 0.9995  # Air resistance coefficient (1 means no air resistance)
ball_size = 100
boundary_thickness = 10

class Notification:
    def __init__(self, message, index, duration=5):
        self.message = message
        self.timestamp = time.time()
        self.duration = duration
        self.fade_duration = 0.5
        self.index = index
        self.start_position = (10, screen_height)  # Start at the bottom of the screen
        self.target_position = None  # Target position will be set later
        self.current_position = self.start_position  # Initial current position
        self.animation_timestamp = time.time()  # Separate timestamp for animation

    def update(self):
        return (time.time() - self.timestamp) < self.duration

    def get_opacity(self):
        elapsed = time.time() - self.timestamp
        if elapsed < self.fade_duration:
            return int((elapsed / self.fade_duration) * 255)
        elif elapsed > self.duration - self.fade_duration:
            return int(((self.duration - elapsed) / self.fade_duration) * 255)
        else:
            return 255

    def update_position(self):
        elapsed = time.time() - self.animation_timestamp
        easing_time = min(elapsed, self.fade_duration)
        easing_factor = 1 - (2 ** (-10 * easing_time / self.fade_duration))
        self.current_position = (self.start_position[0], self.start_position[1] + (self.target_position[1] - self.start_position[1]) * easing_factor)

    def draw(self, screen):
        text = font.render(self.message, True, (255, 255, 255))
        text.set_alpha(self.get_opacity())
        self.update_position()
        screen.blit(text, self.current_position)

class NotificationManager:
    def __init__(self):
        self.notifications = []

    def add_notification(self, message):
        base_position = (10, screen_height - 50)
        for notification in self.notifications:
            notification.index += 1  # Increment index of existing notifications
            notification.start_position = notification.current_position  # Set start position to current position
            notification.target_position = (base_position[0], base_position[1] - notification.index * 40)
            notification.animation_timestamp = time.time()  # Update animation timestamp
        new_notification = Notification(message, 0)
        new_notification.start_position = (base_position[0], screen_height)
        new_notification.target_position = base_position
        self.notifications.append(new_notification)

    def update(self):
        current_time = time.time()
        self.notifications = [n for n in self.notifications if n.update() and n.current_position[1] > -50]
        
    def draw(self, screen):
        for notification in self.notifications:
            notification.draw(screen)

growing_circles = []

class GrowingCircle:
    def __init__(self, x, y, initial_radius, growth_rate, color, initial_alpha=255, fade_rate=255, layer=1):
        self.pos = np.array([x, y], dtype='float64')
        self.radius = initial_radius
        self.growth_rate = growth_rate
        self.color = color
        self.alpha = initial_alpha
        self.fade_rate = fade_rate  # Rate at which the alpha decreases
        self.layer = layer

    def update(self, dt):
        self.radius += self.growth_rate * dt
        self.alpha -= self.fade_rate * dt
        self.alpha = max(self.alpha, 0)
        self.radius = max(self.radius, 0)
        return self.alpha > 0

    def draw(self, screen):
        surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        surface = surface.convert_alpha()
        color_without_alpha = self.color[:3]
        
        # Draw filled circle
        pygame.gfxdraw.filled_circle(surface, int(self.radius), int(self.radius), int(self.radius), color_without_alpha + (int(self.alpha),))
        
        
        # Draw anti-aliased outer edge
        pygame.gfxdraw.aacircle(surface, int(self.radius), int(self.radius), int(self.radius), color_without_alpha + (int(self.alpha),))
        
        # Blit the surface with transparency onto the main screen
        screen.blit(surface, (self.pos[0] - self.radius, self.pos[1] - self.radius))
class Ball:
    def __init__(self, x, y, size, color, velocity):
        self.pos = np.array([x, y], dtype='float64')
        self.size = size
        self.radius = size // 2
        self.color = color
        self.velocity = np.array(velocity, dtype='float64')
        self.invulnerable = True
        self.invulnerable_timer = 999999999
        self.has_bounced = False
        self.collision_points = []
        self.line_opacities = []

    def update(self, dt, center, circle_radius):
        self.velocity += gravity * dt
        self.velocity *= air_resistance
        self.pos += self.velocity * dt
        self.check_collision_with_boundary(center, circle_radius)
        
        if self.invulnerable:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                
        if show_trail:
            new_circle = GrowingCircle(self.pos[0], self.pos[1], self.radius, -140, self.color, 150, 200)
            growing_circles.append(new_circle)
        
        for i in range(len(self.line_opacities)):
            self.line_opacities[i] = max(self.line_opacities[i] - dt * 255, 90)

    def check_collision_with_boundary(self, center, circle_radius):
        to_center = self.pos - center
        distance_to_center = np.linalg.norm(to_center)
        if distance_to_center + self.radius > circle_radius - boundary_thickness / 2:
            normal = to_center / distance_to_center
            collision_point = center + normal * (circle_radius - boundary_thickness / 2)
            self.velocity -= 2 * np.dot(self.velocity, normal) * normal
            self.pos = center + normal * (circle_radius - boundary_thickness / 2 - self.radius)
            self.on_collision(collision_point)
            
    def on_collision(self, collision_point):
        if show_lines:
            self.collision_points.append(collision_point)
            self.line_opacities.append(255)
            self.line_opacities = [255 for _ in self.line_opacities]

        if show_collision_growing_circle:
            new_circle = GrowingCircle(collision_point[0], collision_point[1], 25, 10, self.color)
            growing_circles.append(new_circle)
        
        if show_background_growing_circle:
            background_circle = GrowingCircle(center[0], center[1], circle_radius + (boundary_thickness / 2), 25, self.color, layer=0)
            growing_circles.append(background_circle)
        
        play_next_midi_notes()

        # Apply modifier for ball bounce event
        apply_modifier("ball_bounce", self)

    def draw(self, screen):
        surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        if show_lines:
            for idx, point in enumerate(self.collision_points):
                color_with_opacity = (*self.color[:3], int(self.line_opacities[idx]))  # Ensure it's an RGBA tuple
                direction = np.array(self.pos) - np.array(point)
                direction_length = np.linalg.norm(direction)
                if direction_length > 5:  # Avoid division by zero or negative length
                    direction = direction / direction_length  # Normalize the direction
                    
                    # Calculate the normal at the collision point
                    normal = point - center
                    normal_length = np.linalg.norm(normal)
                    if normal_length > 0:
                        normal = normal / normal_length  # Normalize the normal vector

                        # Calculate the angle between the direction and the normal
                        dot_product = np.dot(direction, normal)
                        dot_product = np.clip(dot_product, -1.0, 1.0)  # Clip dot product to valid range for arccos
                        angle = np.arccos(dot_product)  # Angle in radians
                        
                        # Shorten the line more as the angle increases
                        shorten_factor = 5 + 2 * (angle / np.pi)
                        new_point = np.array(point) + direction * shorten_factor
                        pygame.draw.line(surface, color_with_opacity, (int(new_point[0]), int(new_point[1])), (int(self.pos[0]), int(self.pos[1])), 1)
        
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius, 1)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.pos[0]), int(self.pos[1])), int((4 * self.radius) / 5))
        
        screen.blit(surface, (0, 0))

def get_random_velocity():
    angle = random.uniform(0, 2 * np.pi)
    speed = random.uniform(100, 1000)
    return np.array([speed * np.cos(angle), speed * np.sin(angle)], dtype='float64')

def check_ball_collisions():
    global balls
    new_balls = []
    while balls:
        ball = balls.pop(0)
        if not ball.invulnerable:
            collided = False
            for other_ball in balls:
                if np.linalg.norm(ball.pos - other_ball.pos) < ball.radius + other_ball.radius:
                    collided = True
                    balls.remove(other_ball)
                    break
            if not collided:
                new_balls.append(ball)
        else:
            new_balls.append(ball)
    balls = new_balls

def get_random_color():
    hue = random.randint(0, 360)
    color = pygame.Color(0)
    color.hsva = (hue, 100, 100, 100)
    return color

center = np.array([screen_width // 2, screen_height // 2], dtype='float64')
circle_radius = 300
balls = []  # Initialize an empty list for balls

notification_manager = NotificationManager()

if midi_files:
    notification_manager.add_notification(f"MIDI file found: {midi_files[0]}")
else:
    notification_manager.add_notification("No MIDI file found")

selected_modifier = list(modifiers.keys())[0] if modifiers else None
dragging = False
drag_offset = pygame.Vector2(0, 0)


# Initialize color and hue
hue = 0
change_hue = True  # Variable to toggle hue-changing

# Toggle features
show_lines = True
show_trail = True
show_background_growing_circle = True
show_collision_growing_circle = True


# Main loop
running = True
menu_open = False
menu_minimized = False

menu_rect = pygame.Rect(50, 50, 620, 620)
header_rect = pygame.Rect(50, 50, 620, 40)
close_button = pygame.Rect(header_rect.right - 30, header_rect.y + 5, 20, 20)
minimize_button = pygame.Rect(header_rect.right - 60, header_rect.y + 5, 20, 20)


while running:
    dt = clock.tick(framerate) / 1000.0
    click_processed = False  # Reset click_processed at the start of each frame

    if change_hue:
        hue = (hue + dt * 10) % 360
        color = pygame.Color(0)
        color.hsva = (hue, 100, 100, 100)
    else:
        color = pygame.Color(255, 255, 255)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                new_ball = Ball(center[0], center[1], ball_size, get_random_color(), get_random_velocity())
                balls.append(new_ball)
            elif event.key == pygame.K_m:
                menu_open = not menu_open
                menu_minimized = False
            elif event.key == pygame.K_1:
                show_lines = not show_lines
                notification_manager.add_notification(f"Show lines turned {'on' if show_lines else 'off'}")
            elif event.key == pygame.K_2:
                show_trail = not show_trail
                notification_manager.add_notification(f"Show trail turned {'on' if show_trail else 'off'}")
            elif event.key == pygame.K_3:
                change_hue = not change_hue
                notification_manager.add_notification(f"Change hue turned {'on' if change_hue else 'off'}")
            elif event.key == pygame.K_4:
                show_background_growing_circle = not show_background_growing_circle
                notification_manager.add_notification(f"Show background reactive circle turned {'on' if show_background_growing_circle else 'off'}")
            elif event.key == pygame.K_5:
                show_collision_growing_circle = not show_collision_growing_circle
                notification_manager.add_notification(f"Show collision circle turned {'on' if show_collision_growing_circle else 'off'}")
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            # Define triangle_rects before usage
            triangle_rects = []
            menu_rect, header_rect, close_button, minimize_button, item_rects, triangle_rects = draw_modifier_menu(screen, font, modifiers, selected_modifiers, expanded_modifier, dragging, drag_offset, menu_minimized)
            dragging, drag_offset, click_processed = handle_mouse_events(event, menu_rect, header_rect, close_button, minimize_button, dragging, drag_offset, click_processed)
            if event.type == pygame.MOUSEBUTTONDOWN:
                for item_rect, modifier_name in item_rects:
                    if item_rect.collidepoint(event.pos):
                        toggle_modifier(modifier_name, selected_modifiers)
                        click_processed = True
                expanded_modifier, click_processed = handle_triangle_click(event, triangle_rects, expanded_modifier, click_processed)

    for ball in balls:
        ball.update(dt, center, circle_radius)

    check_ball_collisions()

    growing_circles = [circle for circle in growing_circles if circle.update(dt) and circle.radius > 0]

    screen.fill((0, 0, 0))

    for circle in sorted(growing_circles, key=lambda c: c.layer):
        if circle.layer == 0:
            circle.draw(screen)

    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius + int(boundary_thickness / 2), color)
    pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius + int(boundary_thickness / 2), color)

    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius - boundary_thickness, (0, 0, 0))
    pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - boundary_thickness, (0, 0, 0))
    for circle in growing_circles:
        if circle.layer != 0:
            circle.draw(screen)
        
    for ball in balls:
        ball.draw(screen)

    if menu_open:
        menu_rect, header_rect, close_button, minimize_button, item_rects, triangle_rects = draw_modifier_menu(screen, font, modifiers, selected_modifiers, expanded_modifier, dragging, drag_offset, menu_minimized)

    notification_manager.update()
    notification_manager.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()