# Vib-Ribbon Minus Guide for Mappers

Hello!

As of version 0.1.0, there is no capability for automatically mapped songs yet, so it is a good idea to learn how to map manually.

## Using existing software

### Mapping

Currently, 4-key osu!mania and Quaver files can be converted to Vib-Ribbon Minus formatted URC files (vib files).

To map with these wonderful rhythm games, you need to know the order of obstacles:

**B**lock, **P**it, **L**oop, and **W**ave.

These go from left to right.

In other words, the key farthest to the left places a block on the ribbon, and the key farthest to the right places a wave on the ribbon.

When you put two notes at the same millisecond, it becomes a complex piece, meaning you have to press two keys to pass it.

That's basically it for the *mapping* part. Just map VRM levels like you would osu!mania or Quaver levels. Slider notes have no effect and function like single tap notes.

### Conversion


You might need a little Python knowledge to really comprehend what's going on, but hopefully this guide will suffice. In the future, we plan to make this into a GUI, or at least a command line application.

First, install Python 3.10 or above. [Click here to be taken to the download page.](https://www.python.org/downloads/).

**When/if it asks you to add Python to your PATH variable, say yes.**

Then, open `conversions.py` with a text editor or IDE (Notepad, VS Code, Atom, PyCharm, etc, but **not Microsoft Word or other office oriented word processors**) and scroll down to the bottom of the file.

After that, ending on where you're converting from, press enter at the last line and paste the following:

**for osu!mania mappers**

```
osumania("OSU FILE.osu",
         "DESTINATION FILE.vib",
         bpm_scroll_speed=True,
         shadow=0
)
```

**for Quaver mappers**

```
quaver("QUAVER FILE.qua",
       "DESTINATION FILE.vib",
       bpm_scroll_speed=True,
       shadow=0
)

```

Replace "OSU/QUAVER FILE.osu\/qua" with the path to your map in osu!mania or Quaver, and replace "DESTINATION FILE.vib" with where you would like your converted file to be located.

For example, if I want a VIB file in `C:\Maps\The Stinky Song`, you would put in `C:\\Maps\\The Stinky Song\\The Stinky Song.vib`.

**Windows users, make sure to use double backslashes!**

Save your data and open command prompt/terminal. This can be done in Windows with <kbd>Win</kbd> + <kbd>R</kbd> and typing in `cmd`.

In Mac, you can open Spotlight Search (<kbd>Cmd</kbd> + <kbd>Space</kbd>) and type in "terminal" to open terminal.

If you're using Linux, there are many ways to do so, depending on your distribution or desktop environment. A common way to open one is by using <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>T</kbd>. At the end of the day, as long as you have one open, it should be A-OK.

If you already know how to use the command line, just run `conversions.py`. If you don't, I will walk you through.

To run the converter, it needs to be run through a terminal or command prompt.

Depending on your Python setup, you can run:

`python "path/to/conversions.py"`
or
`python3 "path/to/conversions.py"`

You can omit the last bit and drag `conversions.py` into the command window.

Then press enter and your map should convert! Note that some maps may not perfectly convert. So be sure to check over the map in case there are any errors that would cause the game to freak out.
