# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MAPIR_ProcessingDockWidget
                                 A QGIS plugin
 Widget for processing images captured by MAPIR cameras
                             -------------------
        begin                : 2016-09-26
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Peau Productions
        email                : ethan@peauproductions.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import warnings
warnings.filterwarnings("ignore")

os.umask(0)
import sys
import shutil
from PyQt5 import QtCore, QtGui, QtWidgets

import PyQt5.uic as uic

# from qgis.core import QgsMessageLog

from scipy import stats
import numpy as np
import subprocess
import cv2
import copy
import hid
import time
import distutils
from distutils import dir_util
from MAPIR_Enums import *
from Calculator import *
from LUT_Dialog import *
from Vignette import *
from ViewerSave_Dialog import *
import struct
# import KernelBrowserViewer

modpath = os.path.dirname(os.path.realpath(__file__))

# print(str(modpath))
if not os.path.exists(modpath + os.sep + "instring.txt"):
    istr = open(modpath + os.sep + "instring.txt", "w")
    istr.close()
# sys.path.insert(0, modpath)
# if sys.platform == "win32":  # Windows OS
#
#     # pypath = os.path.split(os.path.split(sys.executable)[0])[0] + os.sep + "apps" + os.sep + "Python27"
#     # if not os.path.exists(pypath + os.sep + "Scripts" + os.sep + "exiftool.exe")\
#     #        or not os.path.exists(pypath + os.sep + "Scripts" + os.sep + "dcraw.exe")\
#     #        or not os.path.exists(pypath + os.sep + "Scripts" + os.sep + "cygwin1.dll")\
#     #        or not os.path.exists(pypath + os.sep + "Lib" + os.sep + "site-packages" + os.sep + "exiftool.py")\
#     #        or not os.path.exists(pypath + os.sep + "Lib" + os.sep + "site-packages" + os.sep + "exiftool.pyc")\
#     #        or not os.path.exists(pypath + os.sep + "Lib" + os.sep + "site-packages" + os.sep + "cv2.pyd"):
#     #    os.chmod(pypath,0777)
#     #    shutil.copy(modpath + os.sep + "exiftool.exe", pypath + os.sep + "Scripts")
#     #    shutil.copy(modpath + os.sep + "dcraw.exe", pypath + os.sep + "Scripts")
#     #    shutil.copy(modpath + os.sep + "cygwin1.dll", pypath + os.sep + "Scripts")
#     #    shutil.copy(modpath + os.sep + "exiftool.py", pypath + os.sep + "Lib" + os.sep + "site-packages")
#     #    shutil.copy(modpath + os.sep + "exiftool.pyc", pypath + os.sep + "Lib" + os.sep + "site-packages")
#     #    shutil.copy(modpath + os.sep + "cv2.pyd", pypath + os.sep + "Lib" + os.sep + "site-packages")
#
# elif sys.platform == "darwin":
#     if not os.path.exists(r'/usr/local/bin/brew'):
#         subprocess.call([r'/usr/bin/ruby', r'-e',
#                          r'"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"', r'<',
#                          r'/dev/null'])
#         subprocess.call([r'/usr/local/bin/brew', r'tap', r'homebrew/science'])
#     if not os.path.exists(r'/usr/local/bin/dcraw'):
#         subprocess.call([r'/usr/local/bin/brew', r'install', r'dcraw'])
#
#     if not os.path.exists(r'/usr/local/bin/exiftool'):
#         subprocess.call([r'/usr/local/bin/brew', r'install', r'exiftool'])
#
#     if not os.path.exists(r'/usr/local/bin/opencv2'):
#         subprocess.call([r'/usr/local/bin/brew', r'install', r'opencv2'])
#     sys.path.append(r'/usr/local/bin')
#     sys.path.append(r'/usr/local/bin/dcraw')
#     sys.path.append(r'/usr/local/bin/exiftool')
#     sys.path.append(r'/usr/local/bin/opencv2')

from osgeo import gdal

import glob

all_cameras = []
if sys.platform == "win32":
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

# if sys.platform == "win32":
#       import exiftool
#       exiftool.executable = modpath + os.sep + "exiftool.exe"
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_base.ui'))
MODAL_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_modal.ui'))
CAN_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_CAN.ui'))
TIME_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_time.ui'))
DEL_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_delete.ui'))
TRANSFER_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_transfer.ui'))

class KernelTransfer(QtWidgets.QDialog, TRANSFER_CLASS):
    parent = None

    def __init__(self, parent=None):
        """Constructor."""
        super(KernelTransfer, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)
    def on_ModalBrowseButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.ModalOutputFolder.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.ModalOutputFolder.text())
            self.ModalSaveButton.setEnabled(True)
    def on_ModalSaveButton_released(self):
        self.parent.transferoutfolder  = self.ModalOutputFolder.text()
        self.parent.yestransfer = True
        self.parent.selection_made = True
        QtWidgets.QApplication.processEvents()
        self.close()

    def on_ModalCancelButton_released(self):
        self.parent.yestransfer = False
        self.parent.selection_made = True
        QtWidgets.QApplication.processEvents()
        self.close()


class KernelDelete(QtWidgets.QDialog, DEL_CLASS):
    parent = None

    def __init__(self, parent=None):
        """Constructor."""
        super(KernelDelete, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)

    def on_ModalSaveButton_released(self):
        for drv in self.parent.driveletters:
            if os.path.isdir(drv + r":" + os.sep + r"dcim"):
                # try:
                files = glob.glob(drv + r":" + os.sep + r"dcim/*/*")
                for file in files:
                    os.unlink(file)
        self.close()

    def on_ModalCancelButton_released(self):
        self.close()


class KernelModal(QtWidgets.QDialog, MODAL_CLASS):
    parent = None

    def __init__(self, parent=None):
        """Constructor."""
        super(KernelModal, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)

    def on_ModalSaveButton_released(self):
        seconds = int(self.SecondsLine.text())
        minutes = int(self.MinutesLine.text())
        hours = int(self.HoursLine.text())
        days = int(self.DaysLine.text())
        weeks = int(self.WeeksLine.text())
        if (seconds / 60) > 1:
            minutes += int(seconds / 60)
            seconds = seconds % 60
        if (minutes / 60) > 1:
            hours += int(minutes / 60)
            minutes = minutes % 60
        if (hours / 24) > 1:
            days += int(hours / 24)
            hours = hours % 24
        if (days / 7) > 1:
            weeks += int(days / 7)
            days = days % 7
        self.parent.seconds = seconds
        self.parent.minutes = minutes
        self.parent.hours = hours
        self.parent.days = days
        self.parent.weeks = weeks
        self.parent.writeToIntervalLine()

        # weeks /= 604800
        # days /= 86400
        # hours /= 3600
        # minutes /= 60
        # seconds += minutes + hours + days + weeks
        #
        # MAPIR_ProcessingDockWidget.interval = int(seconds)
        self.close()

    def on_ModalCancelButton_released(self):
        self.close()


class KernelCAN(QtWidgets.QDialog, CAN_CLASS):
    parent = None

    def __init__(self, parent=None):
        """Constructor."""
        super(KernelCAN, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)

    def on_ModalSaveButton_released(self):
        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_CAN_NODE_ID.value
        nodeid = int(self.KernelNodeID.text())
        buf[2] = nodeid

        self.parent.writeToKernel(buf)
        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_BLOCK_WRITE_REPORT
        buf[1] = eRegister.RG_CAN_BIT_RATE_1.value
        buf[2] = 2
        bitrate = int(self.KernelBitRate.currentText())
        bit1 = (bitrate >> 8) & 0xff
        bit2 = bitrate & 0xff
        buf[3] = bit1
        buf[4] = bit2

        buf = [0] * 512
        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_BLOCK_WRITE_REPORT
        buf[1] = eRegister.RG_CAN_SAMPLE_POINT_1.value
        buf[2] = 2
        samplepoint = int(self.KernelSamplePoint.text())
        sample1 = (samplepoint >> 8) & 0xff
        sample2 = samplepoint & 0xff
        buf[3] = sample1
        buf[4] = sample2
        self.close()

    def on_ModalCancelButton_released(self):
        self.close()


class KernelTime(QtWidgets.QDialog, TIME_CLASS):
    parent = None
    timer = QtCore.QTimer()
    BUFF_LEN = 512
    SET_EVENT_REPORT = 1
    SET_COMMAND_REPORT = 3
    SET_REGISTER_WRITE_REPORT = 5
    SET_REGISTER_BLOCK_WRITE_REPORT = 7
    SET_REGISTER_READ_REPORT = 9
    SET_REGISTER_BLOCK_READ_REPORT = 11
    SET_CAMERA = 13
    def __init__(self, parent=None):
        """Constructor."""
        super(KernelTime, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1)
    def on_ModalSaveButton_released(self):
        self.timer.stop()

        if self.parent.KernelCameraSelect.currentIndex() == 0:
            for p in self.parent.paths:
                self.parent.camera = p

                self.adjustRTC()
            self.parent.camera = self.parent.paths[0]
        else:
            self.adjustRTC()

    def adjustRTC(self):
        buf = [0] * 512

        buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
        buf[1] = eRegister.RG_REALTIME_CLOCK.value
        buf[2] = 8
        t = QtCore.QDateTime.toMSecsSinceEpoch(self.KernelReferenceTime.dateTime())
        buf[3] = t & 0xff
        buf[4] = (t >> 8) & 0xff
        buf[5] = (t >> 16) & 0xff
        buf[6] = (t >> 24) & 0xff
        buf[7] = (t >> 32) & 0xff
        buf[8] = (t >> 40) & 0xff
        buf[9] = (t >> 48) & 0xff
        buf[10] = (t >> 54) & 0xff
        self.parent.writeToKernel(buf)
        buf = [0] * 512

        buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_REALTIME_CLOCK.value
        buf[2] = 8
        r = self.parent.writeToKernel(buf)[2:11]
        val = r[0] | (r[1] << 8) | (r[2] << 16) | (r[3] << 24) | (r[4] << 32) | (r[5] << 40) | (r[6] << 48) | (
        r[7] << 56)

        offset = QtCore.QDateTime.currentMSecsSinceEpoch() - val

        while offset > 0.01:
            if self.KernelTimeSelect.currentIndex() == 0:
                buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
                buf[1] = eRegister.RG_REALTIME_CLOCK.value
                buf[2] = 8
                t = QtCore.QDateTime.toMSecsSinceEpoch(QtCore.QDateTime.currentDateTimeUtc().addSecs(18).addMSecs(offset))
                buf[3] = t & 0xff
                buf[4] = (t >> 8) & 0xff
                buf[5] = (t >> 16) & 0xff
                buf[6] = (t >> 24) & 0xff
                buf[7] = (t >> 32) & 0xff
                buf[8] = (t >> 40) & 0xff
                buf[9] = (t >> 48) & 0xff
                buf[10] = (t >> 54) & 0xff
                self.parent.writeToKernel(buf)
                buf = [0] * 512

                buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
                buf[1] = eRegister.RG_REALTIME_CLOCK.value
                buf[2] = 8
                r = self.parent.writeToKernel(buf)[2:11]
                val = r[0] | (r[1] << 8) | (r[2] << 16) | (r[3] << 24) | (r[4] << 32) | (r[5] << 40) | (r[6] << 48) | (
                    r[7] << 56)

                offset = QtCore.QDateTime.currentMSecsSinceEpoch() - val
            elif self.KernelTimeSelect.currentIndex() == 1:
                buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
                buf[1] = eRegister.RG_REALTIME_CLOCK.value
                buf[2] = 8
                t = QtCore.QDateTime.toMSecsSinceEpoch(QtCore.QDateTime.currentDateTimeUtc().addMSecs(offset))
                buf[3] = t & 0xff
                buf[4] = (t >> 8) & 0xff
                buf[5] = (t >> 16) & 0xff
                buf[6] = (t >> 24) & 0xff
                buf[7] = (t >> 32) & 0xff
                buf[8] = (t >> 40) & 0xff
                buf[9] = (t >> 48) & 0xff
                buf[10] = (t >> 54) & 0xff
                self.parent.writeToKernel(buf)
                buf = [0] * 512

                buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
                buf[1] = eRegister.RG_REALTIME_CLOCK.value
                buf[2] = 8
                r = self.parent.writeToKernel(buf)[2:11]
                val = r[0] | (r[1] << 8) | (r[2] << 16) | (r[3] << 24) | (r[4] << 32) | (r[5] << 40) | (r[6] << 48) | (
                    r[7] << 56)

                offset = QtCore.QDateTime.currentMSecsSinceEpoch() - val
            else:

                buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
                buf[1] = eRegister.RG_REALTIME_CLOCK.value
                buf[2] = 8
                t = QtCore.QDateTime.toMSecsSinceEpoch(QtCore.QDateTime.currentDateTime().addMSecs(offset))
                buf[3] = t & 0xff
                buf[4] = (t >> 8) & 0xff
                buf[5] = (t >> 16) & 0xff
                buf[6] = (t >> 24) & 0xff
                buf[7] = (t >> 32) & 0xff
                buf[8] = (t >> 40) & 0xff
                buf[9] = (t >> 48) & 0xff
                buf[10] = (t >> 54) & 0xff
                self.parent.writeToKernel(buf)
                buf = [0] * 512

                buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
                buf[1] = eRegister.RG_REALTIME_CLOCK.value
                buf[2] = 8
                r = self.parent.writeToKernel(buf)[2:11]
                val = r[0] | (r[1] << 8) | (r[2] << 16) | (r[3] << 24) | (r[4] << 32) | (r[5] << 40) | (r[6] << 48) | (
                    r[7] << 56)

                offset = QtCore.QDateTime.currentMSecsSinceEpoch() - val

        self.close()

    def on_ModalCancelButton_released(self):
        self.timer.stop()
        self.close()

    def tick(self):
        buf = [0] * 512

        buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_REALTIME_CLOCK.value
        buf[2] = 8
        r = self.parent.writeToKernel(buf)[2:11]
        val = r[0] | (r[1] << 8) | (r[2] << 16) | (r[3] << 24) | (r[4] << 32) | (r[5] << 40) | (r[6] << 48) | (r[7] << 56)
        self.KernelCameraTime.setDateTime(QtCore.QDateTime.fromMSecsSinceEpoch(val))
        if self.KernelTimeSelect.currentIndex() == 0:
            self.KernelReferenceTime.setDateTime(QtCore.QDateTime.currentDateTimeUtc().addSecs(18))
        elif self.KernelTimeSelect.currentIndex() == 1:
            self.KernelReferenceTime.setDateTime(QtCore.QDateTime.currentDateTimeUtc())
        else:
            self.KernelReferenceTime.setDateTime(QtCore.QDateTime.currentDateTime())
class tPoll:
    def __init__(self):
        request = 0
        code = 0
        len = 0 #Len can also store the value depending on the code given
        values = []
class tEventInfo:
    def __init__(self):
        mode = 0
        process = 0
        focusing = 0
        inversion = 0
        nr_faces = 0






