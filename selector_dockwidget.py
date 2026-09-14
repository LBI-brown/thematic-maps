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
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsProject
from qgis.gui import QgsExtentWidget  # 1. Import the QGIS Extent Widget
from qgis.utils import iface          # Import iface to access the active map canvas

# Load the UI file dynamically using uic
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
                                            'selector_dockwidget_base.ui'))


class SelectorDockWidget(QDockWidget, FORM_CLASS):
    """Main class for the Theme Selector dock widget."""
    
    def __init__(self, parent=None):
        """Constructor: Set up the UI and initialize attributes."""
        super().__init__(parent)
        self.setupUi(self)

        # 2. Initialize the QgsExtentWidget
        self.extentWidget = QgsExtentWidget(self)
        
        # 3. Connect it to the map canvas so "Draw on Canvas" functions work
        self.extentWidget.setMapCanvas(iface.mapCanvas())
        
        # 4. Add it to an existing layout in your UI.
        # inside your selector_dockwidget_base.ui file.
        if hasattr(self, 'coverageSelector'):
            self.verticalLayout.addWidget(self.extentWidget)
        else:
            # Fallback if no specific layout name matches, creates a default layout
            from qgis.PyQt.QtWidgets import QVBoxLayout
            if not self.widget().layout():
                self.widget().setLayout(QVBoxLayout())
            self.widget().layout().addWidget(self.extentWidget)

    def getAvailableThemes(self):
        """
        Retrieve and return the available map themes from the current 
        QGIS project.

        Returns:
            list: A list of available theme names.
        """
        return QgsProject.instance().mapThemeCollection().mapThemes()

     def get_user_extent(self):
        # 2. Extract the chosen bounding box as a QgsRectangle
        chosen_extent = self.extent_widget.outputExtent()
        return chosen_extent
