import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsProject

from .layout_setup import layoutSetup

# Get the path to the UI file (assumes it is in the same directory as this script)
UI_PATH = os.path.join(os.path.dirname(__file__), 'layout_setup.ui')

class LayoutRunnerDialog(QDialog):
    def __init__(self, coverage_layer, parent=None):
        super().__init__(parent)
        # Load the UI file dynamically
        uic.loadUi(UI_PATH, self)
        self.coverage_layer = coverage_layer
        
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
            
        # 3. Ensure the layout is a Print Layout (and not a Report) 
        # because reports do not share the exact same .atlas() configurations
        if not isinstance(selected_layout, QgsPrintLayout):
            QMessageBox.critical(
                self, 
                "Invalid Layout Type", 
                "The chosen layout is not a standard Print Layout. Maps cannot be managed via Atlas rules here."
            )
            return 
            
        # 4. Pass the selected layout into your target script or function
        layoutSetup(selected_layout, self.coverage_layer)

    


