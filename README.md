# VISNOTATE: An Opensource tool for Gaze-based Annotation of WSI Data

* [Introduction](#introduction)
* [Requirements](#requirements)
* [Installation and Setup](#installation-and-setup)
* [Supported Hardware and Software](#supported-hardware-and-software)
* [Reference](#reference)

# Introduction
This repo contains the source code for 'Visnotate' which is a tool that can be used to track gaze patterns on Whole Slide Images (WSI) in the svs format. Visnotate was used to evaluate the efficacy of gaze-based labeling of histopathology data. The details of our research on gaze-based annotation can be found in the following paper:

* Komal Mariam, Osama Mohammed Afzal, Wajahat Hussain, Muhammad Umar Javed, Amber Kiyani, Nasir Rajpoot, Syed Ali Khurram and Hassan Aqeel Khan, **"On Smart Gaze based Annotation of Histopathology Images for Training of Deep Convolutional Neural Networks",** *submitted to IEEE Journal of Biomedical and Health Informatics.*

![blockDiagram](https://github.com/UmarJ/lsiv-python3/blob/master/Visnotate%20Diagram.png)

# Requirements
- Openslide
- Python 3.7

# Installation and Setup
Some basic installation and setup instructions here. Something like a demo script would be good.

# Supported Hardware and Software
At this time visinotate supports the GazePoint GP3, tracking hardware. WSI's are read using openslide software and we support only the `.svs` file format. We do have plans to add support for other gaze tracking hardware and image formats later.

# Reference
This repo was used to generate the results for the following paper on Gaze-based labelling of Pathology data. 
   
* Komal Mariam, Osama Mohammed Afzal, Wajahat Hussain, Muhammad Umar Javed, Amber Kiyani, Nasir Rajpoot, Syed Ali Khurram and Hassan Aqeel Khan, **"On Smart Gaze based Annotation of Histopathology Images for Training of Deep Convolutional Neural Networks",** *submitted to IEEE Journal of Biomedical and Health Informatics.*


**BibTex Reference:** Available after acceptance.
