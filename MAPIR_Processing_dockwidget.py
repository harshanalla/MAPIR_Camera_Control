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

from PIL import Image
from PIL.TiffTags import TAGS

os.umask(0)
from LensLookups import *
import datetime
import sys
import shutil
import platform
import itertools
import ctypes
import string
import win32api
import PIL
import bitstring
from PyQt5 import QtCore, QtGui, QtWidgets

import PyQt5.uic as uic

import numpy as np
import subprocess
import cv2
import copy
import hid
import time
import json
import math

from MAPIR_Enums import *
from Calculator import *
from LUT_Dialog import *
from Vignette import *
from BandOrder import *
from ViewerSave_Dialog import *
import xml.etree.ElementTree as ET
import KernelConfig
from MAPIR_Converter import *
from Exposure import *
from ArrayTypes import AdjustYPR, CurveAdjustment
# import KernelBrowserViewer

modpath = os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(modpath + os.sep + "instring.txt"):
    istr = open(modpath + os.sep + "instring.txt", "w")
    istr.close()

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
# DEL_CLASS, _ = uic.loadUiType(os.path.join(
#     os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_delete.ui'))
TRANSFER_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_transfer.ui'))
ADVANCED_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_Advanced.ui'))
MATRIX_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_matrix.ui'))

class DebayerMatrix(QtWidgets.QDialog, MATRIX_CLASS):
    parent = None

    GAMMA_LIST = [{"CCM": [1,0,0,0,1,0,0,0,1], "RGB_OFFSET": [0,0,0], "GAMMA": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0]},
                  {"CCM": [1,0,1.402,1,-0.34414,-0.71414,1,1.772,0], "RGB_OFFSET": [0, 0, 0],
                   "GAMMA": [2.3,1.3,2.3,0.3,0.3,0.3,2.3,2.3,1,2,1,2,2,2,1,2,1,2,2,0,2,0,2,0]},
                  {"CCM": [3.2406,-1.5372,-0.498,-0.9689,1.8756,0.0415,0.0557,-0.2040,1.0570 ], "RGB_OFFSET": [0, 0, 0],
                   "GAMMA": [7.0,0.0,6.5,3.0,6.0,8.0,5.5,13.0,5.0,22.0,4.5,38.0,3.5,102.0,2.5,230.0,1.75,422.0,1.25,679.0,0.875,1062.0,0.625,1575.0]},]

    def __init__(self, parent=None):
        """Constructor."""
        super(DebayerMatrix, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)

    def on_ModalSaveButton_released(self):



        self.close()

    def on_ModalCancelButton_released(self):
        self.close()


class AdvancedOptions(QtWidgets.QDialog, ADVANCED_CLASS):
    parent = None

    def __init__(self, parent=None):
        """Constructor."""
        super(AdvancedOptions, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)
        try:
            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_READ_REPORT
            buf[1] = eRegister.RG_UNMOUNT_SD_CARD_S.value
            # if self.SDCTUM.text():
            #     buf[2] = int(self.SDCTUM.text()) if 0 <= int(self.SDCTUM.text()) < 255 else 255

            res = self.parent.writeToKernel(buf)[2]
            self.SDCTUM.setText(str(res))

            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_READ_REPORT
            buf[1] = eRegister.RG_VIDEO_ON_DELAY.value
            # buf[2] = int(self.VCRD.text()) if 0 <= int(self.VCRD.text()) < 255 else 255

            res = self.parent.writeToKernel(buf)[2]
            self.VCRD.setText(str(res))

            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_READ_REPORT
            buf[1] = eRegister.RG_PHOTO_FORMAT.value


            res = self.parent.writeToKernel(buf)[2]
            self.KernelPhotoFormat.setCurrentIndex(int(res))

            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_BLOCK_READ_REPORT
            buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
            buf[2] = 3
            # buf[3] = ord(self.CustomFilter.text()[0])
            # buf[4] = ord(self.CustomFilter.text()[1])
            # buf[5] = ord(self.CustomFilter.text()[2])
            res = self.parent.writeToKernel(buf)
            filt = chr(res[2]) + chr(res[3]) + chr(res[4])

            self.CustomFilter.setText(str(filt))
            QtWidgets.QApplication.processEvents()

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.parent.KernelLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
            # QtWidgets.QApplication.processEvents()

        finally:
            QtWidgets.QApplication.processEvents()
            self.close()
        # for i in range(1, 256):
        #     self.SDCTUM.addItem(str(i))
        #
        # for j in range(1, 256):
        #     self.VCRD.addItem(str(j))
    # def on_ModalBrowseButton_released(self):
    #     with open(modpath + os.sep + "instring.txt", "r+") as instring:
    #         self.ModalOutputFolder.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
    #         instring.truncate(0)
    #         instring.seek(0)
    #         instring.write(self.ModalOutputFolder.text())
    #         self.ModalSaveButton.setEnabled(True)
    def on_SaveButton_released(self):
        # self.parent.transferoutfolder  = self.ModalOutputFolder.text()
        # self.parent.yestransfer = self.TransferBox.isChecked()
        # self.parent.yesdelete = self.DeleteBox.isChecked()
        # self.parent.selection_made = True
        try:

            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_UNMOUNT_SD_CARD_S.value
            val = int(self.SDCTUM.text()) if 0 < int(self.SDCTUM.text()) < 255 else 255
            buf[2] = val

            self.parent.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_VIDEO_ON_DELAY.value
            val = int(self.VCRD.text()) if 0 < int(self.VCRD.text()) < 255 else 255
            buf[2] = val
            self.parent.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_PHOTO_FORMAT.value
            buf[2] = int(self.KernelPhotoFormat.currentIndex())


            self.parent.writeToKernel(buf)
            buf = [0] * 512
            buf[0] = self.parent.SET_REGISTER_BLOCK_WRITE_REPORT
            buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
            buf[2] = 3
            buf[3] = ord(self.CustomFilter.text()[0])
            buf[4] = ord(self.CustomFilter.text()[1])
            buf[5] = ord(self.CustomFilter.text()[2])
            res = self.parent.writeToKernel(buf)

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.parent.KernelLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))

        finally:
            QtWidgets.QApplication.processEvents()
            self.close()

    def on_CancelButton_released(self):
        # self.parent.yestransfer = False
        # self.parent.yesdelete = False
        # self.parent.selection_made = True
        self.close()

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

    def on_DeleteBox_toggled(self):
        if self.DeleteBox.isChecked():
            self.ModalSaveButton.setEnabled(True)
        else:
            self.ModalSaveButton.setEnabled(False)

    def on_ModalSaveButton_released(self):
        self.parent.transferoutfolder  = self.ModalOutputFolder.text()
        self.parent.yestransfer = self.TransferBox.isChecked()
        self.parent.yesdelete = self.DeleteBox.isChecked()
        self.parent.selection_made = True
        QtWidgets.QApplication.processEvents()
        self.close()

    def on_ModalCancelButton_released(self):
        self.parent.yestransfer = False
        self.parent.yesdelete = False
        self.parent.selection_made = True
        QtWidgets.QApplication.processEvents()
        self.close()

# class KernelDelete(QtWidgets.QDialog, DEL_CLASS):
#     parent = None
#
#     def __init__(self, parent=None):
#         """Constructor."""
#         super(KernelDelete, self).__init__(parent=parent)
#         self.parent = parent
#
#         self.setupUi(self)
#
#     def on_ModalSaveButton_released(self):
#         for drv in self.parent.driveletters:
#             if os.path.isdir(drv + r":" + os.sep + r"dcim"):
#                 # try:
#                 files = glob.glob(drv + r":" + os.sep + r"dcim/*/*")
#                 for file in files:
#                     os.unlink(file)
#         self.close()
#
#     def on_ModalCancelButton_released(self):
#         self.close()

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
        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_READ_REPORT
        buf[1] = eRegister.RG_CAN_NODE_ID.value
        nodeid = self.parent.writeToKernel(buf)[2]
        # buf[2] = nodeid

        self.KernelNodeID.setText(str(nodeid))
        # self.parent.writeToKernel(buf)
        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_CAN_BIT_RATE_1.value
        buf[2] = 2
        bitrate = self.parent.writeToKernel(buf)[2:4]
        bitval = ((bitrate[0] << 8) & 0xff00) | bitrate[1]
        self.KernelBitRate.setCurrentIndex(self.KernelBitRate.findText(str(bitval)))
        # bit1 = (bitrate >> 8) & 0xff
        # bit2 = bitrate & 0xff
        # buf[3] = bit1
        # buf[4] = bit2

        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_CAN_SAMPLE_POINT_1.value
        buf[2] = 2
        samplepoint = self.parent.writeToKernel(buf)[2:4]


        sample = ((samplepoint[0] << 8) & 0xff00) | samplepoint[1]
        self.KernelSamplePoint.setText(str(sample))

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

        self.parent.writeToKernel(buf)
        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_BLOCK_WRITE_REPORT
        buf[1] = eRegister.RG_CAN_SAMPLE_POINT_1.value
        buf[2] = 2

        samplepoint = int(self.KernelSamplePoint.text())
        sample1 = (samplepoint >> 8) & 0xff
        sample2 = samplepoint & 0xff
        buf[3] = sample1
        buf[4] = sample2

        self.parent.writeToKernel(buf)
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

        # if self.parent.KernelCameraSelect.currentIndex() == 0:
        #     for p in self.parent.paths:
        #         self.parent.camera = p
        #
        #         self.adjustRTC()
        #     self.parent.camera = self.parent.paths[0]
        # else:
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

