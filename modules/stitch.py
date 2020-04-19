from PIL import Image
import numpy as np
import cv2
import os

# TODO: PIL can do image stitching, no need to bother with np arrays


def join_vertically(dir_path, files):
    files_arr = read_files(dir_path, files)

    #Calculating minimum width for each part in order to avoid concatenation shape mismatch
    minWidth = min([(i.shape[1]) for i in files_arr])
    for i in range( len(files_arr)):
            if (files_arr[i].shape[1] > minWidth):
                files_arr[i] = (files_arr[i])[:,:minWidth]

    final_image = np.concatenate(files_arr)
    return final_image


def join_horizontally(parts):
    par = np.concatenate(parts, axis=1)
    return Image.fromarray(par)


def read_files(path, files):
    files_array = []
    for i in files:
        img = cv2.cvtColor(cv2.imread(os.path.join(path, i)), cv2.COLOR_BGR2RGB)
        files_array.append(img)
    return files_array


def __find_shape(path, files):
    rows, columns = 0
    files_arr = read_files(path, files)
    for img in files_arr:
        rows += img.shape[0]
        if int(img.shape[1]) > columns:
            columns = img.shape[1]
    return (rows, columns)


def save_img(image, name):
    image.save(name + ".png")