# Import
import pstats

from globals import *
import pygame
import random
import datetime
import piece
import coupons
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
import os
import cProfile
import json
import copy

# Init
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=64)

pygame.init()

pygame.mixer.quit()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=64)

icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)

# Game variables
percent = 0
perc_calc = 0
pieces_passed = 0
elapsed_time = 0
animation_state = 0
incorrect_sample = False
pieces = []
increase_time = False
game_state = "notice"
paused = False
combo_stretch = 0
fc = True
rating_show = 0
rating_rotate_dir = True
song_len = 1
piece_queue = []
invisible_pieces = []
render_dist = DEFAULT_RENDER_DISTANCE
song_dir = f"{os.getcwd()}/maps/"
songs = []
song_idx = 0
languages = []
lang_idx = 0
default_lang_idx = 0
offset = 0
latency = 0
hits = 0
use_sfx = True
menu_initted = False
menu_music = True
start_len = 7235
current_scroll_speed = DEFAULT_SCROLL_TIME
lang = "en_US"
locale = {}
cfg = {
    "keybinds": {
        pygame.K_q: "B",
        pygame.K_w: "P",
        pygame.K_o: "W",
        pygame.K_p: "L"
    },
    "lang": "en_US"
}
use_keys = True
SONG_END = pygame.USEREVENT + 1
game_keys = [pygame.K_q, pygame.K_w, pygame.K_o, pygame.K_p]


def save_json():
    global cfg
    with open("options.json", "w", encoding="utf-8") as f:
        cfg["lang"] = lang
        cfg["offset"] = offset
        cfg["use_keys"] = int(use_keys)
        cfg["use_sfx"] = int(use_sfx)
        cfg["menu_music"] = int(menu_music)

        keybinds = copy.copy(cfg["keybinds"])

        # don't save keys as integers
        for i in keybinds:
            val = keybinds[i]
            print(i)
            print(val)
            del cfg["keybinds"][i]
            cfg["keybinds"][pygame.key.name(int(i))] = val

        optstr = json.dumps(cfg, indent=2, separators=(',', ': '))
        f.write(optstr)
        f.close()


# Reload option files
def load_json():
    global locale, cfg, lang, game_keys, use_keys, offset, languages, default_lang_idx, use_sfx, menu_music
    try:
        opt = open(f"options.json", encoding="utf-8")
        cfg = json.loads(opt.read())

        try:
            # Load keybinds
            keybinds_temp = copy.copy(cfg["keybinds"])
            cfg["keybinds"] = {}
            game_keys = []
            for i in keybinds_temp:
                cfg["keybinds"][pygame.key.key_code(i)] = keybinds_temp[i]
                # series of keys used in obstacles
                if keybinds_temp[i] in list("BPWL"):
                    game_keys.append(pygame.key.key_code(i))
        except KeyError:
            cfg["keybinds"] = {pygame.K_q: "B", pygame.K_w: "P", pygame.K_o: "W", pygame.K_p: "L"}

        lang = cfg.get("lang", "en_US")
        use_keys = cfg.get("use_keys", 1)
        offset = cfg.get("offset", 0)

        use_sfx = cfg.get("use_sfx", 1)
        menu_music = cfg.get("menu_music", 1)
        opt.close()
    except FileNotFoundError:
        print("Options file not found.")

    try:
        lfile = open(f"locale/{lang}.json", encoding="utf-8")
        locale = json.loads(lfile.read())
        lfile.close()
    except FileNotFoundError:
        print(f"Could not find locale/{lang}.json, using English locale")
        lfile = open(f"locale/en_US.json", encoding="utf-8")
        locale = json.loads(lfile.read())
        lfile.close()

    try:
        langfile = open("locale/languages.json", encoding="utf-8")
        languages = json.loads(langfile.read())
        lname = [key for key, value in languages.items() if value == lang]
        default_lang_idx = list(languages).index(lname[0])
        lfile.close()
    except FileNotFoundError:
        languages = {"English": "en_US"}
        default_lang_idx = 0


load_json()


# Localization
def localize(string):
    return locale.get(string, string)


# Get song list
print(os.listdir(song_dir))
for f in sorted(os.listdir(song_dir)):
    try:
        has_chart = False
        has_song = False
        for file in os.listdir(f"maps/{f}"):
            if file.endswith(".vib"):
                has_chart = True
            if file.endswith(".mp3") or file.endswith(".ogg"):
                has_song = True
        if has_chart and has_song:
            songs.append(file[:-4])
    except NotADirectoryError:
        pass


# Find the map and music file in the map folder
def get_files_from_map(f):
    map_file = None
    music_file = None
    for file in os.listdir(f"maps/{f}"):
        if file.endswith(".vib") and map_file is None:
            map_file = f"maps/{f}/{file}"
        elif (file.endswith(".mp3") or file.endswith(".ogg")) and music_file is None:
            music_file = f"maps/{f}/{file}"
        if map_file and music_file:
            break
    print((map_file, music_file))
    return (map_file, music_file)


# Sounds
botplay_on = pygame.mixer.Sound("sounds/botplay-on.wav")
botplay_off = pygame.mixer.Sound("sounds/botplay-off.wav")
navigate = pygame.mixer.Sound("sounds/navigate.wav")
confirm = pygame.mixer.Sound("sounds/confirm.wav")
locked = pygame.mixer.Sound("sounds/locked.wav")
hit = pygame.mixer.Sound("sounds/hit-sound.wav")
cb_sound = pygame.mixer.Sound("sounds/cb.wav")
fail_sound = pygame.mixer.Sound("sounds/fail.wav")
song_to_play = "badmans-funk"
song_data = None


# Splashes
splashes = []
with open(asset("splashes.txt"), "r", encoding="utf-8") as f:
    splashes = f.read().split("\n")

# Window title
today = datetime.datetime.today()
if today.month == 12 and today.day == 25:
    pygame.display.set_caption("Vib-Ribbon Minus - Merry Christmas!")
else:
    pygame.display.set_caption("Vib-Ribbon Minus - " + random.choice(splashes))

