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

There is a website available that converts osu!mania and Quaver maps to Vib-Ribbon Minus maps. [Click here](https://playnowknux.github.io/vrm-conversions/) to go there.

It might also be a good idea to bookmark it in case you need it again.

In case the website isn't clear enough, here is what you should do to convert maps:

1. Use the file picker on the left side of the page to pick which map you want to convert.
2. In the future there will be options for how your map is interpreted. There aren't right now, so just click the "Convert" button.
3. Save the file to your map directory (a folder inside the maps directory where you put the map file and the audio file).

### Inside your map folder

Your map folder (not to be confused with the `maps` folder) is where you store your .vib file and your .ogg/.mp3 file. The directory tree should look something like this:

```
vibribbonminus
	- (other folders)
	- maps
		- (other maps)
		- My Map
			- My Map.ogg
            		- My Map.vib
	- VibRibbonMinus.exe
```

Note how all the files inside the folder have the same title as the folder itself.
