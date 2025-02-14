import pygame
import os
from Ball import Ball
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, RED, BLUE, BLACK
from EEG import EEGDevice

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brainball Collision Game")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize balls
        self.ball1 = Ball(
            SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2, "pop_cat.png", RED, {
                'left': pygame.K_a, 'right': pygame.K_d,
                'up': pygame.K_w, 'down': pygame.K_s
            }
        )
        self.ball2 = Ball(
            2 * SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2, "brainball2.png", BLUE, {
                'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
                'up': pygame.K_UP, 'down': pygame.K_DOWN
            }
        )
        # Make sure ball2 has velocity attributes
        self.ball2.velocity_x = 0
        self.ball2.velocity_y = 0

    def run(self, port):
        self.eegDevice = EEGDevice(port)
        print(f"Starting game with {self.eegDevice.ser.port}...")
        while self.running:
            self.handle_events()
            self.eegDevice.fetch_data()  # Active EEG polling
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        # Update keyboard-controlled ball
        keys = pygame.key.get_pressed()
        self.ball1.move(keys)

        # EEG-controlled ball movement with acceleration and bounce
        eeg_attention = self.eegDevice.attention_value
        eeg_meditation = self.eegDevice.meditation_value

        # Use EEG values as acceleration (adjust scaling as needed)
        acceleration_x = (eeg_attention - 50) / 10.0   # range roughly -5 to +5
        acceleration_y = (eeg_meditation - 50) / 10.0    # range roughly -5 to +5

        # Update velocities based on acceleration
        self.ball2.velocity_x += acceleration_x
        self.ball2.velocity_y += acceleration_y

        # Apply friction (damping) so the ball slows down over time
        friction = 0.95
        self.ball2.velocity_x *= friction
        self.ball2.velocity_y *= friction

        # Update ball2's position based on its velocity
        self.ball2.x += self.ball2.velocity_x
        self.ball2.y += self.ball2.velocity_y

        # Bounce off the walls instead of simply clamping:
        # Horizontal boundaries
        if self.ball2.x < 0:
            self.ball2.x = 0
            self.ball2.velocity_x = -self.ball2.velocity_x
        elif self.ball2.x > SCREEN_WIDTH - self.ball2.rect.width:
            self.ball2.x = SCREEN_WIDTH - self.ball2.rect.width
            self.ball2.velocity_x = -self.ball2.velocity_x

        # Vertical boundaries
        if self.ball2.y < 0:
            self.ball2.y = 0
            self.ball2.velocity_y = -self.ball2.velocity_y
        elif self.ball2.y > SCREEN_HEIGHT - self.ball2.rect.height:
            self.ball2.y = SCREEN_HEIGHT - self.ball2.rect.height
            self.ball2.velocity_y = -self.ball2.velocity_y

        # Update the rectangle position for drawing
        self.ball2.rect.x = int(self.ball2.x)
        self.ball2.rect.y = int(self.ball2.y)

        # Collision between balls
        self.ball1.check_collision(self.ball2)

    def draw(self):
        self.screen.fill(WHITE)
        self.ball1.draw(self.screen)
        self.ball2.draw(self.screen)
        # Draw a border around the play area
        pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 5)
        pygame.display.flip()

if __name__ == "__main__":
    port = input("Enter EEG device port: ").strip()
    game = Game()
    game.run(port)
