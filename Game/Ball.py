import pygame
import os
from constants import BALL_RADIUS, BALL_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT, RED
from SkillHolder import SkillHolder
from ListSkill import ChangeColor

class Ball:
    def __init__(self, x, y, image_path, fallback_color, controls):
        self.skillHolder = SkillHolder()
        self.image = None
        self.fallback_color = fallback_color
        self.controls = controls
        
        # Float-based position tracking
        self.x = float(x)
        self.y = float(y)
        
        # Create a rect for collision/drawing purposes (centered at (x,y))
        self.rect = pygame.Rect(0, 0, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.rect.center = (self.x, self.y)
        
        # Use separate velocities for x and y (using floats for smoother movement)
        self.velocity_x = 0.0
        self.velocity_y = 0.0

        # Add a skill (e.g., for color change)
        self.skillHolder.add_skill(ChangeColor(self))
        
        # Load image if available, otherwise use fallback color for drawing
        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (BALL_RADIUS * 2, BALL_RADIUS * 2))

    def move(self, keys):
        """
        For the keyboard-controlled ball, update velocity based on key presses,
        then update position accordingly.
        """
        # Reset velocities each frame
        self.velocity_x = 0
        self.velocity_y = 0
        
        # Update horizontal velocity based on controls
        if 'left' in self.controls and keys[self.controls['left']]:
            self.velocity_x = -BALL_SPEED
        if 'right' in self.controls and keys[self.controls['right']]:
            self.velocity_x = BALL_SPEED
        
        # Update vertical velocity if 'up' and 'down' controls are provided
        if 'up' in self.controls and keys[self.controls['up']]:
            self.velocity_y = -BALL_SPEED
        if 'down' in self.controls and keys[self.controls['down']]:
            self.velocity_y = BALL_SPEED

        # Update position based on velocity
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Update rect to match the new position
        self.rect.center = (int(self.x), int(self.y))
        
        # Keep the ball within the bounds of the display
        self.rect.clamp_ip(pygame.display.get_surface().get_rect())

    def draw(self, screen):
        """
        Draws the ball on the given screen.
        """
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.circle(screen, self.fallback_color, self.rect.center, BALL_RADIUS)

    def check_collision(self, other_ball):
        """
        Checks and handles collision with another ball by swapping velocities
        and updating positions.
        """
        if self.rect.colliderect(other_ball.rect):
            # Swap horizontal and vertical velocities between the balls
            self.velocity_x, other_ball.velocity_x = other_ball.velocity_x, self.velocity_x
            self.velocity_y, other_ball.velocity_y = other_ball.velocity_y, self.velocity_y

            # Update positions based on the swapped velocities to reflect the collision
            self.x += self.velocity_x
            self.y += self.velocity_y
            other_ball.x += other_ball.velocity_x
            other_ball.y += other_ball.velocity_y

            # Update rect positions for both balls
            self.rect.center = (int(self.x), int(self.y))
            other_ball.rect.center = (int(other_ball.x), int(other_ball.y))

    def GetSkillHolder(self):
        return self.skillHolder
    
    def use_skill(self, keys):
        """
        Uses one of the available skills if the corresponding key is pressed.
        """
        skill_keys = [pygame.K_1, pygame.K_2, pygame.K_3]
        skill_names = list(self.skillHolder.skills.keys())
        for i, key in enumerate(skill_keys):
            if keys[key] and i < len(skill_names):
                self.mana = self.skillHolder.use_skill(skill_names[i])
