import urcparse
import globalvars
from pygame import transform


def invert_axis(axis, num):
    new_axis = axis
    if num > 0:
        return axis
    if "bottom" in axis:
        new_axis = axis.replace("bottom", "top")
    elif "top" in axis:
        new_axis = axis.replace("top", "bottom")
    return new_axis


def get_keys(p):
    temp = {"B": False, "P": False, "L": False, "W": False, "oops": False}

    for i in list(p):
        temp[i] = True

    return temp


class InvisiblePiece:
    def __init__(self, **kwargs):
        self.type = kwargs.get("type", "scroll")
        self.time = int(kwargs.get("time", 0))
        self.value = kwargs.get("value", 1000)


class Piece:
    def __init__(self, **kwargs):
        self.type = kwargs.get("type", "B")
        self.time = int(kwargs.get("time", 1000))
        # Scroll duration is in ms
        # v = d/t px/ms (where d is distance in px and c is scroll time in ms)
        self.scroll_time = int(kwargs.get("scroll_time", globalvars.DEFAULT_SCROLL_TIME))
        self.render_distance = int(kwargs.get("render_distance", globalvars.DEFAULT_RENDER_DISTANCE))
        self.hit = kwargs.get("hit", False)
        self.id = kwargs.get("id", 0)
        self.flip = bool(kwargs.get("flip", False))
        self.keys = kwargs.get("keys")
        self.scale = 1
        self.img = None
        self.broken = False

    def x(self, elapsed) -> float:
        # globalvars.MOVEMENT_AREA = SCREEN WIDTH - HIT LINE X
        # from main import globalvars.HIT_LINE_LOC
        return (((self.time - elapsed) / self.scroll_time) * globalvars.MOVEMENT_AREA) + globalvars.HIT_LINE_LOC

    def y(self, ribbon) -> int:
        match self.type.upper():
            case 'B' | 'L' | 'BP' | 'BW' | 'LW' | 'PL':
                y_offset = 2
            case 'P' | 'PW':
                y_offset = -1
            case _:
                y_offset = 0
        return ribbon + y_offset

    # Blit obstacles to the screen
    def blit(self, elapsed, ribbon, imgs, scrn):
        x = self.x(elapsed)

        # BL is offset by 12 px in its image file, so we need to offset it here, too
        if self.type.upper() == "BL":
            x -= 12

        if globalvars.SCREEN_WIDTH <= x or x < 0:
            # don't even bother drawing if it isn't on the screen
            return

        obs_type = self.type.upper()

        # Keep that DUMB DUMB SNAKEY from TROLLING all our images with OPACITY
        if self.img is None:
            type_img = imgs[globalvars.obs_shorthand[obs_type]].copy()
            self.img = type_img
        else:
            type_img = self.img
        default_width = type_img.get_width()
        default_height = type_img.get_height()

        if self.hit:
            type_img.set_alpha(128)

        # Flip
        if self.flip:
            # For some reason, multiplying this by -1 made it flip CORRECTLY
            self.scale = ((((x - globalvars.HIT_LINE_LOC) / globalvars.MOVEMENT_AREA) * 2) - 1) * -1
            if self.scale < 0:
                type_img = transform.rotate(type_img, 180)
            type_img = transform.scale(type_img, (default_width, abs(self.scale) * default_height))

        obs_positions = {
            'B': 'bottomleft',
            'P': 'topleft',
            'L': 'bottomleft',
            'W': 'midleft',
            'BP': 'bottomleft',
            'BL': 'bottomleft',
            'BW': 'bottomleft',
            'PL': 'bottomleft',
            'LW': 'bottomleft',
            'PW': 'topleft'
        }
        scrn.blit(
            type_img,  # obstacle type
            type_img.get_rect(
                **{invert_axis(obs_positions[obs_type], self.scale): (x, self.y(ribbon))}  # position
            )
        )


def parse_file(fn):
    pieces = []
    invisible_pcs = []
    render_dist = 15
    with open(fn, "r") as f:
        urc = urcparse.parse(f.read())
        ctr = 0
        render_dist = int(urc.metadata.get("RenderDist", globalvars.DEFAULT_RENDER_DISTANCE))
        scroll_speed = int(urc.metadata.get("ScrollSpeed", globalvars.DEFAULT_SCROLL_TIME))
        offset_override = int(urc.metadata.get("OffsetOverride", 0))
        for i in urc.events:
            if i.event.lower() == "scroll":
                scroll_speed = int(i.params.get("speed", globalvars.DEFAULT_SCROLL_TIME))
                invisible_pcs.append(InvisiblePiece(
                    type="scroll",
                    time=i.time + offset_override,
                    value=scroll_speed,
                ))
                continue
            pieces.append(Piece(
                type=i.event.upper(),
                time=i.time + offset_override,
                scroll_time=i.params.get("scroll", scroll_speed),
                render_distance=i.params.get("distance", render_dist),
                id=ctr,
                flip=i.params.get("flip", False),
                keys=get_keys(i.event.upper())
            ))
            ctr += 1
        f.close()
    return pieces, render_dist, invisible_pcs
