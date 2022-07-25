class URC:
    def __init__(self):
        self.timeChanges = []
        self.sounds = []
        self.events = []
        self.metadata = {}
        self.__soundlist__ = []
        self.__offsetSounds__ = []
        self.__timelist__ = []  # full of tuples (offset in fb time, starting bar, bpm)
        self.__timescheme__ = 0
        self.__aliases__ = {}

    def __dict__(self):
        return {
            "timeChanges": [dict(i) for i in self.timeChanges],
            "sounds": [dict(i) for i in self.sounds],
            "events": [dict(i) for i in self.events],
            "metadata": self.metadata
        }

    def parse(self, code):
        self = parse(code)

    def find_sound(self, name):
        for i in self.sounds:
            if i.path == name:
                return i
        return None

    def current_time(self, bar):
        if bar < 0:
            return 0
        if bar >= self.timeChanges[-1].startBar:
            return len(self.timeChanges) - 1
        for i in range(0, len(self.timeChanges)):
            if bar < self.timeChanges[i].startBar:
                return i - 1


class URCSound:
    def __init__(self):
        self.path = "default.wav"
        self.offset = 0
        self.offsetType = "st"  # start time

    def __dict__(self):
        return {
            "path": self.path,
            "offset": self.offset,
            "offsetType": self.offsetType
        }


class URCTimeChange:
    def __init__(self):
        self.time = 0
        self.startBar = 0
        self.timeSigTop = 4
        self.timeSigBottom = 4
        self.bpm = 120.0
        self.offset = 0
        self.offsetType = "fb"  # first beat

    def __str__(self):
        return str(self.offset) + " ms: " + str(self.bpm) + " bpm at bar " + str(self.startBar)

    def __dict__(self):
        return {
            "time": self.time,
            "startBar": self.startBar,
            "timeSigTop": self.timeSigTop,
            "timeSigBottom": self.timeSigBottom,
            "bpm": self.bpm,
            "offset": self.offset,
            "offsetType": self.offsetType
        }

    def bar_len(self):
        # get length of whole note
        # multiply by 4 because there are always 4 quarter notes in a whole note,
        # regardless of time signature
        whole_note = (60000 / self.bpm) * 4
        return int((whole_note / self.timeSigBottom) * self.timeSigTop)

    def bar_num(self, ms):
        # length in ms
        bl = self.bar_len()
        return ms / bl


    def bar_to_ms(self, measure, beat):
        bar = measure - self.startBar
        qnote = (60000 / self.bpm)
        if self.timeSigBottom != 4:
            beat_len = qnote * (4 / self.timeSigBottom)
        else:
            beat_len = qnote
        # (bar number * whole note) + (beat length * [beat number in measure])
        duration = (float(bar) * (qnote * 4.0)) + (float(beat_len) * float(beat))
        return int(duration + self.offset)


class URCEvent:
    def __init__(self):
        self.time = 0
        self.event = ""
        self.params = {}

    def __str__(self):
        return self.event + " at " + str(self.time) + " ms"

    def __dict__(self):
        return {
            "time": self.time,
            "event": self.event,
            "params": self.params
        }

    def has_param(self, param):
        try:
            a = self.params[param]
            return True
        except KeyError:
            return False



