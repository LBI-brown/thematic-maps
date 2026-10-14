import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsProject

from .layout_setup import layoutSetup

# Get the path to the UI file (assumes it is in the same directory as this script)
UI_PATH = os.path.join(os.path.dirname(__file__), 'layout_setup.ui')

class LayoutRunnerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the UI file dynamically
        uic.loadUi(UI_PATH, self)
        
        # Connect the QgsLayoutComboBox to the active QGIS project
        self.layoutComboBox.setLayoutManager(QgsProject.instance().layoutManager())
        
        # Connect the button click signal to your execution method
        self.runButton.clicked.connect(self.run_my_script)

    def run_my_script(self):
        # 1. Grab the actual QgsPrintLayout object selected by the user
        selected_layout = self.layoutComboBox.currentLayout()
        
        # 2. Check if a layout is actually selected (handles empty project scenarios)
        if not selected_layout:
            QMessageBox.warning(self, "Warning", "No layout selected or available.")
            return
            
        # 3. Pass the selected layout into your target script or function
        self.layoutSetup(selected_layout)

    


