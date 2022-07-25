SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
HIT_LINE_LOC = 150  # x of judgement line
RIBBON_LOC = 500
DEFAULT_SCROLL_TIME = 1000
MOVEMENT_AREA = SCREEN_WIDTH - HIT_LINE_LOC
DEFAULT_RENDER_DISTANCE = 15
# Obstacle shorthand names
obs_shorthand = {
    'B': 'block',
    'L': 'loop',
    'P': 'pit',
    'W': 'wave',
}

complex_obs = ['BP', 'BL', 'BW', 'PL', 'PW', 'LW']
for i in complex_obs:
    obs_shorthand[i] = i.lower()