def parse(code):
    temp = URC()
    inst = code.replace("\t", "").split("\n")
    offMode = False  # flag for being in an offset block
    currentTc = None  # current time change (for relative beats)
    started = False  # flag for if offsets and metadata have ended and beats have started
    ln = 0

    for i in inst:
        # line number for debugging
        ln += 1

        # comment
        if i.strip().startswith("//"):
            continue

        # off command
        # starts defining offset
        elif i.strip().startswith("off "):
            if offMode:
                raise SyntaxError("Line " + str(ln) + ": Already defining offset")
            if started:
                raise SyntaxError("Line " + str(ln) + ": Cannot define offsets after cues have started")

            offMode = True

            # colon is optional
            cmd = i.strip().replace(":", "").split(" ")
            # set up time change
            currentTc = URCTimeChange()
            currentTc.offsetType = cmd[1]
            currentTc.offset = int(cmd[2])

        # ts
        # (offset command) defines time signature
        elif i.strip().startswith("ts "):
            if not offMode:
                raise SyntaxError("Line " + str(ln) + ": Not defining offset")
            if started:
                raise SyntaxError("Line " + str(ln) + ": Cannot define offsets after cues have started")
            ts = i.strip().split(" ")[1]
            ts = ts.split("/")

            currentTc.timeSigTop = int(ts[0])
            currentTc.timeSigBottom = int(ts[1])

        # bpm
        # (offset command) defines bpm
        elif i.strip().startswith("bpm "):
            if not offMode:
                raise SyntaxError("Line " + str(ln) + ": Not defining offset")
            if started:
                raise SyntaxError("Line " + str(ln) + ": Cannot define offsets after cues have started")
            bpm = float(i.strip().split(" ")[1].strip())
            currentTc.bpm = bpm

        # soff
        # sound offset; defines the offset/onset of a sound
        elif i.strip().startswith("soff "):
            if started:
                raise SyntaxError("Line " + str(ln) + ": Cannot define offsets after cues have started")

            snd = URCSound()
            snd_data = i.strip().split(" ")

            snd.path = snd_data[1]
            snd.offsetType = snd_data[2]
            snd.offset = int(snd_data[3])

            temp.sounds.append(snd)
            # This makes it easier to tell if a certain sound is in urc.sounds
            temp.__offsetSounds__.append(snd.path)

        # meta
        # metadata
        # meta Key Value
        elif i.strip().startswith("meta "):
            if started:
                raise SyntaxError("Line " + str(ln) + ": Cannot define metadata after cues have started")
            md = i.strip().split(" ")
            key = md[1]
            value = " ".join(md[2:])
            temp.metadata[key] = value

        # alias
        elif i.strip().startswith("alias "):
            if started:
                raise SyntaxError("Line " + str(ln) + ": Cannot define metadata after cues have started")
            md = i.strip().split(" ")
            key = md[1]
            if "@" in key:
                raise SyntaxError("Line " + str(ln) + ": Cannot put @ symbol in alias")
            value = " ".join(md[2:])
            temp.__aliases__[key] = value

        # hash mark
        # ends offset block
        elif i.strip().startswith("#"):
            if started:
                raise SyntaxError("Line " + str(ln) + ": Cannot define offsets after cues have started")
            if not offMode:
                raise SyntaxError("Line " + str(ln) + ": Random hash mark")

            offMode = False
            # add time change
            temp.timeChanges.append(currentTc)
            currentTc = None

        # start
        # starts cues
        elif i.strip() == "start":
            started = True

            # order offset changes
            temp.timeChanges.sort(key=lambda x: x.time)

            # cache positions of offset changes
            temp.__timelist__.append([temp.timeChanges[0].offset, 0, temp.timeChanges[0].bpm])

            # count how many bars there are so that it can transition into the next offset
            # after a certain number of milliseconds, the software will cut off a bar early
            # and go to the next one
            # where does each measure start
            # solve later

            # revelation
            # where does each measure begin?
            # calculate length in bars from offset of previous measure to (offset of current measure - 1 ms)
            # then floor the bar number and add 1

            ctr = 0
            for i in temp.timeChanges[1:]:
                ctr += 1
                tc = [i.offset, 0, i.bpm]
                timeChangeLength = temp.timeChanges[ctr].offset - temp.timeChanges[ctr - 1].offset - 1
                barNum = int(temp.timeChanges[ctr -1].bar_num(timeChangeLength)) + 1
                tc[1] = barNum + temp.__timelist__[ctr - 1][1]
                temp.__timelist__.append(tc)
                i.startBar = tc[1]



        # r (relative)
        elif i.strip().startswith("r"):
            if offMode or not started:
                raise SyntaxError("Line " + str(ln) + ": Events can only be placed after a start statement")

            evt = URCEvent()

            args = i.strip().split(" ")
            measure_info = args[1].split(",")
            measure_info[0] = int(measure_info[0])

            # set current offset
            temp.__timescheme__ = temp.current_time(measure_info[0])

            # parse measure information
            if "/" in measure_info[1]:
                mfrac = measure_info[1].split("/")
                mfrac[0] = int(mfrac[0])
                mfrac[1] = int(mfrac[1])
                measure_info[1] = (mfrac[0] / mfrac[1]) * 4  # consider replacing 4???

            # not to be confused with temp.__timelist__
            evt.time = temp.timeChanges[temp.__timescheme__].bar_to_ms(measure_info[0], measure_info[1])

            # add event
            # check if alias
            if args[2].startswith("@"):
                al_temp = args[2].split("@")[1]
                if al_temp in temp.__aliases__:
                    evt.event = temp.__aliases__[al_temp]
                else:
                    raise ReferenceError("Line " + str(ln) + ": Could not find alias " + al_temp)
            else:
                evt.event = args[2]

            # add sound to soundlist for easier searching
            if evt.event not in temp.__soundlist__ and "." in evt.event:
                temp.__soundlist__.append(evt.event)
                snd_obj = URCSound()
                snd_obj.path = evt.event
                temp.sounds.append(snd_obj)

            # offset the sound if the sound has an offset
            if evt.event in temp.__offsetSounds__:
                snd_obj = temp.find_sound(evt.event)
                # start time offset
                if snd_obj.offsetType == "st":
                    evt.event.time += snd_obj.offset
                # first beat offset
                elif snd_obj.offsetType == "fb":
                    evt.event.time -= snd_obj.offset

            # parameters
            for j in args[3:]:
                if j[0] == "&":
                    kv = j.split("=")

                    # remove ampersand
                    kv[0] = kv[0][1:]

                    # remove semicolon
                    if kv[1][-1:] != ";":
                        raise SyntaxError("Line " + str(ln) + ": Parameter does not end with semicolon")
                    kv[1] = kv[1][:-1]

                    # add to parameters list
                    evt.params[kv[0]] = kv[1]

            temp.events.append(evt)

        # m (milliseconds)
        elif i.strip().startswith("m"):
            if offMode or not started:
                raise SyntaxError("Line " + str(ln) + ": Events can only be placed after a start statement")

            evt = URCEvent()

            args = i.strip().split(" ")

            # no need for measure parsing
            evt.time = int(args[1])

            # add event
            # check if alias
            if args[2].startswith("@"):
                al_temp = args[2].split("@")[1]
                if al_temp in temp.__aliases__:
                    evt.event = temp.__aliases__[al_temp]
                else:
                    raise ReferenceError("Line " + str(ln) + ": Could not find alias " + al_temp)
            else:
                evt.event = args[2]

            # add sound to soundlist for easier searching
            if evt.event not in temp.__soundlist__ and "." in evt.event:
                temp.__soundlist__.append(evt.event)
                snd_obj = URCSound()
                snd_obj.path = evt.event
                temp.sounds.append(snd_obj)

            # offset the sound if the sound has an offset
            if evt.event in temp.__offsetSounds__:
                snd_obj = temp.find_sound(evt.event)
                # start time offset
                if snd_obj.offsetType == "st":
                    evt.event.time += snd_obj.offset
                # first beat offset
                elif snd_obj.offsetType == "fb":
                    evt.event.time -= snd_obj.offset

            # parameters
            for j in args[3:]:
                if j[0] == "&":
                    kv = j.split("=")

                    # remove ampersand
                    kv[0] = kv[0][1:]

                    # remove semicolon
                    if kv[1][-1:] != ";":
                        raise SyntaxError("Line " + str(ln) + ": Parameter does not end with semicolon")
                    kv[1] = kv[1][:-1]

                    # add to parameters list
                    evt.params[kv[0]] = kv[1]

            temp.events.append(evt)


    return temp
