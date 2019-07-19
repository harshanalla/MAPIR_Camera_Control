import os
import subprocess

modpath = os.path.dirname(os.path.realpath(__file__))
image = 'C:\\Users\\Software\\Desktop\\test_images\\target\\2019_0705_140943_047.tif'

subprocess.call([modpath + os.sep + r'FiducialFinder.exe', image], startupinfo=subprocess.STARTUPINFO())