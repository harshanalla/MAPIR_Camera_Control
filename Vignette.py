import os
from PyQt5 import QtCore, QtGui, QtWidgets
import PyQt5.uic as uic
import cv2
import copy
import numpy as np
VIGNETTE_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_vignette.ui'))

class Vignette(QtWidgets.QDialog, VIGNETTE_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(Vignette, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)
    def on_VignetteSaveButton_released(self):
        c1 = float(self.VignetteCoef.text())
        h, w = self.parent.display_image_original.shape[:2]
        pict = cv2.imread(self.parent.KernelBrowserFile.text(), -1)
        if pict.dtype == np.dtype("uint16"):
            pict = pict / 65535.0
            pict = pict * 255.0
            pict = pict.astype("uint8")
        mx = np.percentile(pict, 98)
        mn = np.percentile(pict, 2)
        if len(pict.shape) > 2:
            pict = cv2.cvtColor(pict, cv2.COLOR_BGR2RGB)
        else:
            pict = cv2.cvtColor(pict, cv2.COLOR_GRAY2RGB)
        pict[pict > mx] = mx
        pict[pict < mn] = mn
        cx = w/2
        cy = h/2
        try:
            for y in range(self.parent.display_image_original.shape[:2][0]):
                for x in range(self.parent.display_image_original.shape[:2][1]):
                    dx = (x - cx)/cx
                    dy = (y - cy)/cy

                    r2 = (dx*dx) + (dy*dy)

                    pict[y, x] = (pict[y,x] * (1 + (c1 * r2)))
            self.parent.display_image_original = pict
            self.parent.display_image = pict

            if self.parent.calcwindow:
                self.parent.calcwindow.processIndex()
            if self.parent.LUTwindow:
                self.parent.LUTwindow.RasterMin.setText(str(round(self.parent.LUT_Min, 2)))
                self.parent.LUTwindow.RasterMax.setText(str(round(self.parent.LUT_Max, 2)))
                self.parent.LUTwindow.processLUT()
            self.parent.applyLUT()
            self.parent.applyRaster()
            self.parent.stretchView()
            # if len(pict.shape) > 2:
            #     pict = cv2.cvtColor(pict, cv2.COLOR_BGR2RGB)
            #     img2 = QtGui.QImage(pict, w, h, w * 3, QtGui.QImage.Format_RGB888)
            # else:
            #     img2 = QtGui.QImage(pict, w, h, w , QtGui.QImage.Format_Grayscale8)

        except Exception as e:
            print(e)
    def on_VignetteCloseButton_released(self):
        self.close()