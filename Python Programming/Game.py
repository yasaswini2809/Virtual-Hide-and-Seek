import sys
from math import atan2, degrees
import random
import json
import os
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()
window.fullscreen = True

window.title = 'BVRIT Hide and Seek 3D'
window.borderless = False
window.exit_button.visible = True
window.fps_counter.enabled = True

Sky()
DirectionalLight(shadows=True, y=10, z=-10, rotation=(45, -45, 0)).look_at(Vec3(1, -1, 1))
AmbientLight(color=color.rgba(255, 255, 255, 0.8))

score_file = 'bvrit_scoreboard.json'
if not os.path.exists(score_file):
    with open(score_file, 'w') as f:
        json.dump({}, f)

game_started = False
player_name = "Player" # Default player name
scoreboard_panel_ref = None # To hold reference to the scoreboard panel for destruction
scoreboard_text_entities = [] # List to hold references to text entities in scoreboard
scoreboard_ui_entities = [] # List to hold references to other UI entities (buttons) in scoreboard
game_over_image_entity = None # To hold reference to the game over image

# --- UI Elements Initialization ---
splash_image = Entity(model='quad', texture='image.png', scale_x=camera.aspect_ratio, scale_y=1, parent=camera.ui, z=0.01)
next_button_splash = Button(text="Next", scale=(0.3, 0.1), color=color.orange, y=-0.25, parent=camera.ui, z=0)
exit_button_splash = Button(text="Exit", scale=(0.3, 0.1), color=color.red, y=-0.4, parent=camera.ui, z=0)

# Instruction Screen Elements
instruction_panel = Entity(model='quad', texture='image copy 2.png', scale_x=camera.aspect_ratio, scale_y=1, parent=camera.ui, z=0.01, enabled=False, visible=False)
instruction_text = Text(
    "!Welcome to BVRIT Hide and Seek 3D!\n"
    "Your goal is to find the hider hidden somewhere in the campus.\n"
    "Clues are based on the names of different blocks.\n\n"
    "*Controls:*\n"
    "W - Move Forward\n"
    "A - Move Left\n"
    "D - Move Right\n"
    "S - Move Backward\n"
    "Mouse - Look Around\n\n"
    "Are you Ready?",
    parent=camera.ui,
    y=0.1,
    origin=(0,0),
    scale=2,
    color=color.brown,
    background=True,
    z=0,
    enabled=False,
    visible=False
)
ready_button_instruction = Button(text="Ready!", scale=(0.3, 0.1), color=color.blue, y=-0.3, parent=camera.ui, z=0, enabled=False, visible=False)
exit_button_instruction = Button(text="Exit", scale=(0.3, 0.1), color=color.red, y=-0.45, parent=camera.ui, z=0, enabled=False, visible=False)


name_image = Entity(model='quad', texture='image copy 2.png', scale_x=camera.aspect_ratio, scale_y=1, parent=camera.ui, z=0.01, enabled=False, visible=False)
name_input = InputField(default_value="Player", scale=(0.5, 0.1), y=0.1, parent=camera.ui, z=0, enabled=False, visible=False)
name_label = Text("Enter your name:", y=0.25, origin=(0,0), scale=3, parent=camera.ui, z=0, enabled=False, visible=False)

start_game_button = Button(text="Start Game", y=0.0, color=color.blue, scale=(0.5,0.1), parent=camera.ui, z=0, enabled=False, visible=False)
scoreboard_button = Button(text="Scoreboard", y=-0.2, color=color.green, scale=(0.5,0.1), parent=camera.ui, z=0, enabled=False, visible=False)
exit_button_name_screen = Button(text="Exit", y=-0.4, color=color.yellow, scale=(0.5,0.1), parent=camera.ui, z=0, enabled=False, visible=False)

