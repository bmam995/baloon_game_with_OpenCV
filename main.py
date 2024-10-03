import pygame
import cv2
import mediapipe as mp
import random

# Initialize Pygame
pygame.init()

# Define screen size
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Balloon Game")

# Initialize the mixer for sound
pygame.mixer.init()

# Load the pop sound (make sure to have a valid sound file like 'pop_sound.wav' in the same directory)
pop_sound = pygame.mixer.Sound("ballon-blows.wav")

# Colors
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# Load MediaPipe Hand tracking model
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Balloon settings
BALLOON_RADIUS = 20
BALLOON_SPEED = 2
POP_DURATION = 10  # Duration for the popping animation

# Frame rate
clock = pygame.time.Clock()
FPS = 30

# OpenCV setup for hand tracking
cap = cv2.VideoCapture(0)

# Function to draw balloon
def draw_balloon(x, y, radius, color):
    pygame.draw.circle(screen, color, (x, y), radius)

# Function to detect collision between hand and balloon
def is_collision(hand_x, hand_y, balloon_x, balloon_y):
    distance = ((hand_x - balloon_x) ** 2 + (hand_y - balloon_y) ** 2) ** 0.5
    return distance < BALLOON_RADIUS

# Function to display a button
def display_button(text, x, y, w, h, color, action=None):
    font = pygame.font.SysFont(None, 55)
    button_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, color, button_rect)
    
    # Render button text
    button_text = font.render(text, True, BLACK)
    screen.blit(button_text, (x + (w - button_text.get_width()) // 2, y + (h - button_text.get_height()) // 2))

    # Detect mouse click
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        if click[0] == 1 and action is not None:
            action()

# Function to restart the game
def restart_game():
    main_game_loop()  # Restart the main game loop

# Main game loop
def main_game_loop():
    # Scoring and game state
    score = 0
    balloon_count = 0
    MAX_BALLOONS = 10

    # Balloons
    balloons = []
    popping_balloons = []  # Store balloons that are popping

    # Local 'running' variable to control this instance of the game loop
    game_running = True

    while game_running:
        # Capture hand movements using OpenCV
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame to match real-time camera display
        frame = cv2.flip(frame, 1)

        # Convert the frame from BGR to RGB (so Pygame can display it correctly)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the RGB image to detect hands using MediaPipe
        results = hands.process(frame_rgb)

        # Resize the frame to match Pygame window size
        frame_rgb = cv2.resize(frame_rgb, (WIDTH, HEIGHT))

        # Convert the RGB image to a format Pygame can display
        frame_surface = pygame.surfarray.make_surface(frame_rgb)

        # Rotate the frame for Pygame (since OpenCV and Pygame coordinate systems differ)
        frame_surface = pygame.transform.rotate(frame_surface, -90)
        frame_surface = pygame.transform.flip(frame_surface, True, False)

        # Blit the camera feed onto the Pygame window
        screen.blit(frame_surface, (0, 0))

        # Hand position variables
        hand_x, hand_y = None, None

        # Check if hand landmarks are detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get hand coordinates (index finger tip for better precision)
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                hand_x = int(index_finger_tip.x * WIDTH)
                hand_y = int(index_finger_tip.y * HEIGHT)

                # Optionally draw hand landmarks for visual feedback
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Update balloon positions
        for balloon in balloons[:]:
            balloon['y'] += BALLOON_SPEED  # Move balloon down

            # Draw balloons
            draw_balloon(balloon['x'], balloon['y'], BALLOON_RADIUS, RED)

            # Check if balloon is missed (hits the ground)
            if balloon['y'] > HEIGHT:
                balloons.remove(balloon)  # Remove balloon
                score -= 1  # Decrease score for missed balloon
                balloon_count += 1

            # Check if balloon is hit by hand
            if hand_x is not None and hand_y is not None:
                if is_collision(hand_x, hand_y, balloon['x'], balloon['y']):
                    popping_balloons.append({'x': balloon['x'], 'y': balloon['y'], 'frame': 0})  # Start pop animation
                    pop_sound.play()  # Play pop sound when balloon is destroyed
                    balloons.remove(balloon)  # Remove balloon
                    score += 1  # Increase score for popping balloon
                    balloon_count += 1

        # Animate popping balloons
        for pop in popping_balloons[:]:
            if pop['frame'] < POP_DURATION:
                # Create pop effect: expand and fade out
                radius = int(BALLOON_RADIUS * (1 + pop['frame'] / POP_DURATION))  # Increase size
                color = (255, 0, 0, 255 - int(255 * (pop['frame'] / POP_DURATION)))  # Fade out
                draw_balloon(pop['x'], pop['y'], radius, RED)  # Draw the balloon with updated size
                pop['frame'] += 1
            else:
                popping_balloons.remove(pop)  # Remove after pop animation ends

        # Add new balloon if less than max and balloon count is not reached
        if len(balloons) < 3 and balloon_count < MAX_BALLOONS:
            balloons.append({'x': random.randint(BALLOON_RADIUS, WIDTH - BALLOON_RADIUS), 'y': 0})

        # Display score
        font = pygame.font.SysFont(None, 55)
        score_text = font.render(f'Score: {score}', True, BLACK)
        screen.blit(score_text, (10, 10))

        # Check if max balloons are reached (Level 1 ends)
        if balloon_count >= MAX_BALLOONS:
            game_running = False  # Properly end this game loop

        # Update the game display
        pygame.display.update()

        # Frame rate control
        clock.tick(FPS)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                return

    # End of Level 1 - Show final score and Restart Button
    while not game_running:
        screen.fill(WHITE)
        final_text = font.render(f'Final Score: {score}', True, BLACK)
        screen.blit(final_text, (WIDTH // 2 - 100, HEIGHT // 2 - 30))

        # Display Restart Button
        display_button("Restart Playing", WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 70, GREEN, restart_game)

        # Update display
        pygame.display.update()

        # Check for quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                return

# Start the game
main_game_loop()

# Cleanup after the game ends
cap.release()
pygame.quit()
