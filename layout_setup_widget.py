import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.core import QgsProject, QgsPrintLayout

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
    
        # DIAGNOSTIC 1: Force a pop-up to prove the button click is working
        QMessageBox.information(self, "Debug", "The runButton click signal was successfully received!")
        
        # 1. Grab the layout
        selected_layout = self.layoutComboBox.currentLayout()
        
        # DIAGNOSTIC 2: Print what was grabbed to the QGIS Python Console
        print(f"DEBUG: Selected layout is: {selected_layout}")
        print(f"DEBUG: Coverage layer is: {self.coverage_layer}")
        
        if not selected_layout:
            QMessageBox.warning(self, "Warning", "No layout selected or available.")
            return
            
        if not isinstance(selected_layout, QgsPrintLayout):
            QMessageBox.critical(self, "Invalid Layout Type", "Not a standard Print Layout.")
            return 
            
            
        # 4. Safely execute the external script/class
        try:
            my_runner = layoutSetup(selected_layout, self.coverage_layer)
            
            QMessageBox.information(self, "Success", "Layout configuration completed successfully!")
            self.accept() # Automatically closes the dialog window on success
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Execution Error", 
                f"An error occurred while setting up the layout:\n\n{str(e)}"
            )
    
    
    
    
    