class MAPIR_ProcessingDockWidget(QtWidgets.QMainWindow, FORM_CLASS):
    BASE_COEFF_SURVEY1_NDVI_JPG = {"red":   {"slope": 331.759383023, "intercept": -6.33770486888},
                                   "green": {"slope": 0.00, "intercept": 0.00},
                                   "blue":  {"slope": 51.3264675118, "intercept": -0.6931339436}
                                  }

    BASE_COEFF_SURVEY2_RED_JPG = {"slope": 16.01240929, "intercept": -2.55421832}
    BASE_COEFF_SURVEY2_RED_TIF = {"slope": 0.24177528, "intercept": -5.09645820}

    BASE_COEFF_SURVEY2_GREEN_JPG = {"slope": 4.82869470, "intercept": -0.60437250}
    BASE_COEFF_SURVEY2_GREEN_TIF = {"slope": 0.07640011, "intercept": -1.39528479}

    BASE_COEFF_SURVEY2_BLUE_JPG = {"slope": 2.67916884, "intercept": -0.39268985}
    BASE_COEFF_SURVEY2_BLUE_TIF = {"slope": 0.03943339, "intercept": -0.67299134}


    BASE_COEFF_SURVEY2_NDVI_JPG = {"red":   {"slope": 6.51199915, "intercept": -0.29870245},
                                   "green": {"slope": 0.00, "intercept": 0.00},
                                   "blue":  {"slope": 10.30416005, "intercept": -0.65112026}
                                  }

    BASE_COEFF_SURVEY2_NDVI_TIF = {"red":   {"slope": 1.06087488594, "intercept": 3.21946584661},
                                   "green": {"slope": 0.00, "intercept": 0.00},
                                   "blue":  {"slope": 1.46482226805, "intercept": -43.6505776052}
                                  }

    BASE_COEFF_SURVEY2_NIR_JPG = {"slope": 7.13619139, "intercept": -0.46967653}
    BASE_COEFF_SURVEY2_NIR_TIF = {"slope":  0.12962333, "intercept": -2.24216724}

    BASE_COEFF_SURVEY3_NGB_TIF = {"red":   {"slope": 6.9623355781520475, "intercept": -0.0864835439375467},
                                  "green": {"slope": 1.8947426321347667, "intercept": -0.0494622920687357},
                                  "blue":  {"slope": 2.743963570586564, "intercept":  -0.03883688306243116}
                                 }

    BASE_COEFF_SURVEY3_NGB_JPG = {"red":   {"slope": 1.3572359350724152, "intercept": -0.23211423412281346},
                                  "green": {"slope": 1.1880427799275182, "intercept": -0.15262065349606874},
                                  "blue":  {"slope": 1.352860697992975, "intercept":  -0.19361810260132328}
                                 }

    BASE_COEFF_SURVEY3_RGN_JPG = {"red":   {"slope": 1.3289958195489457, "intercept": -0.17638075239399503},
                                  "green": {"slope": 1.2902528664499517, "intercept": -0.15262065349606874},
                                  "blue":  {"slope": 1.387381083964384, "intercept":  -0.2193633829181454}
                                 }

    BASE_COEFF_SURVEY3_RGN_TIF = {"red":   {"slope": 3.3823966319413326, "intercept": -0.025581742423831766},
                                  "green": {"slope": 2.0198257823722026, "intercept": -0.019624370783744682},
                                  "blue":  {"slope": 6.639688121967463, "intercept":  -0.025991734455270532}
                                 }

    BASE_COEFF_SURVEY3_OCN_JPG = {"red":   {"slope": 1.0228327654792326, "intercept": -0.1847085716228949},
                                  "green": {"slope":  1.0655229303683258, "intercept": -0.1921036590734388},
                                  "blue":  {"slope": 1.0562618906633048, "intercept":  -0.2037317328293336}
                                 }

    BASE_COEFF_SURVEY3_OCN_TIF = {"red":   {"slope": 1.557354345031938, "intercept": -0.0790237907829558},
                                  "green": {"slope": 1.3794503108318112, "intercept": -0.0743811687912796},
                                  "blue":  {"slope": 2.1141137232666183, "intercept": -0.0650818927718132}
                                 }

    BASE_COEFF_SURVEY3_NIR_TIF = {"slope":  13.2610911247, "intercept": 0.0}

    BASE_COEFF_SURVEY3_RE_JPG = {"slope":  0.12962333, "intercept": -2.24216724}
    BASE_COEFF_SURVEY3_RE_TIF = {"slope":  14.637430522690837, "intercept": -0.11816284659122683}

    BASE_COEFF_DJIX3_NDVI_JPG = {"red":   {"slope": 4.63184993, "intercept": -0.34430543},
                                 "green": {"slope": 0.00, "intercept": 0.00},
                                 "blue":  {"slope": 16.36429964, "intercept": -0.49413940}
                                }

    BASE_COEFF_DJIX3_NDVI_TIF = {"red":   {"slope": 0.01350319, "intercept": -0.74925346},
                                 "green": {"slope": 0.00, "intercept": 0.00},
                                 "blue":  {"slope": 0.03478272, "intercept": -0.77810008}
                                }

    BASE_COEFF_DJIPHANTOM4_NDVI_JPG = {"red":   {"slope": 0.03333209, "intercept": -1.17016961},
                                       "green": {"slope": 0.00, "intercept": 0.00},
                                       "blue":  {"slope": 0.05373502, "intercept": -0.99455214}
                                      }

    BASE_COEFF_DJIPHANTOM4_NDVI_TIF = {"red":   {"slope": 0.03333209, "intercept": -1.17016961},
                                       "green": {"slope": 0.00, "intercept": 0.00},
                                       "blue":  {"slope": 0.05373502, "intercept": -0.99455214}
                                      }

    BASE_COEFF_DJIPHANTOM3_NDVI_JPG = {"red":   {"slope": 3.44708472, "intercept": -1.54494979},
                                       "green": {"slope": 0.00, "intercept": 0.00},
                                       "blue":  {"slope": 6.35407929, "intercept": -1.40606832}
                                      }

    BASE_COEFF_DJIPHANTOM3_NDVI_TIF = {"red":   {"slope":  0.01752340, "intercept": -1.37495554},
                                       "green": {"slope": 0.00, "intercept": 0.00},
                                       "blue":  {"slope": 0.03700812, "intercept": -1.41073753}
                                      }

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
    qrcoeffs = []

    qrcoeffs2 = []
    qrcoeffs3 = []
    qrcoeffs4 = []
    qrcoeffs5 = []
    qrcoeffs6 = []
    coords = []
    # drivesfound = []
    ref = ""
    refindex = ["oldrefvalues", "newrefvalues"] #version 1 - old, version 2 - new
    refvalues = {
    "oldrefvalues":{
        "660/850": [[0.87032549, 0.52135779, 0.23664799], [0, 0, 0], [0.8463514, 0.51950608, 0.22795518]],
        "446/800": [[0.8419608509, 0.520440145, 0.230113958], [0, 0, 0], [0.8645652801, 0.5037779363, 0.2359041624]],
        "850": [[0.8463514, 0.51950608, 0.22795518], [0, 0, 0], [0, 0, 0]],

        "650": [[0.87032549, 0.52135779, 0.23664799], [0, 0, 0], [0, 0, 0]],
        "550": [[0, 0, 0], [0.87415089, 0.51734381, 0.24032515], [0, 0, 0]],
        "450": [[0, 0, 0], [0, 0, 0], [0.86469794, 0.50392915, 0.23565447]],
        "725": [0.8609978650653954, 0.5211329995745606, 0.23324225504400245],
        "490/615/808": [0.8472247816774043, 0.5200480372488874, 0.23065111839727553],
        "Mono450": [0.8634818638, 0.5024087105, 0.2351860396],
        "Mono550": [0.8740616379, 0.5173070235, 0.2402423818],
        "Mono650": [0.8705783136, 0.5212290524, 0.2366437854],
        "Mono725": [0.8606071247, 0.521474266, 0.2337744252],
        "Mono808": [0.8406184266, 0.5203405498, 0.2297701185],
        "Mono850": [0.8481919553, 0.519491643, 0.2278713071],
        "Mono405": [0.8556905469, 0.4921243183, 0.2309899254],
        "Mono518": [0.8729814889, 0.5151370187, 0.2404729692],
        "Mono632": [0.8724034645, 0.5209649915, 0.2374529161],

        "Mono590": [0.8747043911, 0.5195596573, 0.2392049856],
        "550/660/850": [[0.8474610999, 0.5196055607, 0.2279922965],[0.8699940018, 0.5212235151, 0.2364397706],[0.8740311726, 0.5172611881, 0.2402870156]]

    },
    "newrefvalues":{
        "660/850": [[0.87032549, 0.52135779, 0.23664799], [0, 0, 0], [0.8653063177, 0.2798126291, 0.2337498097, 0.0193295348]],
        "446/800": [[0.7882333002, 0.2501235178, 0.1848459584, 0.020036883], [0, 0, 0], [0.8645652801, 0.5037779363, 0.2359041624]],
        "725" : [0.8688518306024209, 0.26302553751154756, 0.2127410973890211, 0.019551020566927594],
        "850": [[0.8649280907, 0.2800907016, 0.2340131491, 0.0195446727], [0, 0, 0], [0, 0, 0]],

        "650": [[0.8773469949, 0.2663571183, 0.199919444, 0.0192325637], [0, 0, 0], [0, 0, 0]],
        "550": [[0, 0, 0], [0.8686559344, 0.2655697585, 0.1960837144, 0.0195629009], [0, 0, 0]],
        "450": [[0, 0, 0], [0, 0, 0], [0.7882333002, 0.2501235178, 0.1848459584, 0.020036883]],
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
        "490/615/808": [[0.8414604806, 0.2594283565, 0.1897271608, 0.0197180224],
                        [0.8751529643, 0.2673261446, 0.2007025375, 0.0192817427],
                        [0.868782908, 0.27845399, 0.2298671821, 0.0211305297]],
        "475/550/850": [[0.8348841674, 0.2580074987, 0.1890252099, 0.01975703], [0.8689592421, 0.2656248359, 0.1961875592, 0.0195576511],
                        [0.8653063177, 0.2798126291, 0.2337498097, 0.0193295348]]

    }}
    pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                     "greenmax": 0.0, "greenmin": 65535.0,
                     "bluemax": 0.0, "bluemin": 65535.0}

    multiplication_values = {"red":   {"slope": 0.00, "intercept": 0.00},
                             "green": {"slope": 0.00, "intercept": 0.00},
                             "blue":  {"slope": 0.00, "intercept": 0.00},
                             "mono":  {"slope": 0.00, "intercept": 0.00}
                            }

    monominmax = {"min": 65535.0,"max": 0.0}
    imkeys_JPG = np.array(list(range(0, 255)))
    imkeys = np.array(list(range(0, 65536)))
    weeks = 0
    days = 0
    hours = 0
    minutes = 0
    seconds = 1
    conv = None
    kcr = None
    analyze_bands = []
    modalwindow = None
    calcwindow = None
    LUTwindow = None
    M_Shutter_Window = None
    A_Shutter_Window = None
    Bandwindow = None
    Advancedwindow = None
    rdr = []
    ManualExposurewindow = None
    AutoExposurewindow = None
    BandNames = {
        "RGB": [644, 0, 0],
        "405": [405, 0, 0],
        "450": [450, 0, 0],
        "490": [490, 0, 0],
        "518": [518, 0, 0],
        "550": [550, 0, 0],
        "590": [590, 0, 0],
        "615": [615, 0, 0],
        "632": [632, 0, 0],
        "650": [650, 0, 0],
        "685": [685, 0, 0],
        "725": [725, 0, 0],
        "780": [780, 0, 0],
        "808": [808, 0, 0],
        "850": [850, 0, 0],
        "880": [880, 0, 0],
        "940": [940, 0, 0],
        "945": [945, 0, 0],
        "UVR": [870, 0, 395],
        "NGB": [850, 550, 475],
        "RGN": [660, 550, 850],
        "OCN": [615, 490, 808],

    }
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
    yesdelete = False
    selection_made = False
    POLL_TIME = 3000

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

    COLOR_CORRECTION_VECTORS = [1.58796, -0.1036, 0.18497, -0.01213, 1, 0.11236, 0.00793, -0.06779, 1.78981]
    regs = []

    DJIS = ["DJI Phantom 4", "DJI Phantom 4 Pro", "DJI Phantom 3a", "DJI Phantom 3p", "DJI X3"]
    SURVEYS = ["Survey1", "Survey2", "Survey3"]
    KERNELS = ["Kernel 1.2", "Kernel 3.2", "Kernel 14.4", "Kernel 14.4"]
    ANGLE_SHIFT_QR = 7

    JPGS = ["jpg", "JPG", "jpeg", "JPEG"]
    TIFS = ["tiff", "TIFF", "tif", "TIF"]

    CHECKED = 2 # QT creator syntax for checkState(); 2 signifies the box is checked, 0 is unchecked
    UNCHECKED = 0

    ISO_VALS = (1,2,4,8,16,32)
    lensvals = None
    def __init__(self, parent=None):
        """Constructor."""
        super(MAPIR_ProcessingDockWidget, self).__init__(parent)

        self.setupUi(self)
        self.ViewerCalcButton.setStyleSheet("QPushButton { background-color: None; color: #3f3f3f; }")
        self.LUTButton.setStyleSheet("QPushButton { background-color: None ; color: #3f3f3f;} ")

        try:
            legend = cv2.imread(os.path.dirname(__file__) + "/lut_legend.jpg")
            legh, legw = legend.shape[:2]

            self.legend_frame = QtGui.QImage(legend.data, legw, legh, legw, QtGui.QImage.Format_Grayscale8)
            self.LUTGraphic.setPixmap(QtGui.QPixmap.fromImage(
                QtGui.QImage(self.legend_frame)))
            self.LegendLayout_2.hide()

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))

    def exitTransfer(self, drv='C'):
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
        # self.exitTransfer()
        self.ConnectKernels()

    def on_KernelConnect_released(self):
        # self.exitTransfer()
        self.ConnectKernels()

    def ConnectKernels(self):
        self.KernelLog.append(' ')
        all_cameras = hid.enumerate(self.VENDOR_ID, self.PRODUCT_ID)
        if all_cameras == []:
            self.KernelLog.append("No cameras found! Please check your USB connection and try again.")

        else:
            self.paths.clear()
            self.pathnames.clear()

            for cam in all_cameras:
                if cam['product_string'] == 'HID Gadget':
                    self.camera = cam['path']
                    buf = [0] * 512
                    buf[0] = self.SET_REGISTER_READ_REPORT
                    buf[1] = eRegister.RG_CAMERA_LINK_ID.value

                    arid = self.writeToKernel(buf)[2]
                    self.paths.insert(arid, cam['path'])
                    QtWidgets.QApplication.processEvents()

            self.KernelCameraSelect.blockSignals(True)
            self.KernelCameraSelect.clear()
            self.KernelCameraSelect.blockSignals(False)
            try:
                for i, path in enumerate(self.paths):
                    QtWidgets.QApplication.processEvents()
                    self.camera = path
                    buf = [0] * 512
                    buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
                    buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
                    buf[2] = 3

                    res = self.writeToKernel(buf)
                    item = chr(res[2]) + chr(res[3]) + chr(res[4])
                    self.pathnames.append(item)

                    if i == 0:
                        item += " (Master)"

                    else:
                        item += " (Slave)"

                    self.KernelLog.append("Found Camera: " + str(item))
                    QtWidgets.QApplication.processEvents()
                    self.KernelCameraSelect.blockSignals(True)
                    self.KernelCameraSelect.addItem(item)
                    self.KernelCameraSelect.blockSignals(False)

                self.camera = self.paths[0]

                try:
                    self.KernelUpdate()
                    QtWidgets.QApplication.processEvents()

                except Exception as e:
                    exc_type, exc_obj,exc_tb = sys.exc_info()
                    print(e)
                    print("Line: " + str(exc_tb.tb_lineno))
                    QtWidgets.QApplication.processEvents()

            except Exception as e:
                exc_type, exc_obj,exc_tb = sys.exc_info()
                self.KernelLog.append("Error: (" + str(e) + ' Line: ' + str(exc_tb.tb_lineno) +  ") connecting to camera, please ensure all cameras are connected properly and not in transfer mode.")
                QtWidgets.QApplication.processEvents()

    def UpdateLensID(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_LENS_ID.value
        buf[2] = DROPDOW_2_LENS.get((self.KernelFilterSelect.currentText(), self.KernelLensSelect.currentText()), 255)
        self.writeToKernel(buf)

    def on_KernelLensSelect_currentIndexChanged(self):
        try:
            self.UpdateLensID()
            self.KernelUpdate()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.KernelLog.append("Error: " + e)

    def on_KernelFilterSelect_currentIndexChanged(self):
        try:
            # threeletter = self.KernelFilterSelect.currentText()
            # buf = [0] * 512
            # buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
            # buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
            # buf[2] = 3
            # buf[3] = ord(threeletter[0])
            # buf[4] = ord(threeletter[1])
            # buf[5] = ord(threeletter[2])
            # res = self.writeToKernel(buf)
            self.UpdateLensID()
            self.KernelUpdate()

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.KernelLog.append("Error: " + e)

    def on_KernelArraySelect_currentIndexChanged(self):
        if not self.KernelTransferButton.isChecked():

            try:
                dval = int(self.KernelArraySelect.currentText())
                tempcam = copy.deepcopy(self.camera)

                for cam in self.paths:
                    self.camera = cam
                    buf = [0] * 512
                    buf[0] = self.SET_REGISTER_WRITE_REPORT
                    buf[1] = eRegister.RG_CAMERA_ARRAY_TYPE.value
                    buf[2] = dval
                    self.writeToKernel(buf)

                self.camera = tempcam
                self.KernelUpdate()

            except Exception as e:
                exc_type, exc_obj,exc_tb = sys.exc_info()
                self.KernelLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
        QtWidgets.QApplication.processEvents()
    def on_KernelCameraSelect_currentIndexChanged(self):
        # if self.KernelCameraSelect.currentIndex() == 0:
        #     self.array_indicator = True
        # else:
        #     self.array_indicator = False
        self.camera = self.paths[self.KernelCameraSelect.currentIndex()]

        # self.KernelFilterSelect.blockSignals(True)
        # self.KernelFilterSelect.setCurrentIndex(self.KernelFilterSelect.findText(self.KernelCameraSelect.currentText()))
        # self.KernelFilterSelect.blockSignals(False)
        if not self.KernelTransferButton.isChecked():
            try:
                self.KernelUpdate()
            except Exception as e:
                exc_type, exc_obj,exc_tb = sys.exc_info()
                self.KernelLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
        QtWidgets.QApplication.processEvents()
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
                # self.imkeys = np.array(list(range(0, 65536)))
                self.displaymin = self.display_image.min()
                self.displaymax = self.display_image.max()


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
                #self.ViewerCalcButton.blockSignals(True)
                self.LUTButton.blockSignals(True)
                self.LUTBox.blockSignals(True)
                self.ViewerIndexBox.blockSignals(True)
                self.ViewerStretchBox.blockSignals(True)

                self.ViewerCalcButton.setStyleSheet("QPushButton { background-color: rgb(50,180,50); color: white }")
                self.LUTBox.setEnabled(False)
                self.LUTBox.setChecked(False)
                self.ViewerIndexBox.setEnabled(False)
                self.ViewerIndexBox.setChecked(False)
                self.ViewerStretchBox.setChecked(True)

                #self.ViewerCalcButton.blockSignals(False)
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))

    def on_ViewerSaveButton_released(self):

        if self.savewindow == None:
            self.savewindow = SaveDialog(self)
        self.savewindow.resize(385, 110)
        self.savewindow.exec_()

        QtWidgets.QApplication.processEvents()

    def on_LUTButton_released(self):
        if self.display_image_original is not None:
            if self.LUTwindow == None:
                self.LUTwindow = Applicator(self)
            self.LUTwindow.resize(385, 160)
            self.LUTwindow.show()
        else:
            None

        QtWidgets.QApplication.processEvents()
    def on_ViewerCalcButton_released(self):
        if self.display_image_original is not None:
        
            if self.LUTwindow == None:
                self.calcwindow = Calculator(self)

            self.calcwindow.resize(685, 250)
            self.calcwindow.show()
            QtWidgets.QApplication.processEvents()

        else:
            None

    def on_ZoomIn_released(self):
        if self.image_loaded == True:
            try:
                # self.KernelViewer.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
                factor = 1.15
                self.KernelViewer.scale(factor, factor)
            except Exception as e:
                exc_type, exc_obj,exc_tb = sys.exc_info()
                print(e)
                print("Line: " + str(exc_tb.tb_lineno))
    def on_ZoomOut_released(self):
        if self.image_loaded == True:
            try:
                # self.KernelViewer.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
                factor = 1.15
                self.KernelViewer.scale(1/factor, 1/factor)
            except Exception as e:
                exc_type, exc_obj,exc_tb = sys.exc_info()
                print(e)
                print("Line: " + str(exc_tb.tb_lineno))
    def on_ZoomToFit_released(self):
        self.mapscene = QtWidgets.QGraphicsScene()
        self.mapscene.addPixmap(QtGui.QPixmap.fromImage(
            QtGui.QImage(self.frame)))

        self.KernelViewer.setScene(self.mapscene)
        self.KernelViewer.fitInView(self.mapscene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.KernelViewer.setFocus()
        QtWidgets.QApplication.processEvents()
    # TODO Block
    # def wheelEvent(self, event):
    #     if self.image_loaded == True:
    #         try:
    #
    #         except Exception as e:
    # exc_type, exc_obj,exc_tb = sys.exc_info()
    #             print(str(e) + ' ) + str(exc_tb.tb_lineno

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
    # exc_type, exc_obj,exc_tb = sys.exc_info()
    #             print(str(e) + ' ) + str(selfexc_tb.tb_lineno):
    # TODO end block
    def resizeEvent(self, event):
        # redraw the image in the viewer every time the window is resized
        if self.image_loaded == True:
            self.mapscene = QtWidgets.QGraphicsScene()
            self.mapscene.addPixmap(QtGui.QPixmap.fromImage(
                QtGui.QImage(self.frame)))

            self.KernelViewer.setScene(self.mapscene)

            self.KernelViewer.setFocus()
            QtWidgets.QApplication.processEvents()

    def KernelUpdate(self):
        try:
            self.KernelExposureMode.blockSignals(True)

            self.KernelVideoOut.blockSignals(True)
            self.KernelFolderCount.blockSignals(True)
            self.KernelBeep.blockSignals(True)
            self.KernelPWMSignal.blockSignals(True)
            self.KernelLensSelect.blockSignals(True)
            self.KernelFilterSelect.blockSignals(True)
            self.KernelArraySelect.blockSignals(True)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
            buf[1] = eRegister.RG_CAMERA_SETTING.value
            buf[2] = eRegister.RG_SIZE.value

            res = self.writeToKernel(buf)[2:]
            self.regs = res




            shutter = self.getRegister(eRegister.RG_SHUTTER.value)
            if shutter == 0:
                self.KernelExposureMode.setCurrentIndex(0)
                self.KernelMESettingsButton.setEnabled(False)
                self.KernelAESettingsButton.setEnabled(True)
            else:
                self.KernelExposureMode.setCurrentIndex(1)
                self.KernelMESettingsButton.setEnabled(True)
                self.KernelAESettingsButton.setEnabled(False)



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



            fil = str(LENS_LOOKUP.get(self.getRegister(eRegister.RG_LENS_ID.value), 255)[2])
            self.KernelFilterSelect.setCurrentIndex(self.KernelFilterSelect.findText(fil))

            lens = str(LENS_LOOKUP.get(self.getRegister(eRegister.RG_LENS_ID.value), 255)[0][0]) + "mm"
            self.KernelLensSelect.setCurrentIndex(self.KernelLensSelect.findText(lens))

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
            # self.KernelPanel.append("Hardware ID: " + str(self.getRegister(eRegister.RG_HARDWARE_ID.value)))
            # self.KernelPanel.append("Firmware version: " + str(self.getRegister(eRegister.RG_FIRMWARE_ID.value)))
            self.KernelPanel.append("Sensor: " + str(self.getRegister(eRegister.RG_SENSOR_ID.value)))
            self.KernelPanel.append("Lens: " + str(LENS_LOOKUP.get(self.getRegister(eRegister.RG_LENS_ID.value), 255)[0][0]) + "mm")
            self.KernelPanel.append(
                "Filter: " + str(LENS_LOOKUP.get(self.getRegister(eRegister.RG_LENS_ID.value), "")[2]))
            # if shutter == 0:
            #     self.KernelPanel.append("Shutter: Auto")
            # else:
            #     self.KernelPanel.append("Shutter: " + self.M_Shutter_Window.KernelShutterSpeed.itemText(self.getRegister(eRegister.RG_SHUTTER.value) -1) + " sec")
            self.KernelPanel.append("ISO: " + str(self.getRegister(eRegister.RG_ISO.value)) + "00")
            # # self.KernelPanel.append("WB: " + str(self.getRegister(eRegister.RG_WHITE_BALANCE.value)))
            # self.KernelPanel.append("AE Setpoint: " + str(self.getRegister(eRegister.RG_AE_SETPOINT.value)))
            buf = [0] * 512
            buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
            buf[1] = eRegister.RG_CAMERA_ID.value
            buf[2] = 6
            st = self.writeToKernel(buf)
            serno = str(chr(st[2]) + chr(st[3]) + chr(st[4]) + chr(st[5]) + chr(st[6]) + chr(st[7]))
            self.KernelPanel.append("Serial #: " + serno)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_READ_REPORT
            buf[1] = eRegister.RG_CAMERA_ARRAY_TYPE.value
            artype = str(self.writeToKernel(buf)[2])
            self.KernelArraySelect.setCurrentIndex(int(self.KernelArraySelect.findText(artype)))
            self.KernelPanel.append("Array Type: " + str(artype))
            buf = [0] * 512
            buf[0] = self.SET_REGISTER_READ_REPORT
            buf[1] = eRegister.RG_CAMERA_LINK_ID.value
            arid = self.writeToKernel(buf)[2]
            self.KernelPanel.append("Array ID: " + str(arid))

            self.KernelExposureMode.blockSignals(False)
            # self.KernelShutterSpeed.blockSignals(False)
            # self.KernelISO.blockSignals(False)

            self.KernelVideoOut.blockSignals(False)
            self.KernelFolderCount.blockSignals(False)
            self.KernelBeep.blockSignals(False)
            self.KernelPWMSignal.blockSignals(False)
            self.KernelLensSelect.blockSignals(False)
            self.KernelFilterSelect.blockSignals(False)
            self.KernelArraySelect.blockSignals(False)
            QtWidgets.QApplication.processEvents()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.KernelLog.append("Error: (" + str(e) + ' Line: ' + str(
                exc_tb.tb_lineno) + ") updating interface.")
        # self.KernelGain.blockSignals(False)
        # self.KernelSetPoint.blockSignals(False)
    def on_KernelFolderButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.KernelTransferFolder.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.KernelTransferFolder.text())

    cancel_auto = False
    def on_KernelAutoCancel_released(self):
        self.cancel_auto = True




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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))

    def getXML(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_MEDIA_FILE_NAME_A.value
        buf[2] = 3
        res = self.writeToKernel(buf)

        filt = chr(res[2]) + chr(res[3]) + chr(res[4])

        buf = [0] * 512
        buf[0] = self.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_CAMERA_SETTING.value
        buf[2] = eRegister.RG_SIZE.value

        res = self.writeToKernel(buf)
        self.regs = res[2:]
        sens = str(self.getRegister(eRegister.RG_SENSOR_ID.value))
        lens = str(self.getRegister(eRegister.RG_LENS_ID.value))

        buf = [0] * 512
        buf[0] = self.SET_REGISTER_READ_REPORT
        buf[1] = eRegister.RG_CAMERA_ARRAY_TYPE.value
        artype = str(self.writeToKernel(buf)[2])

        buf = [0] * 512
        buf[0] = self.SET_REGISTER_READ_REPORT
        buf[1] = eRegister.RG_CAMERA_LINK_ID.value
        arid = str(self.writeToKernel(buf)[2])

        return (filt, sens, lens, arid, artype)
    def on_KernelMatrixButton_toggled(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_BLOCK_WRITE_REPORT
        buf[1] = eRegister.RG_COLOR_GAMMA_START.value
        buf[2] = 192
        try:
            if self.KernelMatrixButton.isChecked():
                mtx = (np.array([3.2406,-1.5372,-0.498,-0.9689,1.8756,0.0415,0.0557,-0.2040,1.0570]) * 16384.0).astype("uint32")
                offset = (np.array([0.0, 0.0, 0.0])).astype("uint32")
                gamma = (np.array([7.0,0.0,6.5,3.0,6.0,8.0,5.5,13.0,5.0,22.0,4.5,38.0,3.5,102.0,2.5,230.0,1.75,422.0,1.25,679.0,0.875,1062.0,0.625, 1575.0]) * 16.0).astype("uint32")
                # buf[3::] = struct.pack("<36i", *(mtx.tolist() + offset.tolist() + gamma.tolist()))
            else:
                mtx = (np.array([1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0]) * 16384.0).astype("uint32")
                offset = (np.array([0.0, 0.0, 0.0])).astype("uint32")
                gamma = (np.array([1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0,0.0]) * 16.0).astype("uint32")
            buf[3::] = struct.pack("<36L", *(mtx.tolist() + gamma.tolist() + offset.tolist()))

            # for i in range(len(buf)):
            #     buf[i] = int(buf[i])
            self.writeToKernel(buf)
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.KernelLog.append("Error: " + str(e) + ' Line: ' + str(exc_tb.tb_lineno))
    def getAvailableDrives(self):
        if 'Windows' not in platform.system():
            return []
        drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        return list(itertools.compress(string.ascii_uppercase, map(lambda x: ord(x) - ord('0'), bin(drive_bitmask)[:1:-1])))
    def on_KernelTransferButton_toggled(self):
        self.KernelLog.append(' ')
        currentcam = None
        try:
            if not self.camera:
                raise ValueError('Device not found')
            else:
                currentcam = self.camera

            if self.KernelTransferButton.isChecked():
                self.driveletters.clear()


                # if self.KernelCameraSelect.currentIndex() == 0:
                try:

                    for place, cam in enumerate(self.paths):
                        self.camera = cam
                        QtWidgets.QApplication.processEvents()
                        numds = win32api.GetLogicalDriveStrings().split(':\\\x00')[:-1]

                        # time.sleep(2)
                        xmlret = self.getXML()
                        buf = [0] * 512
                        buf[0] = self.SET_COMMAND_REPORT
                        buf[1] = eCommand.CM_TRANSFER_MODE.value
                        self.writeToKernel(buf)
                        self.KernelLog.append("Camera " + str(self.pathnames[self.paths.index(cam)]) + " entering Transfer mode")
                        QtWidgets.QApplication.processEvents()
                        treeroot = ET.parse(modpath + os.sep + "template.kernelconfig")
                        treeroot.find("Filter").text = xmlret[0]
                        treeroot.find("Sensor").text = xmlret[1]
                        treeroot.find("Lens").text = xmlret[2]
                        treeroot.find("ArrayID").text = xmlret[3]
                        treeroot.find("ArrayType").text = xmlret[4]
                        keep_looping = True
                        while keep_looping:
                            numds = set(numds)
                            numds1 = set(win32api.GetLogicalDriveStrings().split(':\\\x00')[:-1])
                            if numds == numds1:
                                pass
                            else:

                                drv = list(numds1 - numds)[0]
                                if len(drv) == 1:
                                    self.driveletters.append(drv)

                                    self.KernelLog.append("Camera " + str(self.pathnames[self.paths.index(cam)]) + " successfully connected to drive " + drv + ":" + os.sep)
                                    files = glob.glob(drv + r":" + os.sep + r"dcim/*/*.[tm]*", recursive=True)
                                    folders = glob.glob(drv + r":" + os.sep + r"dcim/*/")
                                    if folders:
                                        for fold in folders:
                                            if os.path.exists(fold + str(self.pathnames[self.paths.index(cam)]) + ".kernelconfig"):
                                                os.unlink(fold + str(self.pathnames[self.paths.index(cam)]) + ".kernelconfig")
                                            treeroot.write(fold + str(self.pathnames[self.paths.index(cam)]) + ".kernelconfig")
                                    else:
                                        if not os.path.exists(drv + r":" + os.sep + r"dcim" + os.sep + str(self.pathnames[self.paths.index(cam)])):
                                            os.mkdir(drv + r":" + os.sep + r"dcim" + os.sep + str(self.pathnames[self.paths.index(cam)]))
                                        treeroot.write(
                                            drv + r":" + os.sep + r"dcim" + os.sep + str(self.pathnames[self.paths.index(cam)]) + ".kernelconfig")

                                    keep_looping = False


                                else:
                                    numds = win32api.GetLogicalDriveStrings().split(':\\\x00')[:-1]
                                QtWidgets.QApplication.processEvents()



                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    self.KernelLog.append(str(e))
                    self.KernelLog.append("Line: " + str(exc_tb.tb_lineno))
                    QtWidgets.QApplication.processEvents()
                    self.camera = currentcam

                self.camera = currentcam






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
                            files = glob.glob(drv + r":" + os.sep + r"dcim/*/*", recursive=True)
                            threechar = ''
                            try:
                                threechar = files[0].split(os.sep)[-1][1:4]
                            except Exception as e:
                                self.KernelLog.append(r"No files detected in drive " + drv + r'. Moving to next camera.')
                                pass
                            for fold in folders:


                                if os.path.exists(self.transferoutfolder + os.sep + threechar):
                                    foldercount = 1
                                    endloop = False
                                    while endloop is False:
                                        outdir = self.transferoutfolder + os.sep + threechar + '_' + str(foldercount)
                                        if os.path.exists(outdir):
                                            foldercount += 1
                                        else:
                                            shutil.copytree(fold, outdir)
                                            endloop = True
                                else:
                                    outdir = self.transferoutfolder + os.sep + threechar
                                    shutil.copytree(fold, outdir)
                                QtWidgets.QApplication.processEvents()
                                # for file in files:
                                #     # if file.split(os.sep)[-1][1:4] == threechar:

                                # else:
                                #     threechar = file.split(os.sep)[-1][1:4]
                                #     os.mkdir(self.transferoutfolder + os.sep + threechar)
                                #     shutil.copy(file, self.transferoutfolder + os.sep + threechar)
                                QtWidgets.QApplication.processEvents()
                            if threechar:
                                self.KernelLog.append("Finished extracting images from Camera " + str(threechar) + " number " + str(place + 1) + " of " + str(len(self.driveletters)) + ", at drive " + drv + r':')
                            QtWidgets.QApplication.processEvents()
                        else:
                            self.KernelLog.append("No DCIM folder found in drive " + str(drv) + r":")
                            QtWidgets.QApplication.processEvents()
                    self.yestransfer = False
                if self.yesdelete:
                    for drv in self.driveletters:
                        if os.path.isdir(drv + r":" + os.sep + r"dcim"):
                            # try:
                            files = glob.glob(drv + r":" + os.sep + r"dcim/*/*")
                            self.KernelLog.append("Deleting files from drive " + str(drv))
                            for file in files:
                                os.unlink(file)
                            folds = glob.glob(drv + r":" + os.sep + r"dcim/*")
                            for file in folds:
                                os.unlink(file)
                            self.KernelLog.append("Finished deleting files from drive " + str(drv))
                    self.yesdelete = False
                    # self.modalwindow = KernelDelete(self)
                    # self.modalwindow.resize(400, 200)
                    # self.modalwindow.exec_()

            else:
                for place, cam in enumerate(self.paths):
                    try:
                        self.camera = cam
                        self.exitTransfer(self.driveletters[place])
                    except:

                        pass
            self.camera = currentcam
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            # self.exitTransfer()
            # self.KernelTransferButton.setChecked(False)
            self.KernelLog.append("Error: " + str(e) + ' Line: ' + str(exc_tb.tb_lineno))
            QtWidgets.QApplication.processEvents()
            self.camera = currentcam




    def on_KernelExposureMode_currentIndexChanged(self):
        # self.KernelExposureMode.blockSignals(True)
        if self.KernelExposureMode.currentIndex() == 1: #Manual

            self.KernelMESettingsButton.setEnabled(True)
            self.KernelAESettingsButton.setEnabled(False)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_SHUTTER.value
            buf[2] = 9

            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_ISO.value
            buf[2] = 1

            res = self.writeToKernel(buf)

            QtWidgets.QApplication.processEvents()
        else: #Auto

            self.KernelMESettingsButton.setEnabled(False)
            self.KernelAESettingsButton.setEnabled(True)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_SHUTTER.value
            buf[2] = 0

            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_SELECTION.value
            # buf[2] = self.AutoAlgorithm.currentIndex()
            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_MAX_SHUTTER.value
            # buf[2] = self.AutoMaxShutter.currentIndex()

            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_MIN_SHUTTER.value
            # buf[2] = self.AutoMinShutter.currentIndex()

            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_MAX_GAIN.value
            # buf[2] = self.AutoMaxISO.currentIndex()

            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_F_STOP.value
            # buf[2] = self.AutoFStop.currentIndex()

            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_GAIN.value
            # buf[2] = self.AutoGain.currentIndex()

            res = self.writeToKernel(buf)

            buf = [0] * 512
            buf[0] = self.SET_REGISTER_WRITE_REPORT
            buf[1] = eRegister.RG_AE_SETPOINT.value
            # buf[2] = self.AutoSetpoint.currentIndex()

            res = self.writeToKernel(buf)

            QtWidgets.QApplication.processEvents()
        # self.KernelExposureMode.blockSignals(False)
    def on_KernelAESettingsButton_released(self):
        self.A_Shutter_Window = A_EXP_Control(self)
        self.A_Shutter_Window.resize(350, 350)
        self.A_Shutter_Window.exec_()
        # self.KernelUpdate()
    def on_KernelMESettingsButton_released(self):
        self.M_Shutter_Window = M_EXP_Control(self)
        self.M_Shutter_Window.resize(250, 125)
        self.M_Shutter_Window.exec_()
        # self.KernelUpdate()


    def on_KernelCaptureButton_released(self):
        # if self.KernelCameraSelect.currentIndex() == 0:
        for cam in self.paths:
            self.camera = cam
            self.captureImage()
        self.camera = self.paths[0]
        # else:
        #     self.captureImage()
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))


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
    # def on_TestButton_released(self):
    #     buf = [0] * 512
    #     buf[0] = self.SET_COMMAND_REPORT
    #     buf[1] = eRegister.RG_CAMERA_ARRAY_TYPE.value
    #     artype = self.writeToKernel(buf)[2]
    #     print(artype)
    #     try:
    #         self.KernelUpdate()
    #     except Exception as e:
    #         exc_type, exc_obj,exc_tb = sys.exc_info()
    #         print(e)
    #         print("Line: " + str(exc_tb.tb_lineno))
    def writeToKernel(self, buffer):
        try:

            dev = hid.device()
            dev.open_path(self.camera)
            q = dev.write(buffer)
            if buffer[0] == self.SET_COMMAND_REPORT and buffer[1] == eCommand.CM_TRANSFER_MODE.value:
                dev.close()
                return q
            else:
                r = dev.read(self.BUFF_LEN)
                dev.close()
                return r
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.KernelLog.append("Error: " + str(e) + ' Line: ' + str(exc_tb.tb_lineno))


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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))

    def on_KernelAdvancedSettingsButton_released(self):
        self.Advancedwindow = AdvancedOptions(self)
        # self.modalwindow = KernelCAN(self)
        self.Advancedwindow.resize(400, 200)
        self.Advancedwindow.exec_()
        # try:
        #     self.KernelUpdate()
        # except Exception as e:
        # exc_type, exc_obj,exc_tb = sys.exc_info()
        #     print(e + ' ) + exc_tb.tb_lineno
    def on_KernelFolderCount_currentIndexChanged(self):
        buf = [0] * 512
        buf[0] = self.SET_REGISTER_WRITE_REPORT
        buf[1] = eRegister.RG_MEDIA_FILES_CNT.value
        buf[2] = self.KernelFolderCount.currentIndex()

        self.writeToKernel(buf)
        try:
            self.KernelUpdate()
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))

    def on_KernelCANButton_released(self):
        self.modalwindow = KernelCAN(self)
        self.modalwindow.resize(400, 200)
        self.modalwindow.exec_()
        # try:
        #     self.KernelUpdate()
        # except Exception as e:
        #     exc_type, exc_obj,exc_tb = sys.exc_info()
        #     print(e)
        #     print("Line: " + str(exc_tb.tb_lineno))

    def on_KernelTimeButton_released(self):
        self.modalwindow = KernelTime(self)
        self.modalwindow.resize(400, 200)
        self.modalwindow.exec_()
        # try:
        #     self.KernelUpdate()
        # except Exception as e:
        # exc_type, exc_obj,exc_tb = sys.exc_info()
        #     print(e + ' ) + exc_tb.tb_lineno

    def writeToIntervalLine(self):
        self.KernelIntervalLine.clear()
        self.KernelIntervalLine.setText(
            str(self.weeks) + 'w, ' + str(self.days) + 'd, ' + str(self.hours) + 'h, ' + str(self.minutes) + 'm,' + str(
                self.seconds) + 's')

    #########Pre-Process Steps: Start#################
    def on_PreProcessLens_currentIndexChanged(self):
        if self.PreProcessCameraModel.currentText() == "Kernel 14.4":
            if self.PreProcessFilter.currentText() in ["644 (RGB)", "550/660/850"]:
                self.PreProcessVignette.setEnabled(True)

            else:
                self.PreProcessVignette.setChecked(False)
                self.PreProcessVignette.setEnabled(False)

            if self.PreProcessFilter.currentText() == "644 (RGB)":
                self.PreProcessColorBox.setEnabled(True)

            else:
                self.PreProcessColorBox.setChecked(False)
                self.PreProcessColorBox.setEnabled(False)


    def on_PreProcessFilter_currentIndexChanged(self):
        if ((self.PreProcessCameraModel.currentText() == "Kernel 14.4" and self.PreProcessFilter.currentText() == "644 (RGB)")
                or (self.PreProcessCameraModel.currentText() == "Survey3" and self.PreProcessFilter.currentText() == "RGB")):

            self.PreProcessColorBox.setEnabled(True)

            if self.PreProcessCameraModel == "Kernel 14.4":
                self.PreProcessVignette.setEnabled(True)

        elif self.PreProcessCameraModel.currentText() == "Kernel 14.4":
            if self.PreProcessFilter.currentText() not in ["644 (RGB)", "550/660/850"]:
                self.PreProcessVignette.setChecked(False)
                self.PreProcessVignette.setEnabled(False)

            if self.PreProcessFilter.currentText() != "644 (RGB)":
                self.PreProcessColorBox.setChecked(False)
                self.PreProcessColorBox.setEnabled(False)

            if self.PreProcessFilter.currentText() in ["644 (RGB)", "550/660/850"]:
                self.PreProcessVignette.setEnabled(True)

        elif self.PreProcessCameraModel.currentText() == "Kernel 3.2":
            if self.PreProcessFilter.currentText() in ["405", "450", "490", "518",
                                                       "550", "590", "615", "632",
                                                       "685", "725", "780","808", 
                                                       "850", "880","940"]:

                self.PreProcessVignette.setEnabled(True)
            else:
                self.PreProcessVignette.setChecked(False)
                self.PreProcessVignette.setEnabled(False)

        elif self.PreProcessCameraModel.currentText() == "Survey3":
            self.PreProcessVignette.setEnabled(False)

            if self.PreProcessFilter.currentText() == "RGB":
                self.PreProcessMonoBandBox.setChecked(False)

            elif self.PreProcessFilter.currentText() == "OCN":
                self.PreProcessMonoBandBox.setChecked(False)

            elif self.PreProcessFilter.currentText() == "RGN":
                self.PreProcessMonoBandBox.setChecked(False)

            elif self.PreProcessFilter.currentText() == "NGB":
                self.PreProcessMonoBandBox.setChecked(False)

            elif self.PreProcessFilter.currentText() == "RE":
                self.PreProcessMonoBandBox.setChecked(True)
                self.Band_Dropdown.setCurrentIndex(0)

            elif self.PreProcessFilter.currentText() == "NIR":
                self.PreProcessMonoBandBox.setChecked(True)
                self.Band_Dropdown.setCurrentIndex(0)

            if self.PreProcessFilter.currentText() != "RGB":
                self.PreProcessColorBox.setEnabled(False)


        elif self.PreProcessCameraModel.currentText() == "Survey2":
            self.PreProcessVignette.setEnabled(False)

            if self.PreProcessFilter.currentText() == "Red + NIR (NDVI)":
                self.PreProcessMonoBandBox.setChecked(False)

            elif self.PreProcessFilter.currentText() == "NIR":
                self.PreProcessMonoBandBox.setChecked(True)
                self.Band_Dropdown.setCurrentIndex(0)

            elif self.PreProcessFilter.currentText() == "Red":
                self.PreProcessMonoBandBox.setChecked(True)
                self.Band_Dropdown.setCurrentIndex(0)

            elif self.PreProcessFilter.currentText() == "Green":
                self.PreProcessMonoBandBox.setChecked(True)
                self.Band_Dropdown.setCurrentIndex(1)

            elif self.PreProcessFilter.currentText() == "Blue":
                self.PreProcessMonoBandBox.setChecked(True)
                self.Band_Dropdown.setCurrentIndex(2)

            elif self.PreProcessFilter.currentText() == "RGB":
                self.PreProcessMonoBandBox.setChecked(False)

            if self.PreProcessFilter.currentText() != "RGB":
                self.PreProcessColorBox.setEnabled(False)
       
        else:
            self.PreProcessColorBox.setChecked(False)
            self.PreProcessColorBox.setEnabled(False)
        QtWidgets.QApplication.processEvents()

    def on_PreProcessCameraModel_currentIndexChanged(self):
        self.PreProcessVignette.setChecked(False)
        self.PreProcessVignette.setEnabled(False)
        self.PreProcessColorBox.setChecked(False)
        self.PreProcessColorBox.setEnabled(False)
        self.PreProcessDarkBox.setChecked(False)
        self.PreProcessDarkBox.setEnabled(False)

        self.PreProcessMonoBandBox.setChecked(False)
        self.Band_Dropdown.setEnabled(False)
        self.PreProcessMonoBandBox.setEnabled(True)

        if self.PreProcessCameraModel.currentText() == "Kernel 3.2":
            self.PreProcessDarkBox.setEnabled(True)
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["405", "450", "490", "518",
                                            "550", "590", "615", "632",
                                            "650", "685", "725", "780",
                                            "808", "850", "880", "940",
                                            "945"])

            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["9.6mm"])
            self.PreProcessLens.setEnabled(False)


        elif self.PreProcessCameraModel.currentText() == "Kernel 14.4":
            self.PreProcessDarkBox.setEnabled(True)
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(
                ["550/660/850", "475/550/850", "644 (RGB)", "850"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.37mm", "8.25mm"])
            self.PreProcessLens.setEnabled(True)

        elif self.PreProcessCameraModel.currentText() == "Survey3":
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["RGB", "OCN", "RGN", "NGB", "RE", "NIR"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.PreProcessLens.setEnabled(True)
            self.PreProcessColorBox.setEnabled(True)

        elif self.PreProcessCameraModel.currentText() == "Survey2":
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)

        elif self.PreProcessCameraModel.currentText() == "Survey1":
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Blue + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)

        elif self.PreProcessCameraModel.currentText() == "DJI Phantom 4":
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)

        elif self.PreProcessCameraModel.currentText() == "DJI Phantom 4 Pro":
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["RGN"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)

        elif self.PreProcessCameraModel.currentText() in ["DJI Phantom 3a", "DJI Phantom 3p", "DJI X3"]:
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

    def on_PreProcessMonoBandBox_toggled(self):
        if self.PreProcessMonoBandBox.checkState() == 2:
            self.Band_Dropdown.addItems(["Band 1 (Red)", "Band 2 (Green)", "Band 3 (Blue)"])
            self.Band_Dropdown.setEnabled(True)

        elif self.histogramClipBox.checkState() == 0:
            self.Band_Dropdown.clear()
            self.Band_Dropdown.setEnabled(False)

        QtWidgets.QApplication.processEvents()

    def on_PreProcessDarkBox_toggled(self):
        if self.PreProcessDarkBox.checkState() == 0:
            self.PreProcessJPGBox.setEnabled(True)
        else:
            self.PreProcessJPGBox.setEnabled(False)

    def on_PreProcessJPGBox_toggled(self):
        if self.PreProcessCameraModel.currentText() in self.KERNELS:
            if self.PreProcessJPGBox.checkState() == 0:
                self.PreProcessDarkBox.setEnabled(True)
            else:
                self.PreProcessDarkBox.setEnabled(False)

    def on_CalibrationCameraModel_currentIndexChanged(self):

        if self.CalibrationCameraModel.currentText() == "Kernel 1.2" or self.CalibrationCameraModel.currentText() == "Kernel 3.2":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880","940","945"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentText() == "Kernel 14.4":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(
                ["550/660/850", "475/550/850", "644 (RGB)", "850"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentText() == "Survey3":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["OCN", "RGN", "NGB", "RE", "NIR"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens.setEnabled(True)

        elif self.CalibrationCameraModel.currentText() == "Survey2":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentText() == "Survey1":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentText() == "DJI Phantom 4":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentText() == "DJI Phantom 4 Pro":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentText() == "DJI Phantom 3a":
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["RGN"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)

        elif self.CalibrationCameraModel.currentText() in ["DJI Phantom 3p", "DJI X3"]:
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

    def on_CalibrationCameraModel_2_currentIndexChanged(self):
        if self.CalibrationCameraModel_2.currentText() == "Kernel 1.2" or self.CalibrationCameraModel_2.currentText() == "Kernel 3.2":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880","940","945"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentText() == "Kernel 14.4":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(
                ["550/660/850", "475/550/850", "644 (RGB)", "850"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentText() == "Survey3":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["OCN", "RGN", "NGB", "RE", "NIR"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_2.setEnabled(True)

        elif self.CalibrationCameraModel_2.currentText() == "Survey2":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentText() == "Survey1":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentText() == "DJI Phantom 4":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentText() == "DJI Phantom 4 Pro":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_2.setEnabled(True)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentText() == "DJI Phantom 3a":
            self.CalibrationFilter_2.clear()
            self.CalibrationFilter_2.addItems(["RGN"])
            self.CalibrationFilter_2.setEnabled(False)
            self.CalibrationLens_2.clear()
            self.CalibrationLens_2.addItems(["3.97mm"])
            self.CalibrationLens_2.setEnabled(False)

        elif self.CalibrationCameraModel_2.currentText() in ["DJI Phantom 3p", "DJI X3"]:
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

    def on_CalibrationCameraModel_3_currentIndexChanged(self):
        if self.CalibrationCameraModel_3.currentText() == "Kernel 1.2" or self.CalibrationCameraModel_3.currentText() == "Kernel 3.2":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880","940","945"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentText() == "Kernel 14.4":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(
                ["550/660/850", "475/550/850", "644 (RGB)", "850"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentText() == "Survey3":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["OCN", "RGN", "NGB", "RE", "NIR"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_3.setEnabled(True)

        elif self.CalibrationCameraModel_3.currentText() == "Survey2":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentText() == "Survey1":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentText() == "DJI Phantom 4":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentText() == "DJI Phantom 4 Pro":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_3.setEnabled(True)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentText() == "DJI Phantom 3a":
            self.CalibrationFilter_3.clear()
            self.CalibrationFilter_3.addItems(["RGN"])
            self.CalibrationFilter_3.setEnabled(False)
            self.CalibrationLens_3.clear()
            self.CalibrationLens_3.addItems(["3.97mm"])
            self.CalibrationLens_3.setEnabled(False)

        elif self.CalibrationCameraModel_3.currentText() in ["DJI Phantom 3p", "DJI X3"]:
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

    def on_CalibrationCameraModel_4_currentIndexChanged(self):
        if self.CalibrationCameraModel_4.currentText() == "Kernel 1.2" or self.CalibrationCameraModel_4.currentText() == "Kernel 3.2":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880","940","945"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentText() == "Kernel 14.4":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(
                ["550/660/850", "475/550/850", "644 (RGB)", "850"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentText() == "Survey3":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["OCN", "RGN", "NGB", "RE", "NIR"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_4.setEnabled(True)

        elif self.CalibrationCameraModel_4.currentText() == "Survey2":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentText() == "Survey1":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentText() == "DJI Phantom 4":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentText() == "DJI Phantom 4 Pro":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_4.setEnabled(True)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentText() == "DJI Phantom 3a":
            self.CalibrationFilter_4.clear()
            self.CalibrationFilter_4.addItems(["RGN"])
            self.CalibrationFilter_4.setEnabled(False)
            self.CalibrationLens_4.clear()
            self.CalibrationLens_4.addItems(["3.97mm"])
            self.CalibrationLens_4.setEnabled(False)

        elif self.CalibrationCameraModel_4.currentText() in ["DJI Phantom 3p", "DJI X3"]:
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

    def on_CalibrationCameraModel_5_currentIndexChanged(self):
        if self.CalibrationCameraModel_5.currentText() == "Kernel 1.2" or self.CalibrationCameraModel_5.currentText() == "Kernel 3.2":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880","940","945"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentText() == "Kernel 14.4":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(
                ["550/660/850", "475/550/850", "644 (RGB)", "850"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentText() == "Survey3":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["OCN", "RGN", "NGB", "RE", "NIR"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_5.setEnabled(True)

        elif self.CalibrationCameraModel_5.currentText() == "Survey2":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentText() == "Survey1":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentText() == "DJI Phantom 4":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentText() == "DJI Phantom 4 Pro":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_5.setEnabled(True)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentText() == "DJI Phantom 3a":
            self.CalibrationFilter_5.clear()
            self.CalibrationFilter_5.addItems(["RGN"])
            self.CalibrationFilter_5.setEnabled(False)
            self.CalibrationLens_5.clear()
            self.CalibrationLens_5.addItems(["3.97mm"])
            self.CalibrationLens_5.setEnabled(False)

        elif self.CalibrationCameraModel_5.currentText() in ["DJI Phantom 3p", "DJI X3"]:
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

    def on_CalibrationCameraModel_6_currentIndexChanged(self):
        if self.CalibrationCameraModel_6.currentText() == "Kernel 1.2" or self.CalibrationCameraModel_6.currentText() == "Kernel 3.2":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["405", "450", "490", "518", "550", "590", "615", "632", "650", "685", "725", "780", "808", "850", "880","940","945"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentText() == "Kernel 14.4":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(
                ["550/660/850", "475/550/850", "644 (RGB)", "850"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentText() == "Survey3":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["OCN", "RGN", "NGB", "RE", "NIR"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems([" 3.37mm (Survey3W)", "8.25mm (Survey3N)"])
            self.CalibrationLens_6.setEnabled(True)

        elif self.CalibrationCameraModel_6.currentText() == "Survey2":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentText() == "Survey1":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentText() == "DJI Phantom 4":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentText() == "DJI Phantom 4 Pro":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["Red + NIR (NDVI)", "RGN"])
            self.CalibrationFilter_6.setEnabled(True)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentText() == "DJI Phantom 3a":
            self.CalibrationFilter_6.clear()
            self.CalibrationFilter_6.addItems(["RGN"])
            self.CalibrationFilter_6.setEnabled(False)
            self.CalibrationLens_6.clear()
            self.CalibrationLens_6.addItems(["3.97mm"])
            self.CalibrationLens_6.setEnabled(False)

        elif self.CalibrationCameraModel_6.currentText() in ["DJI Phantom 3p", "DJI X3"]:
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

    def on_VignetteFileSelectButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.VignetteFileSelect.setText(QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0])
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.VignetteFileSelect.text())

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
                self.PreProcessLog.append("Finished Processing Images.")

            except Exception as e:
                exc_type, exc_obj,exc_tb = sys.exc_info()
                self.PreProcessLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
            
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
                self.findQR(self.CalibrationQRFile.text(), [self.CalibrationCameraModel, self.CalibrationFilter, self.CalibrationLens])
                self.qrcoeffs = copy.deepcopy(self.multiplication_values["mono"])
                print("Multplication Values: ", self.multiplication_values)
                self.useqr = True

            else:
                #self.useqr = False
                self.CalibrationLog.append("Attention! Please select a target image.\n")

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))

    def on_CalibrationGenButton_2_released(self):
        try:
            if self.CalibrationCameraModel_2.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_2.text()) > 0:

                self.findQR(self.CalibrationQRFile_2.text(), [self.CalibrationCameraModel_2, self.CalibrationFilter_2, self.CalibrationLens_2])
                self.qrcoeffs2 = copy.deepcopy(self.multiplication_values["mono"])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
    def on_CalibrationGenButton_3_released(self):
        try:
            if self.CalibrationCameraModel_3.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_3.text()) > 0:
                self.findQR(self.CalibrationQRFile_3.text(), [self.CalibrationCameraModel_3, self.CalibrationFilter_3, self.CalibrationLens_3])
                self.qrcoeffs3 = copy.deepcopy(self.multiplication_values["mono"])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
    def on_CalibrationGenButton_4_released(self):
        try:
            if self.CalibrationCameraModel_4.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_4.text()) > 0:
                self.qrcoeffs4 = self.findQR(self.CalibrationQRFile_4.text(), [self.CalibrationCameraModel_4, self.CalibrationFilter_4, self.CalibrationLens_4])
                self.qrcoeffs4 = copy.deepcopy(self.multiplication_values["mono"])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
    def on_CalibrationGenButton_5_released(self):
        try:
            if self.CalibrationCameraModel_5.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_5.text()) > 0:
                self.qrcoeffs5 = self.findQR(self.CalibrationQRFile_5.text(), [self.CalibrationCameraModel_5, self.CalibrationFilter_5, self.CalibrationLens_5])
                self.qrcoeffs5 = copy.deepcopy(self.multiplication_values["mono"])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
    def on_CalibrationGenButton_6_released(self):
        try:
            if self.CalibrationCameraModel_6.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")
            elif len(self.CalibrationQRFile_6.text()) > 0:
                self.qrcoeffs6 = self.findQR(self.CalibrationQRFile_6.text(), [self.CalibrationCameraModel_6, self.CalibrationFilter_6, self.CalibrationLens_6])
                self.qrcoeffs6 = copy.deepcopy(self.multiplication_values["mono"])
                self.useqr = True
            else:
                self.CalibrationLog.append("Attention! Please select a target image.\n")
        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))

    #Function that calibrates global max and mins
    def calibrate(self, mult_values, value):
        slope = mult_values["slope"]
        intercept = mult_values["intercept"]

        return int((slope * value) + intercept)

    def get_HC_value(self, color):
        HCP = int(self.HCP_value.text()) / 100
        unique, counts = np.unique(color, return_counts=True)
        freq_array = np.asarray((unique, counts)).T

        freq_dict = {}
        mode = self.calculate_mode(freq_array)

        for i in freq_array:
            freq_dict[i[0]] = i[1]

        HC_Value = 0
        for pixel in freq_array:
            if pixel[0] > mode:
                if round(pixel[1] / freq_dict[mode], 2) == HCP:
                    HC_Value = pixel[0]
                    break
        return HC_Value

    def on_histogramClipBox_toggled(self):
        if self.histogramClipBox.checkState() == 2:
            self.Histogram_Clipping_Percentage.setEnabled(True)
            self.HCP_value.setEnabled(True)

        elif self.histogramClipBox.checkState() == 0:
            self.Histogram_Clipping_Percentage.setEnabled(False)
            self.HCP_value.setEnabled(False)
            self.HCP_value.clear()
    
    def check_HCP_value(self):
        if "." in self.HCP_value.text():
            return True

        if self.histogramClipBox.checkState() and not self.HCP_value.text():
            return True

        elif (self.histogramClipBox.checkState() and (int(self.HCP_value.text()) < 1 or int(self.HCP_value.text()) > 100)):
            return True

        else:
            return False

    def failed_calibration(self):
        self.failed_calib = True
        self.CalibrationLog.append("No default calibration data for selected camera model. Please please supply a MAPIR Reflectance Target to proceed.\n")

    def on_CalibrateButton_released(self):
        self.failed_calib = False

        if not self.CalibrationQRFile.text() and self.CalibrationInFolder.text():
            self.useqr = False
            self.CalibrationLog.append("Attempting to calibrate without MAPIR Reflectance Target...\n")

        try:
            if self.CalibrationCameraModel.currentIndex() == -1\
                    and self.CalibrationCameraModel_2.currentIndex() == -1 \
                    and self.CalibrationCameraModel_3.currentIndex() == -1 \
                    and self.CalibrationCameraModel_4.currentIndex() == -1 \
                    and self.CalibrationCameraModel_5.currentIndex() == -1 \
                    and self.CalibrationCameraModel_6.currentIndex() == -1:
                self.CalibrationLog.append("Attention! Please select a camera model.\n")


            elif self.check_HCP_value():
                self.CalibrationLog.append("Attention! Please select a Histogram Clipping Percentage value between 1-100.")
                self.CalibrationLog.append("For example 20%, please enter 20\n")
            
            elif len(self.CalibrationInFolder.text()) <= 0 \
                    and len(self.CalibrationInFolder_2.text()) <= 0 \
                    and len(self.CalibrationInFolder_3.text()) <= 0 \
                    and len(self.CalibrationInFolder_4.text()) <= 0 \
                    and len(self.CalibrationInFolder_5.text()) <= 0 \
                    and len(self.CalibrationInFolder_6.text()) <= 0:
                self.CalibrationLog.append("Attention! Please select a calibration folder.\n")
            
            else:
                self.CalibrationLog.append("Analyzing Input Directory. Please wait... \n")
                self.firstpass = True
                # self.CalibrationLog.append("CSV Input: \n" + str(self.refvalues))
                # self.CalibrationLog.append("Calibration button pressed.\n")
                calfolder = self.CalibrationInFolder.text()
                calfolder2 = self.CalibrationInFolder_2.text()
                calfolder3 = self.CalibrationInFolder_3.text()
                calfolder4 = self.CalibrationInFolder_4.text()
                calfolder5 = self.CalibrationInFolder_5.text()
                calfolder6 = self.CalibrationInFolder_6.text()
                self.pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                      "greenmax": 0.0, "greenmin": 65535.0,
                                      "bluemax": 0.0, "bluemin": 65535.0}

                self.HC_max = {"redmax": 0.0,
                               "greenmax": 0.0, 
                               "bluemax": 0.0, }

                self.HC_mono_max = 0

                # self.CalibrationLog.append("Calibration target folder is: " + calfolder + "\n")
                files_to_calibrate = []
                files_to_calibrate2 = []
                files_to_calibrate3 = []
                files_to_calibrate4 = []
                files_to_calibrate5 = []
                files_to_calibrate6 = []


                indexes = [[self.CalibrationCameraModel.currentText(), self.CalibrationFilter.currentText(), self.CalibrationLens.currentText()],
                           [self.CalibrationCameraModel_2.currentText(), self.CalibrationFilter_2.currentText(),
                            self.CalibrationLens_2.currentText()],
                           [self.CalibrationCameraModel_3.currentText(), self.CalibrationFilter_3.currentText(),
                            self.CalibrationLens_3.currentText()],
                           [self.CalibrationCameraModel_4.currentText(), self.CalibrationFilter_4.currentText(),
                            self.CalibrationLens_4.currentText()],
                           [self.CalibrationCameraModel_5.currentText(), self.CalibrationFilter_5.currentText(),
                            self.CalibrationLens_5.currentText()],
                           [self.CalibrationCameraModel_6.currentText(), self.CalibrationFilter_6.currentText(),
                            self.CalibrationLens_6.currentText()],
                           ]

                folderind = [calfolder,
                             calfolder2,
                             calfolder3,
                             calfolder4,
                             calfolder5,
                             calfolder6]


                for j, ind in enumerate(indexes):
                    CHECKED = 2
                    UNCHECKED = 0

                    camera_model = ind[0]
                    filt = ind[1]
                    lens = ind[2]

                    if camera_model == "":
                        pass

                    elif self.check_if_RGB(camera_model, filt, lens):

                        if os.path.exists(folderind[j]):
                            files_to_calibrate = []
                            os.chdir(folderind[j])
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))

                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate[0]:
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir = folderind[j] + os.sep + "Calibrated_" + str(foldercount)

                                    if os.path.exists(outdir):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir)
                                        endloop = True

                        for i, calpixel in enumerate(files_to_calibrate):
                            img = cv2.imread(calpixel, -1)

                            if len(img.shape) < 3:
                                raise IndexError("RGB filter was selected but input folders contain MONO images")

                            blue = img[:, :, 0]
                            green = img[:, :, 1]
                            red = img[:, :, 2]

                            # these are a little confusing, but the check to find the highest and lowest pixel value
                            # in each channel in each image and keep the highest/lowest value found.
                            if self.seed_pass == False:
                                self.pixel_min_max["redmax"] = red.max()
                                self.pixel_min_max["redmin"] = red.min()

                                self.pixel_min_max["greenmax"] = green.max()
                                self.pixel_min_max["greenmin"] = green.min()

                                self.pixel_min_max["bluemax"] = blue.max()
                                self.pixel_min_max["bluemin"] = blue.min()

                                if self.histogramClipBox.checkState() == self.CHECKED:
                                    self.HC_max["redmax"] = self.get_HC_value(red)
                                    self.HC_max["greenmax"] = self.get_HC_value(green)
                                    self.HC_max["bluemax"] = self.get_HC_value(blue)

                                self.seed_pass = True

                            else:
            
                                try:
                                #compare current image min-max with global min-max (non-calibrated)
                                    self.pixel_min_max["redmax"] = max(red.max(), self.pixel_min_max["redmax"])
                                    self.pixel_min_max["redmin"] = min(red.min(), self.pixel_min_max["redmin"])
                                    
                                    self.pixel_min_max["greenmax"] = max(green.max(), self.pixel_min_max["greenmax"])
                                    self.pixel_min_max["greenmin"] = min(green.min(), self.pixel_min_max["greenmin"])
                                    

                                    self.pixel_min_max["bluemax"] = max(blue.max(), self.pixel_min_max["bluemax"])
                                    self.pixel_min_max["bluemin"] = min(blue.min(), self.pixel_min_max["bluemin"])


                                    if self.histogramClipBox.checkState() == self.CHECKED:
                                        self.HC_max["redmax"] = max(self.get_HC_value(red), self.HC_max["redmax"])
                                        self.HC_max["greenmax"] = max(self.get_HC_value(green), self.HC_max["greenmax"])
                                        self.HC_max["bluemax"] = max(self.get_HC_value(blue), self.HC_max["bluemax"])


                                except Exception as e:
                                    print("ERROR: ", e)

                        min_max_list = ["redmax", "redmin", "greenmax", "greenmin", "bluemin", "bluemax"]
                        if not self.useqr:
                            filetype = calpixel.split(".")[-1]
                            min_max_wo_g_list = ["redmax", "redmin", "bluemin", "bluemax"]

                            if camera_model == "Survey1":  # Survey1_NDVI
                                min_max_list = min_max_wo_g_list
                                if filetype in self.JPGS:
                                    base_coef = self.BASE_COEFF_SURVEY1_NDVI_JPG

                                else:
                                    self.failed_calibration()
                                    break

                            elif camera_model == "Survey2" and filt == "Red + NIR (NDVI)": #Survey 2 + Red + NIR
                                min_max_list = min_max_wo_g_list

                                if filetype in self.TIFS:
                                    base_coef = self.BASE_COEFF_SURVEY2_NDVI_TIF

                                elif filetype in self.JPGS:
                                    base_coef = self.BASE_COEFF_SURVEY2_NDVI_JPG

                                else:
                                    self.failed_calibration()
                                    break

                            elif camera_model == "DJI Phantom 3a":
                                min_max_list = min_max_wo_g_list
                                if filetype in self.TIFS:
                                    base_coef = self.BASE_COEFF_DJIX3_NDVI_TIF

                                elif filetype in self.JPGS:
                                    base_coef = self.BASE_COEFF_DJIX3_NDVI_JPG

                                else:
                                    self.failed_calibration()
                                    break

                            elif camera_model == "DJI Phantom 4":
                                min_max_list = min_max_wo_g_list
                                if filetype in self.TIFS:
                                    base_coef = self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF
                        
                                elif filetype in self.JPGS:
                                    base_coef = self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG

                                else:
                                    self.failed_calibration()
                                    break

                            elif camera_model in ["DJI Phantom 4 Pro", "DJI Phantom 3a"]:
                                min_max_list = min_max_wo_g_list

                                if filetype in self.TIFS:
                                    base_coef = self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF

                                elif filetype in self.JPGS:
                                    base_coef = self.BASE_COEFF_DJIPHANTOM3_NDVI_JPG
                                else:
                                    self.failed_calibration()
                                    break

                            elif camera_model == "Survey3":

                                if filt == "RGN":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY3_RGN_JPG
                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY3_RGN_TIF

                                elif filt == "OCN":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY3_OCN_JPG
                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY3_OCN_TIF

                                elif filt == "NGB":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY3_NGB_JPG
                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY3_NGB_TIF

                                else:
                                    self.failed_calibration()
                                    break

                            else:
                                self.failed_calibration()
                                break

                            for min_max in min_max_list:
                                if len(min_max) == 6:
                                    color = min_max[:3]
                                elif len(min_max) == 7:
                                    color = min_max[:4]
                                else:
                                    color = min_max[:5]

                                self.pixel_min_max[min_max] = self.calibrate(base_coef[color], self.pixel_min_max[min_max])

                            if self.histogramClipBox.checkState() == self.CHECKED:
                                self.HC_max["redmax"] = self.calibrate(base_coef["Red"], self.HC_max["redmax"])
                                self.HC_max["greenmax"] = self.calibrate(base_coef["Green"], self.HC_max["greenmax"])
                                self.HC_max["bluemax"] = self.calibrate(base_coef["Blue"], self.HC_max["bluemax"])


                        self.seed_pass = False

                        #Calibrate global max and mins
                        if self.useqr:

                            for min_max in min_max_list:
                                if len(min_max) == 6:
                                    color = min_max[:3]
                                elif len(min_max) == 7:
                                    color = min_max[:4]
                                else:
                                    color = min_max[:5]

                                self.pixel_min_max[min_max] = self.calibrate(self.multiplication_values[color], self.pixel_min_max[min_max])


                            if self.histogramClipBox.checkState() == self.CHECKED:
                                self.HC_max["redmax"] = self.calibrate(self.multiplication_values["red"], self.HC_max["redmax"])
                                self.HC_max["greenmax"] = self.calibrate(self.multiplication_values["green"], self.HC_max["greenmax"])
                                self.HC_max["bluemax"] = self.calibrate(self.multiplication_values["blue"], self.HC_max["bluemax"])

                        for i, calfile in enumerate(files_to_calibrate):

                            cameramodel = ind
                            if self.useqr:
                                # self.CalibrationLog.append("Using QR")
                                try:
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " of " + str(len(files_to_calibrate)))
                                    QtWidgets.QApplication.processEvents()

                                    self.CalibratePhotos(calfile, self.multiplication_values, self.pixel_min_max, outdir, ind)
                                except Exception as e:
                                    print("ERROR: ", e)
                                    exc_type, exc_obj,exc_tb = sys.exc_info()
                                    self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
                            else:
                                self.CalibrationLog.append("Calibrating image " + str(i + 1) + " of " + str(len(files_to_calibrate)))
                                QtWidgets.QApplication.processEvents()

                                self.CalibratePhotos(calfile, base_coef, self.pixel_min_max, outdir, ind)

                    else:
                        if os.path.exists(folderind[j]):
                            files_to_calibrate = []
                            os.chdir(folderind[j])
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
                            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))

                            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate[0]:
                                foldercount = 1
                                endloop = False
                                while endloop is False:
                                    outdir = folderind[j] + os.sep + "Calibrated_" + str(foldercount)

                                    if os.path.exists(outdir):
                                        foldercount += 1
                                    else:
                                        os.mkdir(outdir)
                                        endloop = True

                        for i, calpixel in enumerate(files_to_calibrate):
                            img = cv2.imread(calpixel, -1)

                            if len(img.shape) > 2:
                                raise IndexError("Mono filter was selected but input folders contain RGB images")

                            if self.seed_pass == False:
                                self.monominmax["max"] = img.max()
                                self.monominmax["min"] = img.min()

                                if self.histogramClipBox.checkState() == self.CHECKED:
                                    self.HC_mono_max = self.get_HC_value(img)
      
                                self.seed_pass = True

                            else:
            
                                try:
                                    #compare current image min-max with global min-max (non-calibrated)
                                    self.monominmax["max"] = max(img.max(), self.monominmax["max"])
                                    self.monominmax["min"] = min(img.min(), self.monominmax["min"])

                                    if self.histogramClipBox.checkState() == self.CHECKED:
                                        self.HC_mono_max = max(self.get_HC_value(img), self.HC_mono_max)

                                except Exception as e:
                                    print("ERROR: ", e)

                        if not self.useqr:
                            filetype = calpixel.split(".")[-1]

                            if camera_model == "Survey2":
                                if filt == "Red":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY2_RED_JPG

                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY2_RED_TIF

                                    else:
                                        self.failed_calibration()
                                        break

                                elif filt == "Green":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY2_GREEN_JPG

                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY2_GREEN_TIF

                                    else:
                                        self.failed_calibration()
                                        break

                                elif filt == "Blue":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY2_BLUE_JPG

                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY2_BLUE_TIF

                                    else:
                                        self.failed_calibration()
                                        break

                                elif filt == "NIR":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY2_NIR_JPG

                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY2_NIR_TIF

                                    else:
                                        self.failed_calibration()
                                        break

                                else:
                                        self.failed_calibration()
                                        break

                            elif camera_model == "Survey3":
                                if filt == "RE":
                                    if filetype in self.JPGS:
                                        base_coef = self.BASE_COEFF_SURVEY3_RE_JPG

                                    elif filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY3_RE_TIF

                                    else:
                                        self.failed_calibration()
                                        break

                                elif filt == "NIR":
                                    if filetype in self.TIFS:
                                        base_coef = self.BASE_COEFF_SURVEY3_NIR_TIF

                                    else:
                                        self.failed_calibration()
                                        break

                            self.monominmax["max"] = self.calibrate(base_coef, self.monominmax["max"])
                            self.monominmax["min"] = self.calibrate(base_coef, self.monominmax["min"])

                        if self.useqr:
                            self.monominmax["max"] = self.calibrate(self.multiplication_values["mono"], self.monominmax["max"])
                            self.monominmax["min"] = self.calibrate(self.multiplication_values["mono"], self.monominmax["min"])

                            if self.histogramClipBox.checkState() == self.CHECKED:
                                self.HC_mono_max = self.calibrate(self.multiplication_values["mono"], self.HC_mono_max)
                                

                        for i, calfile in enumerate(files_to_calibrate):

                            cameramodel = ind
                            if self.useqr:

                                try:
                                    self.CalibrationLog.append("Calibrating image " + str(i + 1) + " of " + str(len(files_to_calibrate)))
                                    QtWidgets.QApplication.processEvents()
                                    self.CalibrateMono(calfile, self.multiplication_values["mono"], outdir, ind)

                                except Exception as e:
                                    print("ERROR: ", e)
                                    exc_type, exc_obj,exc_tb = sys.exc_info()
                                    self.CalibrationLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
                            else:
                                self.CalibrationLog.append("Calibrating image " + str(i + 1) + " of " + str(len(files_to_calibrate)))
                                QtWidgets.QApplication.processEvents()

                                self.CalibrateMono(calfile, base_coef, outdir, ind)
      

                if not self.failed_calib:
                    self.CalibrationLog.append("Finished Calibrating " + str(len(files_to_calibrate) + len(files_to_calibrate2) + len(files_to_calibrate3) + len(files_to_calibrate4) + len(files_to_calibrate5) + len(files_to_calibrate6)) + " images\n")
                self.CalibrateButton.setEnabled(True)
                self.seed_pass = False

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(repr(e))
            print("Line: " + str(exc_tb.tb_lineno))
            self.CalibrationLog.append(str(repr(e)))

    def CalibrateMono(self, photo, coeff, output_directory, ind):
        try:
            refimg = cv2.imread(photo, -1)

            maxpixel = self.monominmax["max"]
            minpixel = self.monominmax["min"]

            refimg = ((refimg * coeff["slope"]) + coeff["intercept"])

            if self.histogramClipBox.checkState() == self.CHECKED:
                global_HC_max = self.HC_mono_max
                
                refimg[refimg > global_HC_max] = global_HC_max
                maxpixel = global_HC_max

            refimg = ((refimg - minpixel) / (maxpixel - minpixel))

            if self.IndexBox.checkState() == self.UNCHECKED:
            #Float to JPG
                if photo.split('.')[2].upper() == "JPG" or photo.split('.')[2].upper() == "JPEG" or self.Tiff2JpgBox.checkState() > 0:
                    refimg *= 255
                    refimg = refimg.astype(int)
                    refimg = refimg.astype("uint8")

          
                else: #Float to Tiff
                    refimg *= 65535
                    refimg = refimg.astype(int)
                    refimg = refimg.astype("uint16")

            else: #Float to Index
                refimg[refimg > 1.0] = 1.0
                refimg[refimg < 0.0] = 0.0
                refimg = refimg.astype("float")
                refimg = cv2.normalize(refimg.astype("float"), None, 0.0, 1.0, cv2.NORM_MINMAX)

            if self.Tiff2JpgBox.checkState() > 0:
                self.CalibrationLog.append("Making JPG")
                QtWidgets.QApplication.processEvents()
                cv2.imencode(".jpg", refimg)
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

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))


    def calculate_mode(self, freq_array):
        pixel_freq = 0
        mode = 0
        for pixel in freq_array:
            if pixel[1] > pixel_freq:
                pixel_freq = pixel[1]
                mode = pixel[0]
        return mode

    def CalibratePhotos(self, photo, coeffs, minmaxes, output_directory, ind):  
        refimg = cv2.imread(photo, -1)

        camera_model = ind[0]
        filt = ind[1]
        lens = ind[2]

        ### split channels (using cv2.split caused too much overhead and made the host program crash)
        alpha = []
        blue = refimg[:, :, 0]
        green = refimg[:, :, 1]
        red = refimg[:, :, 2]

        if refimg.shape[2] > 3:
            alpha = refimg[:, :, 3]
            refimg = copy.deepcopy(refimg[:, :, :3])

        red = ((red * coeffs["red"]["slope"]) + coeffs["red"]["intercept"])
        green = ((green * coeffs["green"]["slope"]) + coeffs["green"]["intercept"])
        blue = ((blue * coeffs["blue"]["slope"]) + coeffs["blue"]["intercept"])

        ### find the global maximum (maxpixel) and minimum (minpixel) calibrated pixel values over the entire directory.
        if camera_model == "Survey1":  ###Survey1 NDVI
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            # blue = refimg[:, :, 0] - (refimg[:, :, 2] * 0.80)  # Subtract the NIR bleed over from the blue channel

        elif camera_model in ["Survey2", "Survey3"] and filt in ["NIR", "Red", "RE"]:
            ### red and NIR
            maxpixel = minmaxes["redmax"]
            minpixel = minmaxes["redmin"]

        elif camera_model == "Survey2" and filt == "Green":
            ### green
            maxpixel = minmaxes["greenmax"]
            minpixel = minmaxes["greenmin"]

        elif camera_model == "Survey2" and filt == "Blue":
            ### blue
            maxpixel = minmaxes["bluemax"]
            minpixel = minmaxes["bluemin"]

        elif camera_model == "Survey3":
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            maxpixel = minmaxes["greenmax"] if minmaxes["greenmax"] > maxpixel else maxpixel
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            minpixel = minmaxes["greenmin"] if minmaxes["greenmin"] < minpixel else minpixel
         
        elif camera_model == "DJI Phantom 4 Pro":
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            maxpixel = minmaxes["greenmax"] if minmaxes["greenmax"] > maxpixel else maxpixel
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            minpixel = minmaxes["greenmin"] if minmaxes["greenmin"] < minpixel else minpixel

        else:  ###Survey2 NDVI
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            # if ind[0] == 4:
            #     red = refimg[:, :, 2] - (refimg[:, :, 0] * 0.80)  # Subtract the NIR bleed over from the red channel
    
        ### Scale calibrated values back down to a useable range (Adding 1 to avoid 0 value pixels, as they will cause a
        #### divide by zero case when creating an index image

        #if self.histogramClipBox.checkState() == UNCHECKED:
            #convert pixel value to float
        if self.histogramClipBox.checkState() == self.CHECKED:
            global_HC_max = self.HC_max["redmax"] if self.HC_max["redmax"] > self.HC_max["bluemax"] else self.HC_max["bluemax"]
            global_HC_max = self.HC_max["greenmax"] if self.HC_max["greenmax"] > global_HC_max else global_HC_max
            
            #global_HC_max = ((global_HC_max - minpixel) / (maxpixel - minpixel))
            #global_HC_max *= 255
            red[red > global_HC_max] = global_HC_max
            green[green > global_HC_max] = global_HC_max
            blue[blue > global_HC_max] = global_HC_max

            maxpixel = global_HC_max



        red = ((red - minpixel) / (maxpixel - minpixel))
        green = ((green - minpixel) / (maxpixel - minpixel))
        blue = ((blue - minpixel) / (maxpixel - minpixel))

        if self.IndexBox.checkState() == self.UNCHECKED:
            #Float to JPG
            if photo.split('.')[2].upper() == "JPG" or photo.split('.')[2].upper() == "JPEG" or self.Tiff2JpgBox.checkState() > 0:
                red *= 255
                green *= 255
                blue *= 255

                red = red.astype(int)
                green = green.astype(int)
                blue = blue.astype(int)

                # index = self.calculateIndex(red, blue)
                # cv2.imwrite(output_directory + photo.split('.')[1] + "_CALIBRATED_INDEX." + photo.split('.')[2], index)

                red = red.astype("uint8")
                green = green.astype("uint8")
                blue = blue.astype("uint8")

      
            else: #Float to Tiff

                # maxpixel *= 10
                # minpixel *= 10

                # tempimg = cv2.merge((blue, green, red)).astype("float32")
                # cv2.imwrite(output_directory + photo.split('.')[1] + "_Percent." + photo.split('.')[2], tempimg)

                red *= 65535
                green *= 65535
                blue *= 65535

                red = red.astype(int)
                green = green.astype(int)
                blue = blue.astype(int)

                ### Merge the channels back into a single image
                red = red.astype("uint16")
                green = green.astype("uint16")
                blue = blue.astype("uint16")

            refimg = cv2.merge((blue, green, red))

        else: #Float to Index
            green[green > 1.0] = 1.0
            red[red > 1.0] = 1.0
            blue[blue > 1.0] = 1.0

            green[green < 0.0] = 0.0
            red[red < 0.0] = 0.0
            blue[blue < 0.0] = 0.0

            red = red.astype("float")
            green = green.astype("float")
            blue = blue.astype("float")

            refimg = cv2.merge((blue, green, red))
            refimg = cv2.normalize(refimg.astype("float"), None, 0.0, 1.0, cv2.NORM_MINMAX)


        if camera_model == "Survey2" and filt == "Red + NIR (NDVI)":
            ### Remove green information if NDVI camera
           refimg[:, :, 1] = 1

        elif camera_model in ["Survey1", "DJI Phantom 4", "DJI Phantom 3a", "DJI Phantom 3p"]:
            refimg[:, :, 1] = 1

        elif camera_model in ["Survey2", "Survey3"] and filt in ["NIR", "Red", "RE"]:
            ### Remove blue and green information if NIR or Red camera
            # refimg[:, :, 0] = 1
            # refimg[:, :, 1] = 1
            refimg = refimg[:, :, 2]

        elif camera_model == "Survey2" and filt == "Green":
            ### Remove blue and red information if GREEN camera
            # refimg[:, :, 0] = 1
            # refimg[:, :, 2] = 1
            refimg = refimg[:, :, 1]

        elif camera_model == "Survey2" and filt == "Green":
            ### Remove red and green information if BLUE camera
            # refimg[:, :, 1] = 1
            # refimg[:, :, 2] = 1
            refimg = refimg[:, :, 0]

        if self.Tiff2JpgBox.checkState() > 0:
            self.CalibrationLog.append("Making JPG")
            QtWidgets.QApplication.processEvents()
            cv2.imencode(".jpg", refimg)
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
            exc_type, exc_obj,exc_tb = sys.exc_info()
            print(e)
            print("Line: " + str(exc_tb.tb_lineno))
            return False

    def check_if_RGB(self, camera, filt, lens): #Kernel 14.4, Survey 3 - RGBs, and Phantoms
        if camera in self.DJIS:
            return True

        elif (camera == "Survey3" and filt not in ["RE", "NIR"]):
            return True

        elif camera == "Kernel 14.4":
            return True

        elif camera == "Survey2" and filt == "Red + NIR (NDVI)":
            return True

        else:
            return False

    def bad_target_photo(self, channels):
        for channel in channels:
            if channel != sorted(channel, reverse=True):
                return True

            for targ in channel:
                if math.isnan(targ):
                    return True

        return False


    def print_center_targs(self, image, targ1values, targ2values, targ3values, targ4values, target1, target2, target3, target4, angle):
        t1_str = image.split(".")[0] + "_t1." + image.split(".")[1]
        t1_image = targ1values
        cv2.imwrite(t1_str, t1_image)

        t2_str = image.split(".")[0] + "_t2." + image.split(".")[1]
        t2_image = targ2values
        cv2.imwrite(t2_str, t2_image)

        t3_str = image.split(".")[0] + "_t3." + image.split(".")[1]
        t3_image = targ3values
        cv2.imwrite(t3_str, t3_image)

        t4_str = image.split(".")[0] + "_t4." + image.split(".")[1]
        t4_image = targ4values
        cv2.imwrite(t4_str, t4_image)

        if angle > self.ANGLE_SHIFT_QR:
            image_line = image.split(".")[0] + "_circles_shift." + image.split(".")[1]
        else:
            image_line = image.split(".")[0] + "_circles_orig." + image.split(".")[1]
        line_image = cv2.imread(image, -1)

        cv2.circle(line_image,target1, 15, (0,0,255), -1)
        cv2.circle(line_image,target2, 15, (255,0,0), -1)
        cv2.circle(line_image,target3, 15, (255,255,0), -1)
        cv2.circle(line_image,target4, 15, (255,0,255), -1)
        
        cv2.imwrite(image_line, line_image)

    def get_LOBF_values(self, x, y):
        mean_x = np.mean(x)
        mean_y = np.mean(y)

        numer = sum((x - mean_x) * (y - mean_y))
        denom = sum(np.power(x - mean_x, 2))

        slope = numer / denom
        intercept = mean_y - (slope * mean_x)

        return slope, intercept

    def get_filetype(self, image):
        if image.split(".")[1] in self.JPGS:
            return "JPG"

        elif image.split(".")[1] in self.TIFS:
            return "TIF"