timer_text = Text(text="", position=(.7,.45), scale=1.5, enabled=False, origin=(0.5,0.5))
score_text = Text(text="", position=(.7,.4), scale=1.5, enabled=False, origin=(0.5,0.5))
lives_text = Text(text="", position=(.7,.35), scale=1.5, enabled=False, origin=(0.5,0.5))
clue_text = Text(text="", position=(-.7,.45), scale=1.5, enabled=False, origin=(-0.5,0.5))
hint_text = Text('', position=(0, 0.35), scale=2, origin=(0,0), color=color.orange, enabled=False)
catch_button = Button(text="Catch!", scale=(0.2,0.1), position=(0.7, 0.3), color=color.red, enabled=False, visible=False)


# --- Game Variables ---
campus_blocks = {
    "Library": (10,0,10),
    "Diamond Block": (30,0,5),
    "Fresh Choice": (-10,0,10),
    "Ground": (-20,0,-10),
    "Hostel": (0,0,30),
    "IT Block": (25,0,-15),
    "SethammaBlock": (-25,0,-15),
    "EEE Block": (35,0,20),
    "ECE Block": (-30,0,25),
    "Kala vedika": (20,0,-25),
    "Fast Food": (-20,0,-30)
}

block_clues = {
    "Library": "📚 The place where you find different thoughts of authors.",
    "Diamond Block": "💎 Shines bright like your knowledge.",
    "Fresh Choice": "🍽 A spot to fill your tummy with tasty bites.",
    "Ground": "🏃‍♂ Where legs run wild in games and drills.",
    "Hostel": "🛏 Where the night stories begin and snores echo.",
    "IT Block": "💻 Home of code, bugs, and coffee-fueled nights.",
    "SethammaBlock": "🧠 Logic rules here with lines of code.",
    "EEE Block": "⚡ Buzzes with circuits and voltage.",
    "ECE Block": "📡 Signals fly here silently.",
    "Kala vedika": "🎭 Where talent comes alive on stage.",
    "Fast Food": "🥪 A pitstop for snack lovers."
}


block_entities = {}
label_entities = []
road_entities = []
player = None
hider = None
score = 0
timer = 60
lives = 3
difficulty_speed = 1.0
arrow = None
ground_entity = None
half_hint_given = False
end_message_displayed = False
showing_button = False

# --- Music and SFX Variables ---
game_music = None # Initialize a variable to hold our music object

# NEW: Load SFX here after app = Ursina()
button_click_sfx = None
victory_sfx = None
game_over_sfx = None

try:
    button_click_sfx = Audio('button_click.mp3', loop=False, autoplay=False, volume=1)
    victory_sfx = Audio('victory.mp3', loop=False, autoplay=False, volume=0.5)
    game_over_sfx = Audio('game_over.mp3', loop=False, autoplay=False, volume=1)
except Exception as e:
    print(f"Error loading SFX: {e}. Make sure the sound files exist and are valid audio formats.")

# --- Functions ---

def hide_all_ui_screens():
    splash_image.enabled = False
    splash_image.visible = False
    next_button_splash.enabled = False
    next_button_splash.visible = False
    exit_button_splash.enabled = False
    exit_button_splash.visible = False

    instruction_panel.enabled = False
    instruction_panel.visible = False
    instruction_text.enabled = False
    instruction_text.visible = False
    ready_button_instruction.enabled = False
    ready_button_instruction.visible = False
    exit_button_instruction.enabled = False
    exit_button_instruction.visible = False

    name_image.enabled = False
    name_image.visible = False
    name_input.enabled = False
    name_input.visible = False
    name_label.enabled = False
    name_label.visible = False
    start_game_button.enabled = False
    start_game_button.visible = False
    scoreboard_button.enabled = False
    scoreboard_button.visible = False
    exit_button_name_screen.enabled = False
    exit_button_name_screen.visible = False

    global scoreboard_panel_ref, game_over_image_entity
    if scoreboard_panel_ref:
        destroy(scoreboard_panel_ref)
        scoreboard_panel_ref = None
    for entity in scoreboard_text_entities:
        destroy(entity)
    scoreboard_text_entities.clear()
    for entity in scoreboard_ui_entities:
        destroy(entity)
    scoreboard_ui_entities.clear()
    if game_over_image_entity:
        destroy(game_over_image_entity)
        game_over_image_entity = None


