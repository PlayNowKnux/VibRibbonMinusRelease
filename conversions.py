import math
import os
import yaml
import traceback

# TODO: Add support for copying music files
# TODO: Port to command line

def clamp(num, min_value, max_value):
    num = max(min(num, max_value), min_value)
    return num


def calc_scroll_speed(bpm, **kwargs):
    # scroll speed is 2000 at 120 bpm
    precedent = kwargs.get("default_bpm", 120) * kwargs.get("default_scroll", 2000)
    return round(precedent / bpm)


class TimeSection:
    def __init__(self):
        self.bpm = 120
        self.offset = 0
        self.success = 0

    def from_osumania(self, txt):
        try:
            data = txt.split(",")
            self.offset = round(float(data[0]))
            # if uninherited
            if int(data[6]):
                self.bpm = round(60_000 / float(data[1]), 3)
                self.success = 1
            else:
                self.success = 0
        except IndexError:
            traceback.print_exc()
        except ValueError:
            pass

    def from_quaver(self, o):
        try:
            self.offset = o.get("StartTime", 0)
            self.bpm = o["Bpm"]
            print(f"[Timing] StartTime: {self.offset},  Bpm: {self.bpm}")
            self.success = 1
        except KeyError:
            traceback.print_exc()

    def to_vib(self):
        return f"\noff fb {self.offset}:\nbpm {self.bpm}\n#\n"


class Note:
    def __init__(self):
        self.hits = [0,0,0,0]
        self.time = 0
        self.success = 0
        self.special = ""
        self.value = 0

    def from_osumania(self, txt):
        try:
            # assuming line is like 320,192,259,1,0,0:0:0:0:
            data = txt.split(",")
            # x
            x = clamp(math.floor(int(data[0]) * 4 / 512), 0, 3)
            self.hits[x] = 1
            self.time = int(data[2])
            self.success = 1
        except IndexError:
            traceback.print_exc()
        except ValueError:
            pass

    def from_quaver(self, o):
        try:
            self.time = o["StartTime"]
            self.hits[o["Lane"] - 1] = 1

            print(f"[Note] StartTime: {self.time},  Lane: {o['Lane']}")
            self.success = 1
        except KeyError:
            traceback.print_exc()

    def to_vib(self):
        vib_str = f"m {self.time} "
        tp = ""
        if not self.special:
            for idx, v in enumerate(self.hits):
                if len(tp) == 2:
                    break
                if v:
                    tp += list("BPLW")[idx]
        else:
            tp += self.special + " "
            match self.special:
                case "scroll":
                    tp += f"&speed={self.value};"
        return vib_str + tp + "\n"


def osumania(infile, outfile, **kwargs):
    with open(infile, "r", encoding="utf-8") as f:
        data = f.read().split("\n")
        f.close()
    outstr = ""
    timing_points = []
    notes = []
    shadow = kwargs.get("shadow", 0)
    bpm_scroll_speed = kwargs.get("bpm_scroll_speed", 1)
    state = ""
    for inst in data:
        if inst.startswith("["):
            state = inst
        elif state == "[TimingPoints]":
            tp = TimeSection()
            tp.from_osumania(inst)
            if tp.success:
                timing_points.append(tp)
        elif state == "[HitObjects]":
            ho = Note()
            ho.from_osumania(inst)
            if ho.success:
                try:
                    if ho.time == notes[-1].time:
                        notes[-1].from_osumania(inst)
                    else:
                        notes.append(ho)
                except IndexError:
                    notes.append(ho)

    if shadow:
        # Only allow one note in a certain amount of time
        next_shadow_time = 0
        ok_notes = []
        for note in notes:
            if note.time >= next_shadow_time:
                ok_notes.append(note)
                next_shadow_time = note.time + shadow
        notes = ok_notes

    headers = """meta FileFormat VibRibbonMinus"""

    if bpm_scroll_speed:
        for i in timing_points:
            n = Note()
            n.time = i.offset
            n.special = "scroll"
            n.value = calc_scroll_speed(i.bpm)
            notes.append(n)
        notes.sort(key=lambda n: n.time)
        headers += f"\nmeta ScrollSpeed {calc_scroll_speed(timing_points[0].bpm)}"

    outstr += headers
    for i in timing_points:
        outstr += i.to_vib()

    outstr += "\nstart\n"

    for i in notes:
        outstr += i.to_vib()

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(outstr)
        f.close()


def quaver(infile, outfile, **kwargs):
    with open(infile, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f.read())
        f.close()
    outstr = ""
    timing_points = []
    notes = []
    shadow = kwargs.get("shadow", 0)
    bpm_scroll_speed = kwargs.get("bpm_scroll_speed", 1)

    if data["Mode"] != "Keys4":
        return "Not a 4-key map"

    for i in data["TimingPoints"]:
        tp = TimeSection()
        tp.from_quaver(i)
        timing_points.append(tp)

    for i in data["HitObjects"]:
        h = Note()
        append = False
        try:
            if notes[-1].time == i["StartTime"]:
                h = notes[-1]
            else:
                raise IndexError
        except IndexError:
            append = True
        finally:
            h.from_quaver(i)
            if append:
                notes.append(h)

    if shadow:
        # Only allow one note in a certain amount of time
        next_shadow_time = 0
        ok_notes = []
        for note in notes:
            if note.time >= next_shadow_time:
                ok_notes.append(note)
                next_shadow_time = note.time + shadow
        notes = ok_notes

    headers = """meta FileFormat VibRibbonMinus"""

    if bpm_scroll_speed:
        for i in timing_points:
            n = Note()
            n.time = i.offset
            n.special = "scroll"
            n.value = calc_scroll_speed(i.bpm)
            notes.append(n)
        notes.sort(key=lambda n: n.time)
        headers += f"\nmeta ScrollSpeed {calc_scroll_speed(timing_points[0].bpm)}"

    outstr += headers
    for i in timing_points:
        outstr += i.to_vib()

    outstr += "\nstart\n"

    for i in notes:
        outstr += i.to_vib()

    with open(outfile, "w", encoding="utf-8") as f:
        print("Begin outstr:\n")
        print(outstr)
        f.write(outstr)
        f.close()

#if __name__ == "__main__":
 #   osumania("C:/Users/choco/AppData/Local/osu!/Songs/beatmap-637922835223276278-ComputerSaloon/Separation From Reality - Computer Saloon (CC445) [Vib-Ribbon].osu",
  #           "C:/Users/choco/Desktop/Code/Github/vibribbonminus/maps/Computer Saloon/Computer Saloon.vib",
   #          bpm_scroll_speed=True)
    #quaver("C:/Program Files (x86)/Steam/steamapps/common/Quaver/Songs/1655431622000/1655431622000.qua",
    #       "C:/Users/choco/Desktop/Code/Github/vibribbonminus/maps/Sugar Rush/Sugar Rush.vib")