class MAPIR_ProcessingDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    BASE_COEFF_SURVEY2_RED_JPG = [-2.55421832, 16.01240929, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_SURVEY2_GREEN_JPG = [0.0, 0.0, -0.60437250, 4.82869470, 0.0, 0.0]
    BASE_COEFF_SURVEY2_BLUE_JPG = [0.0, 0.0, 0.0, 0.0, -0.39268985, 2.67916884]
    BASE_COEFF_SURVEY2_NDVI_JPG = [-0.29870245, 6.51199915, 0.0, 0.0, -0.65112026, 10.30416005]
    BASE_COEFF_SURVEY2_NIR_JPG = [-0.46967653, 7.13619139, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_SURVEY1_NDVI_JPG = [-6.33770486888, 331.759383023, 0.0, 0.0, -0.6931339436, 51.3264675118]
    BASE_COEFF_SURVEY2_RED_TIF = [-5.09645820, 0.24177528, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_SURVEY2_GREEN_TIF = [0.0, 0.0, -1.39528479, 0.07640011, 0.0, 0.0]
    BASE_COEFF_SURVEY2_BLUE_TIF = [0.0, 0.0, 0.0, 0.0, -0.67299134, 0.03943339]
    BASE_COEFF_SURVEY2_NDVI_TIF = [3.21946584661, 1.06087488594, 0.0, 0.0, -43.6505776052, 1.46482226805]
    BASE_COEFF_SURVEY2_NIR_TIF = [-2.24216724, 0.12962333, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_DJIX3_NDVI_JPG = [-0.34430543, 4.63184993, 0.0, 0.0, -0.49413940, 16.36429964]
    BASE_COEFF_DJIX3_NDVI_TIF = [-0.74925346, 0.01350319, 0.0, 0.0, -0.77810008, 0.03478272]
    BASE_COEFF_DJIPHANTOM4_NDVI_JPG = [-1.17016961, 0.03333209, 0.0, 0.0, -0.99455214, 0.05373502]
    BASE_COEFF_DJIPHANTOM4_NDVI_TIF = [-1.17016961, 0.03333209, 0.0, 0.0, -0.99455214, 0.05373502]
    BASE_COEFF_DJIPHANTOM3_NDVI_JPG = [-1.54494979, 3.44708472, 0.0, 0.0, -1.40606832, 6.35407929]
    BASE_COEFF_DJIPHANTOM3_NDVI_TIF = [-1.37495554, 0.01752340, 0.0, 0.0, -1.41073753, 0.03700812]
    BASE_COEFF_KERNEL_F644 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F405 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F450 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F520 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F550 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F632 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F650 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F725 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F808 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F850 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F395_870 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F475_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F550_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F660_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F475_550_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F550_660_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    # eFilter = mousewheelFilter()
    camera = 0
    poll = []
    ei = tEventInfo()
    capturing = False
    SQ_TO_TARG = 2.1875
    SQ_TO_SQ = 5.0
    CORNER_TO_CORNER = 5.25
    CORNER_TO_TARG = 10.0
    TARGET_LENGTH = 2.0
    TARG_TO_TARG = 2.6
    dialog = None
    imcols = 4608
    imrows = 3456
    imsize = imcols * imrows
    closingPlugin = QtCore.pyqtSignal()
    firstpass = True
    useqr = False
    qrcoeffs = []  # Red Intercept, Red Slope,  Green Intercept, Green Slope, Blue Intercept, Blue Slope

    qrcoeffs2 = []
    qrcoeffs3 = []
    qrcoeffs4 = []
    qrcoeffs5 = []
    qrcoeffs6 = []

    # drivesfound = []
    ref = ""
    refindex = ["oldrefvalues", "newrefvalues"]
    refvalues = {
    "oldrefvalues":{
        "660/850": [[0.87032549, 0.52135779, 0.23664799], [0, 0, 0], [0.8463514, 0.51950608, 0.22795518]],
        "446/800": [[0.8419608509, 0.520440145, 0.230113958], [0, 0, 0], [0.8645652801, 0.5037779363, 0.2359041624]],
        "850": [[0.8463514, 0.51950608, 0.22795518], [0, 0, 0], [0, 0, 0]],
        "808": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        "650": [[0.87032549, 0.52135779, 0.23664799], [0, 0, 0], [0, 0, 0]],
        "550": [[0, 0, 0], [0.87415089, 0.51734381, 0.24032515], [0, 0, 0]],
        "450": [[0, 0, 0], [0, 0, 0], [0.86469794, 0.50392915, 0.23565447]],
        "Mono450": [0.8634818638, 0.5024087105, 0.2351860396],
        "Mono550": [0.8740616379, 0.5173070235, 0.2402423818],
        "Mono650": [0.8705783136, 0.5212290524, 0.2366437854],
        "Mono725": [0.8606071247, 0.521474266, 0.2337744252],
        "Mono808": [0.8406184266, 0.5203405498, 0.2297701185],
        "Mono850": [0.8481919553, 0.519491643, 0.2278713071],
        "Mono405": [0.8556905469, 0.4921243183, 0.2309899254],
        "Mono518": [0.8729814889, 0.5151370187, 0.2404729692],
        "Mono632": [0.8724034645, 0.5209649915, 0.2374529161],
        # "Mono660": [0.8704202831, 0.5212214688, 0.2365919358],
        "Mono590": [0.8747043911, 0.5195596573, 0.2392049856],
        "550/660/850": [[0.8474610999, 0.5196055607, 0.2279922965],[0.8699940018, 0.5212235151, 0.2364397706],[0.8740311726, 0.5172611881, 0.2402870156]]

    },
    "newrefvalues":{

        "Mono405": [0.6959473282,  0.2437485737, 0.1799017476, 0.0205591758],
        "Mono450": [0.7882333002, 0.2501235178, 0.1848459584, 0.020036883],
        "Mono490": [0.8348841674, 0.2580074987, 0.1890252099, 0.01975703],
        "Mono518": [0.8572181897, 0.2628629357, 0.192259471, 0.0196629792],
        "Mono550": [0.8686559344, 0.2655697585, 0.1960837144, 0.0195629009],
        "Mono590": [0.874586922, 0.2676592931, 0.1993779934, 0.0193745668],
        "Mono615": [0.8748454449, 0.2673426216, 0.1996415667, 0.0192891156],
        "Mono632": [0.8758224323, 0.2670055225, 0.2023045295, 0.0192596465],
        "Mono650": [0.8773469949, 0.2663571183, 0.199919444, 0.0192325637],
        "Mono685": [0.8775925081, 0.2648548355, 0.1945563456, 0.0192860556],
        "Mono725": [0.8756774317, 0.266883373, 0.21603525, 0.194527158],
        "Mono780": [0.8722125382, 0.2721842015, 0.2238493387, 0.0196295938],
        "Mono808": [0.8699458632, 0.2780141682, 0.2283300902, 0.0216592377],
        "Mono850": [0.8649280907, 0.2800907016, 0.2340131491, 0.0195446727],
        "Mono880": [0.8577996233, 0.2673899041, 0.2371926238, 0.0202034892],
        "550/660/850": [[0.8689592421, 0.2656248359, 0.1961875592, 0.0195576511], [0.8775934407, 0.2661207692, 0.1987265874, 0.0192249327],
                        [0.8653063177, 0.2798126291, 0.2337498097, 0.0193295348]],
        "475/550/850": [[0.8348841674, 0.2580074987, 0.1890252099, 0.01975703], [0.8689592421, 0.2656248359, 0.1961875592, 0.0195576511],
                        [0.8653063177, 0.2798126291, 0.2337498097, 0.0193295348]]
        # "Mono450": [10.137101, 24.131129, 2.500000],
        # "Mono550": [13.050459, 25.918403, 2.444385],
        # "Mono650": [42.873777, 25.681838, 2.400000],
        # "Mono725": [57.362319, 26.209292, 2.444148],
        # "Mono808": [80.761967, 27.552786, 2.522048],
        # "Mono850": [85.470884, 27.989664, 2.476279],
        # "Mono405": [10.419592, 23.297778, 2.579408],
        # "Mono518": [10.192879, 25.668374, 2.500000],
        # "Mono632": [40.314177, 25.624361, 2.400000],
        # "Mono615": [36.590561, 25.575475, 2.400000],
        #
        # "Mono590": [28.088219, 25.614054, 2.400000],
        # "Mono780": [72.470173, 27.114517, 2.500000],
        # "Mono880": [86.40861, 28.33615, 2.387391],
        # # "550/660/850": [[0.12730952, .2591748, 0.02444606], [0.42100882, 0.2567382, 0.0240000],
        # #                 [0.85491034, 0.27943831, 0.0247464]],
        # "550/660/850": [[12.730952, 25.91748, 2.444606], [42.100882, 25.67382, 2.40000],
        #                 [85.491034, 27.943831, 2.47464]],
        # "475/550/850": [[9.893005, 24.868873, 2.5], [14.1338, 25.919591, 2.440347],
        #                 [85.217001, 27.952459, 2.516666]]

    }}
    pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                     "greenmax": 0.0, "greenmin": 65535.0,
                     "bluemax": 0.0, "bluemin": 65535.0}
    multiplication_values = {"Red": [0.00],
                             "Green": [0.00],
                             "Blue": [0.00]}
    monominmax = {"min": 65535.0,"max": 0.0}
    weeks = 0
    days = 0
    hours = 0
    minutes = 0
    seconds = 1
    modalwindow = None
    calcwindow = None
    LUTwindow = None
    VigWindow = None
    ndvipsuedo = None
    savewindow = None
    index_to_save = None
    LUT_to_save = None
    LUT_Min = -1.0
    LUT_Max = 1.0
    array_indicator = False
    seed_pass = False
    transferoutfolder = None
    yestransfer = False
    selection_made = False
    POLL_TIME = 3000
    # SLOW_POLL = 10000
    slow = 0
    regs = [0] * eRegister.RG_SIZE.value
    paths = []
    pathnames = []
    driveletters = []
    source = 0
    evt = 0
    info = 0
    VENDOR_ID = 0x525
    PRODUCT_ID = 0xa4ac
    BUFF_LEN = 512
    SET_EVENT_REPORT = 1
    SET_COMMAND_REPORT = 3
    SET_REGISTER_WRITE_REPORT = 5
    SET_REGISTER_BLOCK_WRITE_REPORT = 7
    SET_REGISTER_READ_REPORT = 9
    SET_REGISTER_BLOCK_READ_REPORT = 11
    SET_CAMERA = 13
    display_image = None
    display_image_original = None
    displaymax = None
    displaymin = None
    mapscene = None
    frame = None
    legend_frame = None
    legend_scene = None
    image_loaded = False
    # mMutex = QMutex()
    regs = []
    paths_1_2 = []
    paths_3_0 = []
    paths_14_0 = []
    ISO_VALS = (1,2,4,8,16,32)
    def __init__(self, parent=None):
        """Constructor."""
        super(MAPIR_ProcessingDockWidget, self).__init__(parent)

        self.setupUi(self)
        try:

            legend = cv2.imread(os.path.dirname(__file__) + "/lut_legend.jpg")
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # legend = cv2.cvtColor(legend, cv2.COLOR_GRAY2RGB)
            legh, legw = legend.shape[:2]
            self.legend_frame = QtGui.QImage(legend.data, legw, legh, legw, QtGui.QImage.Format_Grayscale8)
            # self.LUTGraphic.setPixmap(QtGui.QPixmap.fromImage(img2))
            self.LUTGraphic.setPixmap(QtGui.QPixmap.fromImage(
                QtGui.QImage(self.legend_frame)))
            self.LegendLayout_2.hide()
        except Exception as e:
            print(e)
        # try:
        #     self.KernelViewer = KernelBrowserViewer.KernelBrowserViewer(self)
        # except Exception as e:
        #     print(e)
        # self.timer.timeout.connect(self.tick)

    # def tick(self):
    # try:
    #   self.KernelUpdate()
# except Exception as e:
# print(e
    def exitTransfer(self, drv = 'C'):
        tmtf = r":/dcim/tmtf.txt"

        if drv == 'C':
            while drv is not '[':
                if os.path.isdir(drv + r":/dcim/"):
                    try:
                        if not os.path.exists(drv + tmtf):
                            self.KernelLog.append("Camera mounted at drive " + drv + " leaving transfer mode")
                            file = open(drv + tmtf, "w")
                            file.close()
                    except:
                        self.KernelLog.append("Error disconnecting drive " + drv)

                drv = chr(ord(drv) + 1)
        else:
            if os.path.isdir(drv + r":/dcim/"):
                try:
                    if not os.path.exists(drv + tmtf):
                        self.KernelLog.append("Camera mounted at drive " + drv + " leaving transfer mode")
                        file = open(drv + tmtf, "w")
                        file.close()
                except:
                    self.KernelLog.append("Error disconnecting drive " + drv)
    def on_KernelRefreshButton_released(self):
        self.ConnectKernels()
    def on_KernelConnect_released(self):

        self.ConnectKernels()
    def ConnectKernels(self):
        self.KernelLog.append(' ')
        all_cameras = hid.enumerate(self.VENDOR_ID, self.PRODUCT_ID)

        if all_cameras == []:

            self.KernelLog.append("No cameras found! Please check your USB connection and try again.")
        else:
            self.paths.clear()
            # self.paths_1_2.clear()
            # self.paths_3_0.clear()
            # self.paths_14_0.clear()
            for cam in all_cameras:
                # self.KernelLog.append("Subscript1")
                self.paths.append(cam['path'])


            # if len(self.paths) > 1:
            #     temppaths = self.paths
            #     arids = []
            #     for path in self.paths:@
            #         self.camera = path
            #         buf = [0] * 512
            #         buf[0] = self.SET_REGISTER_READ_REPORT
            #         buf[1] = eRegister.RG_CAMERA_LINK_ID.value
            #         arid = self.writeToKernel(buf)[2]
            #         arids.append(arid)
                # [self.paths for (y, self.paths) in sorted(zip(arids, temppaths), key=lambda pair: pair[0])]
                # for count, id in enumerate(arids):
                #     self.paths[id] = temppaths[count]

            self.KernelCameraSelect.blockSignals(True)
            self.KernelCameraSelect.clear()
            self.KernelCameraSelect.addItem("All")
            self.KernelCameraSelect.blockSignals(False)
            try:
                for i, path in enumerate(self.paths):
                    # line = 0
                    self.camera = path
                    # self.KernelLog.append(str(line + 1))
                    buf = [0] * 512
                    # self.KernelLog.append(str(line + 2))
                    buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
                    # self.KernelLog.append(str(line + 3))
                    buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
                    # self.KernelLog.append(str(line + 4))
                    buf[2] = 3
                    # self.KernelLog.append(str(line + 5))
                    times = 0
                    res = self.writeToKernel(buf)
                    while res is None and times < 5:
                        res = self.writeToKernel(buf)
                        times += 1
                    # self.KernelLog.append(str(line + 6))
                    # print(chr(res[2]) + chr(res[3]) + chr(res[4]))
                    # self.KernelLog.append("Subscript2")
                    item = chr(res[2]) + chr(res[3]) + chr(res[4])
                    if i == 0:
                        self.KernelFilterSelect.blockSignals(True)
                        self.KernelFilterSelect.setCurrentIndex(self.KernelFilterSelect.findText(item))
                        self.KernelFilterSelect.blockSignals(False)
                    # self.KernelLog.append(str(line + 7))
                    self.KernelLog.append("Found Camera: " + str(item))
                    # self.KernelLog.append(str(line + 8))
                    # buf = [0] * 512
                    # buf[0] = self.SET_REGISTER_READ_REPORT
                    # buf[1] = eRegister.RG_SENSOR_ID.value
                    # res = self.writeToKernel(buf, True)[0][i]
                    # if res[2] == 2:
                    #     self.paths_1_2.append(path)
                    # elif res[2] == 1:
                    #     self.paths_3_0.append(path)
                    # elif res[2] == 0:
                    #     self.paths_14_0.append(path)
                    self.pathnames.append(item)
                    # self.KernelLog.append(str(line + 9))
                    self.KernelCameraSelect.blockSignals(True)
                    # self.KernelLog.append(str(line + 10))
                    self.KernelCameraSelect.addItem(item)
                    # self.KernelLog.append(str(line + 11))
                    self.KernelCameraSelect.blockSignals(False)
                    # self.KernelLog.append(str(line + 12))
                # self.KernelLog.append("Subscript3")
                self.camera = self.paths[0]

                try:
                    # self.KernelLog.append("Updating UI")
                    self.KernelUpdate()
                except Exception as e:
                    print(e)
            except Exception as e:
                self.KernelLog.append("Error: (" + str(e) +  ") connecting to camera, please ensure all cameras are connected properly and not in transfer mode.")
    # def on_Kernel3LetterSave_released(self):
    #     threeletter = self.Kernel3LetterID.text()
    #     buf = [0] * 512
    #     buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
    #     buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
    #     buf[2] = 3
    #     buf[3] = ord(threeletter[0])
    #     buf[4] = ord(threeletter[1])
    #     buf[5] = ord(threeletter[2])
    #     res = self.writeToKernel(buf)
    #     try:
    #         self.KernelUpdate()
    #     except Exception as e:
    #         print(e)
    def on_KernelFilterSelect_currentIndexChanged(self):
        try:
            threeletter = self.KernelFilterSelect.currentText()
            buf = [0] * 512
            buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
            buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
            buf[2] = 3
            buf[3] = ord(threeletter[0])
            buf[4] = ord(threeletter[1])
            buf[5] = ord(threeletter[2])
            res = self.writeToKernel(buf)

            self.KernelUpdate()
        except Exception as e:
            self.KernelLog.append("Error: " + e)
    def on_KernelCameraSelect_currentIndexChanged(self):
        if self.KernelCameraSelect.currentIndex() == 0:
            self.array_indicator = True
        else:
            self.array_indicator = False
        self.camera = self.paths[self.KernelCameraSelect.currentIndex() - 1]
        self.KernelFilterSelect.blockSignals(True)
        self.KernelFilterSelect.setCurrentIndex(self.KernelFilterSelect.findText(self.KernelCameraSelect.currentText()))
        self.KernelFilterSelect.blockSignals(False)
        if not self.KernelTransferButton.isChecked():
            try:
                self.KernelUpdate()
            except Exception as e:
                print(e)
    # def on_KernelArraySelect_currentIndexChanged(self):
    #     if self.KernelArraySelect.currentIndex() == 0:
    #         self.array_indicator = False
    #         self.KernelCameraSelect.setEnabled(True)
    #     else:
    #         self.array_indicator = True
    #         self.KernelCameraSelect.setEnabled(False)
    def on_VignetteButton_released(self):
        if self.VigWindow == None:
            self.VigWindow = Vignette(self)
        self.VigWindow.resize(385, 160)
        self.VigWindow.show()
    def on_KernelBrowserButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelBrowserFile.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelBrowserFile.text())
        try:
            # self.KernelViewer.verticalScrollBar().blockSignals(True)
            # self.KernelViewer.horizontalScrollBar().blockSignals(True)

            # self.KernelViewer.installEventFilter(self.eFilter)
            if os.path.exists(self.KernelBrowserFile.text()):
                self.display_image = cv2.imread(self.KernelBrowserFile.text(), -1)
                # if self.display_image == None:
                #     self.display_image = gdal.Open(self.KernelBrowserFile.text())
                #     self.display_image = np.array(self.display_image.GetRasterBand(1).ReadAsArray())
                if self.display_image.dtype == np.dtype("uint16"):
                    self.display_image = self.display_image / 65535.0
                    self.display_image = self.display_image * 255.0
                    self.display_image = self.display_image.astype("uint8")
                self.displaymax = np.percentile(self.display_image, 98)
                self.displaymin = np.percentile(self.display_image, 2)
                self.display_image[self.display_image > self.displaymax] = self.displaymax
                self.display_image[self.display_image < self.displaymin] = self.displaymin
                if len(self.display_image.shape) > 2:
                    self.display_image = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
                else:
                    self.display_image = cv2.cvtColor(self.display_image, cv2.COLOR_GRAY2RGB)
                self.display_image_original = copy.deepcopy(self.display_image)
                h, w = self.display_image.shape[:2]



                # self.image_loaded = True

                # self.display_image = ((self.display_image - self.display_image.min())/(self.display_image.max() - self.display_image.min())) * 255.0


                # browser_w = self.KernelViewer.width()
                # browser_h = self.KernelViewer.height()

                self.image_loaded = True
                self.stretchView()
                self.ViewerCalcButton.blockSignals(True)
                self.LUTButton.blockSignals(True)
                self.LUTBox.blockSignals(True)
                self.ViewerIndexBox.blockSignals(True)
                self.ViewerStretchBox.blockSignals(True)

                self.ViewerCalcButton.setEnabled(True)
                self.LUTButton.setEnabled(False)
                self.LUTBox.setEnabled(False)
                self.LUTBox.setChecked(False)
                self.ViewerIndexBox.setEnabled(False)
                self.ViewerIndexBox.setChecked(False)
                self.ViewerStretchBox.setChecked(True)

                self.ViewerCalcButton.blockSignals(False)
                self.LUTButton.blockSignals(False)
                self.LUTBox.blockSignals(False)
                self.ViewerIndexBox.blockSignals(False)
                self.ViewerStretchBox.blockSignals(False)

                self.savewindow = None
                self.LUTwindow = None
                self.LUT_to_save = None
                self.LUT_Max = 1.0
                self.LUT_Min = -1.0
                self.updateViewer(keepAspectRatio=True)

        except Exception as e:
            print(str(e))
    def on_ViewerStretchBox_toggled(self):
        self.stretchView()
    def stretchView(self):
        try:
            if self.image_loaded:
                if self.ViewerStretchBox.isChecked():
                    h, w = self.display_image.shape[:2]

                    if len(self.display_image.shape) > 2:
                        self.display_image[:, :, 0] = cv2.equalizeHist(self.display_image[:, :, 0])
                        self.display_image[:, :, 1] = cv2.equalizeHist(self.display_image[:, :, 1])
                        self.display_image[:, :, 2] = cv2.equalizeHist(self.display_image[:, :, 2])
                    else:
                        self.display_image = cv2.equalizeHist(self.display_image)
                    if not (self.ViewerIndexBox.isChecked() or self.LUTBox.isChecked()):
                        self.LegendLayout_2.hide()
                        if len(self.display_image.shape) > 2:
                            self.frame = QtGui.QImage(self.display_image.data, w, h, w * 3, QtGui.QImage.Format_RGB888)
                        else:
                            self.frame = QtGui.QImage(self.display_image.data, w, h, w, QtGui.QImage.Format_RGB888)
                else:
                    if not (self.ViewerIndexBox.isChecked() or self.LUTBox.isChecked()):
                        self.LegendLayout_2.hide()
                        h, w = self.display_image_original.shape[:2]
                        if len(self.display_image_original.shape) > 2:
                            self.frame = QtGui.QImage(self.display_image_original.data, w, h, w * 3, QtGui.QImage.Format_RGB888)
                        else:
                            self.frame = QtGui.QImage(self.display_image_original.data, w, h, w, QtGui.QImage.Format_RGB888)
                self.updateViewer(keepAspectRatio=False)
        except Exception as e:
            print(e)
    def on_ViewerIndexBox_toggled(self):
        self.applyRaster()
    def applyRaster(self):
        try:
            h, w = self.display_image.shape[:2]
            if self.LUTBox.isChecked():
                pass
            else:
                if self.ViewerIndexBox.isChecked():
                    self.frame = QtGui.QImage(self.calcwindow.ndvi.data, w, h, w, QtGui.QImage.Format_Grayscale8)
                    legend = cv2.imread(os.path.dirname(__file__) + r'\lut_legend.jpg', 0).astype("uint8")
                    # legend = cv2.cvtColor(legend, cv2.COLOR_GRAY2RGB)
                    legh, legw = legend.shape[:2]

                    self.legend_frame = QtGui.QImage(legend.data, legw, legh, legw, QtGui.QImage.Format_Grayscale8)
                    self.LUTGraphic.setPixmap(QtGui.QPixmap.fromImage(
                        QtGui.QImage(self.legend_frame)))
                    self.LegendLayout_2.show()
                else:
                    self.LegendLayout_2.hide()
                    self.frame = QtGui.QImage(self.display_image.data, w, h, w * 3, QtGui.QImage.Format_RGB888)
                self.updateViewer(keepAspectRatio=False)
        except Exception as e:
            print(e)
    def updateViewer(self, keepAspectRatio = True):
        self.mapscene = QtWidgets.QGraphicsScene()

        self.mapscene.addPixmap(QtGui.QPixmap.fromImage(
            QtGui.QImage(self.frame)))

        self.KernelViewer.setScene(self.mapscene)
        if keepAspectRatio:
            self.KernelViewer.fitInView(self.mapscene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.KernelViewer.setFocus()
        # self.KernelViewer.setWheelAction(2)
        QtWidgets.QApplication.processEvents()

    def on_LUTBox_toggled(self):
        self.applyLUT()
    def applyLUT(self):
        try:
            h, w = self.display_image.shape[:2]
            if self.LUTBox.isChecked():
                if self.LUTwindow.ClipOption.currentIndex() == 1:
                    self.frame = QtGui.QImage(self.ndvipsuedo.data, w, h, w * 4, QtGui.QImage.Format_RGBA8888)
                else:
                    self.frame = QtGui.QImage(self.ndvipsuedo.data, w, h, w * 3, QtGui.QImage.Format_RGB888)

                legend = cv2.imread(os.path.dirname(__file__) + r'\lut_legend_rgb.jpg', -1).astype("uint8")
                legend = cv2.cvtColor(legend, cv2.COLOR_BGR2RGB)
                legh, legw = legend.shape[:2]
                self.legend_frame = QtGui.QImage(legend.data, legw, legh, legw * 3, QtGui.QImage.Format_RGB888)
                self.LUTGraphic.setPixmap(QtGui.QPixmap.fromImage(
                    QtGui.QImage(self.legend_frame)))
                self.LegendLayout_2.show()
                # if self.LUTwindow.ClipOption.currentIndex() == 2:
                #     temp = copy.deepcopy(self.calcwindow.ndvi)
                #     if self.ViewerIndexBox.isChecked():
                #
                #         self.ndvipsuedo[temp <= self.LUTwindow._min, 0] = temp[temp <= self.LUTwindow._min]
                #         self.ndvipsuedo[temp <= self.LUTwindow._min, 1] = temp[temp <= self.LUTwindow._min]
                #         self.ndvipsuedo[temp <= self.LUTwindow._min, 2] = temp[temp <= self.LUTwindow._min]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max, 0] = temp[temp >= self.LUTwindow._max]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max, 1] = temp[temp >= self.LUTwindow._max]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max, 2] = temp[temp >= self.LUTwindow._max]
                #     else:
                #         self.ndvipsuedo[temp <= self.LUTwindow._min] = self.display_image[temp <= self.LUTwindow._min]
                #         # self.ndvipsuedo[temp <= workingmin, 1] = temp[temp <= workingmin]
                #         # self.ndvipsuedo[temp <= workingmin, 2] = temp[temp <= workingmin]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max] = self.display_image[temp >= self.LUTwindow._max]
                #         # self.ndvipsuedo[temp >= workingmax, 1] = temp[temp >= workingmax]
                #         # self.ndvipsuedo[temp >= workingmax, 2] = temp[temp >= workingmax]
            else:
                legend = cv2.imread(os.path.dirname(__file__) + r'\lut_legend.jpg', 0).astype("uint8")
                # legend = cv2.cvtColor(legend, cv2.COLOR_GRAY2RGB)
                legh, legw = legend.shape[:2]
                self.legend_frame = QtGui.QImage(legend.data, legw, legh, legw, QtGui.QImage.Format_Grayscale8)
                self.LUTGraphic.setPixmap(QtGui.QPixmap.fromImage(
                    QtGui.QImage(self.legend_frame)))

                # if self.LUTwindow.ClipOption.currentIndex() == 2:
                #     temp = copy.deepcopy(self.calcwindow.ndvi)
                #     if self.ViewerIndexBox.isChecked():
                #
                #         self.ndvipsuedo[temp <= self.LUTwindow._min, 0] = temp[temp <= self.LUTwindow._min]
                #         self.ndvipsuedo[temp <= self.LUTwindow._min, 1] = temp[temp <= self.LUTwindow._min]
                #         self.ndvipsuedo[temp <= self.LUTwindow._min, 2] = temp[temp <= self.LUTwindow._min]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max, 0] = temp[temp >= self.LUTwindow._max]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max, 1] = temp[temp >= self.LUTwindow._max]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max, 2] = temp[temp >= self.LUTwindow._max]
                #     else:
                #         self.ndvipsuedo[temp <= self.LUTwindow._min] = self.display_image[temp <= self.LUTwindow._min]
                #         # self.ndvipsuedo[temp <= workingmin, 1] = temp[temp <= workingmin]
                #         # self.ndvipsuedo[temp <= workingmin, 2] = temp[temp <= workingmin]
                #         self.ndvipsuedo[temp >= self.LUTwindow._max] = self.display_image[temp >= self.LUTwindow._max]
                #         # self.ndvipsuedo[temp >= workingmax, 1] = temp[temp >= workingmax]
                #         # self.ndvipsuedo[temp >= workingmax, 2] = temp[temp >= workingmax]
                if self.ViewerIndexBox.isChecked():
                    self.LegendLayout_2.show()
                    self.frame = QtGui.QImage(self.calcwindow.ndvi.data, w, h, w, QtGui.QImage.Format_Grayscale8)
                else:
                    self.LegendLayout_2.hide()
                    self.frame = QtGui.QImage(self.display_image.data, w, h, w * 3, QtGui.QImage.Format_RGB888)
            self.updateViewer(keepAspectRatio=False)

            QtWidgets.QApplication.processEvents()
        except Exception as e:
            print(e)

    def on_ViewerSaveButton_released(self):

        if self.savewindow == None:
            self.savewindow = SaveDialog(self)
        self.savewindow.resize(385, 110)
        self.savewindow.exec_()



        QtWidgets.QApplication.processEvents()

    def on_LUTButton_released(self):
        if self.LUTwindow == None:
            self.LUTwindow = Applicator(self)
        self.LUTwindow.resize(385, 160)
        self.LUTwindow.show()

        QtWidgets.QApplication.processEvents()
    def on_ViewerCalcButton_released(self):
        if self.LUTwindow == None:
            self.calcwindow = Calculator(self)
        self.calcwindow.resize(385, 250)
        self.calcwindow.show()
        QtWidgets.QApplication.processEvents()
    def on_ZoomIn_released(self):
        if self.image_loaded == True:
            try:
                # self.KernelViewer.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
                factor = 1.15
                self.KernelViewer.scale(factor, factor)
            except Exception as e:
                print(e)
    def on_ZoomOut_released(self):
        if self.image_loaded == True:
            try:
                # self.KernelViewer.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
                factor = 1.15
                self.KernelViewer.scale(1/factor, 1/factor)
            except Exception as e:
                print(e)
    def on_ZoomToFit_released(self):
        self.mapscene = QtWidgets.QGraphicsScene()
        self.mapscene.addPixmap(QtGui.QPixmap.fromImage(
            QtGui.QImage(self.frame)))

        self.KernelViewer.setScene(self.mapscene)
        self.KernelViewer.fitInView(self.mapscene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.KernelViewer.setFocus()
        QtWidgets.QApplication.processEvents()
    # def wheelEvent(self, event):
    #     if self.image_loaded == True:
    #         try:
    #
    #         except Exception as e:
    #             print(str(e))

    # def eventFilter(self, obj, event):
    #
    #     if self.image_loaded == True:
    #         try:
    #             self.KernelViewer.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
    #             factor = 1.15
    #             if int(event.angleDelta().y()) > 0:
    #                 self.KernelViewer.scale(factor, factor)
    #             else:
    # def wheelEvent(self, event):
    #     if self.image_loaded == True:
    #         try:
    #             self.KernelBrowserViewer.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
    #             factor = 1.15
    #             if int(event.angleDelta().y()) > 0:
    #                 self.KernelBrowserViewer.scale(factor, factor)
    #             else:
    #                 self.KernelBrowserViewer.scale(1.0/factor, 1.0/factor)
    #         except Exception as e:
    #             print(str(e))
    def resizeEvent(self, event):
        # redraw the image in the viewer every time the window is resized
        if self.image_loaded == True:
            self.mapscene = QtWidgets.QGraphicsScene()
            self.mapscene.addPixmap(QtGui.QPixmap.fromImage(
                QtGui.QImage(self.frame)))

            self.KernelViewer.setScene(self.mapscene)

            self.KernelViewer.setFocus()
            QtWidgets.QApplication.processEvents()
        print("resize")
    def KernelUpdate(self):
        self.KernelExposureMode.blockSignals(True)
        self.KernelShutterSpeed.blockSignals(True)
        self.KernelISO.blockSignals(True)
        self.KernelVideoOut.blockSignals(True)
        self.KernelFolderCount.blockSignals(True)
        self.KernelBeep.blockSignals(True)
        self.KernelPWMSignal.blockSignals(True)
        self.KernelGain.blockSignals(True)
        self.KernelSetPoint.blockSignals(True)
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_CAMERA_SETTING.value
        buf[2] = eRegister.RG_SIZE.value

        res = self.writeToKernel(buf)
        self.regs = res[2:]
        shutter = self.getRegister(eRegister.RG_SHUTTER.value)
        if shutter == 0:
            self.KernelExposureMode.setCurrentIndex(0)
            self.KernelISO.setEnabled(False)
            self.KernelShutterSpeed.setEnabled(False)
            self.KernelGain.setEnabled(True)
            self.KernelSetPoint.setEnabled(True)
        else:
            self.KernelExposureMode.setCurrentIndex(1)
            self.KernelISO.setEnabled(True)
            self.KernelShutterSpeed.setEnabled(True)
            self.KernelGain.setEnabled(False)
            self.KernelSetPoint.setEnabled(False)

        self.KernelShutterSpeed.setCurrentIndex(shutter - 1)

        iso = self.getRegister(eRegister.RG_ISO.value)
        if iso == self.ISO_VALS[0]:

            self.KernelISO.setCurrentIndex(0)
        elif iso == self.ISO_VALS[1]:
            self.KernelISO.setCurrentIndex(1)
        elif iso == self.ISO_VALS[2]:
            self.KernelISO.setCurrentIndex(2)
        else:
            self.KernelISO.setCurrentIndex(3)

        dac = self.getRegister(eRegister.RG_DAC.value)

        hdmi = self.getRegister(eRegister.RG_HDMI.value)

        if hdmi == 1 and dac == 1:
            self.KernelVideoOut.setCurrentIndex(3)
        elif hdmi == 0 and dac == 1:
            self.KernelVideoOut.setCurrentIndex(2)
        elif hdmi == 1 and dac == 0:
            self.KernelVideoOut.setCurrentIndex(1)
        else:
            self.KernelVideoOut.setCurrentIndex(0)


        media = self.getRegister(eRegister.RG_MEDIA_FILES_CNT.value)
        self.KernelFolderCount.setCurrentIndex(media)



        beep = self.getRegister(eRegister.RG_BEEPER_ENABLE.value)
        if beep != 0:
            self.KernelBeep.setChecked(True)
        else:
            self.KernelBeep.setChecked(False)

        pwm = self.getRegister(eRegister.RG_PWM_TRIGGER.value)
        if pwm != 0:
            self.KernelPWMSignal.setChecked(True)
        else:
            self.KernelPWMSignal.setChecked(False)

        self.KernelPanel.clear()
        self.KernelPanel.append("Hardware ID: " + str(self.getRegister(eRegister.RG_HARDWARE_ID.value)))
        self.KernelPanel.append("Firmware version: " + str(self.getRegister(eRegister.RG_FIRMWARE_ID.value)))
        self.KernelPanel.append("Sensor: " + str(self.getRegister(eRegister.RG_SENSOR_ID.value)))
        self.KernelPanel.append("Lens: " + str(self.getRegister(eRegister.RG_LENS_ID.value)))
        if shutter == 0:
            self.KernelPanel.append("Shutter: Auto")
        else:
            self.KernelPanel.append("Shutter: " + self.KernelShutterSpeed.itemText(self.getRegister(eRegister.RG_SHUTTER.value) -1) + " sec")
        self.KernelPanel.append("ISO: " + str(self.getRegister(eRegister.RG_ISO.value)) + "00")
        self.KernelPanel.append("WB: " + str(self.getRegister(eRegister.RG_WHITE_BALANCE.value)))
        self.KernelPanel.append("AE Setpoint: " + str(self.getRegister(eRegister.RG_AE_SETPOINT.value)))
        self.KernelPanel.append("Video resolution: " + str(self.getRegister(eRegister.RG_VIDEO_RESOLUTION.value)))
        self.KernelPanel.append("Photo resolution: " + str(self.getRegister(eRegister.RG_PHOTO_RESOLUTION.value)/10) + " Mpix")
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_READ_REPORT
        buf[1] = eRegister.RG_CAMERA_ARRAY_TYPE.value
        artype = self.writeToKernel(buf)[2]
        self.KernelPanel.append("Array Type: " + str(artype))
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_READ_REPORT
        buf[1] = eRegister.RG_CAMERA_LINK_ID.value
        arid = self.writeToKernel(buf)[2]
        self.KernelPanel.append("Array ID: " + str(arid))

        self.KernelExposureMode.blockSignals(False)
        self.KernelShutterSpeed.blockSignals(False)
        self.KernelISO.blockSignals(False)
        self.KernelVideoOut.blockSignals(False)
        self.KernelFolderCount.blockSignals(False)
        self.KernelBeep.blockSignals(False)
        self.KernelPWMSignal.blockSignals(False)
        self.KernelGain.blockSignals(False)
        self.KernelSetPoint.blockSignals(False)
    def on_KernelFolderButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelTransferFolder.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelTransferFolder.text())

    cancel_auto = False
    def on_KernelAutoCancel_released(self):
        self.cancel_auto = True
    # def on_KernelAutoTransfer_released(self):
    #
    #      Add the auto transfer check.



    def on_KernelBandButton1_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelBand1.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelBand1.text())
    def on_KernelBandButton2_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelBand2.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelBand2.text())
    def on_KernelBandButton3_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelBand3.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelBand3.text())
    def on_KernelBandButton4_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelBand4.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelBand4.text())
    def on_KernelBandButton5_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelBand5.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelBand5.text())
    def on_KernelBandButton6_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelBand6.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelBand6.text())

    def on_KernelRenameOutputButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelRenameOutputFolder.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelRenameOutputFolder.text())
    def on_KernelRenameButton_released(self):
        try:
            folder1 = []
            folder2 = []
            folder3 = []
            folder4 = []
            folder5 = []
            folder6 = []
            if len(self.KernelBand1.text()) > 0:
                folder1.extend(glob.glob(self.KernelBand1.text() + os.sep + "*.tif?"))
                folder1.extend(glob.glob(self.KernelBand1.text() + os.sep + "*.jpg"))
                folder1.extend(glob.glob(self.KernelBand1.text() + os.sep + "*.jpeg"))
            if len(self.KernelBand2.text()) > 0:
                folder2.extend(glob.glob(self.KernelBand2.text() + os.sep + "*.tif?"))
                folder2.extend(glob.glob(self.KernelBand2.text() + os.sep + "*.jpg"))
                folder2.extend(glob.glob(self.KernelBand2.text() + os.sep + "*.jpeg"))
            if len(self.KernelBand3.text()) > 0:
                folder3.extend(glob.glob(self.KernelBand3.text() + os.sep + "*.tif?"))
                folder3.extend(glob.glob(self.KernelBand3.text() + os.sep + "*.jpg"))
                folder3.extend(glob.glob(self.KernelBand3.text() + os.sep + "*.jpeg"))
            if len(self.KernelBand4.text()) > 0:
                folder4.extend(glob.glob(self.KernelBand4.text() + os.sep + "*.tif?"))
                folder4.extend(glob.glob(self.KernelBand4.text() + os.sep + "*.jpg"))
                folder4.extend(glob.glob(self.KernelBand4.text() + os.sep + "*.jpeg"))
            if len(self.KernelBand5.text()) > 0:
                folder5.extend(glob.glob(self.KernelBand5.text() + os.sep + "*.tif?"))
                folder5.extend(glob.glob(self.KernelBand5.text() + os.sep + "*.jpg"))
                folder5.extend(glob.glob(self.KernelBand5.text() + os.sep + "*.jpeg"))
            if len(self.KernelBand6.text()) > 0:
                folder6.extend(glob.glob(self.KernelBand6.text() + os.sep + "*.tif?"))
                folder6.extend(glob.glob(self.KernelBand6.text() + os.sep + "*.jpg"))
                folder6.extend(glob.glob(self.KernelBand6.text() + os.sep + "*.jpeg"))
            folder1.sort()
            folder2.sort()
            folder3.sort()
            folder4.sort()
            folder5.sort()
            folder6.sort()
            outfolder = self.KernelRenameOutputFolder.text()
            if not os.path.exists(outfolder):
                os.mkdir(outfolder)
            all_folders = [folder1, folder2, folder3, folder4, folder5, folder6]
            underscore = 1
            for folder in all_folders:

                counter = 1

                if len(folder) > 0:
                    if self.KernelRenameMode.currentIndex() == 0:
                        for tiff in folder:


                            shutil.copyfile(tiff, outfolder + os.sep + "IMG_" + str(counter).zfill(5) + '_' + str(
                                underscore) + '.' + tiff.split('.')[1])
                            counter = counter + 1
                        underscore = underscore + 1
                    elif self.KernelRenameMode.currentIndex() == 2:
                        for tiff in folder:
                            shutil.copyfile(tiff, outfolder + os.sep + str(self.KernelRenamePrefix.text()) + tiff.split(os.sep)[-1])
                            counter = counter + 1
                        underscore = underscore + 1
            self.KernelLog.append("Finished Renaming All Files.")
        except Exception as e:
            print(e)
    def on_KernelTransferButton_toggled(self):
        self.KernelLog.append(' ')
        try:
            if self.camera is None:
                raise ValueError('Device not found')


            if self.KernelTransferButton.isChecked():
                self.driveletters.clear()



                if self.KernelCameraSelect.currentIndex() == 0:
                    try:
                        for place, cam in enumerate(self.paths):
                            self.camera = cam
                            self.captureImage()
                            buf = [0] * 512
                            buf[0] = self.SET_COMMAND_REPORT
                            buf[1] = eCommand.CM_TRANSFER_MODE.value
                            time.sleep(5)
                            self.writeToKernel(buf)
                            self.KernelLog.append("Camera " + str(self.pathnames[place]) + " entering Transfer mode")

                            # self.KernelLog.append("Confirming camera entered transfer mode...")
                            QtWidgets.QApplication.processEvents()
                            found = False
                            stop = time.time()
                            while int(time.time() - stop) < 30:
                                QtWidgets.QApplication.processEvents()
                                try:

                                    drv = 'C'
                                    while drv is not '[':
                                        # self.KernelLog.append("Drives " + str(self.driveletters))
                                        if os.path.isdir(drv + r":/dcim/"):
                                            files = glob.glob(drv + r":" + os.sep + r"dcim/*/*")
                                            if files:
                                                # self.KernelLog.append("Found Files")
                                                threechar = files[-1].split(os.sep)[-1][1:4]
                                                # self.KernelLog.append("Three Characters = " + str(threechar))
                                                if threechar == self.pathnames[place]:
                                                    self.KernelLog.append("Camera " + str(self.pathnames[place]) + " successfully connected to drive " + drv + ":" + os.sep)
                                                    QtWidgets.QApplication.processEvents()
                                                    found = True
                                                    self.driveletters.append(drv)
                                                    # self.KernelLog.append(str(self.driveletters))
                                                    os.unlink(files[-1])
                                                    break
                                        drv = chr(ord(drv) + 1)
                                    if found == True:
                                        break
                                except:
                                    self.KernelLog.append("Eror checking drive " + drv)
                            if found == False:
                                raise ValueError("Camera " +  str(self.pathnames[place]) + " did not switch modes successfully.")

                    except Exception as value_error:
                        self.KernelLog.append(str(value_error))
                        QtWidgets.QApplication.processEvents()







                else:
                    self.captureImage()
                    buf = [0] * 512
                    buf[0] = self.SET_COMMAND_REPORT
                    buf[1] = eCommand.CM_TRANSFER_MODE.value
                    self.writeToKernel(buf)
                    self.KernelLog.append("Selected camera entering Transfer mode")

                self.modalwindow = KernelTransfer(self)
                self.modalwindow.resize(400, 200)
                self.modalwindow.exec_()
                # self.KernelLog.append("We made it out of transfer window")
                if self.yestransfer:
                    # self.KernelLog.append("Transfer was enabled")
                    for place, drv in enumerate(self.driveletters):
                        ix = place + 1
                        self.KernelLog.append("Extracting images from Camera " + str(ix) + " of " + str(len(self.driveletters)) + ", at drive " + drv + r':')
                        QtWidgets.QApplication.processEvents()
                        if os.path.isdir(drv + r":" + os.sep + r"dcim"):
                            # try:
                            folders = glob.glob(drv + r":" + os.sep + r"dcim/*/")
                            files = glob.glob(drv + r":" + os.sep + r"dcim/*/*")
                            for fold in folders:
                                threechar = files[0].split(os.sep)[-1][1:4]

                                if os.path.exists(self.transferoutfolder + os.sep + threechar):
                                    foldercount = 1
                                    endloop = False
                                    while endloop is False:
                                        outdir = self.transferoutfolder + os.sep + threechar + str(foldercount)
                                        if os.path.exists(outdir):
                                            foldercount += 1
                                        else:
                                            os.mkdir(outdir)
                                            endloop = True
                                else:
                                    outdir = self.transferoutfolder + os.sep + threechar
                                    os.mkdir(outdir)
                                QtWidgets.QApplication.processEvents()
                                for file in files:
                                    if file.split(os.sep)[-1][1:4] == threechar:
                                        shutil.copy(file, outdir)
                                    else:
                                        threechar = file.split(os.sep)[-1][1:4]
                                        os.mkdir(self.transferoutfolder + os.sep + threechar)
                                        shutil.copy(file, self.transferoutfolder + os.sep + threechar)
                                    QtWidgets.QApplication.processEvents()
                            self.KernelLog.append("Finished extracting images from Camera " + str(place + 1) + " of " + str(len(self.driveletters)))
                            QtWidgets.QApplication.processEvents()
                        else:
                            self.KernelLog.append("No DCIM folder found in drive " + str(drv) + r":")
                            QtWidgets.QApplication.processEvents()

                    self.modalwindow = KernelDelete(self)
                    self.modalwindow.resize(400, 200)
                    self.modalwindow.exec_()

            else:
                for place, cam in enumerate(self.paths):
                    self.exitTransfer(self.driveletters[place])
        except Exception as e:
            self.exitTransfer()
            self.KernelTransferButton.setChecked(False)
            self.KernelLog.append("Error: " + str(e))
            QtWidgets.QApplication.processEvents()


    def on_KernelGain_currentIndexChanged(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_AE_GAIN.value
        if self.KernelExposureMode.currentIndex() == 0:
            buf[2] = self.KernelGain.currentIndex()
        else:
            buf[2] = 2
        res = self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)

    def on_KernelSetPoint_currentIndexChanged(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_AE_SETPOINT.value
        if self.KernelExposureMode.currentIndex() == 0:
            buf[2] = self.KernelSetPoint.currentIndex()
        else:
            buf[2] = 2
        res = self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)

    def on_KernelExposureMode_currentIndexChanged(self):
        if self.KernelCameraSelect.currentIndex() == 0:
            for path in self.paths:
                self.camera = path
                self.setExposure()
        else:
            self.setExposure()
    def setExposure(self):
        if self.KernelExposureMode.currentIndex() == 0:
            self.KernelShutterSpeed.setEnabled(True)
            self.KernelISO.setEnabled(True)
            self.KernelGain.setEnabled(False)
            self.KernelSetPoint.setEnabled(False)
            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_GAIN.value
            buf[2] = 2

            res = self.writeToKernel(buf)
            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_SETPOINT.value
            buf[2] = 2

            res = self.writeToKernel(buf)
            try:
                self.KernelUpdate()
            except Exception as e:
                print(e)
        else:
            self.KernelShutterSpeed.setEnabled(False)
            self.KernelISO.setEnabled(False)
            self.KernelGain.setEnabled(True)
            self.KernelSetPoint.setEnabled(True)
            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_SHUTTER.value
            buf[2] = 1

            res = self.writeToKernel(buf)
            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_ISO.value
            buf[2] = 8

            res = self.writeToKernel(buf)
            try:
                self.KernelUpdate()
            except Exception as e:
                print(e)
    def on_KernelCaptureButton_released(self):
        if self.KernelCameraSelect.currentIndex() == 0:
            for cam in self.paths:
                self.camera = cam
                self.captureImage()
            self.camera = self.paths[0]
        else:
            self.captureImage()
    def captureImage(self):
        try:
            buf = [0] * 512

            buf[0] = self.SET_COMMAND_REPORT
            if self.KernelCaptureMode.currentIndex() == 0:



                buf[1] = eCommand.CM_CAPTURE_PHOTO.value


            elif self.KernelCaptureMode.currentIndex() == 1:
                buf[1] = eCommand.CM_CONTINUOUS.value

            elif self.KernelCaptureMode.currentIndex() == 2:

                buf[1] = eCommand.CM_TIME_LAPSE.value

            elif self.KernelCaptureMode.currentIndex() == 3:

                buf[1] = eCommand.CM_RECORD_VIDEO.value
            elif self.KernelCaptureMode.currentIndex() == 4:

                buf[1] = eCommand.CM_RECORD_LOOPING_VIDEO.value
            else:
                self.KernelLog.append("Invalid capture mode.")

            if self.capturing == False:
                buf[2] = 1
                self.capturing = True
            else:
                buf[2] = 0
                self.capturing = False


            res = self.writeToKernel(buf)

            self.KernelUpdate()
        except Exception as e:
            print(e)
    def on_KernelShutterSpeed_currentIndexChanged(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_SHUTTER.value
        if self.KernelExposureMode.currentIndex() == 1:
            buf[2] = self.KernelShutterSpeed.currentIndex() + 1

        res = self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)
    def on_KernelISO_currentIndexChanged(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_ISO.value
        if self.KernelExposureMode.currentIndex() == 1:
            buf[2] = self.ISO_VALS[self.KernelISO.currentIndex()]
        else:
            buf[2] = self.ISO_VALS[3]

        res = self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)

    def getRegister(self, code):
        if code < eRegister.RG_SIZE.value:
            return self.regs[code]
        else:
            return 0
    def setRegister(self, code, value):
        if code >= eRegister.RG_SIZE.value:
            return False
        elif value == self.regs[code]:
            return False
        else:
            self.regs[code] = value
            return True
    def on_TestButton_released(self):
        buf = [0] * 512
        buf[0] = self.SET_COMMAND_REPORT
        buf[1] = eRegister.RG_CAMERA_ARRAY_TYPE.value
        artype = self.writeToKernel(buf)[2]
        print(artype)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)
    def writeToKernel(self, buffer):
        try:
            # if self.KernelCameraSelect.currentIndex() == 0 and rlist == False:
            #     r = []
            #     q = []
            #     rr = []
            #     for i, path in enumerate(self.paths):
            #         dev = hid.device()
            #         dev.open_path(path)
            #         q.append(dev.write(buffer))
            #         if buffer[0] == 3 and buffer[1] == 1:
            #             dev.close()
            #             return q
            #         else:
            #             r.append(dev.read(self.BUFF_LEN))
            #             dev.close()
            #
            #     return r
            # else:
            dev = hid.device()
            dev.open_path(self.camera)
            q = dev.write(buffer)
            if buffer[0] == 3 and buffer[1] == 1:
                dev.close()
                return q
            else:
                r = dev.read(self.BUFF_LEN)
                dev.close()
                return r
        except Exception as e:
            self.KernelLog.append("Error: " + str(e))


    def on_KernelBeep_toggled(self):
        buf = [0] * 512

        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_BEEPER_ENABLE.value
        if self.KernelBeep.isChecked():
            buf[2] = 1
        else:
            buf[2] = 0

        res = self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)
    def on_KernelPWMSignal_toggled(self):
        buf = [0] * 512

        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_PWM_TRIGGER.value
        if self.KernelPWMSignal.isChecked():
            buf[2] = 1
        else:
            buf[2] = 0

        res = self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)
    def on_KernelResetButton_released(self):
        buf = [0] * 512
        buf[0] = self.SET_COMMAND_REPORT
        buf[1] = eRegister.CM_RESET_CAMERA.value

        self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)
    def on_KernelFolderCount_currentIndexChanged(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_MEDIA_FILES_CNT.value
        buf[2] = self.KernelFolderCount.currentIndex()

        self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)
    def on_KernelVideoOut_currentIndexChanged(self):
        if self.KernelVideoOut.currentIndex() == 0:  # No Output
            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_DAC.value  # DAC Register
            buf[2] = 0
            self.writeToKernel(buf)

            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_HDMI.value  # HDMI Register
            buf[2] = 0
            self.writeToKernel(buf)
        elif self.KernelVideoOut.currentIndex() == 1:  # HDMI
            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_DAC.value  # DAC Register
            buf[2] = 0
            self.writeToKernel(buf)

            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_HDMI.value  # HDMI Register
            buf[2] = 1
            self.writeToKernel(buf)
        elif self.KernelVideoOut.currentIndex() == 2:  # SD( DAC )
            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_DAC.value  # DAC Register
            buf[2] = 1
            self.writeToKernel(buf)

            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_HDMI.value  # HDMI Register
            buf[2] = 0
            self.writeToKernel(buf)
        else:  # Both outputs
            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_DAC.value  # DAC Register
            buf[2] = 1
            self.writeToKernel(buf)

            buf = [0] * 512

            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_HDMI.value  # HDMI Register
            buf[2] = 1
            self.writeToKernel(buf)
        # self.camera.close()
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)
    def on_KernelIntervalButton_released(self):
        self.modalwindow = KernelModal(self)
        self.modalwindow.resize(400, 200)
        self.modalwindow.exec_()

        num = self.seconds % 168
        if num == 0:
            num = 1
        self.seconds = num
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)

    def on_KernelCANButton_released(self):
        self.modalwindow = KernelCAN(self)
        self.modalwindow.resize(400, 200)
        self.modalwindow.exec_()
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)

    def on_KernelTimeButton_released(self):
        self.modalwindow = KernelTime(self)
        self.modalwindow.resize(400, 200)
        self.modalwindow.exec_()
        try:
            self.KernelUpdate()
        except Exception as e:
            print(e)

    def writeToIntervalLine(self):
        self.KernelIntervalLine.clear()
        self.KernelIntervalLine.setText(
            str(self.weeks) + 'w, ' + str(self.days) + 'd, ' + str(self.hours) + 'h, ' + str(self.minutes) + 'm,' + str(
                self.seconds) + 's')

    #########Pre-Process Steps: Start#################
    def on_PreProcessCameraModel_currentIndexChanged(self, int):
        if self.PreProcessCameraModel.currentIndex() == 0 or self.PreProcessCameraModel.currentIndex() == 1:

            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880", "550/660/850", "475/550/850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(
                ["550/660/850", "475/550/850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 3:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["RGB", "RGN", "NGB", "NIR"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.PreProcessLens.setEnabled(True)
        elif self.PreProcessCameraModel.currentIndex() == 4:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 5:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Blue + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 6:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 7:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["RGN"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() > 7:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        else:
            self.PreProcessLens.clear()
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)

    def on_CalibrationCameraModel_currentIndexChanged(self, int):
        if self.CalibrationCameraModel.currentIndex() == 0 or self.CalibrationCameraModel.currentIndex() == 1:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880", "550/660/850", "475/550/850"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 2:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(
                ["550/660/850", "475/550/850"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 3:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["RGB", "RGN", "NGB", "NIR" ])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens.setEnabled(True)
        elif self.CalibrationCameraModel.currentIndex() == 4:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 5:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 5:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentIndex() == 6:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentIndex() == 7:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["RGN"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() > 7:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)


        else:
            self.CalibrationLens.clear()
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.setEnabled(False)

    def on_CalibrationCameraModel_2_currentIndexChanged(self, int):
        if self.CalibrationCameraModel_2.currentIndex() == 0 or self.CalibrationCameraModel_2.currentIndex() == 1:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(
                ["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850",
                 "880", "550/660/850", "475/550/850"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(
                ["550/660/850", "475/550/850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)
        elif self.CalibrationCameraModel_2.currentIndex() == 3:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["RGB", "RGN", "NGB", "NIR"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_2.setEnabled(True)
        elif self.CalibrationCameraModel_2.currentIndex() == 4:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)
        elif self.CalibrationCameraModel_2.currentIndex() == 5:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)
        elif self.CalibrationCameraModel_2.currentIndex() == 5:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentIndex() == 6:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentIndex() == 7:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["RGN"])
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)
        elif self.CalibrationCameraModel_2.currentIndex() > 7:
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)


        else:
            self.CalibrationLens_2.clear()
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.setEnabled(False)

    def on_CalibrationCameraModel_3_currentIndexChanged(self, int):
        if self.CalibrationCameraModel_3.currentIndex() == 0 or self.CalibrationCameraModel_3.currentIndex() == 1:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(
                ["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850",
                 "880", "550/660/850", "475/550/850"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(
                ["550/660/850", "475/550/850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)
        elif self.CalibrationCameraModel_3.currentIndex() == 3:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["RGB", "RGN", "NGB", "NIR"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_3.setEnabled(True)
        elif self.CalibrationCameraModel_3.currentIndex() == 4:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)
        elif self.CalibrationCameraModel_3.currentIndex() == 5:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)
        elif self.CalibrationCameraModel_3.currentIndex() == 5:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentIndex() == 6:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentIndex() == 7:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["RGN"])
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)
        elif self.CalibrationCameraModel_3.currentIndex() > 7:
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)


        else:
            self.CalibrationLens_3.clear()
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.setEnabled(False)

    def on_CalibrationCameraModel_4_currentIndexChanged(self, int):
        if self.CalibrationCameraModel_4.currentIndex() == 0 or self.CalibrationCameraModel_4.currentIndex() == 1:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(
                ["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850",
                 "880", "550/660/850", "475/550/850"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(
                ["550/660/850", "475/550/850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)
        elif self.CalibrationCameraModel_4.currentIndex() == 3:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["RGB", "RGN", "NGB", "NIR"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_4.setEnabled(True)
        elif self.CalibrationCameraModel_4.currentIndex() == 4:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)
        elif self.CalibrationCameraModel_4.currentIndex() == 5:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)
        elif self.CalibrationCameraModel_4.currentIndex() == 5:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentIndex() == 6:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentIndex() == 7:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["RGN"])
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)
        elif self.CalibrationCameraModel_4.currentIndex() > 7:
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)


        else:
            self.CalibrationLens_4.clear()
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.setEnabled(False)

    def on_CalibrationCameraModel_5_currentIndexChanged(self, int):
        if self.CalibrationCameraModel_5.currentIndex() == 0 or self.CalibrationCameraModel_5.currentIndex() == 1:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(
                ["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850",
                 "880", "550/660/850", "475/550/850"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(
                ["550/660/850", "475/550/850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)
        elif self.CalibrationCameraModel_5.currentIndex() == 3:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["RGB", "RGN", "NGB", "NIR"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_5.setEnabled(True)
        elif self.CalibrationCameraModel_5.currentIndex() == 4:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)
        elif self.CalibrationCameraModel_5.currentIndex() == 5:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)
        elif self.CalibrationCameraModel_5.currentIndex() == 5:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentIndex() == 6:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentIndex() == 7:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["RGN"])
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)
        elif self.CalibrationCameraModel_5.currentIndex() > 7:
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)


        else:
            self.CalibrationLens_5.clear()
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.setEnabled(False)

    def on_CalibrationCameraModel_6_currentIndexChanged(self, int):
        if self.CalibrationCameraModel_6.currentIndex() == 0 or self.CalibrationCameraModel_6.currentIndex() == 1:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(
                ["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850",
                 "880", "550/660/850", "475/550/850"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(
                ["550/660/850", "475/550/850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)
        elif self.CalibrationCameraModel_6.currentIndex() == 3:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["RGB", "RGN", "NGB", "NIR"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_6.setEnabled(True)
        elif self.CalibrationCameraModel_6.currentIndex() == 4:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)
        elif self.CalibrationCameraModel_6.currentIndex() == 5:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)
        elif self.CalibrationCameraModel_6.currentIndex() == 5:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentIndex() == 6:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentIndex() == 7:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["RGN"])
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)
        elif self.CalibrationCameraModel_6.currentIndex() > 7:
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)


        else:
            self.CalibrationLens_6.clear()
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.setEnabled(False)



    def on_PreProcessInButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            folder = QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read())
            self.PreProcessInFolder.setText(folder)
            self.PreProcessOutFolder.setText(folder)
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.PreProcessInFolder.text())

    def on_PreProcessOutButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.PreProcessOutFolder.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.PreProcessOutFolder.text())


    def on_PreProcessButton_released(self):
        if self.PreProcessCameraModel.currentIndex() == -1:
            self.PreProcessLog.append("Attention! Please select a camera model.\n")
        else:
            # self.PreProcessLog.append(r'Extracting vignette corection data')


            infolder = self.PreProcessInFolder.text()
            if len(infolder) == 0:
                self.PreProcessLog.append("Attention! Please select an input folder.\n")
                return 0
            outdir = self.PreProcessOutFolder.text()
            if len(outdir) == 0:
                self.PreProcessLog.append("Attention! No Output folder selected, creating output under input folder.\n")
                outdir = infolder
            foldercount = 1
            endloop = False
            while endloop is False:
                outfolder = outdir + os.sep + "Processed_" + str(foldercount)
                if os.path.exists(outfolder):
                    foldercount += 1
                else:
                    os.mkdir(outfolder)
                    endloop = True

            # self.PreProcessLog.append("Input folder: " + infolder)
            # self.PreProcessLog.append("Output folder: " + outfolder)
            try:
                self.preProcessHelper(infolder, outfolder)
            except Exception as e:
                self.PreProcessLog.append(str(e))
            self.PreProcessLog.append("Finished Processing Images.")
            # if os.path.exists(modpath + os.sep + 'Vig'):
            #     shutil.rmtree(modpath + os.sep + 'Vig')

                # Pre-Process Steps: End

                # Calibration Steps: Start

    def on_CalibrationInButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationInFolder.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationInFolder.text())
    def on_CalibrationInButton_2_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationInFolder_2.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationInFolder_2.text())
    def on_CalibrationInButton_3_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationInFolder_3.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationInFolder_3.text())
    def on_CalibrationInButton_4_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationInFolder_4.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationInFolder_4.text())
    def on_CalibrationInButton_5_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationInFolder_5.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationInFolder_5.text())
    def on_CalibrationInButton_6_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationInFolder_6.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationInFolder_6.text())


    def on_CalibrationQRButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationQRFile.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationQRFile.text())
    def on_CalibrationQRButton_2_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationQRFile_2.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationQRFile_2.text())
    def on_CalibrationQRButton_3_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationQRFile_3.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationQRFile_3.text())
    def on_CalibrationQRButton_4_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationQRFile_4.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationQRFile_4.text())
    def on_CalibrationQRButton_5_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationQRFile_5.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationQRFile_5.text())
    def on_CalibrationQRButton_6_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationQRFile_6.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationQRFile_6.text())

    def on_CalibrationGenButton_released(self):
        try:
            if self.CalibrationCameraModel.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile.text()) > 0:
                self.qrcoeffs = self.findQR(self.CalibrationQRFile.text(), [self.CalibrationCameraModel.currentIndex(), self.CalibrationFilter.currentIndex(), self.CalibrationLens.currentIndex()])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            self.CalibrationLog.append(str(e))
    def on_CalibrationGenButton_2_released(self):
        try:
            if self.CalibrationCameraModel_2.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_2.text()) > 0:
                self.qrcoeffs2 = self.findQR(self.CalibrationQRFile_2.text(), [self.CalibrationCameraModel_2.currentIndex(), self.CalibrationFilter_2.currentIndex(), self.CalibrationLens_2.currentIndex()])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            self.CalibrationLog.append(str(e))
    def on_CalibrationGenButton_3_released(self):
        try:
            if self.CalibrationCameraModel_3.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_3.text()) > 0:
                self.qrcoeffs3 = self.findQR(self.CalibrationQRFile_3.text(), [self.CalibrationCameraModel_3.currentIndex(), self.CalibrationFilter_3.currentIndex(), self.CalibrationLens_3.currentIndex()])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            self.CalibrationLog.append(str(e))
    def on_CalibrationGenButton_4_released(self):
        try:
            if self.CalibrationCameraModel_4.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_4.text()) > 0:
                self.qrcoeffs4 = self.findQR(self.CalibrationQRFile_4.text(), [self.CalibrationCameraModel_4.currentIndex(), self.CalibrationFilter_4.currentIndex(), self.CalibrationLens_4.currentIndex()])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            self.CalibrationLog.append(str(e))
    def on_CalibrationGenButton_5_released(self):
        try:
            if self.CalibrationCameraModel_5.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_5.text()) > 0:
                self.qrcoeffs5 = self.findQR(self.CalibrationQRFile_5.text(), [self.CalibrationCameraModel_5.currentIndex(), self.CalibrationFilter_5.currentIndex(), self.CalibrationLens_5.currentIndex()])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            self.CalibrationLog.append(str(e))
    def on_CalibrationGenButton_6_released(self):
        try:
            if self.CalibrationCameraModel_6.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_6.text()) > 0:
                self.qrcoeffs6 = self.findQR(self.CalibrationQRFile_6.text(), [self.CalibrationCameraModel_6.currentIndex(), self.CalibrationFilter_6.currentIndex(), self.CalibrationLens_6.currentIndex()])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            self.CalibrationLog.append(str(e))

    def on_CalibrateButton_released(self):
        try:
            if self.CalibrationCameraModel.currentIndex() == -1\
                    and self.CalibrationCameraModel_2.currentIndex() == -1 \
                    and self.CalibrationCameraModel_3.currentIndex() == -1 \
                    and self.CalibrationCameraModel_4.currentIndex() == -1 \
                    and self.CalibrationCameraModel_5.currentIndex() == -1 \
                    and self.CalibrationCameraModel_6.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationInFolder.text()) <= 0 \
                    and len(self.CalibrationInFolder_2.text()) <= 0 \
                    and len(self.CalibrationInFolder_3.text()) <= 0 \
                    and len(self.CalibrationInFolder_4.text()) <= 0 \
                    and len(self.CalibrationInFolder_5.text()) <= 0 \
                    and len(self.CalibrationInFolder_6.text()) <= 0:
                self.CalibrationLog.append("Attention! Please select a calibration folder.\n")
            else:
                self.firstpass = True
                # self.CalibrationLog.append("CSV Input: \n" + str(self.refvalues))
                # self.CalibrationLog.append("Calibration button pressed.\n")
                calfolder = self.CalibrationInFolder.text()
                calfolder2 = self.CalibrationInFolder_2.text()
                calfolder3 = self.CalibrationInFolder_3.text()
                calfolder4 = self.CalibrationInFolder_4.text()
                calfolder5 = self.CalibrationInFolder_5.text()
                calfolder6 = self.CalibrationInFolder_6.text()
                pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                 "greenmax": 0.0, "greenmin": 65535.0,
                                 "bluemax": 0.0, "bluemin": 65535.0}
                # self.CalibrationLog.append("Calibration target folder is: " + calfolder + "\n")
                files_to_calibrate = []
                files_to_calibrate2 = []
                files_to_calibrate3 = []
                files_to_calibrate4 = []
                files_to_calibrate5 = []
                files_to_calibrate6 = []

                # self.CalibrationLog.append("Files to calibrate[0]: " + files_to_calibrate[0])



                indexes = [[self.CalibrationCameraModel.currentIndex(), self.CalibrationFilter.currentIndex(), self.CalibrationLens.currentIndex()],
                           [self.CalibrationCameraModel_2.currentIndex(), self.CalibrationFilter_2.currentIndex(),
                            self.CalibrationLens_2.currentIndex()],
                           [self.CalibrationCameraModel_3.currentIndex(), self.CalibrationFilter_3.currentIndex(),
                            self.CalibrationLens_3.currentIndex()],
                           [self.CalibrationCameraModel_4.currentIndex(), self.CalibrationFilter_4.currentIndex(),
                            self.CalibrationLens_4.currentIndex()],
                           [self.CalibrationCameraModel_5.currentIndex(), self.CalibrationFilter_5.currentIndex(),
                            self.CalibrationLens_5.currentIndex()],
                           [self.CalibrationCameraModel_6.currentIndex(), self.CalibrationFilter_6.currentIndex(),
                            self.CalibrationLens_6.currentIndex()],
                           ]
                # self.multiplication_values[self.qrcoeffs,
                #               self.qrcoeffs2,
                #               self.qrcoeffs3,
                #               self.qrcoeffs4,
                #               self.qrcoeffs5,
                #               self.qrcoeffs6]

                folderind = [calfolder,
                             calfolder2,
                             calfolder3,
                             calfolder4,
                             calfolder5,
                             calfolder6]

                for j, ind in enumerate(indexes):
                    # self.CalibrationLog.append("Checking folder " + str(j + 1))
                    if ind[0] == -1:
                        pass
                    elif ind[0] > 1:
                        if os.path.exists(folderind[j]):
                            # print("Cal1")
                            files_to_calibrate = []
                            os.chdir(folderind[j])
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                            print(str(files_to_calibrate))
                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate[0]:
                                # self.CalibrationLog.append("Found files to Calibrate.\n")
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir = folderind[j] + os.sep + "Calibrated_" + str(foldercount)
                                    if os.path.exists(outdir):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir)
                                        endloop = True
                                for calpixel in files_to_calibrate:
                                    # print("MM1")
                                    os.chdir(folderind[j])
                                    temp1 = cv2.imread(calpixel, -1)
                                    self.monominmax["min"] = min(temp1.min(), self.monominmax["min"])
                                    self.monominmax["max"] = max(temp1.max(), self.monominmax["max"])


                        for calpixel in files_to_calibrate:

                            img = cv2.imread(calpixel, -1)

                            blue = img[:, :, 0]
                            green = img[:, :, 1]
                            red = img[:, :, 2]


                            if self.useqr == True:
                                red = (self.multiplication_values["Red"] * red)
                                green = (self.multiplication_values["Green"] * green)
                                blue = (self.multiplication_values["Blue"] * blue)
                            # these are a little confusing, but the check to find the highest and lowest pixel value
                            # in each channel in each image and keep the highest/lowest value found.
                            if self.seed_pass == False:
                                pixel_min_max["redmax"] = np.percentile(red, 99)
                                pixel_min_max["redmin"] = np.percentile(red, 1)
                                pixel_min_max["greenmax"] = np.percentile(green, 99)
                                pixel_min_max["greenmin"] = np.percentile(green, 1)
                                pixel_min_max["bluemax"] = np.percentile(blue, 99)
                                pixel_min_max["bluemin"] = np.percentile(blue, 1)

                                # pixel_min_max["redmax"] = red.max()
                                # pixel_min_max["redmin"] = red.min()
                                # pixel_min_max["greenmax"] = green.max()
                                # pixel_min_max["greenmin"] = green.min()
                                # pixel_min_max["bluemax"] = blue.max()
                                # pixel_min_max["bluemin"] = blue.min()
                                self.seed_pass = True
                            else:
                                # pixel_min_max["redmax"] = max(red.max(), pixel_min_max["redmax"])
                                # pixel_min_max["redmin"] = min(red.min(), pixel_min_max["redmin"])
                                # pixel_min_max["greenmax"] = max(green.max(), pixel_min_max["greenmax"])
                                # pixel_min_max["greenmin"] = min(green.min(), pixel_min_max["greenmin"])
                                # pixel_min_max["bluemax"] = max(blue.max(), pixel_min_max["bluemax"])
                                # pixel_min_max["bluemin"] = min(blue.min(), pixel_min_max["bluemin"])

                                pixel_min_max["redmax"] = max(np.percentile(red, 99), pixel_min_max["redmax"])
                                pixel_min_max["redmin"] = min(np.percentile(red, 1), pixel_min_max["redmin"])
                                pixel_min_max["greenmax"] = max(np.percentile(green, 99), pixel_min_max["greenmax"])
                                pixel_min_max["greenmin"] = min(np.percentile(green, 1), pixel_min_max["greenmin"])
                                pixel_min_max["bluemax"] = max(np.percentile(blue, 99), pixel_min_max["bluemax"])
                                pixel_min_max["bluemin"] = min(np.percentile(blue, 1), pixel_min_max["bluemin"])


                        else:
                            if ind[0] == 5:  # Survey1_NDVI
                                    pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_SURVEY1_NDVI_JPG[0]
                                    pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_SURVEY1_NDVI_JPG[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[3]) \
                                                               + self.BASE_COEFF_SURVEY1_NDVI_JPG[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[3]) \
                                                               + self.BASE_COEFF_SURVEY1_NDVI_JPG[2]
                            elif (ind[0] == 4) and ind[1] == 0:
                                if "tif" or "TIF" in calpixel:
                                    pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_SURVEY2_NDVI_TIF[0]
                                    pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_SURVEY2_NDVI_TIF[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[3]) \
                                                               + self.BASE_COEFF_SURVEY2_NDVI_TIF[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[3]) \
                                                               + self.BASE_COEFF_SURVEY2_NDVI_TIF[2]
                                elif "jpg" or "JPG" in calpixel:
                                    pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_SURVEY2_NDVI_JPG[0]
                                    pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_SURVEY2_NDVI_JPG[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[3]) \
                                                               + self.BASE_COEFF_SURVEY2_NDVI_JPG[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[3]) \
                                                               + self.BASE_COEFF_SURVEY2_NDVI_JPG[2]
                            elif ind[0] == 8:
                                if "tif" or "TIF" in calpixel:
                                    pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIX3_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIX3_NDVI_TIF[0]
                                    pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIX3_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIX3_NDVI_TIF[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIX3_NDVI_TIF[3]) \
                                                               + self.BASE_COEFF_DJIX3_NDVI_TIF[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIX3_NDVI_TIF[3]) \
                                                               + self.BASE_COEFF_DJIX3_NDVI_TIF[2]
                                elif "jpg" or "JPG" in calpixel:
                                    pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIX3_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_DJIX3_NDVI_JPG[0]
                                    pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIX3_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_DJIX3_NDVI_JPG[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIX3_NDVI_JPG[3]) \
                                                               + self.BASE_COEFF_DJIX3_NDVI_JPG[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIX3_NDVI_JPG[3]) \
                                                               + self.BASE_COEFF_DJIX3_NDVI_JPG[2]
                            elif ind[0] == 5:
                                if "tif" or "TIF" in calpixel:
                                    pixel_min_max["redmax"] = (
                                                              pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[0]
                                    pixel_min_max["redmin"] = (
                                                              pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[2]
                                elif "jpg" or "JPG" in calpixel:
                                    pixel_min_max["redmax"] = (
                                                              pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[0]
                                    pixel_min_max["redmin"] = (
                                                              pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[2]
                            elif ind[0] == 6 or ind[0] > 7:
                                if "tif" or "TIF" in calpixel:
                                    pixel_min_max["redmax"] = (
                                                              pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                    pixel_min_max["redmin"] = (
                                                              pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                                elif "jpg" or "JPG" in calpixel:
                                    pixel_min_max["redmax"] = (
                                                              pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                    pixel_min_max["redmin"] = (
                                                              pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                              + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                    pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                                    pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                        3]) \
                                                               + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]

                        for i, calfile in enumerate(files_to_calibrate):

                            cameramodel = ind
                            if self.useqr == True:
                                # self.CalibrationLog.append("Using QR")
                                try:
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " of " + str(len(files_to_calibrate)))
                                    QtWidgets.QApplication.processEvents()


                                    self.CalibratePhotos(calfile, self.multiplication_values, pixel_min_max, outdir, ind)
                                except Exception as e:
                                    self.CalibrationLog.append(str(e))
                            else:
                                # self.CalibrationLog.append("NOT Using QR")
                                if cameramodel == 3 and self.CalibrationFilter.currentIndex() == 0:  # Survey2 NDVI
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NDVI_TIF, pixel_min_max, outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NDVI_JPG, pixel_min_max, outdir, ind)
                                elif cameramodel == 3 and self.CalibrationFilter.currentIndex() == 1:  # Survey2 NIR
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NIR_TIF, pixel_min_max, outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NIR_JPG, pixel_min_max, outdir, ind)
                                elif cameramodel == 3 and self.CalibrationFilter.currentIndex() == 2:  # Survey2 RED
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_RED_TIF, pixel_min_max, outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_RED_JPG, pixel_min_max, outdir, ind)
                                elif cameramodel == 3 and self.CalibrationFilter.currentIndex() == 3:  # Survey2 GREEN
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_GREEN_TIF, pixel_min_max, outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_GREEN_JPG, pixel_min_max, outdir, ind)
                                elif cameramodel == 3 and self.CalibrationFilter.currentIndex() == 4:  # Survey2 BLUE
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_BLUE_TIF, pixel_min_max, outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_BLUE_JPG, pixel_min_max, outdir, ind)
                                elif cameramodel == 4:  # Survey1 NDVI
                                    if "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY1_NDVI_JPG, pixel_min_max, outdir, ind)
                                elif cameramodel == 8:  # DJI X3 NDVI
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_DJIX3_NDVI_TIF, pixel_min_max, outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_DJIX3_NDVI_JPG, pixel_min_max, outdir, ind)
                                elif cameramodel == 5:  # DJI Phantom4 NDVI
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF, pixel_min_max,
                                                             outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG, pixel_min_max,
                                                             outdir, ind)
                                elif cameramodel == 6 or cameramodel == 7:  # DJI PHANTOM3 NDVI
                                    if "TIF" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF, pixel_min_max,
                                                             outdir, ind)
                                    elif "JPG" in calfile.split('.')[2].upper():
                                        self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM3_NDVI_JPG, pixel_min_max,
                                                             outdir, ind)
                                else:
                                    self.CalibrationLog.append(
                                        "No default calibration data for selected camera model. Please please supply a MAPIR Reflectance Target to proceed.\n")
                                    break
                    else:
                        files_to_calibrate = []
                        os.chdir(calfolder)
                        files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                        files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                        files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                        files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                        print(str(files_to_calibrate))
                        files_to_calibrate2 = []
                        os.chdir(calfolder2)
                        files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                        files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                        files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                        files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                        print(str(files_to_calibrate2))
                        files_to_calibrate3 = []
                        os.chdir(calfolder3)
                        files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                        files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                        files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                        files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                        print(str(files_to_calibrate3))
                        files_to_calibrate4 = []
                        os.chdir(calfolder4)
                        files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                        files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                        files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                        files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                        print(str(files_to_calibrate4))
                        files_to_calibrate5 = []
                        os.chdir(calfolder5)
                        files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                        files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                        files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                        files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                        print(str(files_to_calibrate5))
                        files_to_calibrate6 = []
                        os.chdir(calfolder6)
                        files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                        files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                        files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                        files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                        print(str(files_to_calibrate6))

                        for calpixel in files_to_calibrate:
                            # print("MM1")
                            os.chdir(calfolder)
                            temp1 = cv2.imread(calpixel, -1)
                            self.monominmax["min"] = min(temp1.min(), self.monominmax["min"])
                            self.monominmax["max"] = max(temp1.max(), self.monominmax["max"])
                        for calpixel2 in files_to_calibrate2:
                            # print("MM2")
                            os.chdir(calfolder2)
                            temp2 = cv2.imread(calpixel2, -1)

                            self.monominmax["min"] = min(temp2.min(), self.monominmax["min"])
                            self.monominmax["max"] = max(temp2.max(), self.monominmax["max"])
                        for calpixel3 in files_to_calibrate3:
                            # print("MM3")
                            os.chdir(calfolder3)
                            temp3 = cv2.imread(calpixel3, -1)

                            self.monominmax["min"] = min(temp3.min(), self.monominmax["min"])
                            self.monominmax["max"] = max(temp3.max(), self.monominmax["max"])
                        for calpixel4 in files_to_calibrate4:
                            # print("MM4")
                            os.chdir(calfolder4)
                            temp4 = cv2.imread(calpixel4, -1)

                            self.monominmax["min"] = min(temp4.min(), self.monominmax["min"])
                            self.monominmax["max"] = max(temp4.max(), self.monominmax["max"])
                        for calpixel5 in files_to_calibrate5:
                            # print("MM5")
                            os.chdir(calfolder5)
                            temp5 = cv2.imread(calpixel5, -1)

                            self.monominmax["min"] = min(temp5.min(), self.monominmax["min"])
                            self.monominmax["max"] = max(temp5.max(), self.monominmax["max"])
                        for calpixel6 in files_to_calibrate6:
                            # print("MM6")
                            os.chdir(calfolder6)
                            temp6 = cv2.imread(calpixel6, -1)

                            self.monominmax["min"] = min(temp6.min(), self.monominmax["min"])
                            self.monominmax["max"] = max(temp6.max(), self.monominmax["max"])

                        if os.path.exists(calfolder):
                            # # print("Cal1")
                            # files_to_calibrate = []
                            # os.chdir(calfolder)
                            # files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            # files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            # files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            # files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                            # print(str(files_to_calibrate))
                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate[0]:
                                # self.CalibrationLog.append("Found files to Calibrate.\n")
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir = calfolder + os.sep + "Calibrated_" + str(foldercount)
                                    if os.path.exists(outdir):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir)
                                        endloop = True

                                for i, calfile in enumerate(files_to_calibrate):
                                    # print("cb1")
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " from folder 1")
                                    QtWidgets.QApplication.processEvents()
                                    os.chdir(calfolder)
                                    if self.useqr == True:
                                        # self.CalibrationLog.append("Using QR")
                                        self.CalibrateMono(calfile, self.qrcoeffs, outdir, ind)
                                    else:
                                        if self.CalibrationFilter.currentIndex() == 0:
                                            self.CalibrateMono(calfile, self.BASE_COEFF_KERNEL_F590, outdir, ind)
                                        elif self.CalibrationFilter.currentIndex() == 1:
                                            self.CalibrateMono(calfile, self.BASE_COEFF_KERNEL_F650, outdir, ind)
                                        elif self.CalibrationFilter.currentIndex() == 2:
                                            self.CalibrateMono(calfile, self.BASE_COEFF_KERNEL_F850, outdir, ind)
                        if os.path.exists(calfolder2):
                            # print("Cal2")
                            # files_to_calibrate2 = []
                            # os.chdir(calfolder2)
                            # files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            # files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            # files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            # files_to_calibrate2.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                            # print(str(files_to_calibrate2))
                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate2[0]:
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir2 = calfolder2 + os.sep + "Calibrated_" + str(foldercount)
                                    if os.path.exists(outdir2):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir2)
                                        endloop = True

                                for i, calfile2 in enumerate(files_to_calibrate2):
                                    # print("cb2")
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " from folder 2")
                                    QtWidgets.QApplication.processEvents()
                                    os.chdir(calfolder2)
                                    if self.useqr == True:
                                        # self.CalibrationLog.append("Using QR")
                                        self.CalibrateMono(calfile2, self.qrcoeffs2, outdir2, ind)
                                    else:
                                        if self.CalibrationFilter.currentIndex() == 0:
                                            self.CalibrateMono(calfile2, self.BASE_COEFF_KERNEL_F590, outdir2)
                                        elif self.CalibrationFilter.currentIndex() == 1:
                                            self.CalibrateMono(calfile2, self.BASE_COEFF_KERNEL_F650, outdir2)
                                        elif self.CalibrationFilter.currentIndex() == 2:
                                            self.CalibrateMono(calfile2, self.BASE_COEFF_KERNEL_F850, outdir2)
                        if os.path.exists(calfolder3):
        #                     # print("Cal3")
        #                     files_to_calibrate3 = []
        #                     os.chdir(calfolder3)
        #                     files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
        #                     files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
        #                     files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
        #                     files_to_calibrate3.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
        #                     print(str(files_to_calibrate3))
                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate3[0]:
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir3 = calfolder3 + os.sep + "Calibrated_" + str(foldercount)
                                    if os.path.exists(outdir3):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir3)
                                        endloop = True

                                for i, calfile3 in enumerate(files_to_calibrate3):
                                    # print("cb3")
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " from folder 3")
                                    QtWidgets.QApplication.processEvents()
                                    os.chdir(calfolder3)
                                    if self.useqr == True:
                                        # self.CalibrationLog.append("Using QR")
                                        self.CalibrateMono(calfile3, self.qrcoeffs3, outdir3, ind)
                                    else:
                                        if self.CalibrationFilter.currentIndex() == 0:
                                            self.CalibrateMono(calfile3, self.BASE_COEFF_KERNEL_F590, outdir3)
                                        elif self.CalibrationFilter.currentIndex() == 1:
                                            self.CalibrateMono(calfile3, self.BASE_COEFF_KERNEL_F650, outdir3)
                                        elif self.CalibrationFilter.currentIndex() == 2:
                                            self.CalibrateMono(calfile3, self.BASE_COEFF_KERNEL_F850, outdir3)
                        if os.path.exists(calfolder4):
                            # print("Cal4")
                            # files_to_calibrate4 = []
                            # os.chdir(calfolder4)
                            # files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            # files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            # files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            # files_to_calibrate4.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                            # print(str(files_to_calibrate4))
                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate4[0]:
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir4 = calfolder4 + os.sep + "Calibrated_" + str(foldercount)
                                    if os.path.exists(outdir4):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir4)
                                        endloop = True

                                for i, calfile4 in enumerate(files_to_calibrate4):
                                    # print("cb2")
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " from folder 4")
                                    QtWidgets.QApplication.processEvents()
                                    os.chdir(calfolder4)
                                    if self.useqr == True:
                                        # self.CalibrationLog.append("Using QR")
                                        self.CalibrateMono(calfile4, self.qrcoeffs4, outdir4, ind)
                                    else:
                                        if self.CalibrationFilter.currentIndex() == 0:
                                            self.CalibrateMono(calfile4, self.BASE_COEFF_KERNEL_F590, outdir4)
                                        elif self.CalibrationFilter.currentIndex() == 1:
                                            self.CalibrateMono(calfile4, self.BASE_COEFF_KERNEL_F650, outdir4)
                                        elif self.CalibrationFilter.currentIndex() == 2:
                                            self.CalibrateMono(calfile4, self.BASE_COEFF_KERNEL_F850, outdir4)
                        if os.path.exists(calfolder5):
                            # print("Cal5")
                            # files_to_calibrate5 = []
                            # os.chdir(calfolder5)
                            # files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            # files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            # files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            # files_to_calibrate5.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                            # print(str(files_to_calibrate5))
                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate5[0]:
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir5 = calfolder5 + os.sep + "Calibrated_" + str(foldercount)
                                    if os.path.exists(outdir5):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir5)
                                        endloop = True

                                for i, calfile5 in enumerate(files_to_calibrate5):
                                    # print("cb5")
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " from folder 5")
                                    QtWidgets.QApplication.processEvents()
                                    os.chdir(calfolder5)
                                    if self.useqr == True:
                                        # self.CalibrationLog.append("Using QR")
                                        self.CalibrateMono(calfile5, self.qrcoeffs5, outdir5, ind)
                                    else:
                                        if self.CalibrationFilter.currentIndex() == 0:
                                            self.CalibrateMono(calfile5, self.BASE_COEFF_KERNEL_F590, outdir5)
                                        elif self.CalibrationFilter.currentIndex() == 1:
                                            self.CalibrateMono(calfile5, self.BASE_COEFF_KERNEL_F650, outdir5)
                                        elif self.CalibrationFilter.currentIndex() == 2:
                                            self.CalibrateMono(calfile5, self.BASE_COEFF_KERNEL_F850, outdir5)
                        if os.path.exists(calfolder6):
                            # print("Cal6")
                            # files_to_calibrate6 = []
                            # os.chdir(calfolder6)
                            # files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            # files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            # files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            # files_to_calibrate6.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
                            # print(str(files_to_calibrate6))
                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate6[0]:
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir6 = calfolder6 + os.sep + "Calibrated_" + str(foldercount)
                                    if os.path.exists(outdir6):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir6)
                                        endloop = True



                                for i, calfile6 in enumerate(files_to_calibrate6):
                                    # print("cb6")
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " from folder 6")
                                    QtWidgets.QApplication.processEvents()
                                    os.chdir(calfolder6)
                                    if self.useqr == True:
                                        # self.CalibrationLog.append("Using QR")
                                        self.CalibrateMono(calfile6, self.qrcoeffs6, outdir6, ind)
                                    else:
                                        if self.CalibrationFilter.currentIndex() == 0:
                                            self.CalibrateMono(calfile6, self.BASE_COEFF_KERNEL_F590, outdir6)
                                        elif self.CalibrationFilter.currentIndex() == 1:
                                            self.CalibrateMono(calfile6, self.BASE_COEFF_KERNEL_F650, outdir6)
                                        elif self.CalibrationFilter.currentIndex() == 2:
                                            self.CalibrateMono(calfile6, self.BASE_COEFF_KERNEL_F850, outdir6)


                self.CalibrationLog.append("Finished Calibrating " + str(len(files_to_calibrate) + len(files_to_calibrate2) + len(files_to_calibrate3) + len(files_to_calibrate4) + len(files_to_calibrate5) + len(files_to_calibrate6)) + " images\n")
                self.seed_pass = False
        except Exception as e:
            print(repr(e))
            self.CalibrationLog.append(str(repr(e)))
    def CalibrateMono(self, photo, coeffs, output_directory, ind):
        refimg = cv2.imread(photo, -1)
        print(str(refimg))
        if len(refimg.shape) > 2:
            refimg = refimg[:,:,0]
        refimg = refimg.astype("uint16")
        pixmin = coeffs(self.monominmax["min"])
        pixmax = coeffs(self.monominmax["max"])
        tempim = coeffs(refimg)
        # pixmin = np.array((((self.monominmax["min"] ^ 2) * coeffs[0]) + (self.monominmax["min"] * coeffs[1]) + coeffs[1]), dtype=object)
        # pixmax = np.array((((self.monominmax["max"] ^ 2) * coeffs[0]) + (self.monominmax["max"] * coeffs[1]) + coeffs[1]), dtype=object)
        # tempim = np.array(((np.power(refimg, 2) * coeffs[0]) + (refimg * coeffs[1]) + coeffs[2]), dtype=object)
        # pixmin = (self.monominmax["min"] * coeffs[1]) + coeffs[0]
        # pixmax = (self.monominmax["max"] * coeffs[1]) + coeffs[0]
        # tempim = (refimg * coeffs[1]) + coeffs[0]
        tempim -= pixmin
        tempim /= (pixmax - pixmin)
        if self.IndexBox.checkState() == 0:
            tempim *= 65535.0

            tempim = tempim.astype("uint16")
        else:
            tempim = tempim.astype("float")
        # print(str(tempim))
        # tempim = np.floor((refimg * coeffs[1]) + coeffs[0]).astype("uint16")
        # tempim[tempim > 65535] = 65535
        # tempim[tempim < 0] = 0
        #
        # tempimg = tempim / tempim.max()
        #
        # tempimg *= 65535
        #
        # tempimg = tempimg.astype("uint16")

        refimg = tempim

        newimg = output_directory + photo.split('.')[1] + "_CALIBRATED." + photo.split('.')[2]

        cv2.imencode(".tif", refimg)
        cv2.imwrite(newimg, refimg)
        srin = gdal.Open(photo)
        inproj = srin.GetProjection()
        transform = srin.GetGeoTransform()
        gcpcount = srin.GetGCPs()
        srout = gdal.Open(newimg, gdal.GA_Update)
        srout.SetProjection(inproj)
        srout.SetGeoTransform(transform)
        srout.SetGCPs(gcpcount, srin.GetGCPProjection())
        self.copyExif(photo, newimg)

    def CalibratePhotos(self, photo, coeffs, minmaxes, output_directory, ind):
        refimg = cv2.imread(photo, -1)

        if True:
        #     clist = np.array([self.qrcoeffs,
        #              self.qrcoeffs2,
        #              self.qrcoeffs3,
        #              self.qrcoeffs4,
        #              self.qrcoeffs5,
        #              self.qrcoeffs6])
        #     refimg *= clist
        #
        #     refimg -= self.monominmax["min"]
        #     refimg /= (self.monominmax["max"] + self.monominmax["min"])
        #     refimg *= 65535
        #
        #     refimg = refimg.astype("uint16")
        # else:
            # kernel = np.ones((2, 2), np.uint16)
            # refimg = cv2.erode(refimg, kernel, iterations=1)
            # refimg = cv2.dilate(refimg, kernel, iterations=1)
            # imsize = np.shape(refimg)
            # if imsize[0] > self.imcols or imsize[1] > self.imrows:
            #     if "tif" or "TIF" in photo:
            #             tempimg = np.memmap(photo, dtype=np.uint16, shape=(imsize))
            #             refimg = None
            #             refimg = tempimg
            #     else:
            #             tempimg = np.memmap(photo, dtype=np.uint8, shape=(imsize))
            #             refimg = None
            #             refimg = tempimg

            ### split channels (using cv2.split caused too much overhead and made the host program crash)
            alpha = []
            blue = refimg[:, :, 0]
            green = refimg[:, :, 1]
            red = refimg[:, :, 2]
            red = (red * self.multiplication_values["Red"])
            green = (green * self.multiplication_values["Green"])
            blue = (blue * self.multiplication_values["Blue"])
            if refimg.shape[2] > 3:
                alpha = refimg[:, :, 3]
                refimg = copy.deepcopy(refimg[:, :, :3])



            ### find the maximum and minimum pixel values over the entire directory.
            if ind[0] == 5:  ###Survey1 NDVI
                maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
                minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
                # blue = refimg[:, :, 0] - (refimg[:, :, 2] * 0.80)  # Subtract the NIR bleed over from the blue channel
            elif ((ind[0] == 3) and (ind[1] == 3)) \
                    or ((ind[0] == 4) \
                    and (ind[1] == 1 or ind[1] == 2)):
                ### red and NIR
                maxpixel = minmaxes["redmax"]
                minpixel = minmaxes["redmin"]
            elif (ind[0] == 4) and ind[1] == 3:
                ### green
                maxpixel = minmaxes["greenmax"]
                minpixel = minmaxes["greenmin"]
            elif ((ind[0] == 4)) and ind[1] == 4:
                ### blue
                maxpixel = minmaxes["bluemax"]
                minpixel = minmaxes["bluemin"]
            elif (ind[0] == 3 and ind[1] == 1) or ind[0] == 2:
                ## RGN
                maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
                maxpixel = minmaxes["greenmax"] if minmaxes["greenmax"] > maxpixel else maxpixel
                minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
                minpixel = minmaxes["greenmin"] if minmaxes["greenmin"] < minpixel else minpixel
                # blue = (refimg[:, :, 0] / 35) * 100


