import PyQt5.uic as uic
import os
from MAPIR_Enums import *
from PyQt5 import QtCore, QtGui, QtWidgets
A_EXP_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_A_Exposure.ui'))

M_EXP_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_M_Exposure.ui'))

#Class for handling Manual Exposure Settings
class M_EXP_Control(QtWidgets.QDialog, M_EXP_CLASS):
    parent = None
    _initial_ISO = None
    _initial_Shutter = None
    def __init__(self, parent=None):
        """Constructor."""
        super(M_EXP_Control, self).__init__(parent=parent)
        self.parent = parent

        self.setupUi(self)
        self.KernelShutterSpeed.blockSignals(True)
        self.KernelISO.blockSignals(True)
        buf = [0] * 512
        buf[0] = self.parent.SET_REGISTER_BLOCK_READ_REPORT
        buf[1] = eRegister.RG_CAMERA_SETTING.value
        buf[2] = eRegister.RG_SIZE.value

        res = self.parent.writeToKernel(buf)
        self.parent.regs = res[2:]
        self._initial_Shutter = shutter = self.parent.getRegister(eRegister.RG_SHUTTER.value)
        self.KernelShutterSpeed.setCurrentIndex(shutter - 1)
        self._initial_ISO = iso = self.parent.getRegister(eRegister.RG_ISO.value)
        self.KernelISO.setCurrentIndex(self.KernelISO.findText(str(iso) + "00"))

        self.KernelShutterSpeed.blockSignals(False)
        self.KernelISO.blockSignals(False)

    # def on_KernelShutterSpeed_currentIndexChanged(self):
    #
    #
    # def on_KernelISO_currentIndexChanged(self):

    def on_ModalSaveButton_released(self):

        new_kernel_shutter_speed = self.KernelShutterSpeed.currentIndex() + 1
        self.parent.write_register_value_to_kernel(eRegister.RG_SHUTTER, new_kernel_shutter_speed)

        new_iso = int(int(self.KernelISO.currentText()) / 100)
        self.parent.write_register_value_to_kernel(eRegister.RG_ISO, new_iso)

        self.close()

    def on_ModalCancelButton_released(self):
        # self.parent.write_register_value_to_kernel(eRegister.RG_SHUTTER, self._initial_Shutter)
        # self.parent.write_register_value_to_kernel(eRegister.RG_ISO, self._initial_ISO)
        self.close()
#Class for handling Auto Exposure Settings
class A_EXP_Control(QtWidgets.QDialog, A_EXP_CLASS):
    parent = None
    _initial_Algorithm = None
    _initial_MAX_Shutter = None
    _initial_MIN_Shutter = None
    _initial_MAX_ISO = None
    _initial_FSTOP = None
    _initial_GAIN = None
    _initial_SETPOINT = None
    def __init__(self, parent=None):
        """Constructor."""
        super(A_EXP_Control, self).__init__(parent=parent)
        self.parent = parent
        self.setupUi(self)

        self._initial_Algorithm = self.parent.read_register_value_from_kernel(eRegister.RG_AE_SELECTION)
        self.AutoAlgorithm.setCurrentIndex(self._initial_Algorithm)
        self.AutoMaxShutter.setCurrentIndex(self.parent.read_register_value_from_kernel(eRegister.RG_AE_MAX_SHUTTER))
        self.AutoMinShutter.setCurrentIndex(self.parent.read_register_value_from_kernel(eRegister.RG_AE_MIN_SHUTTER))
        self.AutoMaxISO.setCurrentIndex(self.parent.read_register_value_from_kernel(eRegister.RG_AE_MAX_GAIN))
        self.AutoFStop.setCurrentIndex(self.parent.read_register_value_from_kernel(eRegister.RG_AE_F_STOP))
        self.AutoGain.setCurrentIndex(self.parent.read_register_value_from_kernel(eRegister.RG_AE_GAIN))
        self.AutoSetpoint.setCurrentIndex(self.parent.read_register_value_from_kernel(eRegister.RG_AE_SETPOINT))

    def on_ModalSaveButton_released(self):
        self.parent.write_register_value_to_kernel(eRegister.RG_AE_SELECTION, self.AutoAlgorithm.currentIndex())
        self.parent.write_register_value_to_kernel(eRegister.RG_AE_MAX_SHUTTER, self.AutoMaxShutter.currentIndex())
        self.parent.write_register_value_to_kernel(eRegister.RG_AE_MIN_SHUTTER, self.AutoMinShutter.currentIndex())
        self.parent.write_register_value_to_kernel(eRegister.RG_AE_MAX_GAIN, self.AutoMaxISO.currentIndex())
        self.parent.write_register_value_to_kernel(eRegister.RG_AE_F_STOP, self.AutoFStop.currentIndex())
        self.parent.write_register_value_to_kernel(eRegister.RG_AE_GAIN, self.AutoGain.currentIndex())
        self.parent.write_register_value_to_kernel(eRegister.RG_AE_SETPOINT, self.AutoSetpoint.currentIndex())
        self.close()

    def on_ModalCancelButton_released(self):


        self.close()