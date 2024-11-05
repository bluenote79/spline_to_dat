# spline_to_dat

This skript for fusion 360 exports a airfoil spline as dat file.
Sketch a fittet spline from the tail along the top of the airfoil to origin in xy-plane. Got from there along the bottom to the tail.
The skript lets you select the spline, adds the selected amount off fitpoints and writes the normalized data to a dat-file in selig-format.


**Install:**
1. In Fusion 360 go to Utilities > ADD-INS > Skripts and Add-Ins.
2. Create a new script (chose Script, Python and spline_to_dat as name)
3. Right click on the script > Open file location
4. Overwrite the spline_to_dat.py with the one from here.


**Usage:**

## Option 1: Sketch an airfoil to xy-plane using a fitted spline.

1. Select the spline.
2. Enter a name for the spline.
3. Decide how many points should be added to the dat-file.
4. Click OK to start file save dialogue.

<picture>

  <img alt="Illustrates usage of script" src="https://github.com/bluenote79/spline_to_dat/blob/main/option1.jpg">
  
</picture>

## Option 2: Sketch two controlpoint splines.

1. Select the splines. The first selection must be the top curve.
2. Enter a name for the spline.
3. Decide how many points should be added to the dat-file.
4. Click OK to start file save dialogue.

<picture>

  <img alt="Illustrates usage of script" src="https://github.com/bluenote79/spline_to_dat/blob/main/option2.jpg">
  
</picture>