# PyGame components
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Text
font = pygame.font.Font(localize("noto-sans.otf"), 18)
font_int = pygame.font.Font("noto-sans.otf", 18)
font_medium = pygame.font.Font(localize("noto-sans.otf"), 24)
font_respectable = pygame.font.Font(localize("noto-sans.otf"), 30)
font_respectable_int = pygame.font.Font("noto-sans.otf", 30)
font_large = pygame.font.Font(localize("noto-sans.otf"), 36)
font_huge = pygame.font.Font(localize("noto-sans.otf"), 120)
font_rating = pygame.font.Font("roboto.ttf", 120)

# Images
# I read that convert makes it run faster
obstacles = {
    "block": pygame.image.load("images/obstacles/block_small.png").convert_alpha(),
    "loop": pygame.image.load("images/obstacles/loop_small.png").convert_alpha(),
    "wave": pygame.image.load("images/obstacles/wave_small.png").convert_alpha(),
    "pit": pygame.image.load("images/obstacles/pit_small.png").convert_alpha(),
}
for i in complex_obs:
    try:
        obstacles[i.lower()] = pygame.image.load(f"images/obstacles/{i.lower()}.png").convert_alpha()
    except FileNotFoundError:
        print(f"File not found: {i.lower()}.png")

wheel = pygame.image.load("images/menu/wheel.png").convert_alpha()
star_img = pygame.image.load("images/menu/star.png").convert_alpha()
animations = {}