#                 # red[red < 0] = 0
#                 # green[green < 0] = 0
                # tempimg = cv2.merge((blue, green, red)).astype("uint16")
                #
                # cv2.imwrite(str(output_directory + photo.split('.')[1] + "_SUBTRACTION." + photo.split('.')[2]), tempimg)
                # blue = blue.astype("uint16")
                # red = red.astype("uint16")
                # green = green.astype("uint16")
            elif (ind[0] == 3 and ind[1] == 2):
                maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
                maxpixel = minmaxes["greenmax"] if minmaxes["greenmax"] > maxpixel else maxpixel
                minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
                minpixel = minmaxes["greenmin"] if minmaxes["greenmin"] < minpixel else minpixel
                # red = (refimg[:, :, 2] / 30) * 100
                # blue = refimg[:, :, 0] - ((red * 35) / 100)
                # green = refimg[:, :, 1] - ((red * 35) / 100)
#                 # blue[blue < 0] = 0
#                 # green[green < 0] = 0
                # blue = blue.astype("uint16")
                # red = red.astype("uint16")
                # green = green.astype("uint16")
            elif ind[0] == 7:
                maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
                maxpixel = minmaxes["greenmax"] if minmaxes["greenmax"] > maxpixel else maxpixel
                minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
                minpixel = minmaxes["greenmin"] if minmaxes["greenmin"] < minpixel else minpixel
            else:  ###Survey2 NDVI
                maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
                minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
                # if ind[0] == 4:
                #     red = refimg[:, :, 2] - (refimg[:, :, 0] * 0.80)  # Subtract the NIR bleed over from the red channel



                ### Calibrate pixels based on the default reflectance values (or the values gathered from the MAPIR reflectance target)

            # red = (coeffs[0] * red)
            # green = (coeffs[1] * green)
            # blue = (coeffs[2] * blue)



            # index = self.calculateIndex(red, blue)
            # cv2.imwrite(output_directory + photo.split('.')[1] + "_SCALED_INDEX." + photo.split('.')[2], index)

            # if photo.split('.')[2].upper() == "JPG" or photo.split('.')[
            #     2].upper() == "JPEG" or self.Tiff2JpgBox.checkState() > 0:
            #     tempimg = cv2.merge((blue, green, red)).astype("uint8")
            # else:
            #     tempimg = cv2.merge((blue, green, red)).astype("uint16")
            # cv2.imwrite(output_directory + photo.split('.')[1] + "_SCALED." + photo.split('.')[2], tempimg)
            # red = np.array(((np.power(red, 2) * coeffs[0][0]) + (red * coeffs[0][1]) + coeffs[0][2]), dtype=object)
            # green = np.array(((np.power(green, 2) * coeffs[1][0]) + (green * coeffs[1][1]) + coeffs[1][2]), dtype=object)
            # blue = np.array(((np.power(blue, 2) * coeffs[2][0]) + (blue * coeffs[2][1]) + coeffs[2][2]), dtype=object)
            # red = (red * coeffs[1]) + coeffs[0]
            # green = (green * coeffs[3]) + coeffs[2]
            # blue = (blue * coeffs[5]) + coeffs[4]

            ### Scale calibrated values back down to a useable range (Adding 1 to avaoid 0 value pixels, as they will cause a
            #### devide by zero case when creating an index image.
            red = (((red - minpixel) / (maxpixel - minpixel)))
            green = (((green - minpixel) / (maxpixel - minpixel)))
            blue = (((blue - minpixel) / (maxpixel - minpixel)))
            if self.IndexBox.checkState() == 0:
                if photo.split('.')[2].upper() == "JPG" or photo.split('.')[
                    2].upper() == "JPEG" or self.Tiff2JpgBox.checkState() > 0:
                    # self.CalibrationLog.append("Entering JPG")
                    # QtWidgets.QApplication.processEvents()
                    # red = (((red - minpixel) / (maxpixel - minpixel)))
                    # green = (((green - minpixel) / (maxpixel - minpixel)))
                    # blue = (((blue - minpixel) / (maxpixel - minpixel)))
                    # # tempimg = cv2.merge((blue, green, red)).astype("uint8")
                    # # cv2.imwrite(output_directory + photo.split('.')[1] + "_Stretched." + photo.split('.')[2], tempimg)
                    # self.CalibrationLog.append("Removing Gamma")
                    # QtWidgets.QApplication.processEvents()
                    # red = np.power(red, 0.455)
                    # green = np.power(green, 0.455)
                    # blue = np.power(blue, 0.455)

                    red *= 255
                    green *= 255
                    blue *= 255
                    green[green < 0] = 0
                    red[red < 0] = 0
                    blue[blue < 0] = 0
                    red[red > 255] = 255
                    green[green > 255] = 255
                    blue[blue > 255] = 255
                    # index = self.calculateIndex(red, blue)
                    # cv2.imwrite(output_directory + photo.split('.')[1] + "_CALIBRATED_INDEX." + photo.split('.')[2], index)
                    red = red.astype("uint8")
                    green = green.astype("uint8")
                    blue = blue.astype("uint8")
                else:
                    # maxpixel *= 10
                    # minpixel *= 10

                    # tempimg = cv2.merge((blue, green, red)).astype("float32")
                    # cv2.imwrite(output_directory + photo.split('.')[1] + "_Percent." + photo.split('.')[2], tempimg)

                    red *= 65535
                    green *= 65535
                    blue *= 65535
                    # red[blue > 65535] = 65535
                    # red[green > 65535] = 65535
                    #
                    # green[red > 65535] = 65535
                    # green[blue > 65535] = 65535
                    #
                    # blue[red > 65535] = 65535
                    # blue[green > 65535] = 65535

                    green[green > 65535] = 65535
                    red[red > 65535] = 65535
                    blue[blue > 65535] = 65535

    #                 # red[blue < 0] = 0
    #                 # red[green < 0] = 0
                    #
    #                 # green[red < 0] = 0
    #                 # green[blue < 0] = 0
                    #
    #                 # blue[red < 0] = 0
    #                 # blue[green < 0] = 0
    #
                    green[green < 0] = 0
                    red[red < 0] = 0
                    blue[blue < 0] = 0
                # if photo.split('.')[2].upper() == "JPG":  # Remove the gamma correction that is automaticall applied to JPGs
                #     index = self.calculateIndex(red, blue)
                    # cv2.imwrite(output_directory + photo.split('.')[1] + "_CALIBRATED_INDEX." + photo.split('.')[2], index)

                    ### Merge the channels back into a single image
                    red = red.astype("uint16")
                    green = green.astype("uint16")
                    blue = blue.astype("uint16")
                refimg = cv2.merge((blue, green, red))
            else:
                green[green > 1.0] = 1.0
                red[red > 1.0] = 1.0
                blue[blue > 1.0] = 1.0
                green[green < 0.0] = 0.0
                red[red < 0.0] = 0.0
                blue[blue < 0.0] = 0.0
                red = red.astype("float")
                green = green.astype("float")
                blue = blue.astype("float")

            # if alpha == []:
                refimg = cv2.merge((blue, green, red))
                refimg = cv2.normalize(refimg.astype("float"), None, 0.0, 1.0, cv2.NORM_MINMAX)
            # else:
            #     alpha = alpha.astype("uint16")
            #     refimg = cv2.merge((blue, green, red, alpha))
            # if refimg.shape[2] > 3:
            #     white_background_image = np.ones_like(refimg, dtype=np.uint8) * 255
            #     a_factor = alpha[:, :, np.newaxis].astype(np.float32) / 255.0
            #     a_factor = np.concatenate((a_factor, a_factor, a_factor), axis=2)
            #     base = refimg.astype(np.float32) * a_factor
            #     white = white_background_image.astype(np.float32) * (1 - a_factor)
            #     refimg = base + white
            #     ### If the image is a .tiff then change it to a 16 bit color image
            # if "TIF" in photo.split('.')[2].upper() and not self.Tiff2JpgBox.checkState() > 0:
            #     refimg = refimg.astype("uint16")


            if (((ind[0] == 4)) and ind[1] == 0) or ((ind[0] > 4) and (ind[0] != 7)):
                ### Remove green information if NDVI camera
                refimg[:, :, 1] = 1

            elif (ind[0] == 4 and ind[1] == 1) \
                    or (ind[0] == 3 and ind[1] == 3) or (ind[0] == 4 and self.CalibrationFilter.currentIn0dex() == 2):
                ### Remove blue and green information if NIR or Red camera
                refimg[:, :, 0] = 1
                refimg[:, :, 1] = 1
            elif ((ind[0] == 4)) and ind[1] == 3:
                ### Remove blue and red information if GREEN camera
                refimg[:, :, 0] = 1
                refimg[:, :, 2] = 1
            elif ((ind[0] == 4)) and ind[1] == 4:
                ### Remove red and green information if BLUE camera
                refimg[:, :, 1] = 1
                refimg[:, :, 2] = 1

        if self.Tiff2JpgBox.checkState() > 0:
            self.CalibrationLog.append("Making JPG")
            QtWidgets.QApplication.processEvents()
            # cv2.imencode(".jpg", refimg)
            cv2.imwrite(output_directory + photo.split('.')[1] + "_CALIBRATED.JPG", refimg,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 100])

            self.copyExif(photo, output_directory + photo.split('.')[1] + "_CALIBRATED.JPG")

        else:
            newimg = output_directory + photo.split('.')[1] + "_CALIBRATED." + photo.split('.')[2]
            if 'tif' in photo.split('.')[2].lower():
                cv2.imencode(".tif", refimg)
                cv2.imwrite(newimg, refimg)
                srin = gdal.Open(photo)
                inproj = srin.GetProjection()
                transform = srin.GetGeoTransform()
                gcpcount = srin.GetGCPs()
                srout = gdal.Open(newimg, gdal.GA_Update)
                srout.SetProjection(inproj)
                srout.SetGeoTransform(transform)
                srout.SetGCPs(gcpcount, srin.GetGCPProjection())
                srout = None
                srin = None
            else:
                cv2.imwrite(newimg, refimg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            self.copyExif(photo, newimg)


    def calculateIndex(self, visible, nir):
        try:
            nir[nir == 0] = 1
            visible[visible == 0] = 1
            if nir.dtype == "uint8":
                nir = nir / 255.0
                visible = visible / 255.0
            elif nir.dtype == "uint16":
                nir /= 65535.0
                visible /= 65535.0

            numer = nir - visible
            denom = nir + visible

            retval = numer/denom
            return retval
        except Exception as e:
            print(e)
            return False

####Function for finding he QR target and calculating the calibration coeficients\
    def findQR(self, image, ind):
        try:
            self.ref = ""
            subprocess.call([modpath + os.sep + r'FiducialFinder.exe', image], startupinfo=si)
            list = None
            if os.path.exists(r'.' + os.sep + r'calib.txt'):
                with open(r'.' + os.sep + r'calib.txt', 'r+') as cornerfile:
                    list = cornerfile.read()
                    try:
                        list = list.split('[')[1].split(']')[0]
                    except Exception as e:
                        print(e)
                shutil.rmtree(r'.' + os.sep + r'calib.txt', 'r+')
            if list is not None and len(list) > 0:
                self.ref = self.refindex[1]
                # self.CalibrationLog.append(list)
                temp = np.fromstring(str(list), dtype=int, sep=',')
                coords = [[temp[0],temp[1]],[temp[2],temp[3]],[temp[6],temp[7]],[temp[4],temp[5]]]
                # self.CalibrationLog.append()
            else:
                self.ref = self.refindex[0]
                if ind[0] > 2:
                    im = cv2.imread(image)
                    grayscale = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    cl1 = clahe.apply(grayscale)
                else:
                    self.CalibrationLog.append("Looking for QR target")
                    QtWidgets.QApplication.processEvents()
                    im = cv2.imread(image, 0)
                    clahe2 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    cl1 = clahe2.apply(im)
                denoised = cv2.fastNlMeansDenoising(cl1, None, 14, 7, 21)

                threshcounter = 17
                while threshcounter <= 255:
                    ret, thresh = cv2.threshold(denoised, threshcounter, 255, 0)
                    if os.name == "nt":
                        _, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                    else:
                        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                    coords = []
                    count = 0

                    for i in hierarchy[0]:
                        self.traverseHierarchy(hierarchy, contours, count, im, 0, coords)

                        count += 1
                    if len(coords) == 3:
                        break
                    else:
                        threshcounter += 17

                if len(coords) is not 3:
                    self.CalibrationLog.append("Could not find MAPIR ground target.")
                    QtWidgets.QApplication.processEvents()
                    return

            line1 = np.sqrt(np.power((coords[0][0] - coords[1][0]), 2) + np.power((coords[0][1] - coords[1][1]),
                                                                                  2))  # Getting the distance between each centroid
            line2 = np.sqrt(np.power((coords[1][0] - coords[2][0]), 2) + np.power((coords[1][1] - coords[2][1]), 2))
            line3 = np.sqrt(np.power((coords[2][0] - coords[0][0]), 2) + np.power((coords[2][1] - coords[0][1]), 2))

            hypotenuse = line1 if line1 > line2 else line2
            hypotenuse = line3 if line3 > hypotenuse else hypotenuse
            if len(list) > 0:
                slope = (coords[2][1] - coords[1][1]) / (coords[2][0] - coords[1][0])
                dist = coords[0][1] - (slope * coords[0][0]) + ((slope * coords[2][0]) - coords[2][1])
                dist /= np.sqrt(np.power(slope, 2) + 1)
                center = coords[0]
                bottom = coords[1]
                right = coords[2]
            else:
                if hypotenuse == line1:

                    slope = (coords[1][1] - coords[0][1]) / (coords[1][0] - coords[0][0])
                    dist = coords[2][1] - (slope * coords[2][0]) + ((slope * coords[1][0]) - coords[1][1])
                    dist /= np.sqrt(np.power(slope, 2) + 1)
                    center = coords[2]

                    if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):

                        bottom = coords[0]
                        right = coords[1]
                    else:

                        bottom = coords[1]
                        right = coords[0]
                elif hypotenuse == line2:

                    slope = (coords[2][1] - coords[1][1]) / (coords[2][0] - coords[1][0])
                    dist = coords[0][1] - (slope * coords[0][0]) + ((slope * coords[2][0]) - coords[2][1])
                    dist /= np.sqrt(np.power(slope, 2) + 1)
                    center = coords[0]

                    if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):

                        bottom = coords[1]
                        right = coords[2]
                    else:

                        bottom = coords[2]
                        right = coords[1]
                else:

                    slope = (coords[0][1] - coords[2][1]) / (coords[0][0] - coords[2][0])
                    dist = coords[1][1] - (slope * coords[1][0]) + ((slope * coords[0][0]) - coords[0][1])
                    dist /= np.sqrt(np.power(slope, 2) + 1)
                    center = coords[1]
                    if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):
                        # self.CalibrationLog.append("slope and dist share sign")
                        bottom = coords[2]
                        right = coords[0]
                    else:

                        bottom = coords[0]
                        right = coords[2]
            if list is not None and len(list) > 0:
                guidelength = np.sqrt(np.power((center[0] - right[0]), 2) + np.power((center[1] - right[1]), 2))
                pixelinch = guidelength / self.CORNER_TO_CORNER
                rad = (pixelinch * self.CORNER_TO_TARG)
                vx = center[1] - right[1]
                vy = center[0] - right[0]
            else:
                guidelength = np.sqrt(np.power((center[0] - bottom[0]), 2) + np.power((center[1] - bottom[1]), 2))
                pixelinch = guidelength / self.SQ_TO_SQ
                rad = (pixelinch * self.SQ_TO_TARG)
                vx = center[0] - bottom[0]
                vy = center[1] - bottom[1]

            newlen = np.sqrt(vx * vx + vy * vy)

            if list is not None and len(list) > 0:
                targ1x = (rad * (vx / newlen)) + coords[0][0]
                targ1y = (rad * (vy / newlen)) + coords[0][1]
                targ2x = (rad * (vx / newlen)) + coords[1][0]
                targ2y = (rad * (vy / newlen)) + coords[1][1]
                targ3x = (rad * (vx / newlen)) + coords[2][0]
                targ3y = (rad * (vy / newlen)) + coords[2][1]
                targ4x = (rad * (vx / newlen)) + coords[3][0]
                targ4y = (rad * (vy / newlen)) + coords[3][1]

                target1 = (int(targ1x), int(targ1y))
                target2 = (int(targ2x), int(targ2y))
                target3 = (int(targ3x), int(targ3y))
                target4 = (int(targ4x), int(targ4y))
            else:
                targ1x = (rad * (vx / newlen)) + center[0]
                targ1y = (rad * (vy / newlen)) + center[1]
                targ3x = (rad * (vx / newlen)) + right[0]
                targ3y = (rad * (vy / newlen)) + right[1]

                target1 = (int(targ1x), int(targ1y))
                target3 = (int(targ3x), int(targ3y))
                target2 = (int((np.abs(target1[0] + target3[0])) / 2), int(np.abs((target1[1] + target3[1])) / 2))

            im2 = cv2.imread(image, -1)

            # kernel = np.ones((2, 2), np.uint16)
            # im2 = cv2.erode(im2, kernel, iterations=1)
            # im2 = cv2.dilate(im2, kernel, iterations=1)
            if ind[0] > 1 or ((ind[0] < 2) and (ind[1] > 10)):
