# -*- coding: utf-8 -*-
"""
 SelectorDockWidget

 A QGIS plugin for managing layer theme settings from the desktop.
 
        begin                : 2017-07-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com

 This program is free software; you can redistribute it and/or modify
 t under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
"""

import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout
from qgis.core import QgsProject
from qgis.gui import QgsExtentWidget
from qgis.utils import iface

# Load the UI file dynamically using uic
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'selector_dockwidget_base.ui'))


class SelectorDockWidget(QDockWidget, FORM_CLASS):
    """Main class for the Theme Selector dock widget."""
    
    def __init__(self, parent=None):
        """Constructor: Set up the UI and initialize attributes."""
        super().__init__(parent)
        self.setupUi(self)
        
        # Initialize the QgsExtentWidget
        self.extentWidget = QgsExtentWidget(self)
        
        # Connect it to the active map canvas
        self.extentWidget.setMapCanvas(iface.mapCanvas())
        
        # 2. Dynamically swap the placeholder widget 'coverageSelector' 
        # with our newly created QgsExtentWidget inside the layout
        if hasattr(self, 'coverageSelector') and self.coverageSelector.parentWidget():
            parent_layout = self.coverageSelector.parentWidget().layout()
            if parent_layout:
                # Find where coverageSelector sits in the layout grid and swap it
                index = parent_layout.indexOf(self.coverageSelector)
                if index != -1:
                    # Capture the grid parameters (row 1, col 0, colspan 4) automatically
                    row, column, row_span, column_span = parent_layout.getItemPosition(index)
                    parent_layout.removeWidget(self.coverageSelector)
                    self.coverageSelector.deleteLater()
                    
                    # Insert the native QGIS Extent Widget into its place
                    parent_layout.addWidget(self.extentWidget, row, column, row_span, column_span)

    def getAvailableThemes(self):
        """
        Retrieve and return the available map themes from the current 
        QGIS project.

        Returns:
            list: A list of available theme names.
        """
        return QgsProject.instance().mapThemeCollection().mapThemes()

    def getSelectedExtent(self):
        """
        Retrieve the extent currently selected by the user in the UI.

        Returns:
            QgsRectangle: The selected bounding box coordinates.
        """
        return self.extentWidget.outputExtent()