def go_to_instruction_screen():
    if button_click_sfx: button_click_sfx.play() # Play sound
    hide_all_ui_screens()
    instruction_panel.enabled = True
    instruction_panel.visible = True
    instruction_text.enabled = True
    instruction_text.visible = True
    ready_button_instruction.enabled = True
    ready_button_instruction.visible = True
    exit_button_instruction.enabled = True
    exit_button_instruction.visible = True
    mouse.locked = False


def go_to_name_entry():
    if button_click_sfx: button_click_sfx.play() # Play sound
    hide_all_ui_screens()
    name_image.enabled = True
    name_image.visible = True
    name_input.enabled = True
    name_input.visible = True
    name_label.enabled = True
    name_label.visible = True

    start_game_button.enabled = True
    start_game_button.visible = True
    scoreboard_button.enabled = True
    scoreboard_button.visible = True
    exit_button_name_screen.enabled = True
    exit_button_name_screen.visible = True

    mouse.locked = False

def start_game():
    global player_name, game_started, game_music
    if button_click_sfx: button_click_sfx.play() # Play sound
    player_name = name_input.text

    hide_all_ui_screens()

    timer_text.enabled = True
    score_text.enabled = True
    lives_text.enabled = True
    clue_text.enabled = True
    hint_text.enabled = True

    game_started = True
    init_game()

    # --- Start the background music here ---
    if game_music:
        game_music.stop()
    try:
        game_music = Audio('Sneaky Snitch.mp3', loop=True, autoplay=True, volume=1)
    except Exception as e:
        print(f"Error loading music: {e}. Make sure the file exists and is a valid audio format.")


def init_game():
    global player, hider, block_entities, arrow, score, timer, lives, difficulty_speed, half_hint_given, end_message_displayed, ground_entity, road_entities

    score = 0
    timer = 60
    lives = 3
    difficulty_speed = 1.0
    half_hint_given = False
    end_message_displayed = False
    mouse.locked = True

    if player: destroy(player); player = None
    if hider: destroy(hider); hider = None
    if arrow: destroy(arrow); arrow = None
    if ground_entity: destroy(ground_entity); ground_entity = None

    for name, entity in list(block_entities.items()):
        destroy(entity)
    block_entities.clear()
    for label in list(label_entities):
        destroy(label)
    label_entities.clear()

    for road in list(road_entities):
        destroy(road)
    road_entities.clear()

    # --- RECREATE GAME WORLD ENTITIES ---
    ground_entity = Entity(model='plane', texture='grass', scale=(100, 1, 100), collider='box', y=0, z=-0.1)

    player = FirstPersonController(position=(0, 2, -20), origin_y=-.5, speed=5, jump_height=1)
    player.gravity = 0.5

    timer_text.text = f"Time: {int(timer)}"
    score_text.text = f"Score: {score}"
    lives_text.text = f"Lives: {lives}"
    clue_text.text = "Clue: Start moving to get a clue!"

    for name, pos in campus_blocks.items():
        block = Entity(
        model='cube',
        color=color.azure,
        texture='brick',
        collider='box',
        scale=(6, 6, 6),
        position=pos
    )

    # Attach the label as a child of the block
        label = Text(
        text=name,
        parent=block,
        position=(0.75, 0.75, 0.75),
        origin=(0, 0),
        scale=3,
        color=color.white,
        background=True,
        world=True
    )

    block_entities[name] = block
    label_entities.append(label)

    for _ in range(35):
        x, z = random.randint(-45, 45), random.randint(-45, 45)
        Entity(model='cube', color=color.brown, scale=(0.5, 2, 0.5), position=(x, 1, z))
        Entity(model='sphere', color=color.green, scale=2, position=(x, 3, z))

    # --- ROAD CREATION ---
    road_connections = [
        ("Library", "Fresh Choice"),
        ("Library", "Hostel"),
        ("Hostel", "ECE Block"),
        ("Fresh Choice", "Ground"),
        ("Ground", "Fast Food"),
        ("Diamond Block", "IT Block"),
        ("IT Block", "Kala vedika"),
        ("Kala vedika", "SethammaBlock"),
        ("SethammaBlock", "Ground"),
        ("Diamond Block", "EEE Block"),
        ("EEE Block", "Hostel"),
        ("Library", "Diamond Block")
    ]

    road_width = 3
    road_height = 0.05

    for block1_name, block2_name in road_connections:
        pos1 = Vec3(*campus_blocks[block1_name])
        pos2 = Vec3(*campus_blocks[block2_name])

        road_center = (pos1 + pos2) / 2
        road_center.y = road_height

        road_length = distance(pos1, pos2)

        direction = (pos2 - pos1).normalized()
        angle_y = atan2(direction.x, direction.z)
        rotation_y_degrees = degrees(angle_y)

        road = Entity(
            model='cube',
            color=color.black,
            scale=(road_width, road_height, road_length),
            position=road_center,
            rotation_y=rotation_y_degrees,
            collider='box'
        )
        road_entities.append(road)

    arrow = Entity(model='cube', color=color.yellow, scale=(0.3, 1, 0.3), position=player.position + Vec3(0, 3, 0))
    reset_hider()


