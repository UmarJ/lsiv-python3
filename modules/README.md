# Modules

A short description of each of the modules of this program.

## App
The main tkinter window. Contains buttons and a resizable canvas on which the image is drawn.

### Recorder
Handles recording of the user's gaze and provides an interface to toggle gaze tracking. Also provides a keybind to generate heatmap for gaze points recorded during the current session.

### Visualiser
Used to visualise the points generated during a gaze tracking session. Erroneous points can be removed individually or in groups using bounding boxes.

## Dynamic Tiling
Dynamically generates the tiles using the whole slide image and returns a stitched image to `App` based on the current view area.

## Stitch
This module is used to stitch the tiles of the whole slide image into a larger image in order to display the image on the screen or to generate a heatmap. It takes a list of tiles saved in a directory as input and returns the stitched image as output.

## Tracking
This module uses the gaze tracker API to obtain the coordinates of the user's gaze on the screen. It then calculates the coordinates of the points on the whole slide image file using the current position of the canvas. The coordinates are saved to a CSV file corresponding to the current level.

Sampling from the tracker is done at a rate of 10 samples/sec.

## Heatmap Generation
This module can either be called from the recorder interface or as a standalone script. It generates a heatmap for each level that has at least 1 gaze point saved in its CSV.

The previously generated tiles are loaded from disk and missing tiles are generated using the svs file (if required). These tiles are then stitched into a single image for the current level. The image is scaled down to a more suitable size for processing and saved on disk. Finally, `gazeheatplot.py` is called as a subprocess to generate and save the heatmap.

## Utils
Contains utility functions useful for other modules.
