import pygame
import sys
import os
import numpy as np
import random
import time
import pygame.gfxdraw
import pygame.sndarray
from pygame import midi
import mido

# Initialize Pygame
pygame.init()
screen_width = 720
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Ball Bouncing Inside a Circle")
clock = pygame.time.Clock()
framerate = 60

midi_folder = os.path.join(os.path.dirname(__file__), 'MIDI')
midi_files = [f for f in os.listdir(midi_folder) if f.endswith('.mid')]
midi_path = os.path.join(midi_folder, midi_files[0])

mid = mido.MidiFile(midi_path)

midi_notes = []
for msg in mid:
    if not msg.is_meta:
        if msg.type == 'note_on' or msg.type == 'note_off':
            midi_notes.append(msg)

# Initialize Pygame mixer
pygame.mixer.init()
pygame.midi.init()
#midi_out = pygame.midi.Output(0)

# Load sound
sound_folder = os.path.join(os.path.dirname(__file__), 'Sounds')
sound_file = [f for f in os.listdir(sound_folder) if f.endswith('.mp3') or f.endswith('.wav')][0]
sound_path = os.path.join(sound_folder, sound_file)
sound = pygame.mixer.Sound(sound_path)

# Sound slicing variables
sound_array = pygame.sndarray.array(sound)
sound_length = sound.get_length()
hue = 0
sample_rate = sound_array.shape[0] / sound_length

show_lines = True
show_trail = True
change_hue = True
show_background_growing_circle = True
show_collision_growing_circle = True

current_midi_index = 0
currently_playing_sounds = []

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

        if show_collision_growing_circle:
            new_circle = GrowingCircle(collision_point[0], collision_point[1], 25, 10, self.color)
            growing_circles.append(new_circle)
        
        if show_background_growing_circle:
            background_circle = GrowingCircle(center[0], center[1], circle_radius + (boundary_thickness / 2), 25, self.color, layer=0)
            growing_circles.append(background_circle)
        
        play_next_midi_notes()

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

running = True
while running:
    dt = clock.tick(framerate) / 1000.0
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
            elif event.key == pygame.K_1:
                show_lines = not show_lines
                print("Show lines toggled:", show_lines)
            elif event.key == pygame.K_2:
                show_trail = not show_trail
                print("Show trail toggled:", show_trail)
            elif event.key == pygame.K_3:
                change_hue = not change_hue
                print("Change hue toggled:", change_hue)
            elif event.key == pygame.K_4:
                show_background_growing_circle = not show_background_growing_circle
                print("Show background growing circle toggled:", show_background_growing_circle)
            elif event.key == pygame.K_5:
                show_collision_growing_circle = not show_collision_growing_circle
                print("Show collision growing circle toggled:", show_collision_growing_circle)

    for ball in balls:
        ball.update(dt, center, circle_radius)

    check_ball_collisions()

    growing_circles = [circle for circle in growing_circles if circle.update(dt) and circle.radius > 0]

    screen.fill((0, 0, 0))
    
    # Draw the background growing circles
    for circle in sorted(growing_circles, key=lambda c: c.layer):
        if circle.layer == 0:
            circle.draw(screen)

    # Draw outer edge of the boundary with anti-aliasing
    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius + int(boundary_thickness / 2), color)
    pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius + int(boundary_thickness / 2), color)

    # Draw the inner boundary with anti-aliasing
    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius - boundary_thickness, (0, 0, 0))
    pygame.gfxdraw.aacircle(screen, int(center[0]), int(center[1]), circle_radius - boundary_thickness, (0, 0, 0))

    
            
    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius + int(boundary_thickness / 2), color)
    
    pygame.gfxdraw.filled_circle(screen, int(center[0]), int(center[1]), circle_radius - boundary_thickness, (0, 0, 0))

    
    # Draw all other growing circles
    for circle in growing_circles:
        if circle.layer != 0:
            circle.draw(screen)
            
    for ball in balls:
        ball.draw(screen)
    
    pygame.display.flip()

pygame.quit()
sys.exit()