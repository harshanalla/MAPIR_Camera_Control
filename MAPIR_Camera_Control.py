import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from MAPIR_Processing_dockwidget import *


if __name__ == "__main__":
        try:
                app = QApplication(sys.argv)
                myapp = MAPIR_ProcessingDockWidget()
                myapp.show()

        except:
                pass
        sys.exit(app.exec_())