class Star:
    # this class represents one star on the main menu
    def __init__(self):
        self.x = random.randint(50, SCREEN_WIDTH - 50)
        self.y = random.randint(56, SCREEN_HEIGHT // 2)
        self.increasing = True
        self.size = random.randint(2, 100) / 100
        self.img = star_img

    def step(self):
        if self.increasing:
            self.size += 0.0075
            if self.size >= 1:
                self.increasing = False
        else:
            self.size -= 0.0075
            if self.size <= 0.01:
                self.__init__()
                self.size = 0.02

    def blit(self, scrn):
        self.step()
        sx, sy = self.img.get_size()
        sx *= self.size
        sy *= self.size

        img = pygame.transform.scale(self.img, (sx, sy))
        scrn.blit(img, img.get_rect(center=(self.x, self.y)))


star_list = [Star() for i in range(0,5)]


def load_animation(anim):
    global animations
    animations[anim] = []
    for i in os.listdir(f"images/{anim}"):
        animations[anim].append(pygame.image.load(f"images/{anim}/{i}").convert_alpha())
    print(animations)


load_animation("chibri/rabbit/walking")
load_animation("chibri/frog/walking")
load_animation("chibri/worm/walking")
load_animation("chibri/super/walking")
# Preload images for coupons
coupon_imgs = coupons.load_coupon_images("coupons")


def scrolling_text(scrn: object, l: object, idx: object, **kwargs: object) -> object:
    # create song menu
    division = 30
    distance = 150

    # can be center or right
    anchor = kwargs.get("anchor", "right")
    intl = kwargs.get("intl", False)
    center = SCREEN_HEIGHT // 2
    y_pos = int(kwargs.get("y", center))
    for i, item in enumerate(l):
        y = y_pos + (division * (i - idx)) - 17
        # don't render if not on the screen
        if y > SCREEN_HEIGHT:
            break
        if y < 0:
            continue

        # if selected
        if idx == i:
            option_color = "red"
        else:
            option_color = "white"

        # for hardcoded ordering
        text_item = item
        if item.startswith("@"):
            text_item = " ".join(item.split(" ")[1:]) or item

        # this is mostly for language stuff (renders in noto sans)
        if intl:
            f = font_respectable_int.render(text_item * (anchor == "right"), True, option_color)
        else:
            f = font_respectable.render(text_item * (anchor == "right"), True, option_color)
        
        match anchor:
            case "right":
                rect = f.get_rect(topright=(SCREEN_WIDTH + abs(-(i - idx) ** 2) - distance, y))
            case "center":
                rect = f.get_rect(topcenter=(SCREEN_WIDTH // 2, y))
        scrn.blit(f, rect)


# Process a song
def song():
    global elapsed_time, increase_time, pieces, botplay_queue, score, \
        combo, song_len, piece_queue, percent, perc_calc, render_dist, pieces_passed, \
        menu_initted, miss_streak, hit_streak, form, game_state, incorrect_sample, latency, \
        hits, fc, start_len, modifiers, max_combo, note_amt
    menu_initted = False
    piece_queue = []
    pieces_passed = 0
    modifiers = []
    miss_streak = 0
    hit_streak = 0
    latency = 0
    hits = 0
    form = "RABBIT"
    score = 0
    combo = 0
    max_combo = 0
    fc = True
    parsed = piece.parse_file(song_data[0])
    pieces = parsed[0]
    note_amt = len(pieces)
    render_dist = parsed[1]

    # Modifier text
    if botplay:
        modifiers.append(localize("botplay"))
        botplay_queue = [i.time for i in pieces]

    if not use_keys:
        modifiers.append(localize("wildcard"))

    # This is only used to analyze the start sound
    start = MP3("sounds/start.mp3")

    # Analyze the song that we're about to play (mp3)
    if song_data[1].endswith(".mp3"):
        song_muta = MP3(song_data[1])
        song_len = int(song_muta.info.length * 1000)
        if song_muta.info.sample_rate != 44100:
            incorrect_sample = True
            return "sample rate"

    # Analyze the song that we're about to play (ogg Vorbis)
    elif song_data[1].endswith(".ogg"):
        song_muta = OggVorbis(song_data[1])
        song_len = int(song_muta.info.length * 1000)
        if song_muta.info.sample_rate != 44100:
            incorrect_sample = True
            return "sample rate"

    # DONT REMOVE THIS LINE! It's an oldie but a goodie (also it makes the pause function work correctly)
    song.is_song_active = "Active"

    # Load the songs
    pygame.mixer.music.load("sounds/start.mp3")
    pygame.mixer.music.queue(song_data[1])
    pygame.mixer.music.set_endevent(SONG_END)
    start_len = int(start.info.length * 1000)
    print(start_len)

    # Actually play the start jingle and the song
    pygame.mixer.music.play()
    elapsed_time = start_len * -1
    percent = 0.0
    perc_calc = 0
    increase_time = True
    return "ok"


def convertMillis(milliseconds):
    total_seconds = int(milliseconds / 1000)
    minutes = int(total_seconds / 60)
    seconds = int(total_seconds - minutes * 60)
    return "{}:{:02}".format(minutes, seconds)


def toggle_pause():
    global paused, increase_time
    if paused:
        pygame.mixer.music.unpause()
        if song.is_song_active == "Active":
            increase_time = True
        paused = False

        # Pausing the music clears the queue, so I have to re-add the song to the queue if
        # it is playing the start jingle
        if elapsed_time < 0:
            pygame.mixer.music.queue(song_data[1])
    else:
        pygame.mixer.music.pause()
        increase_time = False
        paused = True


# FPS function
def update_fps() -> object:
    get_fps = clock.get_fps()
    match get_fps:
        case num if num < 15:
            fps_color = "red"
        case num if 15 <= num < 30:
            fps_color = "orange"
        case num if 30 <= num < 60:
            fps_color = "yellow"
        case num if 60 <= num < 120:
            fps_color = "green"
        case _:
            fps_color = "cyan"

    fps = f"FPS: {int(get_fps)}"
    fps_text = font.render(fps, True, pygame.Color(fps_color))
    return fps_text


# Variables

song.is_song_active = "Inactive"
txt = font.render('Version 0.1.0', True, pygame.Color(128, 128, 128))
score = 0
miss_streak = 0
hit_streak = 0
form = "RABBIT"
combo = 0
max_combo = 0
game_started = False
modifiers = []
note_amt = 0
keys_pressed = {
    "B": False,
    "P": False,
    "L": False,
    "W": False,
    "oops": False  # placeholder
}


player_color = "white"

run = 1


def translate_key(k):
    return cfg["keybinds"].get(k, "oops")


# Time judgement function
def judge_time(ms) -> str:
    match abs(ms):
        case m if m <= 18:
            judgement = "MARVELOUS"
            judgement_color = pygame.Color(0, 179, 179)
        case m if m <= 43:
            judgement = "PERFECT"
            judgement_color = pygame.Color(255, 255, 102)
        case m if m <= 76:
            judgement = "GREAT"
            judgement_color = pygame.Color(51, 204, 51)
        case m if m <= 106:
            judgement = "GOOD"
            judgement_color = pygame.Color(0, 102, 204)
        case m if m <= 127:
            judgement = "BAD"
            judgement_color = pygame.Color(204, 51, 255)
        case m if m <= 163:
            judgement = "MISS"
            judgement_color = pygame.Color(153, 0, 0)
        case _:
            judgement = ""
            judgement_color = pygame.Color(0, 179, 179)

    return judgement, judgement_color


def judge_time_text(args) -> str:
    # The text that displays your judgement
    judge_result = font_large.render(args[0], True, args[1])
    # This has nothing to do with score coupons, I just didn't want to rewrite the whole function
    judge_result = coupons.rot_center(judge_result, judge_result.get_rect(), 5 * ((-2 * rating_rotate_dir) + 1))[0]
    return judge_result


def find_id(pl, id):
    try:
        index = [x.id for x in pl].index(id)
    except ValueError:
        index = -1
    return index


def form_check():
    global form, miss_streak, hit_streak
    if hit_streak > 20:
        miss_streak = 0
        hit_streak = 0
        match form:
            case "WORM":
                print("frog")
                return "FROG"
            case "FROG":
                print("rabbit")
                return "RABBIT"
            case "RABBIT":
                print("super")
                return "SUPER"
    if miss_streak > 0 and form == "SUPER":
        miss_streak = 0
        print("super miss")
        return "RABBIT"
    elif miss_streak > 12:
        miss_streak = 0
        match form:
            case "WORM":
                print("fail")
                return "FAIL"
            case "FROG":
                print("worm")
                return "WORM"
            case "RABBIT":
                print("frog")
                return "FROG"
    return form


def remove_bad_pc(p):
    # Returns a boolean
    return not p.time < elapsed_time - HIT_LINE_LOC


def remove_bad_pc_hit(p):
    # Also returns a boolean
    return remove_bad_pc(p) and not p.hit


def playsound(snd):
    if use_sfx:
        pygame.mixer.Sound.play(snd)


def toggle_botplay():
    global botplay
    botplay = not botplay
    if botplay:
        playsound(botplay_on)
    else:
        playsound(botplay_off)


judge_txt = judge_time_text(judge_time(128000))
botplay_queue = []
botplay = False


# Initialize score object
fl = coupons.FlakeList(coupon_imgs, y=60)


def main_loop():
    """
    Some things to note about screens

    1. They must always have an event handler inside of them, or else the game will freeze.
    2. They must return whatever "state" is, unless they are changing screens.
        For example, if state is "game", then game_screen() must return "game" to keep the while loop running.

    """
    global game_state
    while True:
        match game_state:
            case "notice":
                game_state = notice_screen()
            case "title":
                game_state = title_screen()
            case "main_menu":
                game_state = main_menu()
            case "song_select":
                game_state = song_select_screen()
            case "options_menu":
                game_state = options_menu()
            case "language_menu":
                game_state = language_menu()
            case "language_purgatory":
                game_state = language_purgatory()
            case "game":
                game_state = game_screen()
            case "pause":
                game_state = pause_screen()
            case "score":
                game_state = score_screen()
            case "fail":
                game_state = fail_screen()
            case "quit":
                pygame.quit()
                # profiling
                # https://www.youtube.com/watch?v=m_a0fN48Alw
                stats = pstats.Stats(pr)
                stats.sort_stats(pstats.SortKey.TIME)
                stats.print_stats()
                exit()


def blank_screen():
    # A template for screens
    clock.tick(240)
    screen.fill("black")

    # Blits and shits

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"

    pygame.display.update()
    return "blank"


def break_combo():
    global combo, pieces_passed, percent, miss_streak, hit_streak, fc
    fc = False
    pieces_passed += 1
    miss_streak += 1
    hit_streak = 0
    percent = perc_calc / pieces_passed
    if combo > 10 or cfg.get('instant_combo_break_sound', 0):
        playsound(cb_sound)
    combo = 0


last_hit = 0


def calculate_score(j):
    streak = combo
    if combo > 11:
        streak = 11

    if form == "QUEEN":
        base_score = 22
    else:
        base_score = streak + 1

    js = ["BAD", "GOOD", "GREAT", "PERFECT", "MARVELOUS"]
    base_score += js.index(j)

    return base_score



def hit_piece():
    global score, combo, judge_txt, percent, perc_calc, player_color, combo_stretch, rating_rotate_dir, rating_show, \
        pieces_passed, keys_pressed, miss_streak, hit_streak, latency, hits, max_combo, last_hit
    # Hit sound
    playsound(hit)

    # Evaluate piece queue
    good_list = piece_queue
    temp_list = []
    for i in good_list:
        if not i.hit:
            temp_list.append(i)
    good_list = temp_list
    # prevent errors
    if len(good_list) == 0:
        good_list.append(piece.Piece(time=-10000))

    # Piece to evaluate timing of
    the_piece = good_list[0]
    times = [abs(good_list[0].time - elapsed_time)]
    absolute_times = [good_list[0].time, None]
    try:
        # If the next piece's timing window is closer to elapsed_time than the previous piece's timing window, then
        # judge the next piece

        # Distance from elapsed_time
        times.append(abs(good_list[1].time - elapsed_time))
        # Actual time
        absolute_times[1] = good_list[1].time

        if times[0] >= times[1]:  # and (good_list[0].hit or times[1] < 163):
            the_piece = good_list[1]

    except IndexError:
        # If there are no more pieces
        the_piece = good_list[0]

    keys_pressed["oops"] = False

    if the_piece.hit:
        print(f"[HIT] Piece at {the_piece.time} already hit (elapsed_time: {elapsed_time}) (absolute_times[0]: {absolute_times[0]}) (absolute_times[1]: {absolute_times[1]})")
        return

    time_since_last_hit = elapsed_time - last_hit
    last_hit = elapsed_time
    time_judgement = judge_time(the_piece.time - elapsed_time)
    try:
        # Debug stuff
        print(f"[PIECE TIMES] 0: ({good_list[0].time} ms) {times[0]}; 1: ({good_list[1].time} ms) {times[1]}")
        print(f"[STATS] {the_piece.type} at {the_piece.time} ms hit at {elapsed_time} ms; {time_judgement[0] or '(no judgement)'} \
({elapsed_time - the_piece.time} ms); TSLH: {time_since_last_hit} ms")
    except IndexError:
        # if there is no next piece
        print(f"[PIECE TIMES] 0: ({good_list[0].time} ms) {times[0]};")
        print(
            f"[STATS] {the_piece.type} at {the_piece.time} ms hit at {elapsed_time} ms; {time_judgement[0] or '(no judgement)'} \
({elapsed_time - the_piece.time} ms); TSLH: {time_since_last_hit} ms")

    if time_judgement[0] != "":
        the_piece_idx = find_id(piece_queue, the_piece.id)
        print(f"[ID] Piece at {the_piece.time} has an id of {the_piece_idx}")

        # Check if correct keys are pressed
        if piece_queue[the_piece_idx].keys == keys_pressed or botplay or not use_keys:
            piece_queue[the_piece_idx].hit = True

            match time_judgement[0]:
                case "MARVELOUS":
                    perc_calc += 100
                    pieces_passed += 1
                    hit_streak += 1
                case "PERFECT":
                    perc_calc += 95
                    pieces_passed += 1
                    hit_streak += 1
                case "GREAT":
                    perc_calc += 75
                    pieces_passed += 1
                    hit_streak += 1
                case "GOOD":
                    perc_calc += 60
                    pieces_passed += 1
                    hit_streak += 1
                case "BAD":
                    perc_calc += 50
                    pieces_passed += 1
                    hit_streak += 1
                case "MISS":
                    break_combo()
                case _:
                    pass

            rating_show = 100
            if pieces_passed > 0:
                percent = perc_calc / pieces_passed
            if time_judgement[0] != "":
                # make it ready for average
                latency_temp = latency
                latency_temp *= hits
                # add numbers to latency
                latency_temp += (the_piece.time - elapsed_time)
                hits += 1
                # divide to get average
                latency_temp /= hits
                latency = latency_temp

            if time_judgement[0] not in ["MISS", ""]:
                score += calculate_score(time_judgement[0])
                combo += 1
                if combo > max_combo:
                    max_combo += 1
                combo_stretch = 60
                rating_rotate_dir = not rating_rotate_dir


            judge_txt = judge_time_text(time_judgement)


############################################################

# MENU

menu_options = [
    localize("menu_play_song"),
    localize("menu_options"),
    localize("menu_tutorial"),
    localize("menu_back")
]
pause_options = [
    localize("pause_resume"),
    localize("pause_try_again"),
    localize("pause_quit_to_menu"),
    localize("pause_quit_game")
]
options_options = [
    localize("options_language"),
    localize("options_music"),
    localize("options_sfx"),
    localize("menu_back")
]
selected_option = 0


# pre-game loading
def title_pre_screen():
    global game_started, menu_initted, menu_music
    menu_initted = False
    print(pygame.key.get_pressed())
    if menu_music:
        pygame.mixer.music.load("sounds/theme.mp3")
        pygame.mixer.music.play(-1)
    game_started = True


def init_menu():
    global menu_initted, menu_music, game_started, selected_option
    game_started = False
    if menu_music:
        pygame.mixer.music.load("sounds/menu.mp3")
        pygame.mixer.music.play(-1)
    selected_option = 0
    menu_initted = True


notice_lines = [
    (font_huge.render("NOTICE", True, "white"), 150),
    (font_medium.render("This fangame is and always will be free and open-source.", True, "white"), 230),
    (font_medium.render("If you have spent money on anything related to Vib-Ribbon Minus,", True, "white"), 260),
    (font_medium.render("YOU HAVE BEEN SCAMMED.", True, "white"), 290),
    (font_medium.render("We are not affiliated with the creators of Vib-Ribbon.", True, "white"), 350),
    (font_medium.render("Support the original release by buying Vib-Ribbon for the PS3 on PSN.", True, "white"), 410),
    (font_medium.render("Press any key to dismiss", True, "white"), 500),
    (font_medium.render("Press ESC to dismiss permanently", True, "white"), 530),
]


def notice_screen():
    # Hey, you! We don't want any money from this!
    clock.tick(240)
    screen.fill("black")

    if cfg.get("dismiss_notice", 0):
        return "title"

    # God, I wish PyGame supported newlines
    for i in notice_lines:
        screen.blit(i[0], i[0].get_rect(center=(SCREEN_WIDTH // 2, i[1])))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                cfg["dismiss_notice"] = 1
                save_json()
            return "title"

    pygame.display.update()
    return "notice"


# TITLE


def title_screen():
    global fl, percent
    if not game_started:
        title_pre_screen()
    clock.tick(240)
    screen.fill((0, 0, 0))

    screen.blit(update_fps(), (10, 10))
    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))

    title_text = font_large.render("vib-ribbon minus", True, "white")
    # The subtitle text is for readability in other languages.
    subtitle_text = font.render(localize("subtitle"), True, "white")
    caption_text = font_medium.render(localize("start_msg"), True, "white")

    screen.blit(title_text, (title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))))
    screen.blit(subtitle_text, (subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 150))))
    screen.blit(caption_text, (caption_text.get_rect(center=(SCREEN_WIDTH // 2, 480))))

    # Coupons
    fl.change_y(360)
    fl.change(score)
    fl.blit(pygame.time.get_ticks(), screen)

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                playsound(confirm)
                return "main_menu"
            if event.key == pygame.K_ESCAPE:
                return "quit"
        if event.type == pygame.QUIT:
            return "quit"

    pygame.display.update()
    return "title"


menu_anim = 0
zzz_alpha = 255

ribbon_chibri_1 = pygame.image.load("images/menu/ribbon_chibri_1.png").convert_alpha()
ribbon_chibri_2 = pygame.image.load("images/menu/ribbon_chibri_2.png").convert_alpha()
zzz = pygame.image.load("images/menu/zzz.png").convert_alpha()


def chibri_bg():
    global menu_anim, ribbon_chibri_1, ribbon_chibri_2, zzz_alpha
    menu_anim += 1

    if menu_anim > 600:
        menu_anim = 0
    elif menu_anim < 300:
        zzz_alpha = 255
    match menu_anim:
        case menu_anim if menu_anim > 300:
            frame = ribbon_chibri_1
            screen.blit(zzz, zzz.get_rect(center=(320, SCREEN_HEIGHT - 220)))
            zzz_alpha -= 1
            zzz.set_alpha(zzz_alpha)
        case _:
            frame = ribbon_chibri_2
    if SCREEN_WIDTH != 1280:
        # PyGame is like the PlayStation 1 in that it doesn't have decimal pixel locations
        frame = pygame.transform.scale(frame, (SCREEN_WIDTH, int(SCREEN_HEIGHT * (208/720))))
    screen.blit(frame, frame.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200)))
    for i in star_list:
        i.blit(screen)


def main_menu():
    global SCREEN_WIDTH, SCREEN_HEIGHT, fl, selected_option
    clock.tick(240)
    screen.fill("black")
    if not menu_initted:
        init_menu()
    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))

    # Add Chibri to the menu
    chibri_bg()

    for i in range(0, len(menu_options)):
        if i == selected_option:
            color = "red"
        else:
            color = "white"
        s = menu_options[i]
        t = font_large.render(s, True, pygame.Color(color))
        screen.blit(t, t.get_rect(topright=((SCREEN_WIDTH - 120), (SCREEN_HEIGHT // 2) + (i * 60) - 60)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_RETURN:
                    playsound(confirm)
                    match selected_option:
                        case 0:
                            selected_option = 0
                            return "song_select"
                        case 1:
                            selected_option = 0
                            return "options_menu"
                        case 2:
                            pygame.mixer.Sound.stop(confirm)
                            playsound(locked)
                            return "main_menu"
                        case 3:
                            selected_option = 0
                            return "title"
                        case _:
                            selected_option = 0
                            return "title"
                case pygame.K_ESCAPE:
                    return "title"
                case pygame.K_UP:
                    playsound(navigate)
                    if selected_option == 0:
                        selected_option = len(menu_options) - 1
                    else:
                        selected_option -= 1
                case pygame.K_DOWN:
                    playsound(navigate)
                    if selected_option > len(menu_options) - 2:
                        selected_option = 0
                    else:
                        selected_option += 1
                case pygame.K_l:
                    playsound(confirm)
                    load_json()

    pygame.display.update()
    return "main_menu"


# SONG SELECT
def song_select_screen():
    global song_idx, song_to_play, game_started, song_data, increase_time, incorrect_sample, menu_initted

    if not menu_initted:
        init_menu()

    clock.tick(240)
    screen.fill("black")

    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))
    chibri_bg()
    scrolling_text(screen, songs, song_idx)

    screen.blit(wheel, wheel.get_rect(center=(SCREEN_WIDTH - 60, SCREEN_HEIGHT // 2)))

    if botplay:
        bp_txt = font_respectable.render(localize("botplay"), True, "white")
        screen.blit(bp_txt, bp_txt.get_rect(bottomleft=(10, SCREEN_HEIGHT - 10)))

    if incorrect_sample:
        is_txt = font.render(localize("incorrect_sample"), True, "white")
        screen.blit(is_txt, is_txt.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            incorrect_sample = False
            match event.key:
                case pygame.K_UP:
                    if song_idx != 0:
                        song_idx -= 1
                        playsound(navigate)
                case pygame.K_DOWN:
                    if song_idx != len(songs) - 1:
                        song_idx += 1
                        playsound(navigate)
                case pygame.K_RETURN:
                    song_to_play = songs[song_idx]
                    song_data = get_files_from_map(song_to_play)
                    playsound(confirm)
                    if song() == "sample rate":
                        menu_initted = True
                        increase_time = False
                        incorrect_sample = True
                        return "song_select"
                    return "game"
                case pygame.K_ESCAPE:
                    playsound(confirm)
                    return "main_menu"
                case pygame.K_b:
                    toggle_botplay()
        if event.type == pygame.MOUSEBUTTONDOWN:
            incorrect_sample = False
            if event.button == 4:
                if song_idx != 0:
                    song_idx -= 1
                    playsound(navigate)
            elif event.button == 5:
                if song_idx != len(songs) - 1:
                    song_idx += 1
                    playsound(navigate)

    pygame.display.update()
    return "song_select"


def options_menu():
    global SCREEN_WIDTH, SCREEN_HEIGHT, fl, selected_option, menu_music, lang_idx, use_sfx
    clock.tick(240)
    screen.fill("black")
    if not menu_initted:
        init_menu()
    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))

    chibri_bg()

    for i in range(0, len(options_options)):
        if i == selected_option:
            color = "red"
        else:
            color = "white"
        s = options_options[i]
        t = font_large.render(s, True, pygame.Color(color))
        screen.blit(t, t.get_rect(topright=((SCREEN_WIDTH - 120), (SCREEN_HEIGHT // 2) + (i * 60) - 60)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_RETURN:
                    playsound(confirm)
                    # Options selection
                    match selected_option:
                        case 0:
                            lang_idx = default_lang_idx
                            return "language_menu"
                        case 1:
                            if menu_music:
                                menu_music = False
                                pygame.mixer.music.stop()
                            else:
                                menu_music = True
                                pygame.mixer.music.load("sounds/menu.mp3")
                                pygame.mixer.music.play(-1)
                        case 2:
                            use_sfx = not use_sfx
                        case _:
                            selected_option = 0
                            return "main_menu"

                case pygame.K_ESCAPE:
                    playsound(confirm)
                    selected_option = 0
                    return "main_menu"

                case pygame.K_UP:
                    playsound(navigate)
                    if selected_option == 0:
                        selected_option = len(options_options) - 1
                    else:
                        selected_option -= 1

                case pygame.K_DOWN:
                    playsound(navigate)
                    if selected_option > len(options_options) - 2:
                        selected_option = 0
                    else:
                        selected_option += 1

    pygame.display.update()
    return "options_menu"


def language_menu():
    global lang_idx, lang
    clock.tick(240)
    screen.fill("black")

    # intl=True means to render the text in Noto sans
    scrolling_text(screen, list(languages), lang_idx, intl=True)
    screen.blit(wheel, wheel.get_rect(center=(SCREEN_WIDTH - 60, SCREEN_HEIGHT // 2)))
    chibri_bg()

    temp_txt = font.render(
        "Version 0.1.0 may have unfinished locales. However, the game should fully support English, and partially"
        " Japanese at this time.",
        True, "white")
    screen.blit(temp_txt, temp_txt.get_rect(bottomleft=(10, SCREEN_HEIGHT - 10)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_UP:
                    if lang_idx != 0:
                        lang_idx -= 1
                        playsound(navigate)
                case pygame.K_DOWN:
                    if lang_idx != len(languages) - 1:
                        lang_idx += 1
                        playsound(navigate)
                case pygame.K_RETURN:
                    playsound(confirm)
                    lang = languages[list(languages)[lang_idx]]
                    save_json()
                    load_json()
                    return "language_purgatory"
                case pygame.K_ESCAPE:
                    playsound(confirm)
                    return "options_menu"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                if lang_idx != 0:
                    lang_idx -= 1
                    playsound(navigate)
            elif event.button == 5:
                if lang_idx != len(languages) - 1:
                    lang_idx += 1
                    playsound(navigate)

    pygame.display.update()
    return "language_menu"


def language_purgatory():
    # This is the "changes have been saved, please restart your game" screen.
    clock.tick(240)
    screen.fill("black")

    restart_text = font_int.render(localize("restart_game"), True, "white")
    screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            return "quit"

    pygame.display.update()
    return "language_purgatory"


def pause_screen():
    global SCREEN_WIDTH, SCREEN_HEIGHT, fl, selected_option
    clock.tick(240)
    screen.fill((0, 0, 0))

    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))
    paused_text = font_large.render(localize("pause_text"), True, pygame.Color(255, 255, 255))
    screen.blit(paused_text, paused_text.get_rect(center=(SCREEN_WIDTH // 2, 50)))

    # Coupons
    fl.change_y(50)
    fl.change(score)
    fl.blit(pygame.time.get_ticks(), screen)

    for i in range(0, len(pause_options)):
        if i == selected_option:
            s = f"> {pause_options[i]} <"
        else:
            s = pause_options[i]
        t = font.render(s, True, pygame.Color((255, 255, 255)))
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + (i * 30))))

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_ESCAPE:
                    toggle_pause()
                    return "game"
                case pygame.K_RETURN:
                    playsound(confirm)
                    match selected_option:
                        case 0:
                            toggle_pause()
                            return "game"
                        case 1:
                            toggle_pause()
                            song()
                            return "game"
                        case 2:
                            toggle_pause()
                            pygame.mixer.music.stop()
                            return "song_select"
                        case 3:
                            return "quit"
                        case _:
                            return "quit"
                case pygame.K_UP:
                    playsound(navigate)
                    if selected_option == 0:
                        selected_option = len(pause_options) - 1
                    else:
                        selected_option -= 1
                case pygame.K_DOWN:
                    playsound(navigate)
                    if selected_option > len(pause_options) - 2:
                        selected_option = 0
                    else:
                        selected_option += 1
        if event.type == pygame.QUIT:
            return "quit"

    if selected_option > 3:
        selected_option = 0

    pygame.display.update()
    return "pause"


# GAME


def game_screen():
    global HIT_LINE_LOC, RIBBON_LOC, player_color, score, combo, elapsed_time, judge_txt, pieces, combo, piece_queue, \
        combo_stretch, rating_rotate_dir, rating_show, cfg, keys_pressed, miss_streak, animation_state, selected_option, \
        invisible_pieces, form, hit_streak, current_scroll_speed
    clock.tick(240)
    # Draw objects
    screen.fill((0, 0, 0))

    # Hit line
    pygame.draw.line(screen, (128, 128, 128), (HIT_LINE_LOC, 0), (HIT_LINE_LOC, SCREEN_HEIGHT), 3)

    # Ribbon
    pygame.draw.line(screen, (255, 255, 255), (0, RIBBON_LOC), (SCREEN_WIDTH, RIBBON_LOC), 3)

    # Pieces
    if len(piece_queue) < render_dist and len(pieces) > 0:
        # Fill piece queue
        piece_queue.append(pieces[0])
        del pieces[0]

    # fp = first piece
    fp = True
    for pc in piece_queue:
        if fp:
            # Set the scroll speed to the first piece's scroll speed
            current_scroll_speed = pc.scroll_time
            fp = False
        x = pc.x(elapsed_time)
        pc.blit(elapsed_time, RIBBON_LOC, obstacles, screen)
        pygame.draw.line(screen, (128, 128, 128), (x, RIBBON_LOC), (x, SCREEN_HEIGHT), 2)

    if len(piece_queue) > 0:
        if piece_queue[0].time < elapsed_time - HIT_LINE_LOC:
            if not piece_queue[0].hit and piece_queue[0].time != -10000:
                break_combo()
            del piece_queue[0]

    # Animation
    if animation_state >= 3999:
        animation_state = 0
    try:
        anim_img = animations[f"chibri/{form.lower()}/walking"][animation_state // 1000]
        screen.blit(anim_img, anim_img.get_rect(bottomright=(HIT_LINE_LOC, RIBBON_LOC)))
        animation_state += 30000 // current_scroll_speed
        # print(f'{30000 // current_scroll_speed} = 300 / {current_scroll_speed}')
    except IndexError:
        pass
        # print(30000 // DEFAULT_SCROLL_TIME)

    # Coupons
    fl.change_y(60)
    fl.change(score)
    fl.blit(pygame.time.get_ticks(), screen)

    # Text
    screen.blit(update_fps(), (10, 10))
    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))

    # Botplay hitting
    if botplay and len(botplay_queue):
        if botplay_queue[0] <= elapsed_time:
            hit_piece()
            del botplay_queue[0]

    form = form_check()
    if form == "FAIL":
        pygame.mixer.music.stop()
        playsound(fail_sound)
        selected_option = 0
        return "fail"

    # Event checks
    for event in pygame.event.get():

        # Key pressed
        if event.type == pygame.KEYDOWN:
            match event.key:
                case k if k in game_keys:
                    if not botplay:
                        print(translate_key(event.key))
                        keys_pressed[translate_key(event.key)] = True
                        player_color = "red"
                        hit_piece()

                case pygame.K_ESCAPE:
                    toggle_pause()
                    return "pause"

                case pygame.K_SPACE:
                    song()

                # Temporary Debug Keys
                # case pygame.K_UP:
                # elapsed_time += 10
                # case pygame.K_DOWN:
                # elapsed_time -= 10
                # case pygame.K_LEFT:
                # elapsed_time -= 1
                # case pygame.K_RIGHT:
                # elapsed_time += 1

        """case pygame.K_i:
            RIBBON_LOC -= 10
        case pygame.K_j:
            HIT_LINE_LOC -= 10
        case pygame.K_k:
            RIBBON_LOC += 10
        case pygame.K_l:
            HIT_LINE_LOC += 10
        """
        if event.type == pygame.KEYUP:
            player_color = "white"
            keys_pressed[translate_key(event.key)] = False

        if event.type == SONG_END:
            if elapsed_time < 0:
                # if the song hasn't actually started yet
                print(elapsed_time)
                #pygame.mixer.music.rewind()
                print(elapsed_time)
                elapsed_time = offset
        if event.type == pygame.QUIT:
            return "quit"

    # Success theme
    if elapsed_time >= song_len:
        pygame.mixer.music.load("sounds/success.mp3")
        pygame.mixer.music.play()
        return "score"

    time_left_ms = song_len - elapsed_time

    # Debug Info
    # elapsed_time
    ms_txt = font.render(str(elapsed_time), True, pygame.Color(128, 128, 128))
    # Song enabled?
    song_txt = font.render(f"Song: {song.is_song_active}", True, pygame.Color(128, 0, 128))
    # Amount of pieces loaded
    length_txt = font.render(f"{len(pieces)} pieces remaining", True, pygame.Color(128, 0, 128))
    queue_txt = font.render(f"{len(piece_queue)} pieces in queue", True, pygame.Color(128, 0, 128))
    # Score
    score_txt = font_respectable.render(str(score), True, pygame.Color(255, 255, 255))
    # Combo
    combo_txt = font_large.render(f"{combo}x", True, pygame.Color(255, 255, 255))
    # Form text
    debug_form_txt = font.render(f"Miss streak: {miss_streak}, Hit streak: {hit_streak}, Form: {localize(form)}, Latency: \
{round(latency, 2)} ms", True, pygame.Color(128, 128, 128))


    # Combo stretching
    if combo_stretch:
        scale_factor = (combo_stretch / 100) + 1
        combo_txt = pygame.transform.scale(combo_txt, (
            combo_txt.get_width() * scale_factor, combo_txt.get_height() * scale_factor))
        combo_stretch -= 2

    # Accuracy
    percent_txt = font_respectable.render(f"{round(percent, 2)}%", True, pygame.Color(255, 255, 255))
    # Time remaining
    time_remaining_txt = font.render(convertMillis(time_left_ms), True, pygame.Color(128, 128, 128))

    # screen.blit(ms_txt, (ms_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10))))
    screen.blit(percent_txt, (percent_txt.get_rect(topright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 40))))
    # screen.blit(song_txt, (10, 34))
    # screen.blit(length_txt, (10, 55))
    # screen.blit(queue_txt, (10, 78))

    # Timer that, if above zero, shows the judgement on the screen
    if rating_show:
        screen.blit(judge_txt, (judge_txt.get_rect(center=(SCREEN_WIDTH // 2, 100))))
        rating_show -= 1

    screen.blit(score_txt, (score_txt.get_rect(center=(SCREEN_WIDTH // 2, 30))))
    # screen.blit(debug_form_txt, (debug_form_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))))

    sideform = font_medium.render(f'Form: {localize(form)}', True, pygame.Color(255, 255, 255))
    sidemiss = font_medium.render(f'Miss Streak: {miss_streak}', True, pygame.Color(255, 255, 255))
    sidelatency = font_medium.render(f'Latency: {round(latency, 2)}', True, pygame.Color(255, 255, 255))
    screen.blit(sideform, (sideform.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 110))))
    screen.blit(sidemiss, (sidemiss.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 80))))
    screen.blit(sidelatency, (sidelatency.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 50))))

    screen.blit(combo_txt, combo_txt.get_rect(bottomleft=(10, SCREEN_HEIGHT - 5)))
    screen.blit(time_remaining_txt, (time_remaining_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 75))))

    if len(modifiers):
        # Modifier text
        botplay_text = font_respectable.render(", ".join(modifiers), True, pygame.Color((128, 128, 128)))
        screen.blit(botplay_text, (botplay_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))))

    if increase_time:
        if cfg.get('sync_with_music', False):
            if elapsed_time < 0:
                elapsed_time = pygame.mixer.music.get_pos() - start_len
            else:
                elapsed_time = pygame.mixer.music.get_pos() + offset
                # get_pos returns a value less than zero when the music has stopped
                if elapsed_time < 0:
                    pygame.mixer.music.load("sounds/success.mp3")
                    pygame.mixer.music.play()
                    return "score"
        else:
            elapsed_time += clock.get_time()

    # Display frame
    pygame.display.update()
    return "game"


# SCORE
def score_screen():
    global score, percent, perc_calc, pieces_passed, botplay
    clock.tick(240)
    screen.fill("black")

    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))
    grade = ""

    match percent:
        case percent if percent == 0:
            grade = "N/A"
            grade_color = (255, 255, 255)
        case percent if percent < 50:
            grade = "F"
            grade_color = (255, 255, 255)
        case percent if percent < 60:
            grade = "E"
            grade_color = (132, 0, 16)
        case percent if percent < 70:
            grade = "D"
            grade_color = (255, 0, 31)
        case percent if percent < 80:
            grade = "C"
            grade_color = (255, 127, 0)
        case percent if percent < 90:
            grade = "B"
            grade_color = (156, 205, 9)
        case percent if percent < 95:
            grade = "A"
            grade_color = (10, 132, 81)
        case percent if percent < 98:
            grade = "S"
            grade_color = (248, 223, 95)
        case percent if percent < 99:
            grade = "SS"
            grade_color = (228, 191, 0)
        case percent if percent < 100:
            grade = "SSS"
            grade_color = (182, 152, 0)
        case percent if percent >= 100:
            grade = "V"
            grade_color = (102, 51, 153)

    if not botplay:
        match percent:
            case percent if percent < 60:
                paused_text = font_large.render(localize("win_50"), True, pygame.Color(255, 255, 255))
            case percent if percent < 70:
                paused_text = font_large.render(localize("win_60"), True, pygame.Color(255, 255, 255))
            case percent if percent < 80:
                paused_text = font_large.render(localize("win_70"), True, pygame.Color(255, 255, 255))
            case percent if percent < 90:
                paused_text = font_large.render(localize("win_80"), True, pygame.Color(255, 255, 255))
            case percent if percent < 90.1:
                paused_text = font_large.render(localize("win_90_close"), True, pygame.Color(255, 255, 255))
            case percent if percent < 95:
                paused_text = font_large.render(localize("win_90"), True, pygame.Color(255, 255, 255))
            case percent if percent < 95.1:
                paused_text = font_large.render(localize("win_95_close"), True, pygame.Color(255, 255, 255))
            case percent if percent < 99:
                paused_text = font_large.render(localize("win_95"), True, pygame.Color(255, 255, 255))
            case percent if percent < 100:
                paused_text = font_large.render(localize("win_99"), True, pygame.Color(255, 255, 255))
            case percent if percent >= 100:
                paused_text = font_large.render(localize("win_100"), True, pygame.Color(255, 255, 255))
    else:
        paused_text = font_large.render(localize("win_bot"), True, pygame.Color(255, 255, 255))

    screen.blit(paused_text, paused_text.get_rect(center=(SCREEN_WIDTH // 2, 50)))

    score_text = font_respectable.render(f"{localize('score')}: {score}{localize('pts')}", True,
                                         pygame.Color(255, 255, 255))
    percent_text = font_respectable.render(f"{round(percent, 2)}%", True, pygame.Color(255, 255, 255))
    combo_text = font_respectable.render(f"{localize('combo')}: {max_combo}x/{note_amt}x {'(FC)' * fc}", True, "white")
    grade_text = font_rating.render(f"{grade}", True, pygame.Color(grade_color))

    screen.blit(grade_text, grade_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))
    screen.blit(percent_text, percent_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)))
    screen.blit(combo_text, combo_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))


    caption_text = font_medium.render(localize("win_screen_play_again"), True, "white")
    quit_text = font_medium.render(localize("win_screen_menu"), True, "white")
    screen.blit(caption_text, (caption_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))))
    screen.blit(quit_text, (quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70))))

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_RETURN:
                    song()
                    return "game"
                case pygame.K_ESCAPE:
                    return "song_select"
                # case pygame.K_w:
                #     percent -= .1
                # case pygame.K_s:
                #     percent += .1
                # case pygame.K_UP:
                #     percent -= 1
                # case pygame.K_DOWN:
                #     percent += 1
                # case pygame.K_SPACE:
                #     percent = 100
        if event.type == pygame.QUIT:
            return "quit"

    pygame.display.update()
    return "score"


