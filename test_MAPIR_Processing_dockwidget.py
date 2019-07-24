import glob
import os
from MAPIR_Processing_dockwidget import MAPIR_ProcessingDockWidget
import numpy as np



def test_answer():
    assert 1 == 1

def test_normalize():
    layer_arr = []

    max_pixel = 20
    min_pixel = 0

    for i in range(min_pixel, max_pixel + 1):
        arr = i*np.ones((1, 100))
        layer_arr.extend(arr)
    layer = np.array(layer_arr)

    expected_normalized_layer_arr = []
    normalized_values = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]

    for i in normalized_values:
        arr = i*np.ones((1, 100))
        expected_normalized_layer_arr.extend(arr)
    expected_normalized_layer = np.array(expected_normalized_layer_arr)

    normalized_layer = MAPIR_ProcessingDockWidget.normalize(layer, max_pixel, min_pixel)
    assert np.array_equal(normalized_layer, expected_normalized_layer)


def test_get_processing_image_message():
    counter = 0
    dir_path = '.' + os.path.sep + 'test' + os.path.sep
    file_paths = [dir_path + 'first_input.jpg', dir_path + 'second_input.tif']
    message = MAPIR_ProcessingDockWidget.get_processing_image_message(counter, file_paths)
    assert message == 'Processing Image: 1 of 2  first_input\n'

def test_get_filenames_to_be_changed():
    kernel_band_dir_names = ['kb1', 'kb2', 'kb3', 'kb4', 'kb5', 'kb6']
    filenames_to_be_changed = MAPIR_ProcessingDockWidget.get_filenames_to_be_changed(kernel_band_dir_names)

    folder1 = []
    folder2 = []
    folder3 = []
    folder4 = []
    folder5 = []
    folder6 = []

    if len(kernel_band_dir_names[0]) > 0:
        folder1.extend(glob.glob(kernel_band_dir_names[0] + os.sep + "*.tif?"))
        folder1.extend(glob.glob(kernel_band_dir_names[0] + os.sep + "*.jpg"))
        folder1.extend(glob.glob(kernel_band_dir_names[0] + os.sep + "*.jpeg"))
    if len(kernel_band_dir_names[1]) > 0:
        folder2.extend(glob.glob(kernel_band_dir_names[1] + os.sep + "*.tif?"))
        folder2.extend(glob.glob(kernel_band_dir_names[1] + os.sep + "*.jpg"))
        folder2.extend(glob.glob(kernel_band_dir_names[1] + os.sep + "*.jpeg"))
    if len(kernel_band_dir_names[2]) > 0:
        folder3.extend(glob.glob(kernel_band_dir_names[2] + os.sep + "*.tif?"))
        folder3.extend(glob.glob(kernel_band_dir_names[2] + os.sep + "*.jpg"))
        folder3.extend(glob.glob(kernel_band_dir_names[2] + os.sep + "*.jpeg"))
    if len(kernel_band_dir_names[3]) > 0:
        folder4.extend(glob.glob(kernel_band_dir_names[3] + os.sep + "*.tif?"))
        folder4.extend(glob.glob(kernel_band_dir_names[3] + os.sep + "*.jpg"))
        folder4.extend(glob.glob(kernel_band_dir_names[3] + os.sep + "*.jpeg"))
    if len(kernel_band_dir_names[4]) > 0:
        folder5.extend(glob.glob(kernel_band_dir_names[4] + os.sep + "*.tif?"))
        folder5.extend(glob.glob(kernel_band_dir_names[4] + os.sep + "*.jpg"))
        folder5.extend(glob.glob(kernel_band_dir_names[4] + os.sep + "*.jpeg"))
    if len(kernel_band_dir_names[5]) > 0:
        folder6.extend(glob.glob(kernel_band_dir_names[5] + os.sep + "*.tif?"))
        folder6.extend(glob.glob(kernel_band_dir_names[5] + os.sep + "*.jpg"))
        folder6.extend(glob.glob(kernel_band_dir_names[5] + os.sep + "*.jpeg"))

    folder1.sort()
    folder2.sort()
    folder3.sort()
    folder4.sort()
    folder5.sort()
    folder6.sort()

    assert filenames_to_be_changed == [folder1, folder2, folder3, folder4, folder5, folder6]