####Function for finding the QR target and calculating the calibration coeficients\
    def findQR(self, image, ind):
        try:
            self.ref = ""

            if self.CalibrationTargetSelect.currentIndex() == 0:
                version = "V2"

            elif self.CalibrationTargetSelect.currentIndex() == 1:
                version = "V1"

            camera_model = ind[0].currentText()
            fil = ind[1].currentText()
            lens = ind[2].currentText()

            #Fiducial Finder only needs to be run for Version 2, calib.txt will only be written for Version 2
            if version == "V2":
                meta_im = image.split(".")[0] + "_temp_meta." + image.split(".")[1]
                cv2.imwrite(meta_im, cv2.imread(image, -1))
                self.copyExif(image, meta_im)

                subprocess.call([modpath + os.sep + r'FiducialFinder.exe', image], startupinfo=si)
                im_orig = cv2.imread(image, -1)

                list = None
                im = cv2.imread(image, 0)
                listcounter = 2

                if os.path.exists(r'.' + os.sep + r'calib.txt'):
                    # cv2.imwrite(image.split('.')[-2] + "_original." + image.split('.')[-1], cv2.imread(image, -1))
                    while (list is None or len(list) <= 0) and listcounter < 10:
                        with open(r'.' + os.sep + r'calib.txt', 'r+') as cornerfile:
                            list = cornerfile.read()

                        im = im * listcounter
                        listcounter += 1
                        cv2.imwrite(image, im)
                        subprocess.call([modpath + os.sep + r'FiducialFinder.exe', image], startupinfo=si)

                        try:
                            list = list.split('[')[1].split(']')[0]

                        except Exception as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            print("Error: ", e)
                            print("Line: " + str(exc_tb.tb_lineno))

                    cv2.imwrite(image, im_orig)
                    self.copyExif(meta_im, image)
                    os.remove(meta_im)

                    # os.unlink(image.split('.')[-2] + "_original." + image.split('.')[-1])
                    with open(r'.' + os.sep + r'calib.txt', 'r+') as f:
                        f.truncate()

            #Finding coordinates for Version 2         
            if version == "V2":
                self.CalibrationLog.append("Looking for QR target \n")
                if len(list) > 0:
                    self.ref = self.refindex[1]
                    # self.CalibrationLog.append(list)
                    temp = np.fromstring(str(list), dtype=int, sep=',')
                    self.coords = [[temp[0],temp[1]],[temp[2],temp[3]],[temp[6],temp[7]],[temp[4],temp[5]]]

            #Finding coordinates for Version 1
            else:
                self.CalibrationLog.append("Looking for QR target \n")
                self.ref = self.refindex[0]

                if self.check_if_RGB(camera_model, fil, lens): #if RGB Camera
                    im = cv2.imread(image)
                    grayscale = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)) #increasing contrast
                    cl1 = clahe.apply(grayscale)
                else: #if mono camera
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
                    self.coords = []
                    count = 0

                    if hierarchy is not None:
                        for i in hierarchy[0]:
                            self.traverseHierarchy(hierarchy, contours, count, im, 0)
                            count += 1
    
                    if len(self.coords) == 3:
                        break
                    else:
                        threshcounter += 17

                if len(self.coords) is not 3:
                    self.CalibrationLog.append("Could not find MAPIR ground target.")
                    QtWidgets.QApplication.processEvents()
                    return
     
            line1 = np.sqrt(np.power((self.coords[0][0] - self.coords[1][0]), 2) + np.power((self.coords[0][1] - self.coords[1][1]),
                                                                                  2))  # Getting the distance between each centroid
            line2 = np.sqrt(np.power((self.coords[1][0] - self.coords[2][0]), 2) + np.power((self.coords[1][1] - self.coords[2][1]), 2))
            line3 = np.sqrt(np.power((self.coords[2][0] - self.coords[0][0]), 2) + np.power((self.coords[2][1] - self.coords[0][1]), 2))

            hypotenuse = line1 if line1 > line2 else line2
            hypotenuse = line3 if line3 > hypotenuse else hypotenuse

            #Finding Version 2 Target
            if version == "V2":
                slope = (self.coords[2][1] - self.coords[1][1]) / (self.coords[2][0] - self.coords[1][0])
                dist = self.coords[0][1] - (slope * self.coords[0][0]) + ((slope * self.coords[2][0]) - self.coords[2][1])
                dist /= np.sqrt(np.power(slope, 2) + 1)
                center = self.coords[0]
                right = self.coords[1]
                bottom = self.coords[2]

                slope_center_right = (center[1] - right[1]) / (center[0] - right[0])
                angle = abs(math.degrees(math.atan(slope_center_right)))

            else:
                if hypotenuse == line1:

                    slope = (self.coords[1][1] - self.coords[0][1]) / (self.coords[1][0] - self.coords[0][0])
                    dist = self.coords[2][1] - (slope * self.coords[2][0]) + ((slope * self.coords[1][0]) - self.coords[1][1])
                    dist /= np.sqrt(np.power(slope, 2) + 1)
                    center = self.coords[2]

                    if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):

                        bottom = self.coords[0]
                        right = self.coords[1]
                    else:

                        bottom = self.coords[1]
                        right = self.coords[0]
                elif hypotenuse == line2:

                    slope = (self.coords[2][1] - self.coords[1][1]) / (self.coords[2][0] - self.coords[1][0])
                    dist = self.coords[0][1] - (slope * self.coords[0][0]) + ((slope * self.coords[2][0]) - self.coords[2][1])
                    dist /= np.sqrt(np.power(slope, 2) + 1)
                    center = self.coords[0]

                    if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):

                        bottom = self.coords[1]
                        right = self.coords[2]
                    else:

                        bottom = self.coords[2]
                        right = self.coords[1]
                else:

                    slope = (self.coords[0][1] - self.coords[2][1]) / (self.coords[0][0] - self.coords[2][0])
                    dist = self.coords[1][1] - (slope * self.coords[1][0]) + ((slope * self.coords[0][0]) - self.coords[0][1])
                    dist /= np.sqrt(np.power(slope, 2) + 1)
                    center = self.coords[1]
                    if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):
                        # self.CalibrationLog.append("slope and dist share sign")
                        bottom = self.coords[2]
                        right = self.coords[0]
                    else:

                        bottom = self.coords[0]
                        right = self.coords[2]

            if version == "V2":
                if len(list) > 0:
                    guidelength = np.sqrt(np.power((center[0] - bottom[0]), 2) + np.power((center[1] - bottom[1]), 2))
                    pixelinch = guidelength / self.CORNER_TO_CORNER

                    rad = (pixelinch * self.CORNER_TO_TARG)
                    vx = center[1] - bottom[1]
                    vy = center[0] - bottom[0]

            else:
                guidelength = np.sqrt(np.power((center[0] - bottom[0]), 2) + np.power((center[1] - bottom[1]), 2))
                pixelinch = guidelength / self.SQ_TO_SQ
                rad = (pixelinch * self.SQ_TO_TARG)
                vx = center[0] - bottom[0]
                vy = center[1] - bottom[1]

            newlen = np.sqrt(vx * vx + vy * vy)

            if version == "V2":
                if len(list) > 0:
                    targ1x = (rad * (vx / newlen)) + self.coords[0][0]
                    targ1y = (rad * (vy / newlen)) + self.coords[0][1]
                    targ2x = (rad * (vx / newlen)) + self.coords[1][0]
                    targ2y = (rad * (vy / newlen)) + self.coords[1][1]
                    targ3x = (rad * (vx / newlen)) + self.coords[2][0]
                    targ3y = (rad * (vy / newlen)) + self.coords[2][1]
                    targ4x = (rad * (vx / newlen)) + self.coords[3][0]
                    targ4y = (rad * (vy / newlen)) + self.coords[3][1]

                    if angle > self.ANGLE_SHIFT_QR:
                        corn_to_targ = self.CORNER_TO_TARG - 1
                        rad = (pixelinch * corn_to_targ)
                        targ1y = -(rad * (vy / newlen)) + self.coords[0][1]
                        targ2y = -(rad * (vy / newlen)) + self.coords[1][1]
                        targ3y = -(rad * (vy / newlen)) + self.coords[2][1]
                        targ4y = -(rad * (vy / newlen)) + self.coords[3][1]


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

            #((ind[0] > 1) and (ind[0] == 3 and ind[1] != 2)) or ((ind[0] < 2) and (ind[1] > 10)) or (ind[0] > 5)

            if self.check_if_RGB(camera_model, fil, lens):
                try:
                    targ1values = im2[(target1[1] - int((pixelinch * 0.75) / 2)):(target1[1] + int((pixelinch * 0.75) / 2)),
                                  (target1[0] - int((pixelinch * 0.75) / 2)):(target1[0] + int((pixelinch * 0.75) / 2))]


                    targ2values = im2[(target2[1] - int((pixelinch * 0.75) / 2)):(target2[1] + int((pixelinch * 0.75) / 2)),
                                  (target2[0] - int((pixelinch * 0.75) / 2)):(target2[0] + int((pixelinch * 0.75) / 2))]

                    targ3values = im2[(target3[1] - int((pixelinch * 0.75) / 2)):(target3[1] + int((pixelinch * 0.75) / 2)),
                                  (target3[0] - int((pixelinch * 0.75) / 2)):(target3[0] + int((pixelinch * 0.75) / 2))]
                except Exception as e:
                    exc_type, exc_obj,exc_tb = sys.exc_info()
                    print(e)
                    print("Line: " + str(exc_tb.tb_lineno))

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
                if version == "V2":
                    if len(list) > 0:
                        targ4values = im2[(target4[1] - int((pixelinch * 0.75) / 2)):(target4[1] + int((pixelinch * 0.75) / 2)),
                                      (target4[0] - int((pixelinch * 0.75) / 2)):(target4[0] + int((pixelinch * 0.75) / 2))]
                        t4redmean = np.mean(targ4values[:, :, 2])
                        t4greenmean = np.mean(targ4values[:, :, 1])
                        t4bluemean = np.mean(targ4values[:, :, 0])
                        yred = [0.87, 0.51, 0.23, 0.0]
                        yblue = [0.87, 0.51, 0.23, 0.0]
                        ygreen = [0.87, 0.51, 0.23, 0.0]

                        xred = [t1redmean, t2redmean, t3redmean, t4redmean]
                        xgreen = [t1greenmean, t2greenmean, t3greenmean, t4greenmean]
                        xblue = [t1bluemean, t2bluemean, t3bluemean, t4bluemean]


                else:
                    yred = [0.87, 0.51, 0.23]
                    yblue = [0.87, 0.51, 0.23]
                    ygreen = [0.87, 0.51, 0.23]

                    xred = [t1redmean, t2redmean, t3redmean]
                    xgreen = [t1greenmean, t2greenmean, t3greenmean]
                    xblue = [t1bluemean, t2bluemean, t3bluemean]

                if ((camera_model == "Survey3" and fil == "RGN") or (camera_model == "DJI Phantom 4 Pro") 
                        or (camera_model == "Kernel 14.4" and fil =="550/660/850")):
                    yred = self.refvalues[self.ref]["550/660/850"][0]
                    ygreen = self.refvalues[self.ref]["550/660/850"][1]
                    yblue = self.refvalues[self.ref]["550/660/850"][2]

                elif ((camera_model == "Survey3" and fil == "NGB") 
                    or (camera_model == "Kernel 14.4" and fil == "475/550/850")):

                    yred = self.refvalues[self.ref]["475/550/850"][0]
                    ygreen = self.refvalues[self.ref]["475/550/850"][1]
                    yblue = self.refvalues[self.ref]["475/550/850"][2]

                elif (camera_model == "Survey3" and fil == "OCN"):

                    yred = self.refvalues[self.ref]["490/615/808"][0]
                    ygreen = self.refvalues[self.ref]["490/615/808"][1]
                    yblue = self.refvalues[self.ref]["490/615/808"][2]


                else: #Survey 2 - NDVI
                    yred = self.refvalues[self.ref]["660/850"][0]
                    ygreen = self.refvalues[self.ref]["660/850"][1]
                    yblue = self.refvalues[self.ref]["660/850"][2]

                if self.get_filetype(image) == "JPG":   
                    xred = [x / 255 for x in xred]
                    xgreen = [x / 255 for x in xgreen]
                    xblue = [x / 255 for x in xblue]

                elif self.get_filetype(image) == "TIF":
                    xred = [x / 65535 for x in xred]
                    xgreen = [x / 65535 for x in xgreen]
                    xblue = [x / 65535 for x in xblue]

                x_channels = [xred, xgreen, xblue]
                if self.bad_target_photo(x_channels):
                    raise Exception("Bad reflectance image provided. Please use another reflectance image.")

                red_slope, red_intercept = self.get_LOBF_values(xred, yred)
                green_slope, green_intercept = self.get_LOBF_values(xgreen, ygreen)
                blue_slope, blue_intercept = self.get_LOBF_values(xblue, yblue)

                #return cofr, cofg, cofb
                self.multiplication_values["red"]["slope"] = red_slope
                self.multiplication_values["red"]["intercept"] = red_intercept

                self.multiplication_values["green"]["slope"] = green_slope
                self.multiplication_values["green"]["intercept"] = green_intercept

                self.multiplication_values["blue"]["slope"] = blue_slope
                self.multiplication_values["blue"]["intercept"] = blue_intercept

                if version == "V2":
                    if len(list) > 0:
                        self.CalibrationLog.append("Found QR Target Model 2, please proceed with calibration.")
                    else:
                        self.CalibrationLog.append("Could not find Calibration Target.")
                else:
                    self.CalibrationLog.append("Found QR Target Model 1, please proceed with calibration.")

            else:
                if version == "V2":
                    if len(list) > 0:
                        targ1values = im2[(target1[1] - int((pixelinch * 0.75) / 2)):(target1[1] + int((pixelinch * 0.75) / 2)),
                                      (target1[0] - int((pixelinch * 0.75) / 2)):(target1[0] + int((pixelinch * 0.75) / 2))]
                        targ2values = im2[(target2[1] - int((pixelinch * 0.75) / 2)):(target2[1] + int((pixelinch * 0.75) / 2)),
                                      (target2[0] - int((pixelinch * 0.75) / 2)):(target2[0] + int((pixelinch * 0.75) / 2))]
                        targ3values = im2[(target3[1] - int((pixelinch * 0.75) / 2)):(target3[1] + int((pixelinch * 0.75) / 2)),
                                      (target3[0] - int((pixelinch * 0.75) / 2)):(target3[0] + int((pixelinch * 0.75) / 2))]
                        targ4values = im2[(target4[1] - int((pixelinch * 0.75) / 2)):(target4[1] + int((pixelinch * 0.75) / 2)),
                                      (target4[0] - int((pixelinch * 0.75) / 2)):(target4[0] + int((pixelinch * 0.75) / 2))]

                        if (len(im2.shape) > 2) and fil in ["RE", "NIR", "Red"]:
                            t1mean = np.mean(targ1values[:,:,2])
                            t2mean = np.mean(targ2values[:,:,2])
                            t3mean = np.mean(targ3values[:,:,2])
                            t4mean = np.mean(targ4values[:,:,2])

                        elif (len(im2.shape) > 2) and fil in ["Green"]:
                            t1mean = np.mean(targ1values[:,:,1])
                            t2mean = np.mean(targ2values[:,:,1])
                            t3mean = np.mean(targ3values[:,:,1])
                            t4mean = np.mean(targ4values[:,:,1])

                        elif (len(im2.shape) > 2) and fil in ["Blue"]:
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
                        x = [t1mean, t2mean, t3mean, t4mean]
                else:
                    targ1values = im2[(target1[1] - int((pixelinch * 0.75) / 2)):(target1[1] + int((pixelinch * 0.75) / 2)),
                                  (target1[0] - int((pixelinch * 0.75) / 2)):(target1[0] + int((pixelinch * 0.75) / 2))]
            
                    targ2values = im2[(target2[1] - int((pixelinch * 0.75) / 2)):(target2[1] + int((pixelinch * 0.75) / 2)),
                                  (target2[0] - int((pixelinch * 0.75) / 2)):(target2[0] + int((pixelinch * 0.75) / 2))]

                    targ3values = im2[(target3[1] - int((pixelinch * 0.75) / 2)):(target3[1] + int((pixelinch * 0.75) / 2)),
                                  (target3[0] - int((pixelinch * 0.75) / 2)):(target3[0] + int((pixelinch * 0.75) / 2))]

       
                    if (len(im2.shape) > 2) and fil in ["RE", "NIR", "Red"]:
                        t1mean = np.mean(targ1values[:,:,2])
                        t2mean = np.mean(targ2values[:,:,2])
                        t3mean = np.mean(targ3values[:,:,2])

                    elif (len(im2.shape) > 2) and fil in ["Green"]:
                        t1mean = np.mean(targ1values[:,:,1])
                        t2mean = np.mean(targ2values[:,:,1])
                        t3mean = np.mean(targ3values[:,:,1])

                    elif (len(im2.shape) > 2) and fil in ["Blue"]:
                        t1mean = np.mean(targ1values[:,:,0])
                        t2mean = np.mean(targ2values[:,:,0])
                        t3mean = np.mean(targ3values[:,:,0])
                    else:
                        t1mean = np.mean(targ1values)
                        t2mean = np.mean(targ2values)
                        t3mean = np.mean(targ3values)
                    y = [0.87, 0.51, 0.23]
                    x = [t1mean, t2mean, t3mean]


                if (fil == "NIR" and (camera_model in ["Survey2", "Survey3"])):
                    y = self.refvalues[self.ref]["850"][0]

                elif camera_model == "Survey2" and fil == "Red":
                    y = self.refvalues[self.ref]["650"][0]

                elif camera_model == "Survey2" and fil == "Green":
                    y = self.refvalues[self.ref]["550"][1]

                elif camera_model == "Survey2" and fil == "Blue":
                    y = self.refvalues[self.ref]["450"][2]

                elif fil == "405":
                    y = self.refvalues[self.ref]["Mono405"]

                elif fil == "450":
                    y = self.refvalues[self.ref]["Mono450"]

                elif fil == "490":
                    y = self.refvalues[self.ref]["Mono490"]

                elif fil == "518":
                    y = self.refvalues[self.ref]["Mono518"]

                elif fil == "550":
                    y = self.refvalues[self.ref]["Mono550"]

                elif fil == "590":
                    y = self.refvalues[self.ref]["Mono590"]

                elif fil == "615":
                    y = self.refvalues[self.ref]["Mono615"]

                elif fil == "632":
                    y = self.refvalues[self.ref]["Mono632"]

                elif fil == "650":
                    y = self.refvalues[self.ref]["Mono650"]

                elif fil == "685":
                    y = self.refvalues[self.ref]["Mono685"]

                elif fil == "725":
                    y = self.refvalues[self.ref]["Mono725"]

                elif fil == "808":
                    y = self.refvalues[self.ref]["Mono808"]

                elif fil == "850":
                    y = self.refvalues[self.ref]["Mono850"]

                elif fil == "RE":
                    y = self.refvalues[self.ref]["725"]


                if self.get_filetype(image) == "JPG":
                    x = [i / 255 for i in x]
        
                elif self.get_filetype(image) == "TIF":
                    x = [i / 65535 for i in x]

                if self.bad_target_photo([x]):
                    raise Exception("Bad reflectance image provided. Please use another reflectance image.")

                slope, intercept = self.get_LOBF_values(x, y)

                self.multiplication_values["mono"]["slope"] = slope
                self.multiplication_values["mono"]["intercept"] = intercept

                if version == "V2":
                    if len(list) > 0:
                        self.CalibrationLog.append("Found QR Target Model 2, please proceed with calibration.")
                    else:
                        self.CalibrationLog.append("Could not find Calibration Target.")
                else:
                    self.CalibrationLog.append("Found QR Target Model 1, please proceed with calibration.")
                QtWidgets.QApplication.processEvents()

        except Exception as e:
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.CalibrationLog.append("Error: " + str(e) + ' Line: ' + str(exc_tb.tb_lineno))
            return
            # slope, intcpt, r_value, p_value, std_err = stats.linregress(x, y)
            # self.CalibrationLog.append("Found QR Target, please proceed with calibration.")
            #
            # return [intcpt, slope]
    # Calibration Steps: End

    # Helper functions
    # def debayer(self, m):
    #     r = m[0:: 2, 0:: 2]
    #     g = np.clip(m[1::2, 0::2] // 2 + m[0::2, 1::2] // 2, 0, 2**14 - 1)
    #     b = m[1:: 2, 1:: 2]
    #     # b = (((b - b.min()) / (b.max() - b.min())) * 65536.0).astype("uint16")
    #     # r = (((r - r.min()) / (r.max() - r.min())) * 65536.0).astype("uint16")
    #     # g = (((g - g.min()) / (g.max() - g.min())) * 65536.0).astype("uint16")
    #     return np.dstack([b, g, r])

    def output_mono_band_validation(self):
        camera_model = self.PreProcessCameraModel.currentText()
        filt = self.PreProcessFilter.currentText()

        if not ((camera_model in ["Survey2", "Survey3"]) and (filt in ["RE", "NIR", "Red", "Blue", "Green"])):
            self.PreProcessLog.append("WARNING: Outputting mono band for filter {} is not supported for Calibration Tab \n".format(filt))
    
    def preProcessHelper(self, infolder, outfolder, customerdata=True):
        if self.PreProcessMonoBandBox.isChecked():
            self.output_mono_band_validation()

        if self.PreProcessCameraModel.currentText() in self.DJIS:
            os.chdir(infolder)
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.DNG"))
            infiles.sort()
            counter = 0
            for input in infiles:
                self.PreProcessLog.append(
                    "Processing Image: " + str((counter) + 1) + " of " + str(len(infiles)) +
                    " " + input.split(os.sep)[1])
                QtWidgets.QApplication.processEvents()
                self.openDNG(infolder + input.split('.')[1] + "." + input.split('.')[2], outfolder, customerdata)

                counter += 1

        elif self.PreProcessCameraModel.currentText() in self.KERNELS:
            os.chdir(infolder)
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.[mM][aA][pP][iI][rR]"))
            infiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
            infiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
            counter = 0

            for input in infiles:
                self.PreProcessLog.append(
                    "Processing Image: " + str((counter) + 1) + " of " + str(len(infiles)) +
                    "  " + input.split(os.sep)[1])
                QtWidgets.QApplication.processEvents()
                filename = input.split('.')
                outputfilename = outfolder + filename[1] + '.tif'
                # print(infolder + input.split('.')[1] + "." + input.split('.')[2])
                # print(outfolder + outputfilename)
                self.openMapir(infolder + input.split('.')[1] + "." + input.split('.')[2],  outputfilename, input, outfolder)


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
                        oldfirmware = False

                        if customerdata == True:
                            self.PreProcessLog.append(
                                "Processing Image: " + str(int((counter / 2) + 1)) + " of " + str(int(len(infiles) / 2)) +
                                " " + input.split(os.sep)[1])
                            QtWidgets.QApplication.processEvents()

                        if self.PreProcessCameraModel.currentText() == "Survey3":
                            try:
                                data = np.fromfile(input, dtype=np.uint8)
                                # data2 = np.fromfile("F:\\DCIM\Photo\\2018_0507_142527_011.RAW", dtype=np.uint8)
                                data = np.unpackbits(data)
                                # data2 = np.unpackbits(data2)
                                datsize = data.shape[0]
                                # dat2size = data2.shape[0]
                                data = data.reshape((int(datsize / 4), 4))


                                temp = copy.deepcopy(data[0::2])
                                temp2 = copy.deepcopy(data[1::2])
                                data[0::2] = temp2
                                data[1::2] = temp

                                udata = np.packbits(np.concatenate([data[0::3], np.array([0, 0, 0, 0] * 12000000, dtype=np.uint8).reshape(12000000,4),   data[2::3], data[1::3]], axis=1).reshape(192000000, 1)).tobytes()

                                img = np.fromstring(udata, np.dtype('u2'), (4000 * 3000)).reshape((3000, 4000))

                            except Exception as e:
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                # self.PreProcessLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
                                print(str(e) + ' Line: ' + str(exc_tb.tb_lineno))

                                oldfirmware = True

                        elif self.PreProcessCameraModel.currentText() == "Survey2":
                            with open(input, "rb") as rawimage:
                                img = np.fromfile(rawimage, np.dtype('u2'), (4608 * 3456)).reshape((3456, 4608))

                        if oldfirmware:
                            try:
                                with open(input, "rb") as rawimage:
                                    img = np.fromfile(rawimage, np.dtype('u2'), (4000 * 3000)).reshape((3000, 4000))
                            except Exception as e:
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                # self.PreProcessLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
                                print(str(e) + ' Line: ' + str(exc_tb.tb_lineno))

                        try:
                            color = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB).astype("float32")

                        except Exception as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            # self.PreProcessLog.append(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
                            print(str(e) + ' Line: ' + str(exc_tb.tb_lineno))

                        if self.PreProcessColorBox.isChecked():


                            # redmax = np.setdiff1d(self.imkeys[self.imkeys > int(np.median(color[:,:,0]))], color[:,:,0])[0]
                            # redmin = color[:,:,0].min()

                            redmax = np.percentile(color[:,:,0], 98)
                            redmin = np.percentile(color[:, :, 0], 2)

                            # greenmax = \
                            #     np.setdiff1d(self.imkeys[self.imkeys > int(np.median(color[:,:,2]))], color[:,:,2])[0]
                            # greenmin = color[:,:,2].min()
                            greenmax = np.percentile(color[:, :, 1], 98)

                            greenmin = np.percentile(color[:, :, 1], 2)

                            # bluemax = \
                            #     np.setdiff1d(self.imkeys[self.imkeys > int(np.median(color[:,:,1]))], color[:,:,1])[0]
                            # bluemin = color[:,:,1].min()
                            bluemax = np.percentile(color[:, :, 2], 98)

                            bluemin = np.percentile(color[:, :, 2], 2)

                            # maxpixel = redmax if redmax > bluemax else bluemax
                            # maxpixel = greenmax if greenmax > maxpixel else maxpixel
                            # minpixel = redmin if redmin < bluemin else bluemin
                            # minpixel = greenmin if greenmin < minpixel else minpixel

                            # color = cv2.merge((color[:,:,0],color[:,:,2],color[:,:,1])).astype(np.dtype('u2'))
                            color[:,:,0] = (((color[:,:,0] - redmin) / (redmax - redmin)))
                            color[:,:,2] = (((color[:,:,2] - bluemin) / (bluemax - bluemin)))
                            color[:,:,1] = (((color[:,:,1] - greenmin) / (greenmax - greenmin)))
                            color[color > 1.0] = 1.0
                            color[color < 0.0] = 0.0

                        #if ((self.PreProcessCameraModel.currentText() == "Survey3") 
                         #       and (self.PreProcessFilter.currentText() == "NIR" or  self.PreProcessFilter.currentText() == "RE")):
                          #  color = color[:,:,0]
                        # maxcol = color.max()
                        # mincol = color.min()

                        if self.PreProcessJPGBox.isChecked():
                            # color = (color - int(np.percentile(color, 2))) / (int(np.percentile(color, 98)) - int(np.percentile(color, 2)))
                            color = color * 255.0
                            color = color.astype("uint8")
                            filename = input.split('.')
                            outputfilename = filename[1] + '.jpg'
                            cv2.imencode(".jpg", color)
                        else:
                            #color = (color - int(np.percentile(color, 2))) / (int(np.percentile(color, 98))  - int(np.percentile(color, 2)))
                            color = color * 65535.0
                            color = color.astype("uint16")
                            if not self.PreProcessColorBox.isChecked():
                                color = cv2.bitwise_not(color)
                            filename = input.split('.')
                            outputfilename = filename[1] + '.tif'
                            cv2.imencode(".tif", color)

                        if self.PreProcessMonoBandBox.isChecked():
                            dropdown_value = self.Band_Dropdown.currentText()
                            band = dropdown_value[dropdown_value.find("(")+1:dropdown_value.find(")")]
                            
                            if band == "Red":
                                color = color[:,:,0]
                                color[color >= 65535] = color.min()

                            elif band == "Green":
                                color = color[:,:,1]
                                color[color >= 65535] = color.min()

                            elif band == "Blue":
                                color = color[:,:,2]
                                color[color >= 65535] = color.min()

                        cv2.imwrite(outfolder + outputfilename, color)

                        if customerdata == True:
                            self.copyExif(infolder + infiles[counter + 1], outfolder + outputfilename)
                        counter += 2

                else:
                    self.PreProcessLog.append(
                        "Incorrect file structure. Please arrange files in a RAW, JPG, RAW, JPG... format.")


    def traverseHierarchy(self, tier, cont, index, image, depth):

        if tier[0][index][2] != -1:
            self.traverseHierarchy(tier, cont, tier[0][index][2], image, depth + 1)
            return
        elif depth >= 2:
            c = cont[index]
            moment = cv2.moments(c)
            if int(moment['m00']) != 0:
                x = int(moment['m10'] / moment['m00'])
                y = int(moment['m01'] / moment['m00'])
                self.coords.append([x, y])
            return

    def openDNG(self, inphoto, outfolder, customerdata=True):
        inphoto = str(inphoto)
        newfile = inphoto.split(".")[0] + ".tiff"

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

    def get_dark_frame_value(self, fil_str):
        with open(modpath + os.sep + r'Dark_Frame_Values.json') as json_data:
            DFVS = json.load(json_data)
            dark_frame_value = DFVS["14.4"][self.PreProcessLens.currentText()][fil_str]

        return dark_frame_value

    def openMapir(self, inphoto, outphoto, input, outfolder):
        # self.PreProcessLog.append(str(inphoto) + " " + str(outphoto))
        try:
            if "mapir" in inphoto.split('.')[1]:
                self.conv = Converter()
                if self.PreProcessDarkBox.isChecked():
                    # subprocess.call(
                    #     [modpath + os.sep + r'Mapir_Converter.exe', '-d', os.path.abspath(inphoto),
                    #      os.path.abspath(outphoto)], startupinfo=si)
                    _, _, _, self.lensvals = self.conv.openRaw(inphoto, outphoto, darkscale=True)
                else:
                    # subprocess.call(
                    #     [modpath + os.sep + r'Mapir_Converter.exe', os.path.abspath(inphoto),
                    #      os.path.abspath(outphoto)], startupinfo=si)
                    _, _, _, self.lensvals = self.conv.openRaw(inphoto, outphoto, darkscale=False)
                img = cv2.imread(outphoto, -1)

                try:


                    if self.PreProcessCameraModel.currentText() == "Kernel 14.4":
                        h, w = img.shape[:2]

                        self.PreProcessLog.append("Debayering")
                        QtWidgets.QApplication.processEvents()
                        cv2.imwrite(outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1], img)
                        self.copySimple(outphoto, outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1])

                        color = cv2.cvtColor(img, cv2.COLOR_BAYER_GB2RGB).astype("float32")
                        color2 = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR).astype("float32")
                        # gr = ((color2[:,:,2] + color2[:,:,0])/2).astype("uint16")
                        #
                        # color[:,:,1] = gr
                        #
                        # color[color > 65535] = 65535
                        # color[color < 0] = 0
                        # color[:, :, 1] = color2[:, :, 2]
                        color[:, :, 1] = color2[:, :, 0]
                        # temp1 = color[:,:,0]
                        # color[:,:,0] = color[:,:,2]
                        # color[:,:2] = temp1
                        # color = self.debayer(img)
                        # color = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype("uint16")
                        roff = 0.0
                        goff = 0.0
                        boff = 0.0
                        color = color / 65535.0

                        if self.PreProcessColorBox.isChecked():
                            red_coeffs = self.COLOR_CORRECTION_VECTORS[:3]
                            green_coeffs = self.COLOR_CORRECTION_VECTORS[3:6]
                            blue_coeffs = self.COLOR_CORRECTION_VECTORS[6:9]

                            red = color[:, :, 0] = (red_coeffs[0] * color[:, :, 0]) + (red_coeffs[1] * color[:, :, 1]) + (red_coeffs[2] * color[:, :, 2]) + roff
                            green = color[:, :, 1] = (green_coeffs[0] * color[:, :, 0]) + (green_coeffs[1] * color[:, :, 1]) + (green_coeffs[2] * color[:, :, 2]) + goff
                            blue = color[:, :, 2] = (blue_coeffs[0] * color[:, :, 0]) + (blue_coeffs[1] * color[:, :, 1]) + (blue_coeffs[2] * color[:, :, 2]) + boff

                            #need to rescale not clip
                            color[red > 1.0] = 1.0
                            color[green > 1.0] = 1.0
                            color[blue > 1.0] = 1.0
                            color[red < 0.0] = 0.0
                            color[green < 0.0] = 0.0
                            color[blue < 0.0] = 0.0

                        color = (color * 65535.0).astype("uint16")

                        if self.PreProcessVignette.isChecked():
                            red = color[:, :, 0]
                            green = color[:, :, 1]
                            blue = color[:, :, 2]

                            lens_str = self.PreProcessLens.currentText().split("m")[0]
                            fil_str = self.PreProcessFilter.currentText()[:3]

                            if "/" in self.PreProcessFilter.currentText():
                                fil_names = self.PreProcessFilter.currentText().split("/")
                                fil_str = fil_names[0] + "-" + fil_names[1] + "-" + fil_names[2]

                            dark_frame_value = self.get_dark_frame_value(fil_str)
                            
                            with open(modpath + os.sep + r"vig_" + fil_str + "_" + lens_str + "_" + "1" + r".txt", "rb") as vigfilered:
                                v_array = np.ndarray((h, w), np.dtype("float32"), np.fromfile(vigfilered, np.dtype("float32")))
                                red = red / v_array
                                red[red > 65535.0] = 65535.0
                                red[red < 0.0] = 0.0
                            
                                red -= dark_frame_value

                            with open(modpath + os.sep + r"vig_" + fil_str + "_" + lens_str + "_" + "2" + r".txt", "rb") as vigfilegreen:
                                v_array = np.ndarray((h, w), np.dtype("float32"),
                                                     np.fromfile(vigfilegreen, np.dtype("float32")))
                                green = green / v_array
                                green[green > 65535.0] = 65535.0
                                green[green < 0.0] = 0.0

                                green -= dark_frame_value

                            with open(modpath + os.sep + r"vig_" + fil_str + "_" + lens_str + "_" + "3" + r".txt", "rb") as vigfileblue:
                                v_array = np.ndarray((h, w), np.dtype("float32"),
                                                     np.fromfile(vigfileblue, np.dtype("float32")))
                                blue = blue / v_array
                                blue[blue > 65535.0] = 65535.0
                                blue[blue < 0.0] = 0.0

                                blue -= dark_frame_value

                            red = red.astype("uint16")
                            green = green.astype("uint16")
                            blue = blue.astype("uint16")

                            color =  cv2.merge((blue, green, red))

                        cv2.imencode(".tif", color)

                        cv2.imwrite(outphoto, color)
                        self.copyMAPIR(outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1], outphoto)
                        os.unlink(outphoto.split('.')[0] + r"_TEMP." + outphoto.split('.')[1])

                        self.PreProcessLog.append("Done Debayering \n")
                        QtWidgets.QApplication.processEvents()
                    else:
                        h, w = img.shape[:2]

                        try:
                            if self.PreProcessVignette.isChecked():
                                with open(modpath + os.sep + r'Dark_Frame_Values.json') as json_data:
                                    DFVS = json.load(json_data)
                                    dark_frame_value = DFVS["3.2"][self.PreProcessFilter.currentText()]

                                with open(modpath + os.sep + r"vig_" + str(
                                        self.PreProcessFilter.currentText()) + r".txt", "rb") as vigfile:
                                    # with open(self.VignetteFileSelect.text(), "rb") as vigfile:
                                    v_array = np.ndarray((h, w), np.dtype("float32"),
                                                         np.fromfile(vigfile, np.dtype("float32")))
                                    img = img / v_array
                                    img[img > 65535.0] = 65535.0
                                    img[img < 0.0] = 0.0
                                    img -= dark_frame_value

                                    img = img.astype("uint16")

                                cv2.imwrite(outphoto, img)
                        except Exception as e:
                            print("Error: ", e)
                            exc_type, exc_obj,exc_tb = sys.exc_info()
                            print(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
                            self.PreProcessLog.append("No vignette correction data found")
                            QtWidgets.QApplication.processEvents()

                        self.copyMAPIR(outphoto, outphoto)
                        # self.PreProcessLog.append("Skipped Debayering")
                        QtWidgets.QApplication.processEvents()

                except Exception as e:
                    exc_type, exc_obj,exc_tb = sys.exc_info()
                    print(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
            else:
                try:

                    if self.PreProcessCameraModel.currentText() == "Kernel 14.4":
                        img = cv2.imread(inphoto, 0)

                        color = cv2.cvtColor(img, cv2.COLOR_BAYER_GR2RGB)
                        # color = self.debayer(img)
                        if self.PreProcessVignette.isChecked():
                            red = color[:, :, 0]
                            green = color[:, :, 1]
                            blue = color[:, :, 2]

                            lens_str = self.PreProcessLens.currentText().split("m")[0]
                            fil_str = self.PreProcessFilter.currentText()[:3]

                            if "/" in self.PreProcessFilter.currentText():
                                fil_names = self.PreProcessFilter.currentText().split("/")
                                fil_str = fil_names[0] + "-" + fil_names[1] + "-" + fil_names[2]

                            dark_frame_value = self.get_dark_frame_value(fil_str)
                            
                            with open(modpath + os.sep + r"vig_" + fil_str + "_" + lens_str + "_" + "1" + r".txt", "rb") as vigfilered:
                                v_array = np.ndarray((h, w), np.dtype("float32"), np.fromfile(vigfilered, np.dtype("float32")))
                                red = red / v_array
                                red[red > 65535.0] = 65535.0
                                red[red < 0.0] = 0.0
                            
                                red -= dark_frame_value

                            with open(modpath + os.sep + r"vig_" + fil_str + "_" + lens_str + "_" + "2" + r".txt", "rb") as vigfilegreen:
                                v_array = np.ndarray((h, w), np.dtype("float32"),
                                                     np.fromfile(vigfilegreen, np.dtype("float32")))
                                green = green / v_array
                                green[green > 65535.0] = 65535.0
                                green[green < 0.0] = 0.0

                                green -= dark_frame_value

                            with open(modpath + os.sep + r"vig_" + fil_str + "_" + lens_str + "_" + "3" + r".txt", "rb") as vigfileblue:
                                v_array = np.ndarray((h, w), np.dtype("float32"),
                                                     np.fromfile(vigfileblue, np.dtype("float32")))
                                blue = blue / v_array
                                blue[blue > 65535.0] = 65535.0
                                blue[blue < 0.0] = 0.0

                                blue -= dark_frame_value

                            red = red.astype("uint16")
                            green = green.astype("uint16")
                            blue = blue.astype("uint16")

                            color =  cv2.merge((blue, green, red))

                        self.PreProcessLog.append("Debayering")
                        QtWidgets.QApplication.processEvents()
                        cv2.imencode(".tif", color)
                        cv2.imwrite(outphoto, color)
                        self.copyExif(inphoto, outphoto)
                        self.PreProcessLog.append("Done Debayering \n")
                        QtWidgets.QApplication.processEvents()

                    else:

                        if "mapir" not in inphoto.split('.')[1]:
                            img = cv2.imread(inphoto, -1)
                            h, w = img.shape[:2]

                            try:
                                if self.PreProcessVignette.isChecked():
                                    with open(modpath + os.sep + r'Dark_Frame_Values.json') as json_data:
                                        DFVS = json.load(json_data)
                                        dark_frame_value = DFVS["3.2"][self.PreProcessFilter.currentText()]

                                    with open(modpath + os.sep + r"vig_" + str(
                                            self.PreProcessFilter.currentText()) + r".txt", "rb") as vigfile:
                                        # with open(self.VignetteFileSelect.text(), "rb") as vigfile:
                                        v_array = np.ndarray((h, w), np.dtype("float32"),
                                                             np.fromfile(vigfile, np.dtype("float32")))
                                        img = img / v_array
                                        img[img > 65535.0] = 65535.0
                                        img[img < 0.0] = 0.0
                                        img -= dark_frame_value

                                        img = img.astype("uint16")
                                    cv2.imwrite(outphoto, img)

                                elif self.PreProcessJPGBox.isChecked():
                                    img = img / 255
                                    img = img.astype("uint8")

                                    filename = input.split('.')
                                    outputfilename = filename[1] + '.jpg'
                                    cv2.imencode(".jpg", img)
                                    cv2.imwrite(outfolder + outputfilename, img)

                                    inphoto = outfolder + outputfilename
                                    outphoto = outfolder + outputfilename

                                else:
                                    shutil.copyfile(inphoto, outphoto)

                            except Exception as e:
                                print(e)
                                self.PreProcessLog.append("No vignette correction data found")
                                QtWidgets.QApplication.processEvents()


                            self.copyExif(inphoto, outphoto)
                        else:

                            self.copyExif(outphoto, outphoto)
                        # self.PreP.shaperocessLog.append("Skipped Debayering")
                        QtWidgets.QApplication.processEvents()

                        

                except Exception as e:
                    exc_type, exc_obj,exc_tb = sys.exc_info()
                    print(str(e) + ' Line: ' + str(exc_tb.tb_lineno))
        except Exception as e:
            print("error")
            exc_type, exc_obj,exc_tb = sys.exc_info()
            self.PreProcessLog.append("Error in function openMapir(): " + str(e) + ' Line: ' + str(exc_tb.tb_lineno))
        QtWidgets.QApplication.processEvents()

    def findCameraModel(self, resolution):
        if resolution < 10000000:
            return 'Kernel 3.2MP'
        else:
            return 'Kernel 14.4MP'

    def copyExif(self, inphoto, outphoto):
        subprocess._cleanup()

        try:
            data = subprocess.run(
                args=[modpath + os.sep + r'exiftool.exe', '-m', r'-UserComment', r'-ifd0:imagewidth', r'-ifd0:imageheight',
                      os.path.abspath(inphoto)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE, startupinfo=si).stdout.decode("utf-8")

            data = [line.strip().split(':') for line in data.split('\r\n') if line.strip()]
            ypr = data[0][1].split()
            # ypr = [0.0] * 3

            ypr[0] = abs(float(ypr[0]) % 360.0)
            ypr[1] = abs((float(ypr[1]) + 180.0) % 360.0)
            ypr[2] = abs((float(-ypr[2])) % 360.0)


            w = int(data[1][1])
            h = int(data[2][1])
            model = self.findCameraModel(w * h)
            centralwavelength = self.lensvals[3:6][1]
            bandname = self.lensvals[3:6][0]

            fnumber = self.lensvals[0][1]
            focallength = self.lensvals[0][0]
            lensmodel = self.lensvals[0][0] + "mm"

            # centralwavelength = inphoto.split(os.sep)[-1][1:4]
            if '' not in bandname:
                exifout = subprocess.run(
                    [modpath + os.sep + r'exiftool.exe', r'-config', modpath + os.sep + r'mapir.config', '-m',
                     r'-overwrite_original', r'-tagsFromFile',
                     os.path.abspath(inphoto),
                     r'-all:all<all:all',
                     r'-ifd0:make=MAPIR',
                     r'-Model=' + model,
                     #r'-ifd0:blacklevelrepeatdim=' + str(1) + " " + str(1),
                     #r'-ifd0:blacklevel=0',
                     r'-bandname=' + str(bandname[0] + ', ' + bandname[1] + ', ' + bandname[2]),
                     # r'-bandname2=' + str( r'F' + str(self.BandNames.get(bandname, [0, 0, 0])[1])),
                     # r'-bandname3=' + str( r'F' + str(self.BandNames.get(bandname, [0, 0, 0])[2])),
                     r'-WavelengthFWHM=' + str( self.lensvals[3:6][0][2] + ', ' + self.lensvals[3:6][1][2] + ', ' + self.lensvals[3:6][2][2]) ,
                     r'-ModelType=perspective',
                     r'-Yaw=' + str(ypr[0]),
                     r'-Pitch=' + str(ypr[1]),
                     r'-Roll=' + str(ypr[2]),
                     r'-CentralWavelength=' + str(float(centralwavelength[0])) + ', ' + str(float(centralwavelength[1])) + ', ' + str(float(centralwavelength[2])),
                     r'-Lens=' + lensmodel,
                     r'-FocalLength=' + focallength,
                     r'-fnumber=' + fnumber,
                     r'-FocalPlaneXResolution=' + str(6.14),
                     r'-FocalPlaneYResolution=' + str(4.60),
                     os.path.abspath(outphoto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                    startupinfo=si).stderr.decode("utf-8")
            else:
                if bandname[0].isdigit():
                    bandname[0] = r'F' + bandname[0]
                if bandname[1].isdigit():
                    bandname[1] = r'F' + bandname[1]
                if bandname[2].isdigit():
                    bandname[2] = r'F' + bandname[2]
                exifout = subprocess.run(
                    [modpath + os.sep + r'exiftool.exe', r'-config', modpath + os.sep + r'mapir.config', '-m',
                     r'-overwrite_original', r'-tagsFromFile',
                     os.path.abspath(inphoto),
                     r'-all:all<all:all',
                     r'-ifd0:make=MAPIR',
                     r'-Model=' + model,
                     #r'-ifd0:blacklevelrepeatdim=' + str(1) + " " + str(1),
                     #r'-ifd0:blacklevel=0',
                     r'-bandname=' + str( bandname[0]),
                     r'-ModelType=perspective',
                     r'-WavelengthFWHM=' + str(self.lensvals[3:6][0][2]),
                     r'-Yaw=' + str(ypr[0]),
                     r'-Pitch=' + str(ypr[1]),
                     r'-Roll=' + str(ypr[2]),
                     r'-CentralWavelength=' + str(float(centralwavelength[0])),
                     r'-Lens=' + lensmodel,
                     r'-FocalLength=' + focallength,
                     r'-fnumber=' + fnumber,
                     r'-FocalPlaneXResolution=' + str(6.14),
                     r'-FocalPlaneYResolution=' + str(4.60),
                     os.path.abspath(outphoto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                    startupinfo=si).stderr.decode("utf-8")
        except Exception as e:
            exifout = subprocess.run(
                [modpath + os.sep + r'exiftool.exe', #r'-config', modpath + os.sep + r'mapir.config',
                 r'-overwrite_original_in_place', r'-tagsFromFile',
                 os.path.abspath(inphoto),
                 r'-all:all<all:all',
                 os.path.abspath(outphoto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                startupinfo=si).stderr.decode("utf-8")
            print(exifout)

    def copySimple(self, inphoto, outphoto):
        exifout = subprocess.run(
            [modpath + os.sep + r'exiftool.exe',  # r'-config', modpath + os.sep + r'mapir.config',
             r'-overwrite_original_in_place', r'-tagsFromFile',
             os.path.abspath(inphoto),
             r'-all:all<all:all',
             os.path.abspath(outphoto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
            startupinfo=si).stderr.decode("utf-8")
        print(exifout)

    def copyMAPIR(self, inphoto, outphoto):
        if sys.platform == "win32":
            # with exiftool.ExifTool() as et:
            #     et.execute(r' -overwrite_original -tagsFromFile ' + os.path.abspath(inphoto) + ' ' + os.path.abspath(outphoto))

            try:
                # self.PreProcessLog.append(str(modpath + os.sep + r'exiftool.exe') + ' ' + inphoto + ' ' + outphoto)
                subprocess._cleanup()
                data = subprocess.run(
                    args=[modpath + os.sep + r'exiftool.exe', '-m', r'-ifd0:imagewidth', r'-ifd0:imageheight', os.path.abspath(inphoto)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE, startupinfo=si).stdout.decode("utf-8")
                data = [line.strip().split(':') for line in data.split('\r\n') if line.strip()]
                #ypr = data[0][1].split()
                #
                ypr = [0.0] * 3
                # ypr[0] = abs(float(self.conv.META_PAYLOAD["ATT_Q0"][1]))
                # ypr[1] = -float(self.conv.META_PAYLOAD["ATT_Q1"][1])
                # ypr[2] = ((float(self.conv.META_PAYLOAD["ATT_Q2"][1]) + 180.0) % 360.0)
                ypr[0] = abs(float(self.conv.META_PAYLOAD["ATT_Q0"][1]) % 360.0)
                ypr[1] = abs((float(self.conv.META_PAYLOAD["ATT_Q1"][1]) + 180.0) % 360.0)
                ypr[2] = abs((float(-self.conv.META_PAYLOAD["ATT_Q2"][1])))

                if self.conv.META_PAYLOAD["ARRAY_TYPE"][1] != 0: 
                    ypr = AdjustYPR(int(self.conv.META_PAYLOAD["ARRAY_TYPE"][1]),int(self.conv.META_PAYLOAD["ARRAY_ID"][1]),ypr)
                    ypr = CurveAdjustment(int(self.conv.META_PAYLOAD["ARRAY_TYPE"][1]),int(self.conv.META_PAYLOAD["ARRAY_ID"][1]),ypr)

                w = int(data[0][1])
                h = int(data[1][1])
                model = self.findCameraModel(w * h)
                centralwavelength = [self.lensvals[3:6][0][1], self.lensvals[3:6][1][1], self.lensvals[3:6][2][1]]
                bandname = [self.lensvals[3:6][0][0], self.lensvals[3:6][1][0], self.lensvals[3:6][2][0]]

                fnumber = self.lensvals[0][1]
                focallength = self.lensvals[0][0]
                lensmodel = self.lensvals[0][0] + "mm"

            except Exception as e:
                exc_type, exc_obj,exc_tb = sys.exc_info()
                ypr = None
                print(e)
                print("Line: " + str(exc_tb.tb_lineno))
                print("Warning: No userdefined tags detected")

                # subprocess.call(
                #     [modpath + os.sep + r'exiftool.exe', '-m', r'-overwrite_original', r'-tagsFromFile',
                #      os.path.abspath(inphoto),
                #      # r'-all:all<all:all',
                #      os.path.abspath(outphoto)], startupinfo=si)
            finally:

                if ypr is not None:
                    try:
                        dto = datetime.datetime.fromtimestamp(self.conv.META_PAYLOAD["TIME_SECS"][1])
                        m, s = divmod(self.conv.META_PAYLOAD["GNSS_TIME_SECS"][1], 60)
                        h, m = divmod(m, 60)
                        # dd, h = divmod(h, 24)

                        if self.PreProcessVignette.isChecked():
                            fil_str = self.PreProcessFilter.currentText()[:3]
                            if "/" in self.PreProcessFilter.currentText():
                                fil_names = self.PreProcessFilter.currentText().split("/")
                                fil_str = fil_names[0] + "-" + fil_names[1] + "-" + fil_names[2]
                            DFV = self.get_dark_frame_value(fil_str)
                        else:
                            DFV = None

                        altref = 0 if self.conv.META_PAYLOAD["GNSS_HEIGHT_SEA_LEVEL"][1] >= 0 else 1
                        if '' not in bandname:
                            exifout = subprocess.run(
                                [modpath + os.sep + r'exiftool.exe',  r'-config', modpath + os.sep + r'mapir.config', '-m', r'-overwrite_original', r'-tagsFromFile',
                                 os.path.abspath(inphoto),
                                 r'-all:all<all:all',
                                 r'-ifd0:make=MAPIR',
                                 r'-Model=' + model,
                                 #r'-ifd0:blacklevelrepeatdim=' + str(1) + " " + str(1),
                                 #r'-ifd0:blacklevel=0',
                                 r'-ModelType=perspective',
                                 r'-BlackCurrent=' + str(str(DFV) + ', ' + str(DFV) + ', ' + str(DFV)),
                                 r'-Yaw=' + str(ypr[0]),
                                 r'-Pitch=' + str(ypr[1]),
                                 r'-Roll=' + str(ypr[2]),
                                 r'-CentralWavelength=' + str(float(centralwavelength[0])) + ', ' + str(float(centralwavelength[1])) + ', ' + str(float(centralwavelength[2])),
                                 r'-bandname=' + str(bandname[0] + ', ' + bandname[1] + ', ' + bandname[2]),
                                 # r'-bandname2=' + str( r'F' + self.BandNames.get(bandname, [0,0,0])[1]),
                                 # r'-bandname3=' + str( r'F' + self.BandNames.get(bandname, [0,0,0])[2]),

                                 r'-WavelengthFWHM=' +str( self.lensvals[3:6][0][2] + ', ' + self.lensvals[3:6][1][2] + ', ' + self.lensvals[3:6][2][2]),
                                 r'-GPSLatitude="' + str(self.conv.META_PAYLOAD["GNSS_LAT_HI"][1]) + r'"',

                                 r'-GPSLongitude="' + str(self.conv.META_PAYLOAD["GNSS_LON_HI"][1]) + r'"',
                                 r'-GPSTimeStamp="{hour=' + str(h) + r',minute=' + str(m) + r',second=' + str(s) + r'}"',
                                 r'-GPSAltitude=' + str(self.conv.META_PAYLOAD["GNSS_HEIGHT_SEA_LEVEL"][1]),
                                 # r'-GPSAltitudeE=' + str(self.conv.META_PAYLOAD["GNSS_HEIGHT_ELIPSOID"][1]),
                                 r'-GPSAltitudeRef#=' + str(altref),
                                 r'-GPSTimeStampS=' + str(self.conv.META_PAYLOAD["GNSS_TIME_NSECS"][1]),
                                 r'-GPSLatitudeRef=' + self.conv.META_PAYLOAD["GNSS_VELOCITY_N"][1],
                                 r'-GPSLongitudeRef=' + self.conv.META_PAYLOAD["GNSS_VELOCITY_E"][1],
                                 r'-GPSLeapSeconds=' + str(self.conv.META_PAYLOAD["GNSS_LEAP_SECONDS"][1]),
                                 r'-GPSTimeFormat=' + str(self.conv.META_PAYLOAD["GNSS_TIME_FORMAT"][1]),
                                 r'-GPSFixStatus=' + str(self.conv.META_PAYLOAD["GNSS_FIX_STATUS"][1]),
                                 r'-DateTimeOriginal=' + dto.strftime("%Y:%m:%d %H:%M:%S"),
                                 r'-SubSecTimeOriginal=' + str(self.conv.META_PAYLOAD["TIME_NSECS"][1]),
                                 r'-ExposureTime=' + str(self.conv.META_PAYLOAD["EXP_TIME"][1]),
                                 r'-ExposureMode#=' + str(self.conv.META_PAYLOAD["EXP_MODE"][1]),
                                 r'-ISO=' + str(self.conv.META_PAYLOAD["ISO_SPEED"][1]),
                                 r'-Lens=' + lensmodel,
                                 r'-FocalLength=' + focallength,
                                 r'-fnumber=' + fnumber,
                                 r'-ArrayID=' + str(self.conv.META_PAYLOAD["ARRAY_TYPE"][1]),
                                 r'-ArrayType=' + str(self.conv.META_PAYLOAD["ARRAY_ID"][1]),
                                 r'-FocalPlaneXResolution=' + str(6.14),
                                 r'-FocalPlaneYResolution=' + str(4.60),
                                 os.path.abspath(outphoto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, startupinfo=si).stderr.decode("utf-8")
                        else:

                            exifout = subprocess.run(
                                [modpath + os.sep + r'exiftool.exe', r'-config', modpath + os.sep + r'mapir.config',
                                 '-m', r'-overwrite_original', r'-tagsFromFile',
                                 os.path.abspath(inphoto),
                                 r'-all:all<all:all',
                                 r'-ifd0:make=MAPIR',
                                 r'-Model=' + model,
                                 r'-ModelType=perspective',
                                 r'-BlackCurrent=' + str(DFV),
                                 r'-Yaw=' + str(ypr[0]),
                                 r'-Pitch=' + str(ypr[1]),
                                 r'-Roll=' + str(ypr[2]),
                                 r'-CentralWavelength=' + str(float(centralwavelength[0])),
                                 #r'-ifd0:blacklevelrepeatdim=' + str(1) + " " +  str(1),
                                 #r'-ifd0:blacklevel=0',
                                 # r'-BandName="{band1=' + str(self.BandNames[bandname][0]) + r'band2=' + str(self.BandNames[bandname][1]) + r'band3=' + str(self.BandNames[bandname][2]) + r'}"',
                                 r'-bandname=' + bandname[0],
                                 r'-WavelengthFWHM=' + str(self.lensvals[3:6][0][2]),
                                 r'-GPSLatitude="' + str(self.conv.META_PAYLOAD["GNSS_LAT_HI"][1]) + r'"',

                                 r'-GPSLongitude="' + str(self.conv.META_PAYLOAD["GNSS_LON_HI"][1]) + r'"',
                                 r'-GPSTimeStamp="{hour=' + str(h) + r',minute=' + str(m) + r',second=' + str(
                                     s) + r'}"',
                                 r'-GPSAltitude=' + str(self.conv.META_PAYLOAD["GNSS_HEIGHT_SEA_LEVEL"][1]),
                                 # r'-GPSAltitudeE=' + str(self.conv.META_PAYLOAD["GNSS_HEIGHT_ELIPSOID"][1]),
                                 r'-GPSAltitudeRef#=' + str(altref),
                                 r'-GPSTimeStampS=' + str(self.conv.META_PAYLOAD["GNSS_TIME_NSECS"][1]),
                                 r'-GPSLatitudeRef=' + self.conv.META_PAYLOAD["GNSS_VELOCITY_N"][1],
                                 r'-GPSLongitudeRef=' + self.conv.META_PAYLOAD["GNSS_VELOCITY_E"][1],
                                 r'-GPSLeapSeconds=' + str(self.conv.META_PAYLOAD["GNSS_LEAP_SECONDS"][1]),
                                 r'-GPSTimeFormat=' + str(self.conv.META_PAYLOAD["GNSS_TIME_FORMAT"][1]),
                                 r'-GPSFixStatus=' + str(self.conv.META_PAYLOAD["GNSS_FIX_STATUS"][1]),
                                 r'-DateTimeOriginal=' + dto.strftime("%Y:%m:%d %H:%M:%S"),
                                 r'-SubSecTimeOriginal=' + str(self.conv.META_PAYLOAD["TIME_NSECS"][1]),
                                 r'-ExposureTime=' + str(self.conv.META_PAYLOAD["EXP_TIME"][1]),
                                 r'-ExposureMode#=' + str(self.conv.META_PAYLOAD["EXP_MODE"][1]),
                                 r'-ISO=' + str(self.conv.META_PAYLOAD["ISO_SPEED"][1]),
                                 r'-Lens=' + lensmodel,
                                 r'-FocalLength=' + focallength,
                                 r'-fnumber=' + fnumber,
                                 r'-ArrayID=' + str(self.conv.META_PAYLOAD["ARRAY_TYPE"][1]),
                                 r'-ArrayType=' + str(self.conv.META_PAYLOAD["ARRAY_ID"][1]),
                                 r'-FocalPlaneXResolution=' + str(6.14),
                                 r'-FocalPlaneYResolution=' + str(4.60),
                                 os.path.abspath(outphoto)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, startupinfo=si).stderr.decode("utf-8")
                        print(exifout)

                    except Exception as e:
                        exc_type, exc_obj,exc_tb = sys.exc_info()
                        if self.MapirTab.currentIndex() == 0:
                            self.PreProcessLog.append("Error: " + str(e) + ' Line: ' + str(exc_tb.tb_lineno))
                        elif self.MapirTab.currentIndex() == 1:
                            self.CalibrationLog.append("Error: " + str(e) + ' Line: ' + str(exc_tb.tb_lineno))
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

    def on_AnalyzeInButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            folder = QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read())
            self.AnalyzeInput.setText(folder)
            self.AnalyzeOutput.setText(folder)
            try:
                folders = glob.glob(self.AnalyzeInput.text() + os.sep + r'*' + os.sep)
                filecount = len(glob.glob(folders[0] + os.sep + r'*'))
                for fold in folders:
                    if filecount == len(glob.glob(fold + os.sep + r'*')):
                        pass
                    else:
                        raise ValueError("Sub-Directories must contain the same number of files.")
            except ValueError as ve:
                print("Error: " + ve)
                return 256
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.AnalyzeInput.text())

    def on_AnalyzeOutButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.AnalyzeOutput.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.AnalyzeOutput.text())
    def on_AnalyzeButton_released(self):
        self.kcr = KernelConfig.KernelConfig(self.AnalyzeInput.text())
        for file in self.kcr.getItems():
            self.analyze_bands.append(file.split(os.sep)[-2])
        self.BandOrderButton.setEnabled(True)
        self.AlignButton.setEnabled(True)

    def on_PrefixBox_toggled(self):
        if self.PrefixBox.isChecked():
            self.Prefix.setEnabled(True)
        else:
            self.Prefix.setEnabled(False)
    def on_SuffixBox_toggled(self):
        if self.SuffixBox.isChecked():
            self.Suffix.setEnabled(True)
        else:
            self.Suffix.setEnabled(False)
    def on_LightRefBox_toggled(self):
        if self.LightRefBox.isChecked():
            self.LightRef.setEnabled(True)
        else:
            self.LightRef.setEnabled(False)
    def on_AlignmentPercentageBox_toggled(self):
        if self.AlignmentPercentageBox.isChecked():
            self.AlignmentPercentage.setEnabled(True)
        else:
            self.AlignmentPercentage.setEnabled(False)
    def on_BandOrderButton_released(self):
        if self.Bandwindow == None:
            self.Bandwindow = BandOrder(self, self.kcr.getItems())
        self.Bandwindow.resize(385, 205)
        self.Bandwindow.exec_()
        self.kcr.orderRigs(order=self.rdr)
        self.kcr.createCameraRig()
    def on_AlignButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            cmralign = [QtWidgets.QFileDialog.getOpenFileName(directory=instring.read())[0],]
            instring.truncate(0)
            instring.seek(0)
            instring.write(cmralign[0])
        if self.PrefixBox.isChecked():
            cmralign.append(r'-prefix')
            cmralign.append(self.Prefix.text())
        if self.SuffixBox.isChecked():
            cmralign.append(r'-suffix')
            cmralign.append(self.Suffix.text())
        if self.NoVignettingBox.isChecked():
            cmralign.append(r'-novignetting')
        if self.NoExposureBalanceBox.isChecked():
            cmralign.append(r'-noexposurebalance')
        if self.NoExposureBalanceBox.isChecked():
            cmralign.append(r'-noexposurebalance')
        if self.ForceAlignmentBox.isChecked():
            cmralign.append(r'-realign')
        if self.SeperateFilesBox.isChecked():
            cmralign.append(r'-separatefiles')
        if self.SeperateFoldersBox.isChecked():
            cmralign.append(r'-separatefolders')
        if self.SeperatePagesBox.isChecked():
            cmralign.append(r'-separatepages')
        if self.LightRefBox.isChecked():
            cmralign.append(r'-variablelightref')
            cmralign.append(self.LightRef.text())
        if self.AlignmentPercentageBox.isChecked():
            cmralign.append(r'-alignframepct')
            cmralign.append(self.AlignmentPercentage.text())
        cmralign.append(r'-i')
        cmralign.append(self.AnalyzeInput.text())
        cmralign.append(r'-o')
        cmralign.append(self.AnalyzeOutput.text())
        cmralign.append(r'-c')
        cmralign.append(self.AnalyzeInput.text() + os.sep + "mapir_kernel.camerarig")
        subprocess.call(cmralign)

    # def on_DarkCurrentInputButton_released(self):
    #     with open(modpath + os.sep + "instring.txt", "r+") as instring:
    #         self.DarkCurrentInput.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
    #         instring.truncate(0)
    #         instring.seek(0)
    #         instring.write(self.DarkCurrentInput.text())
    # def on_DarkCurrentOutputButton_released(self):
    #     with open(modpath + os.sep + "instring.txt", "r+") as instring:
    #         self.DarkCurrentOutput.setText(QtWidgets.QFileDialog.getExistingDirectory(directory=instring.read()))
    #         instring.truncate(0)
    #         instring.seek(0)
    #         instring.write(self.DarkCurrentOutput.text())
    # def on_DarkCurrentGoButton_released(self):
    #     folder1 = []
    #     folder1.extend(glob.glob(self.DarkCurrentInput.text() + os.sep + "*.tif?"))
    #     for img in folder1:
    #         QtWidgets.QApplication.processEvents()
    #         self.KernelLog.append("Updating " + str(img))
    #         subprocess.call(
    #             [modpath + os.sep + r'exiftool.exe', '-m', r'-overwrite_original', r'-ifd0:blacklevelrepeatdim=2 2',  img], startupinfo=si)
    #
    #     self.KernelLog.append("Finished updating")

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