def get_direction_hint():
    if not hider or not player:
        return "N/A"
    dir_vec = (hider.position - player.position).normalized()
    player_forward = Vec3(player.forward.x, 0, player.forward.z).normalized()
    player_right = Vec3(player.right.x, 0, player.right.z).normalized()
    forward_dot = dir_vec.dot(player_forward)
    right_dot = dir_vec.dot(player_right)
    if abs(forward_dot) > abs(right_dot):
        return "ahead" if forward_dot > 0 else "behind you"
    else:
        return "to your right" if right_dot > 0 else "to your left"

def get_clue():
    if not hider or not player:
        return "🤔"

    player_pos_flat = Vec3(player.x, 0, player.z)
    hider_pos_flat = Vec3(hider.x, 0, hider.z)

    if distance(player_pos_flat, hider_pos_flat) < 5:
        return "🔥 You are very close!"

    closest_block_name = None
    min_distance_to_hider_block = float('inf')

    for block_name, block_pos in campus_blocks.items():
        d = distance(hider_pos_flat, Vec3(*block_pos))
        if d < min_distance_to_hider_block:
            min_distance_to_hider_block = d
            closest_block_name = block_name

    return block_clues.get(closest_block_name, "🤷‍♂ Clue not available.")


def reset_hider():
    global hider, timer, difficulty_speed, half_hint_given, showing_button

    block_name, block_pos = random.choice(list(campus_blocks.items()))
    hider_pos = Vec3(*block_pos) + Vec3(0, 3, 0)

    if hider:
        hider.position = hider_pos
        hider.visible = False
    else:
        hider = Entity(model='sphere', color=color.red, scale=0.7, position=hider_pos, visible=False)

    timer = 60 / difficulty_speed
    difficulty_speed += 0.2
    half_hint_given = False
    showing_button = False
    catch_button.enabled = False
    catch_button.visible = False
    mouse.locked = True


def catch_hider():
    global score
    if hider and player:
        if distance(Vec3(player.x, 0, player.z), Vec3(hider.x, 0, hider.z)) < 5:
            if victory_sfx: victory_sfx.play() # Play victory sound on successful catch
            hider.visible = True
            score += 1
            score_text.text = f"Score: {score}"
            reset_hider()
        else:
            print("You tried to catch, but you're not close enough!")


def save_score():
    with open(score_file, 'r') as f:
        data = json.load(f)

    if player_name in data:
        if isinstance(data[player_name], list):
            data[player_name].append(score)
        else:
            data[player_name] = [data[player_name], score]
    else:
        data[player_name] = [score]

    with open(score_file, 'w') as f:
        json.dump(data, f)

