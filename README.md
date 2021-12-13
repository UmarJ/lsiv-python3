# VISNOTATE: An Opensource tool for Gaze-based Annotation of WSI Data

* [Introduction](#introduction)
* [Requirements](#requirements)
* [Installation and Setup](#installation-and-setup)
* [Supported Hardware and Software](#supported-hardware-and-software)
* [Reference](#reference)

# Introduction
This repo contains the source code for 'Visnotate' which is a tool that can be used to track gaze patterns on Whole Slide Images (WSI) in the svs format. Visnotate was used to evaluate the efficacy of gaze-based labeling of histopathology data. The details of our research on gaze-based annotation can be found in the following paper:

* Komal Mariam, Osama Mohammed Afzal, Wajahat Hussain, Muhammad Umar Javed, Amber Kiyani, Nasir Rajpoot, Syed Ali Khurram and Hassan Aqeel Khan, **"On Smart Gaze based Annotation of Histopathology Images for Training of Deep Convolutional Neural Networks",** *submitted to IEEE Journal of Biomedical and Health Informatics.*

![blockDiagram](../media/Visnotate%20Diagram.png?raw=true)

# Requirements
- Openslide
- Python 3.7

# Installation and Setup

1. Install openslide. This process is different depending on the operating system.

    #### Windows
    1. Download **64-bit Windows Binaries** from the [openslide download page](https://openslide.org/download/#windows-binaries). [Direct link](https://github.com/openslide/openslide-winbuild/releases/download/v20171122/openslide-win64-20171122.zip) to download the latest version at the time of writing.
    2. Extract the zip archive.
    3. Copy all `.dll` files from `bin` to `C:/Windows/System32`.

    #### Debian/Ubuntu
    ```console
    # apt-get install openslide-tools
    ```

    #### Arch Linux
    ```console
    $ git clone https://aur.archlinux.org/openslide.git
    $ cd openslide
    $ makepkg -si
    ```

    #### macOS
    ```console
    $ brew install openslide
    ```

2. For some operating systems, tkinter needs to be installed as well.

    #### Debian/Ubuntu
    ```console
    # apt-get install python3-tk
    ```

    #### Arch Linux
    ```console
    # pacman -S tk
    ```

3. (Optional) If recording gaze points using a tracker, install the necessary software from its website.

4. Clone this repository.

    ```
    git clone https://github.com/UmarJ/lsiv-python3.git visnotate
    cd visnotate
    ```

5. [Create and activate](https://docs.python.org/3/library/venv.html#creating-virtual-environments) a new python virtual environment if needed. Then install required python modules.
    ```
    python -m pip install -r requirements.txt
    ```

6. (Optional) Start gaze tracking software in the background if tracking gaze points.

7. Run `interface_recorder.py`.

    ```
    python interface_recorder.py
    ```

# Supported Hardware and Software
At this time visinotate supports the GazePoint GP3, tracking hardware. WSI's are read using openslide software and we support only the `.svs` file format. We do have plans to add support for other gaze tracking hardware and image formats later.

# Screenshots

## The Visnotate Interface
![Interface Screenshot](../media/sample-ui.png?raw=true)

## Collected Gazepoints
![Gazepoints Screenshot](../media/sample-gazepoints.png?raw=true)

## Generated Heatmap
![Heatmap Screenshot](../media/sample-heatmap.png?raw=true)

# Reference
This repo was used to generate the results for the following paper on Gaze-based labelling of Pathology data. 
   
* Komal Mariam, Osama Mohammed Afzal, Wajahat Hussain, Muhammad Umar Javed, Amber Kiyani, Nasir Rajpoot, Syed Ali Khurram and Hassan Aqeel Khan, **"On Smart Gaze based Annotation of Histopathology Images for Training of Deep Convolutional Neural Networks",** *submitted to IEEE Journal of Biomedical and Health Informatics.*


**BibTex Reference:** Available after acceptance.