#                 blue = im2[:, :, 0]
#                 green = im2[:, :, 1]
#                 red = im2[:, :, 2]
#                 if ind[0] == 5:  # Survey1_NDVI
#
#                     blue = im2[:, :, 0] - ((im2[:, :, 2] / 5) * 4)
#
#                 elif ((ind[0] == 4) and (ind[1] == 0)):  # Survey2 NDVI
#
#                     red = im2[:, :, 2] - ((im2[:, :, 0] / 5) * 4)
#
#                 elif ((ind[0] == 3) and (ind[1] == 1)): #\
#                         # or ind[0 == 7:
#                     # blue = (im2[:, :, 0] / 35) * 100
#                     red = im2[:, :, 2] - (blue * self.multiplication_values["Red"])
#                     green = im2[:, :, 1] - (blue * self.multiplication_values["Green"])
#                     # blue[blue > 65535] = 65535
#                     # red[red < 0] = 0
#                     # green[green < 0] = 0
#                 elif ((ind[0] == 3) and (ind[1] == 2)):
#                     red = (im2[:, :, 2] / 30) * 100
#                     blue = im2[:, :, 0] - ((red * 35) / 100)
#                     green = im2[:, :, 1] - ((red * 35) / 100)
# #                     # blue[blue < 0] = 0
# #                     # green[green < 0] = 0
#
#                 maxpixel = max(np.percentile(red, 99), np.percentile(green, 99))
#                 maxpixel = max(maxpixel, np.percentile(blue, 99))
#                 minpixel = min(np.percentile(red, 1), np.percentile(green, 1))
#                 minpixel = min(minpixel, np.percentile(blue, 1))
#                 # maxpixel = max(red.max(), green.max())
#                 # maxpixel = max(maxpixel, blue.max())
#                 # minpixel = min(red.min(), green.min())
#                 # minpixel = min(minpixel, blue.min())
#                 if "TIF" in image.split('.')[1].upper():
#                     red = ((red - minpixel) / (maxpixel - minpixel) * 65535)
#                     blue = ((blue - minpixel) / (maxpixel - minpixel) * 65535)
#                     green = ((green - minpixel) / (maxpixel - minpixel) * 65535)
#                     red = red.astype("uint16")
#                     blue = blue.astype("uint16")
#                     green = green.astype("uint16")
#                 else:
#                     red = ((red - minpixel) / (maxpixel - minpixel) * 255)
#                     blue = ((blue - minpixel) / (maxpixel - minpixel) * 255)
#                     green = ((green - minpixel) / (maxpixel - minpixel) * 255)
#                     red = red.astype("uint8")
#                     blue = blue.astype("uint8")
#                     green = green.astype("uint8")
#                 im2 = cv2.merge((blue, green, red))
                try:
                    targ1values = im2[(target1[1] - int((pixelinch * 0.75) / 2)):(target1[1] + int((pixelinch * 0.75) / 2)),
                                  (target1[0] - int((pixelinch * 0.75) / 2)):(target1[0] + int((pixelinch * 0.75) / 2))]


                    targ2values = im2[(target2[1] - int((pixelinch * 0.75) / 2)):(target2[1] + int((pixelinch * 0.75) / 2)),
                                  (target2[0] - int((pixelinch * 0.75) / 2)):(target2[0] + int((pixelinch * 0.75) / 2))]
                    targ3values = im2[(target3[1] - int((pixelinch * 0.75) / 2)):(target3[1] + int((pixelinch * 0.75) / 2)),
                                  (target3[0] - int((pixelinch * 0.75) / 2)):(target3[0] + int((pixelinch * 0.75) / 2))]
                except Exception as e:
                    print(e)

                #                 (self.refvalues[self.ref]["RGN"][2][0] - self.refvalues[self.ref]["Red"][0] ) / \
                #                (self.refvalues[self.ref]["RGN"][2][0] + self.refvalues[self.ref]["Red"][0] )
                #
                # ideal_ndvi_2 = (self.refvalues[self.ref]["RGN"][2][1] - self.refvalues[self.ref]["Red"][1] ) / \
                #                (self.refvalues[self.ref]["RGN"][2][1] + self.refvalues[self.ref]["Red"][1] )
                #
                #
                # ideal_ndvi_3 = (self.refvalues[self.ref]["RGN"][2][2] - self.refvalues[self.ref]["Red"][2]) / \
                #                (self.refvalues[self.ref]["RGN"][2][2] + self.refvalues[self.ref]["Red"][2])
                #
                # ideal_ndvi_4 = (self.refvalues[self.ref]["RGN"][2][3] - self.refvalues[self.ref]["Red"][3]) / \
                #                (self.refvalues[self.ref]["RGN"][2][3] + self.refvalues[self.ref]["Red"][3])

                t1redmean = np.mean(targ1values[:, :, 2])
                t1greenmean = np.mean(targ1values[:, :, 1])
                t1bluemean = np.mean(targ1values[:, :, 0])
                t2redmean = np.mean(targ2values[:, :, 2])
                t2greenmean = np.mean(targ2values[:, :, 1])
                t2bluemean = np.mean(targ2values[:, :, 0])
                t3redmean = np.mean(targ3values[:, :, 2])
                t3greenmean = np.mean(targ3values[:, :, 1])
                t3bluemean = np.mean(targ3values[:, :, 0])



                yred = []
                yblue = []
                ygreen = []
                if list is not None and len(list) > 0:
                    targ4values = im2[(target4[1] - int((pixelinch * 0.75) / 2)):(target4[1] + int((pixelinch * 0.75) / 2)),
                                  (target4[0] - int((pixelinch * 0.75) / 2)):(target4[0] + int((pixelinch * 0.75) / 2))]
                    t4redmean = np.mean(targ4values[:, :, 2])
                    t4greenmean = np.mean(targ4values[:, :, 1])
                    t4bluemean = np.mean(targ4values[:, :, 0])
                    yred = [0.87, 0.51, 0.23, 0.0]
                    yblue = [0.87, 0.51, 0.23, 0.0]
                    ygreen = [0.87, 0.51, 0.23, 0.0]
                    # im2[(target1[1] - int((pixelinch * 0.75) / 2)):(target1[1] + int((pixelinch * 0.75) / 2)),
                    # (target1[0] - int((pixelinch * 0.75) / 2)):(target1[0] + int((pixelinch * 0.75) / 2))] = [0, 255,0]
                    # im2[(target2[1] - int((pixelinch * 0.75) / 2)):(target2[1] + int((pixelinch * 0.75) / 2)),
                    # (target2[0] - int((pixelinch * 0.75) / 2)):(target2[0] + int((pixelinch * 0.75) / 2))] = [255, 0,0]
                    # im2[(target3[1] - int((pixelinch * 0.75) / 2)):(target3[1] + int((pixelinch * 0.75) / 2)),
                    # (target3[0] - int((pixelinch * 0.75) / 2)):(target3[0] + int((pixelinch * 0.75) / 2))] = [0, 0, 255]
                    # im2[(target4[1] - int((pixelinch * 0.75) / 2)):(target4[1] + int((pixelinch * 0.75) / 2)),
                    # (target4[0] - int((pixelinch * 0.75) / 2)):(target4[0] + int((pixelinch * 0.75) / 2))] = [0, 255, 255]
                    #
                    # cv2.imwrite(r"C:\Users\peau\Desktop\NateTest.jpg", im2)

                    xred = [t1redmean, t2redmean, t3redmean, t4redmean]
                    xgreen = [t1greenmean, t2greenmean, t3greenmean, t4greenmean]
                    xblue = [t1bluemean, t2bluemean, t3bluemean, t4bluemean]


                    #
                    # xred = [t3redmean, t4redmean]
                    # xgreen = [t3greenmean, t4greenmean]
                    # xblue = [t3bluemean, t4bluemean]

                else:
                    yred = [0.87, 0.51, 0.23]
                    yblue = [0.87, 0.51, 0.23]
                    ygreen = [0.87, 0.51, 0.23]

                    xred = [t1redmean, t2redmean, t3redmean]
                    xgreen = [t1greenmean, t2greenmean, t3greenmean]
                    xblue = [t1bluemean, t2bluemean, t3bluemean]

                if ind[1] == 1 and (ind[0] == 4) \
                        or (ind[0] == 3 and ind[1] == 3):
                    yred = self.refvalues[self.ref]["850"][0]
                    ygreen = self.refvalues[self.ref]["850"][1]
                    yblue = self.refvalues[self.ref]["850"][2]
                elif ind[1] == 2 and (ind[0] == 4):
                    yred = self.refvalues[self.ref]["650"][0]
                    ygreen = self.refvalues[self.ref]["650"][1]
                    yblue = self.refvalues[self.ref]["650"][2]
                elif ind[1] == 3 and (ind[0] == 4):
                    yred = self.refvalues[self.ref]["550"][0]
                    ygreen = self.refvalues[self.ref]["550"][1]
                    yblue = self.refvalues[self.ref]["550"][2]
                elif ind[1] == 4 and (ind[0] == 4):
                    yred = self.refvalues[self.ref]["450"][0]
                    ygreen = self.refvalues[self.ref]["450"][1]
                    yblue = self.refvalues[self.ref]["450"][2]
                elif (ind[1] == 1 and ind[0] == 3) or (
                    ind[0] == 7) or (ind[0] == 2 and ind[1] == 0):
                    yred = self.refvalues[self.ref]["550/660/850"][0]
                    ygreen = self.refvalues[self.ref]["550/660/850"][1]
                    yblue = self.refvalues[self.ref]["550/660/850"][2]
                elif (ind[0] == 3 and ind[1] == 2) or (ind[0] == 2 and ind[1] == 1):
                    yred = self.refvalues[self.ref]["475/550/850"][0]
                    ygreen = self.refvalues[self.ref]["475/550/850"][1]
                    yblue = self.refvalues[self.ref]["475/550/850"][2]
                else:
                    yred = self.refvalues[self.ref]["660/850"][0]
                    ygreen = self.refvalues[self.ref]["660/850"][1]
                    yblue = self.refvalues[self.ref]["660/850"][2]

                # # # if self.ref == "oldrefvalues":
                #     redslope, redintcpt, r_value, p_value, std_err = stats.linregress(xred, yred)
                #
                #     greenslope, greenintcpt, r_value, p_value, std_err = stats.linregress(xgreen, ygreen)
                #
                #     blueslope, blueintcpt, r_value, p_value, std_err = stats.linregress(xblue, yblue)
                #
                #     self.CalibrationLog.append("Red Slope: " + str(redslope))
                #     self.CalibrationLog.append("Red Intcpt: " + str(redintcpt))
                #     self.CalibrationLog.append("Green Slope: " + str(greenslope))
                #     self.CalibrationLog.append("Green Intcpt: " + str(greenintcpt))
                #     self.CalibrationLog.append("Blue Slope: " + str(blueslope))
                #     self.CalibrationLog.append("Blue Intcpt: " + str(blueintcpt))
                #     self.CalibrationLog.append("Found QR Target, please proceed with calibration.")
                #
                #     return [redintcpt, redslope, greenintcpt, greenslope, blueintcpt, blueslope]
                # if list is None or len(list) == 0:
                #     Ared = np.vstack([xred, np.ones(len(xred))]).T
                #     Agreen = np.vstack([xgreen, np.ones(len(xgreen))]).T
                #     Ablue = np.vstack([xblue, np.ones(len(xblue))]).T
                #
                #     (cred, _, _, _) = np.linalg.lstsq(Ared, yred)
                #
                #
                #     (cgreen, _, _, _) = np.linalg.lstsq(Agreen, ygreen)
                #
                #
                #     (cblue, _, _, _) = np.linalg.lstsq(Ablue, yblue)
                # else:
                #     cred = np.polyfit(xred, yred, 3)
                #     cgreen = np.polyfit(xgreen, ygreen, 3)
                #     cblue = np.polyfit(xblue, yblue, 3)

                xred = np.array(xred)
                xgreen = np.array(xgreen)
                xblue = np.array(xblue)

                xred /= 65535
                xgreen /= 65535
                xblue /= 65535

                yred = np.array(yred)
                ygreen = np.array(ygreen)
                yblue = np.array(yblue)

                cofr = yred[0]/xred[0]
                cofg = ygreen[0]/xgreen[0]
                cofb = yblue[0]/xblue[0]

                # xred *= cofr
                #
                #
                # xgreen *= cofg
                #
                #
                # xblue *= cofb
                # mred, bred, rr, pr, rerr = stats.linregress(xred,yred)
                # mgreen, bgreen, rg, pg, gerr = stats.linregress(xgreen,ygreen)
                # mblue, bblue, rb, pb, berr = stats.linregress(xblue,yblue)

                # yred = (yred * mred) + bred
                # ygreen = (ygreen * mgreen) + bgreen
                # yblue = (yblue * mblue) + bblue
                #
                # maxqry = max(yred.max(), ygreen.max())
                # maxqry = max(maxqry, yblue.max())
                #
                # minqry = min(yred.min(), ygreen.min())
                # minqry = min(minqry, yblue.min())
                #
                # yred = (yred - minqry)/(maxqry - minqry)
                # ygreen = (ygreen - minqry)/(maxqry - minqry)
                # yblue = (yblue - minqry)/(maxqry - minqry)

                #
                # ideal_ndvi = self.calculateIndex(yred, yblue)
                # # self.CalibrationLog.append(str(ideal_ndvi))
                #
                #
                # ideal_gndvi = self.calculateIndex(ygreen, yblue)
                # # self.CalibrationLog.append(str(ideal_ndvi))
                #

                # ared = xred.dot(yred)/xred.dot(xred)
                # agreen = xgreen.dot(ygreen)/xgreen.dot(xgreen)
                # ablue = xblue.dot(yblue)/xblue.dot(xblue)
                #
                #
                #
                # xred = xred * ared
                # xgreen = xgreen * agreen
                # xblue = xblue * ablue
                #
                # # xred = (xred * mred) + bred
                # # xgreen = (xgreen * mgreen) + bgreen
                # # xblue = (xblue * mblue) + bblue
                #
                # maxqr = max(xred.max(), xgreen.max())
                # maxqr = max(maxqr, xblue.max())
                #
                # minqr = min(xred.min(), xgreen.min())
                # minqr = min(minqr, xblue.min())
                #
                # xred = (xred - minqr)/(maxqr - minqr)
                # xgreen = (xgreen - minqr)/(maxqr - minqr)
                # xblue = (xblue - minqr)/(maxqr - minqr)

                # x_ndvi = self.calculateIndex(xred, xblue)
                #
                #
                # # self.CalibrationLog.append(str(x_ndvi))
                #
                # x_gndvi = self.calculateIndex(xgreen, xblue)
                #
                #
                # # self.CalibrationLog.append(str(x_gndvi))
                # ndvi_coeff = ideal_ndvi / x_ndvi
                # gndvi_coeff = ideal_gndvi / x_gndvi


                # self.CalibrationLog.append(str(ndvi_coeff))


                # self.CalibrationLog.append(str(gndvi_coeff))
                self.multiplication_values["Red"] = cofr
                self.multiplication_values["Green"] = cofg
                self.multiplication_values["Blue"] = cofb
                # pred = np.poly1d(cred)
                #
                #
                # pgreen = np.poly1d(cgreen)
                #
                #
                # pblue = np.poly1d(cblue)



                # else:
                #     pred = np.polyfit(xred, yred, 3)
                #
                #     pgreen = np.polyfit(xgreen, ygreen, 3)
                #
                #     pblue = np.polyfit(xblue, yblue, 3)

                # print([xred, xgreen, xblue])

                # print([pred, pgreen, pblue])


                if list is not None and len(list) > 0:
                    self.CalibrationLog.append("Found QR Target Model 2, please proceed with calibration.")
                else:
                    self.CalibrationLog.append("Found QR Target Model 1, please proceed with calibration.")
                # return [ared, agreen, ablue]
            else:
                if list is not None and len(list) > 0:
                    targ1values = im2[(target1[1] - int((pixelinch * 0.75) / 2)):(target1[1] + int((pixelinch * 0.75) / 2)),
                                  (target1[0] - int((pixelinch * 0.75) / 2)):(target1[0] + int((pixelinch * 0.75) / 2))]
                    targ2values = im2[(target2[1] - int((pixelinch * 0.75) / 2)):(target2[1] + int((pixelinch * 0.75) / 2)),
                                  (target2[0] - int((pixelinch * 0.75) / 2)):(target2[0] + int((pixelinch * 0.75) / 2))]
                    targ3values = im2[(target3[1] - int((pixelinch * 0.75) / 2)):(target3[1] + int((pixelinch * 0.75) / 2)),
                                  (target3[0] - int((pixelinch * 0.75) / 2)):(target3[0] + int((pixelinch * 0.75) / 2))]
                    targ4values = im2[(target4[1] - int((pixelinch * 0.75) / 2)):(target4[1] + int((pixelinch * 0.75) / 2)),
                                  (target4[0] - int((pixelinch * 0.75) / 2)):(target4[0] + int((pixelinch * 0.75) / 2))]
                    if len(im2.shape) > 2:
                        t1mean = np.mean(targ1values[:,:,0])
                        t2mean = np.mean(targ2values[:,:,0])
                        t3mean = np.mean(targ3values[:,:,0])
                        t4mean = np.mean(targ4values[:,:,0])
                    else:
                        t1mean = np.mean(targ1values)
                        t2mean = np.mean(targ2values)
                        t3mean = np.mean(targ3values)
                        t4mean = np.mean(targ4values)
                    y = [0.87, 0.51, 0.23, 0.0]
                    if ind[1] == 0:
                        y = self.refvalues[self.ref]["Mono405"]

                    elif ind[1] == 1:
                        y = self.refvalues[self.ref]["Mono450"]

                    elif ind[1] == 2:
                        y = self.refvalues[self.ref]["Mono490"]

                    elif ind[1] == 3:
                        y = self.refvalues[self.ref]["Mono518"]


                    elif ind[1] == 4:
                        y = self.refvalues[self.ref]["Mono550"]


                    elif ind[1] == 5:
                        y = self.refvalues[self.ref]["Mono590"]
                    elif ind[1] == 6:
                        y = self.refvalues[self.ref]["Mono615"]
                    elif ind[1] == 7:
                        y = self.refvalues[self.ref]["Mono632"]
                    elif ind[1] == 8:
                        y = self.refvalues[self.ref]["Mono650"]
                    elif ind[1] == 9:
                        y = self.refvalues[self.ref]["Mono685"]
                    elif ind[1] == 10:
                        y = self.refvalues[self.ref]["Mono725"]
                    elif ind[1] == 11:
                        y = self.refvalues[self.ref]["Mono808"]
                    elif ind[1] == 12:
                        y = self.refvalues[self.ref]["Mono850"]

                    x = [t1mean, t2mean, t3mean, t4mean]
                else:
                    targ1values = im2[int(target1[1] - ((pixelinch * 0.75) / 2)):(target1[1] + ((pixelinch * 0.75) / 2)),
                                  int(target1[0] - ((pixelinch * 0.75) / 2)):(target1[0] + ((pixelinch * 0.75) / 2))]
                    targ2values = im2[int(target2[1] - ((pixelinch * 0.75) / 2)):(target2[1] + ((pixelinch * 0.75) / 2)),
                                  int(target2[0] - ((pixelinch * 0.75) / 2)):(target2[0] + ((pixelinch * 0.75) / 2))]
                    targ3values = im2[int(target3[1] - ((pixelinch * 0.75) / 2)):(target3[1] + ((pixelinch * 0.75) / 2)),
                                  int(target3[0] - ((pixelinch * 0.75) / 2)):(target3[0] + ((pixelinch * 0.75) / 2))]
                    if len(im2.shape) > 2:
                        t1mean = np.mean(targ1values[:,:,0])
                        t2mean = np.mean(targ2values[:,:,0])
                        t3mean = np.mean(targ3values[:,:,0])
                    else:
                        t1mean = np.mean(targ1values)
                        t2mean = np.mean(targ2values)
                        t3mean = np.mean(targ3values)
                    y = [0.87, 0.51, 0.23]
                    if ind[1] == 0:
                        y = self.refvalues[self.ref]["Mono405"]

                    elif ind[1] == 1:
                        y = self.refvalues[self.ref]["Mono450"]


                    elif ind[1] == 2:
                        y = self.refvalues[self.ref]["Mono518"]


                    elif ind[1] == 3:
                        y = self.refvalues[self.ref]["Mono550"]


                    elif ind[1] == 4:
                        y = self.refvalues[self.ref]["Mono590"]
                    elif ind[1] == 5:
                        y = self.refvalues[self.ref]["Mono632"]
                    elif ind[1] == 6:
                        y = self.refvalues[self.ref]["Mono650"]
                    elif ind[1] == 7:
                        y = self.refvalues[self.ref]["Mono615"]
                    elif ind[1] == 8:
                        y = self.refvalues[self.ref]["Mono725"]
                    elif ind[1] == 9:
                        y = self.refvalues[self.ref]["Mono780"]
                    elif ind[1] == 10:
                        y = self.refvalues[self.ref]["Mono808"]

                    elif ind[1] == 11:
                        y = self.refvalues[self.ref]["Mono850"]
                    elif ind[1] == 12:
                        y = self.refvalues[self.ref]["Mono880"]


                    x = [t1mean, t2mean, t3mean]
                x = np.array(x)


                y = np.array(y)


                a = x.dot(y) / x.dot(x)

                if list is not None and len(list) > 0:
                    self.CalibrationLog.append("Found QR Target Model 2, please proceed with calibration.")
                else:
                    self.CalibrationLog.append("Found QR Target Model 1, please proceed with calibration.")
                QtWidgets.QApplication.processEvents()
                return a
        except Exception as e:
            self.CalibrationLog.append(str(e))
            return
            # slope, intcpt, r_value, p_value, std_err = stats.linregress(x, y)
            # self.CalibrationLog.append("Found QR Target, please proceed with calibration.")
            #
            # return [intcpt, slope]
    # Calibration Steps: End


    # Helper functions
    def preProcessHelper(self, infolder, outfolder, customerdata=True):

        if 5 <= self.PreProcessCameraModel.currentIndex() <= 10:
            os.chdir(infolder)
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.DNG"))
            infiles.sort()
            counter = 0
            for input in infiles:
                self.PreProcessLog.append(
                    "processing image: " + str((counter) + 1) + " of " + str(len(infiles)) +
                    " " + input.split(os.sep)[1])
                QtWidgets.QApplication.processEvents()
                self.openDNG(infolder + input.split('.')[1] + "." + input.split('.')[2], outfolder, customerdata)

                counter += 1
        elif 0 <= self.PreProcessCameraModel.currentIndex() <= 2:
            os.chdir(infolder)
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.[mM][aA][pP][iI][rR]"))
            infiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
            infiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
            counter = 0
            for input in infiles:
                self.PreProcessLog.append(
                    "processing image: " + str((counter) + 1) + " of " + str(len(infiles)) +
                    " " + input.split(os.sep)[1])
                QtWidgets.QApplication.processEvents()
                filename = input.split('.')
                outputfilename = outfolder + filename[1] + '.tif'
                # print(infolder + input.split('.')[1] + "." + input.split('.')[2])
                # print(outfolder + outputfilename)
                self.openMapir(infolder + input.split('.')[1] + "." + input.split('.')[2],  outputfilename)


                counter += 1
        else:
            os.chdir(infolder)
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.[rR][aA][wW]"))
            infiles.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
            infiles.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
            infiles.sort()
            if len(infiles) > 1:
                if ("RAW" in infiles[0].upper()) and ("JPG" in infiles[1].upper()):
                    counter = 0
                    for input in infiles[::2]:
                        if customerdata == True:
                            self.PreProcessLog.append(
                                "processing image: " + str((counter / 2) + 1) + " of " + str(len(infiles) / 2) +
                                " " + input.split(os.sep)[1])
                            QtWidgets.QApplication.processEvents()
                        with open(input, "rb") as rawimage:
                            if self.PreProcessCameraModel.currentIndex() == 3:
                                img = np.fromfile(rawimage, np.dtype('u2'), (4000 * 3000)).reshape((3000, 4000))
                            else:
                                img = np.fromfile(rawimage, np.dtype('u2'), self.imsize).reshape(
                                    (self.imrows, self.imcols))
                            color = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB)
                            # color2 = copy.deepcopy(color)
                            # color2 = color2 / 65535.0
                            # color2 = color2 * 255.0
                            # color2 = color2.astype("uint8")
                            # blue, green, red = cv2.split(color2)
                            # blue = cv2.equalizeHist(blue)
                            # green = cv2.equalizeHist(green)
                            # red = cv2.equalizeHist(red)
                            # color2 = cv2.merge((blue,green,red))
                            # color2 = color2 / 255.0
                            # color2 = color2 * 65535.0
                            # color2 = color2.astype("uint16")
                            filename = input.split('.')
                            outputfilename = filename[1] + '.tif'
                            cv2.imencode(".tif", color)
                            # cv2.imencode(".tif", color2)
                            cv2.imwrite(outfolder + outputfilename, color)
                            # outputfilename = filename[1] + '_EQ.tif'
                            # cv2.imwrite(outfolder + outputfilename, color2)
                            if customerdata == True:
                                self.copyExif(infolder + infiles[counter + 1], outfolder + outputfilename)
                        counter += 2

                else:
                    self.PreProcessLog.append(
                        "Incorrect file structure. Please arrange files in a RAW, JPG, RAW, JGP... format.")


    def traverseHierarchy(self, tier, cont, index, image, depth, coords):

        if tier[0][index][2] != -1:
            self.traverseHierarchy(tier, cont, tier[0][index][2], image, depth + 1, coords)
            return
        elif depth >= 2:
            c = cont[index]
            moment = cv2.moments(c)
            if int(moment['m00']) != 0:
                x = int(moment['m10'] / moment['m00'])
                y = int(moment['m01'] / moment['m00'])
                coords.append([x, y])
            return

    def openDNG(self, inphoto, outfolder, customerdata=True):
        inphoto = str(inphoto)
        newfile = inphoto.split(".")[0] + ".tif"
        if not os.path.exists(outfolder + os.sep + newfile.rsplit(os.sep, 1)[1]):
            if sys.platform == "win32":
                subprocess.call([modpath + os.sep + 'dcraw.exe', '-6', '-T', inphoto], startupinfo=si)
            else:
                subprocess.call([r'/usr/local/bin/dcraw', '-6', '-T', inphoto])
            if customerdata == True:
                self.copyExif(os.path.abspath(inphoto), newfile)
            shutil.move(newfile, outfolder)
        else:
            self.PreProcessLog.append("Attention!: " + str(newfile) + " already exists.")

    def openMapir(self, inphoto, outphoto):
        # self.PreProcessLog.append(str(inphoto) + " " + str(outphoto))
        try:
            if "mapir" in inphoto.split('.')[1]:
                if self.PreProcessDarkBox.isChecked():
                    subprocess.call(
                        [modpath + os.sep + r'Mapir_Converter.exe', '-d', os.path.abspath(inphoto),
                         os.path.abspath(outphoto)], startupinfo=si)
                else:
                    subprocess.call(
                        [modpath + os.sep + r'Mapir_Converter.exe', os.path.abspath(inphoto),
                         os.path.abspath(outphoto)], startupinfo=si)
                img = cv2.imread(outphoto, -1)
                try:

                    if self.PreProcessFilter.currentIndex() >= 13 or self.PreProcessCameraModel.currentIndex() == 2:
                        cv2.imwrite(outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1], img)
                        self.copyExif(outphoto, outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1])
                        color = cv2.cvtColor(img, cv2.COLOR_BAYER_GR2RGB).astype("uint16")
                        self.PreProcessLog.append("Debayering")
                        cv2.imencode(".tif", color)
                        cv2.imwrite(outphoto, color)
                        self.copyExif(outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1], outphoto)
                        os.unlink(outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1])
                        self.PreProcessLog.append("Done Debayering")
                    else:
                        self.copyExif(outphoto, outphoto)
                        self.PreProcessLog.append("Skipped Debayering")
                except Exception as e:
                    print(str(e))
            else:
                try:

                    if self.PreProcessFilter.currentIndex() >= 13:
                        img = cv2.imread(inphoto, -1)
                        color = cv2.cvtColor(img, cv2.COLOR_BAYER_GR2RGB).astype("uint16")
                        self.PreProcessLog.append("Debayering")
                        cv2.imencode(".tif", color)
                        cv2.imwrite(outphoto, color)
                        self.copyExif(inphoto, outphoto)
                        self.PreProcessLog.append("Done Debayering")
                    else:
                        if "mapir" not in inphoto.split('.')[1]:
                            shutil.copyfile(inphoto, outphoto)
                            self.copyExif(inphoto, outphoto)
                        else:

                            self.copyExif(outphoto, outphoto)
                        self.PreProcessLog.append("Skipped Debayering")
                except Exception as e:
                    print(str(e))
        except Exception as e:
            self.PreProcessLog.appen("Error in function openMapir(): " + str(e))

    def findCameraModel(self, resolution):
        if resolution == 3145728:
            return "Kernel 3.2MP"
        elif resolution == 14414592:
            return "Kernel 14.4MP"
    def copyExif(self, inphoto, outphoto):
        if sys.platform == "win32":
            # with exiftool.ExifTool() as et:
            #     et.execute(r' -overwrite_original -tagsFromFile ' + os.path.abspath(inphoto) + ' ' + os.path.abspath(outphoto))

            try:
                # self.PreProcessLog.append(str(modpath + os.sep + r'exiftool.exe') + ' ' + inphoto + ' ' + outphoto)
                subprocess._cleanup()
                data = subprocess.run(
                    args=[modpath + os.sep + r'exiftool.exe', '-m', r'-UserComment', r'-ifd0:imagewidth', r'-ifd0:imageheight', os.path.abspath(inphoto)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE, startupinfo=si).stdout.decode("utf-8")
                data = [line.strip().split(':') for line in data.split('\r\n') if line.strip()]
                ypr = data[0][1].split()
                ypr[0] = -float(ypr[0])
                ypr[1] = -float(ypr[1])
                ypr[2] = ((float(ypr[2]) + 180.0) % 360.0)
                w = int(data[1][1])
                h = int(data[2][1])
                model = self.findCameraModel(w * h)
                bandname = inphoto.split(os.sep)[-1][1:4]
                centralwavelength = inphoto.split(os.sep)[-1][1:4]

            except Exception as e:
                ypr = None
                print(e)
                if self.MapirTab.currentIndex() == 0:
                    print("Warning: No userdefined tags detected")
                elif self.MapirTab.currentIndex() == 1:
                    print("Warning: No userdefined tags detected")

                subprocess.call(
                    [modpath + os.sep + r'exiftool.exe', '-m', r'-overwrite_original', r'-tagsFromFile',
                     os.path.abspath(inphoto),
                     # r'-all:all<all:all',
                     os.path.abspath(outphoto)], startupinfo=si)
            finally:
                if ypr is not None:
                    try:

                        exifout = subprocess.run(
                            [modpath + os.sep + r'exiftool.exe',  r'-config', modpath + os.sep + r'mapir.config', '-m', r'-overwrite_original', r'-tagsFromFile',
                             os.path.abspath(inphoto),
                             r'-all:all<all:all',
                             r'-ifd0:make=MAPIR',
                             r'-ifd0:model=' + model,
                             r'-xmp-camera:yaw=' + str(ypr[0]),
                             r'-xmp-camera:pitch=' + str(ypr[1]),
                             r'-xmp-camera:roll=' + str(ypr[2]),
                             r'-xmp-camera:centralwavelength={' + centralwavelength + r'}',
                             r'-xmp-camera:bandname={' + bandname + r'}',

                             os.path.abspath(outphoto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, startupinfo=si).stderr.decode("utf-8")

                    except Exception as e:
                        if self.MapirTab.currentIndex() == 0:
                            self.PreProcessLog.append("Error: " + str(e))
                        elif self.MapirTab.currentIndex() == 1:
                            self.CalibrationLog.append("Error: " + str(e))
                else:
                    # self.PreProcessLog.append("No IMU data detected.")
                    subprocess.call(
                        [modpath + os.sep + r'exiftool.exe', '-m', r'-overwrite_original', r'-tagsFromFile',
                         os.path.abspath(inphoto),
                         # r'-all:all<all:all',
                         os.path.abspath(outphoto)], startupinfo=si)
        else:
            subprocess.call(
                [r'exiftool', r'-overwrite_original', r'-addTagsFromFile', os.path.abspath(inphoto),
                 # r'-all:all<all:all',
                 os.path.abspath(outphoto)])
    def on_DarkCurrentInputButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.DarkCurrentInput.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.DarkCurrentInput.text())
    def on_DarkCurrentOutputButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.DarkCurrentOutput.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.DarkCurrentOutput.text())
    def on_DarkCurrentGoButton_released(self):
        folder1 = []
        folder1.extend(glob.glob(self.DarkCurrentInput.text() + os.sep + "*.tif?"))
        for img in folder1:
            QtWidgets.QApplication.processEvents()
            self.KernelLog.append("Updating " + str(img))
            subprocess.call(
                [modpath + os.sep + r'exiftool.exe', '-m', r'-overwrite_original', r'-ifd0:blacklevelrepeatdim=2 2',  img], startupinfo=si)

        self.KernelLog.append("Finished updating")

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