def show_game_over_screen():
    global game_over_image_entity, game_started, game_music

    game_started = False

    # --- Stop music when game is over ---
    if game_music:
        game_music.stop()
    if game_over_sfx: game_over_sfx.play() # Play game over sound

    global player, hider, arrow, block_entities, label_entities, ground_entity, road_entities
    if player: destroy(player); player = None
    if hider: destroy(hider); hider = None
    if arrow: destroy(arrow); arrow = None
    if ground_entity: destroy(ground_entity); ground_entity = None

    for entity_name, entity in list(block_entities.items()):
        destroy(entity)
    block_entities.clear()

    for label in list(label_entities):
        destroy(label)
    label_entities.clear()

    for road in list(road_entities):
        destroy(road)
    road_entities.clear()

    timer_text.enabled = False
    score_text.enabled = False
    lives_text.enabled = False
    clue_text.enabled = False
    hint_text.enabled = False
    catch_button.enabled = False
    catch_button.visible = False
    mouse.locked = False

    if game_over_image_entity:
        game_over_image_entity.visible = True
        game_over_image_entity.enabled = True
    else:
        game_over_image_entity = Entity(
            model='quad',
            texture='image copy.png',
            scale_x=camera.aspect_ratio,
            scale_y=1,
            parent=camera.ui,
            z=-0.05
        )

    invoke(show_scoreboard, delay=3)

