import glob
import os
from MAPIR_Processing_dockwidget import MAPIR_ProcessingDockWidget

def test_answer():
    assert 1 == 1

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