fail_options = [
    localize("pause_try_again"),
    localize("pause_quit_to_menu"),
    localize("pause_quit_game")
]


# GAME OVER
def fail_screen():
    global fail_sound, miss_streak, selected_option
    clock.tick(240)
    screen.fill("black")

    fail_txt = font_respectable.render(localize("game_over"), True, pygame.Color("white"))
    restart_txt = font.render(f"{localize('score')}: {score}{localize('pts')}", True, pygame.Color("white"))

    screen.blit(txt, (txt.get_rect(topright=(SCREEN_WIDTH - 10, 10))))
    screen.blit(fail_txt, fail_txt.get_rect(center=(SCREEN_WIDTH // 2, 50)))
    screen.blit(restart_txt, restart_txt.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) - 70)))

    for i in range(0, len(fail_options)):
        if i == selected_option:
            s = f"> {fail_options[i]} <"
        else:
            s = fail_options[i]
        t = font.render(s, True, pygame.Color((255, 255, 255)))
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + (i * 30))))

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_ESCAPE:
                    song()
                    return "game"
                case pygame.K_UP:
                    playsound(navigate)
                    if selected_option == 0:
                        selected_option = len(fail_options) - 1
                    else:
                        selected_option -= 1
                case pygame.K_DOWN:
                    playsound(navigate)
                    if selected_option > len(fail_options) - 2:
                        selected_option = 0
                    else:
                        selected_option += 1
                case pygame.K_RETURN:
                    playsound(confirm)
                    match selected_option:
                        case 0:
                            song()
                            return "game"
                        case 1:
                            return "song_select"
                        case 2:
                            return "quit"
                        case _:
                            return "quit"

        if event.type == pygame.QUIT:
            return "quit"

    pygame.display.update()
    return "fail"


with cProfile.Profile() as pr:
    main_loop()

############################################################