def show_scoreboard():
    global scoreboard_panel_ref, game_over_image_entity, scoreboard_text_entities, scoreboard_ui_entities, game_music

    # --- Optionally play a different music for scoreboard or keep silent ---
    if game_music: # If music is playing, stop it for scoreboard
        game_music.stop()
    # You could play a different, more subdued music here if desired:
    # try:
    #     scoreboard_music = Audio('scoreboard_theme.ogg', loop=True, autoplay=True, volume=0.4)
    # except Exception as e:
    #     print(f"Error loading scoreboard music: {e}")


    hide_all_ui_screens()

    if game_over_image_entity:
        game_over_image_entity.visible = False
        game_over_image_entity.enabled = False

    camera.world_position = (0, 0, 0)
    camera.rotation = (0, 0, 0)

    scoreboard_background = Entity(
        model='quad',
        scale=(1.5, 1.8),
        color=color.black66,
        parent=camera.ui,
        z=-0.1
    )
    scoreboard_panel_ref = scoreboard_background

    data = {}
    try:
        with open('bvrit_scoreboard.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading scoreboard file: {e}")
        data = {}

    sorted_scores = sorted(data.items(), key=lambda x: max(x[1]) if x[1] else 0, reverse=True)

    leaderboard_lines = []
    leaderboard_lines.append(f"🏆 Leaderboard 🏆")
    leaderboard_lines.append("")
    if sorted_scores:
        for i, (name, scores) in enumerate(sorted_scores[:10]):
            leaderboard_lines.append(f"{i+1}. {name}: {max(scores) if scores else 0}")
    else:
        leaderboard_lines.append("No scores yet!")

    leaderboard_text = '\n'.join(leaderboard_lines)

    scoreboard_bg_image = Entity(model='quad', texture='image copy.png', scale_x=camera.aspect_ratio, scale_y=1, parent=camera.ui, z=0)
    scoreboard_ui_entities.append(scoreboard_bg_image)

    your_score_text = Text(f"Your Score: {score}", parent=camera.ui, y=0.3, scale=2.5, color=color.rgba(144, 238, 144, 255), origin=(0, 0), z=-0.05)
    scoreboard_text_entities.append(your_score_text)

    leaderboard_display_text = Text(leaderboard_text, parent=camera.ui, y=-0.05, scale=2.5, color=color.white, origin=(0, 0), z=-0.05)
    scoreboard_text_entities.append(leaderboard_display_text)

    play_again_button = Button(
        text="Play Again",
        scale=(0.3, 0.1),
        color=color.green,
        parent=camera.ui,
        y=-0.3,
        x=-0.3,
        z=-0.05
    )
    play_again_button.on_click = reset_game_to_splash_screen # This is assigned later in the binding section
    scoreboard_ui_entities.append(play_again_button)

    scoreboard_exit_button = Button(
        text="Exit Game",
        scale=(0.3, 0.1),
        color=color.red.tint(-0.2),
        parent=camera.ui,
        y=-0.3,
        x=0.35,
        z=-0.05
    )
    scoreboard_exit_button.on_click = application.quit # This is assigned later in the binding section
    scoreboard_ui_entities.append(scoreboard_exit_button)

def reset_game_to_splash_screen():
    global game_started, score, timer, lives, difficulty_speed, half_hint_given, showing_button, end_message_displayed, game_music
    if button_click_sfx: button_click_sfx.play() # Play sound

    # --- Stop music when returning to splash screen ---
    if game_music:
        game_music.stop()

    hide_all_ui_screens()

    score = 0
    timer = 60
    lives = 3
    difficulty_speed = 1.0
    half_hint_given = False
    showing_button = False
    game_started = False
    end_message_displayed = False

    timer_text.enabled = False
    score_text.enabled = False
    lives_text.enabled = False
    clue_text.enabled = False
    hint_text.enabled = False
    catch_button.enabled = False
    catch_button.visible = False

    splash_image.enabled = True
    splash_image.visible = True
    next_button_splash.enabled = True
    next_button_splash.visible = True
    exit_button_splash.enabled = True
    exit_button_splash.visible = True

    mouse.locked = False

def update():
    global timer, score, lives, end_message_displayed, half_hint_given, showing_button

    if not game_started:
        return

    if held_keys['escape']:
        application.quit()

    if not end_message_displayed:
        timer -= time.dt
        timer_text.text = f"Time: {int(timer)}"
        lives_text.text = f"Lives: {lives}"
        clue = get_clue()
        clue_text.text = "Clue: " + (clue if clue is not None else "🤔")

        if clue == "🔥 You are very close!" and not showing_button:
            catch_button.enabled = True
            catch_button.visible = True
            mouse.locked = False
            showing_button = True
        elif clue != "🔥 You are very close!" and showing_button:
            catch_button.enabled = False
            catch_button.visible = False
            mouse.locked = True
            showing_button = False

        if not half_hint_given and timer < (60 / difficulty_speed) / 2:
            hint_text.text = f"Hint: Hider is {get_direction_hint()}"
            half_hint_given = True
        elif half_hint_given:
            hint_text.text = f"Hint: Hider is {get_direction_hint()}"

        game_over = False
        if timer <= 0:
            lives -= 1
            if lives <= 0:
                game_over = True
            else:
                timer = 60 / difficulty_speed
                reset_hider()

        if player and player.y < -5:
            lives -= 1
            player.position = Vec3(0,2,0)
            if lives <= 0:
                game_over = True

        if game_over and not end_message_displayed:
            end_message_displayed = True
            save_score()
            show_game_over_screen()
            return

        if arrow and hider:
            arrow.position = player.position + Vec3(0,3,0)
            direction = (hider.position - player.position).normalized()
            angle_y = atan2(direction.x, direction.z)
            arrow.rotation_y = degrees(angle_y)

        for label in list(label_entities):
            if label and hasattr(label, 'world_position') and label.enabled:
                label.look_at(camera.world_position)
                label.rotation_x = 0
                label.rotation_z = 0

# --- Button Bindings ---
next_button_splash.on_click = go_to_instruction_screen # Changed to go to instruction screen first
exit_button_splash.on_click = application.quit

ready_button_instruction.on_click = go_to_name_entry # From instruction screen to name entry
exit_button_instruction.on_click = application.quit

start_game_button.on_click = start_game
scoreboard_button.on_click = show_scoreboard
exit_button_name_screen.on_click = application.quit
catch_button.on_click = catch_hider


app.run()