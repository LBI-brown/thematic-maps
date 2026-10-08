# -*- coding: utf-8 -*-
"""
ThematicMaps

A QGIS plugin
This plugin maintains themeatic maps in a layout Atlas from layer theme settings

    begin                : 2026-09-01
    git sha              : $Format:%H$
    copyright            : (C) 2026 by Nicholas Brown
    email                : nick@browndesign.co.uk

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""
# pylint: disable = no-name-in-module

import os
from qgis.utils import iface
from qgis.PyQt.QtCore import (
    QSettings,
    QTranslator,
    QCoreApplication,
    QFileInfo,
    Qt,
    QSize,
    QVariant
)
from qgis.PyQt.QtWidgets import (
    QInputDialog,
    QMessageBox
)
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.core import QgsProject, QgsMapThemeCollection, QgsLayoutItemMap, QgsVectorLayer, QgsField, QgsGeometry, QgsFeature, QgsFeatureRequest


# Import the code for the DockWidget
from .thematic_maps_dockwidget import ThematicMapsDockWidget

# Define your target layer configuration
TARGET_LAYER_ID = "coverage_id_001"
LAYER_NAME = "COVERAGE"
GEOMETRY_TYPE = "Polygon"  # Options: 'Point', 'LineString', 'Polygon', 'None'
CRS = "EPSG:4326"
LAYER_THEME_FIELD_NAME = "theme_name"
LAYER_BOOKMARK_FIELD_NAME = "bookmark_name"
LAYER_BOOKMARK_FIELD_ID = "bookmark_id"

class ThematicMaps:
    """QGIS Plugin Implementation.
    """

    def __init__(self, iface):
        """Constructor."""
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'{locale}.qm')
        
        print(f"Detected locale: {locale}")

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dockwidget = ThematicMapsDockWidget()
        self.action = self.dockwidget.toggleViewAction()

        # Remember size of the dockwidget
        settings = QSettings()
        self.dockwidget.resize(settings.value("ThematicMaps/size",
                                              QSize(300, 200)))

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('ThematicMaps', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # Add the dock widget to QGIS interface
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.show()

        #create layer if not existing
        self.coverage_layer()
            
        # Initialize widget functionality
        self.populate()
        self.connect_signals()

       

    def coverage_layer(self):

        project = QgsProject.instance()
        layer = project.mapLayer(TARGET_LAYER_ID)

        if layer:
            print(f"COVERAGE Layer called and found")
        else:
            print(f"Coverage Layer with ID '{TARGET_LAYER_ID}' not found. Creating a new one...")
            
            # 2. Create a new memory (scratch) layer
            # Format URI syntax: "Type?crs=EPSG:xxxx"
            # uri = f"{GEOMETRY_TYPE}?crs={CRS}" DEPRECATED
            layer = QgsVectorLayer(GEOMETRY_TYPE, LAYER_NAME, "memory")
            layer.setCrs(project.crs())
            
            # 3. Set the custom layer ID
            # Note: QGIS automatically appends a random string to custom IDs to ensure absolute uniqueness
            layer.setId(TARGET_LAYER_ID)
            
            # 4. Add a new field to the layer
            # We use dataProvider() to add fields before the layer is loaded into the project registry
            provider = layer.dataProvider()
            theme_name_field = QgsField(LAYER_THEME_FIELD_NAME, QVariant.String, len=200)
            bookmark_name_field = QgsField(LAYER_BOOKMARK_FIELD_NAME, QVariant.String, len=200)
            bookmark_id_field = QgsField(LAYER_BOOKMARK_FIELD_ID, QVariant.String, len=200)
            provider.addAttributes([theme_name_field,bookmark_name_field,bookmark_id_field])
            
            # Update the layer layout to recognize the new field structure
            layer.updateFields()

            # 2. Access the layer's renderer and default symbol
            renderer = layer.renderer()
            symbol = renderer.symbol()
            symbol_layer = symbol.symbolLayer(0)  # Gets the primary QgsSimpleFillSymbolLayer
            
            # 3. Modify the symbol properties
            # Set the stroke (line) color to solid red
            symbol_layer.setStrokeColor(QColor("red"))
            
            # Set the fill color to transparent (Alpha channel = 0)
            symbol_layer.setFillColor(QColor(0, 0, 0, 0))
            
            # Make the stroke line thicker (e.g., 0.6 mm) for better visibility
            symbol_layer.setStrokeWidth(0.6)
            
            # 5. Add the newly created layer to the QGIS Project
            project.addMapLayer(layer)
            layer_node = project.layerTreeRoot().findLayer(layer.id())
            layer_node.setItemVisibilityChecked(True)
            layer.triggerRepaint()
            
            #add existing themes as features
            # Start editing session
            layer.startEditing()
            themes = self.dockwidget.getAvailableThemes()
            #iterate through themes adding features
            new_features = []
            field_index = layer.fields().indexOf(LAYER_THEME_FIELD_NAME)
            for i, value in enumerate(themes):
                # Initialize a clean feature
                fet = QgsFeature(layer.fields())
                fet.setAttribute(field_index, value)
                new_features.append(fet)
            layer.addFeatures(new_features)    
            # 3. Save changes
            layer.commitChanges()

            print(f"Successfully created, added and populated COVERAGE layer: {layer.name()} with ID: {layer.id()}") 

        return layer
        
    #when bookmark changed in combo box update corresponding theme feature in layer
    def update_coverage_layer_extents(self):
        
        layer=self.coverage_layer()
        manager = QgsProject.instance().bookmarkManager()
        theme = self.dockwidget.PresetComboBox.currentText()    
        print(f"current theme: '{theme}'")
        bookmark = self.dockwidget.BookmarkComboBox.currentText()  
        print(f"current bookmark: '{bookmark}'")

        # Find bookmark matching the name 
        bookmark_match = next((b for b in manager.bookmarks() if b.name() == bookmark), None) 

        # Check if we actually have a valid bookmark object before getting the extent
        if bookmark_match is not None:
            geom = QgsGeometry.fromRect(bookmark_match.extent())
            #set canvas extent to bookmark extent
            canvas = iface.mapCanvas()
            canvas.setExtent(geom.boundingBox())
            canvas.refresh() 

             #get field index of bookmark field
            field_idx1 = layer.fields().lookupField(LAYER_BOOKMARK_FIELD_NAME)
            field_idx2 = layer.fields().lookupField(LAYER_BOOKMARK_FIELD_ID)
            layer.startEditing()
        
            try:
                #get first matching feature with theme name
                first_match = self.coverage_feature(theme)
                #change geometry extents if theme already existing   
                layer.changeAttributeValue(first_match.id(), field_idx1, bookmark_match.name())
                layer.changeAttributeValue(first_match.id(), field_idx2, bookmark_match.id())
                layer.changeGeometry(first_match.id(),geom)
                print(f"Feature '{first_match[LAYER_THEME_FIELD_NAME]}' updated successfully.")     
            except:
                print(f"No matching theme found")
            finally:
                layer.commitChanges() 
        else:
            print("Error: No bookmarks found in the manager at all.")

    #return layer feature from theme name
    def coverage_feature(self,theme):
        layer=self.coverage_layer()
        # Create a feature request with a filter expression
        request = QgsFeatureRequest().setFilterExpression(f'"{LAYER_THEME_FIELD_NAME}" = \'{theme}\'')
        # Use an iterator to grab the first match
        features = layer.getFeatures(request)
        first_match = next(features) or None
        return first_match
    
    

    def connect_signals(self):
        """Connect various signals and slots."""
        QgsProject.instance().cleared.connect(self.clear)
        QgsProject.instance().readProject.connect(self.populate)

        #self.iface.mapCanvas().layersChanged.connect(self.set_combo_theme)
        # Connect to map theme collection changes
        QgsProject.instance().bookmarkManager().bookmarkChanged.connect(self.bookmark_updates)
        QgsProject.instance().bookmarkManager().bookmarkRemoved.connect(self.bookmark_updates)
        QgsProject.instance().bookmarkManager().bookmarkAdded.connect(self.populate)
        QgsProject.instance().mapThemeCollection().projectChanged.connect(self.populate)
        
        self.dockwidget.PresetComboBox.currentIndexChanged.connect(self.apply_selected_theme)
        self.dockwidget.BookmarkComboBox.currentIndexChanged.connect(self.update_coverage_layer_extents)
        self.dockwidget.pushButton_replace.clicked.connect(self.replace_maptheme)
        self.dockwidget.pushButton_add.clicked.connect(self.add_maptheme)
        self.dockwidget.pushButton_remove.clicked.connect(self.remove_maptheme)
        self.dockwidget.pushButton_rename.clicked.connect(self.rename_maptheme)
        
        # Disable buttons if no layers present
        if len(QgsProject.instance().mapLayers()) == 0:
            self.disable_buttons()

    def clear(self):
        """Clear combobox and disable buttons."""
        self.dockwidget.PresetComboBox.clear()
        self.dockwidget.BookmarkComboBox.clear()
        self.disable_buttons()

    def populate(self):
        """Populate comboboxes with available themes and bookmarks"""
        print(f"populate fnc called")
        self.clear()
        themes = self.dockwidget.getAvailableThemes()
        bookmarks = self.dockwidget.getAvailableBookmarks()

        for setting in themes:
            self.dockwidget.PresetComboBox.addItem(setting)

        for bmk in bookmarks:
            self.dockwidget.BookmarkComboBox.addItem(f"{bmk.name()}", bmk.id() )
        
        self.set_combo_theme()
        self.enable_buttons()

    #set combobox theme to match theme showing or blank
    def set_combo_theme(self):
        theme = self.get_current_theme()
        bookmark_for_theme = self.bookmark_lookup(theme)
        try:
            theme_index = self.dockwidget.PresetComboBox.findText(theme, Qt.MatchFixedString)
            self.dockwidget.PresetComboBox.setCurrentIndex(theme_index)
            bmk_index = self.dockwidget.BookmarkComboBox.findText(bookmark_for_theme, Qt.MatchFixedString)
            self.dockwidget.BookmarkComboBox.setCurrentIndex(bmk_index)
        except:
            print(f"no matching theme")
            self.dockwidget.PresetComboBox.setCurrentIndex(-1)
            self.dockwidget.BookamarkComboBox.setCurrentIndex(-1)
           

    def apply_selected_theme(self):
        """Apply the selected theme based on the current combobox selection."""
        theme_name = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        QgsProject.instance().mapThemeCollection().applyTheme(theme_name, root, model)
        #update bookmark combo to bookmark associated with theme
        self.set_combo_theme()    

    def remove_maptheme(self):
        """Remove the selected theme."""
        theme = self.dockwidget.PresetComboBox.currentText()
        QgsProject.instance().mapThemeCollection().removeMapTheme(theme)
        feature = self.coverage_feature(theme)
        layer = self.coverage_layer()
        layer.startEditing()
        layer.deleteFeature(feature.id())
        layer.commitChanges()
        layer.triggerRepaint()
        self.populate()

    def replace_maptheme(self):
        """Replace the current theme with a new one."""
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
        QgsProject.instance().mapThemeCollection().update(theme, rec)

    def add_maptheme(self):
        """Add a new theme."""
        map_collection = QgsProject.instance().mapThemeCollection()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        # Check if the current state already exists
        current_state = map_collection.createThemeFromCurrentState(root, model)
        for existing_theme in map_collection.mapThemes():
            if map_collection.mapThemeState(existing_theme) == current_state:
                msg = QMessageBox.warning(None, self.tr("Theme Exists"),
                                          self.tr(f"The theme '{existing_theme}' already exists with this configuration. "
                                                  "Do you still want to create a new theme?"), QMessageBox.Yes | QMessageBox.No)
                if msg == QMessageBox.No:
                    return

        # Ask for new theme name
        new_theme, ok = QInputDialog.getText(None, self.tr('Themename'), self.tr('Name of the new theme'))
        print(f"new theme name: {new_theme}")
        if ok and new_theme != "":
            rec = map_collection.createThemeFromCurrentState(root, model)
            map_collection.insert(new_theme, rec)
            map_collection.applyTheme(new_theme, root, model) 
            print (f"added '{new_theme}' to theme collection")
                                        
            self.populate() 
            self.set_combo_text(new_theme)
            self.dockwidget.BookmarkComboBox.setCurrentIndex(-1)
            
            #add theme to COVERAGE layer
            layer=self.coverage_layer()
            with edit(layer):
                fet = QgsFeature(layer.fields())
                fet[LAYER_THEME_FIELD_NAME] = new_theme
                layer.addFeature(fet) 
                print(f"Successfully added '{new_theme}' to COVERAGE layer")
            
                
    
    def rename_maptheme(self):
        """Rename the selected theme and update map layouts."""
        theme = self.dockwidget.PresetComboBox.currentText()
        name, ok = QInputDialog.getText(None, self.tr('Rename Theme'),
                                        self.tr('New Name:'),
                                        0,
                                        theme)
        if ok and name != "":
            # Access the map theme collection via QgsProject instance
            map_collection = QgsProject.instance().mapThemeCollection()

            # Ensure the theme exists in the collection before renaming
            if theme in map_collection.mapThemes():
                # Rename the theme in the map theme collection
                map_collection.renameMapTheme(theme, name)

                # Reapply the updated theme to the layers and layouts
                root = QgsProject.instance().layerTreeRoot()
                model = iface.layerTreeView().layerTreeModel()

                # Apply the newly renamed theme to all layouts
                layout_manager = QgsProject.instance().layoutManager()
                for layout in layout_manager.layouts():
                    for item in layout.items():
                        if isinstance(item, QgsLayoutItemMap):
                            # Refresh the map item
                            item.refresh()
                            print(f"Refreshed map item in layout '{layout.name()}' for map item.")

                self.update_theme_name_in_layer(theme,name)
                self.populate()
                self.set_combo_text(name)
            else:
                QMessageBox.warning(None, self.tr("Theme Not Found"),
                                    self.tr(f"The theme '{theme}' was not found in the map theme collection."))

    def set_combo_text(self, new_theme):
        """Set combobox to the newly created theme."""
        index = self.dockwidget.PresetComboBox.findText(new_theme, Qt.MatchFixedString)
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)
            print(f"set theme combo text to '{new_theme}'")

    def update_theme_name_in_layer(self, old_theme,new_theme):
        layer=self.coverage_layer()
        #get field index of theme field
        field_idx = layer.fields().lookupField(LAYER_THEME_FIELD_NAME)
        with edit(layer):
        
            try:
                #get first matching feature with theme name
                first_match = self.coverage_feature(old_theme)
                #change theme name  
                # Apply the value change directly to the data provider
                layer.changeAttributeValue(first_match.id(), field_idx, new_theme)
                layer.updateFeature(first_match)
                print(f"'{old_theme}' renamed '{new_theme}'")
            
            #add new theme feature with selectected bookmark geometry             
            except:
                print(f"Could not update '{old_theme}'")
       
        
    
    #update layer when changes to bookmarks made
    def bookmark_updates(self,id):
        print(f"bookmark updates fnc called for bookmark id {id}")
        
        #get values for bookmark or sets to None if removed
        manager = QgsProject.instance().bookmarkManager()
        bookmark = manager.bookmarkById(id)
        print(f"from bookmark_update fnc: {bookmark}")
        bookmark_name = bookmark.name() or None
        bookmark_id = bookmark.id() or None
        #set geometry to new extent or to empty geomtry if bookmark removed
        if bookmark_name is not None:
            geom = QgsGeometry.fromRect(bookmark.extent()) 
            print(f"bookmark geometry found")
        else:
            geom = QgsGeometry()
            print(f"bookmark geometry set to empty")

        
        #index = self.dockwidget.BookmarkComboBox.findData(id)
        #self.dockwidget.BookmarkComboBox.setItemText(index, bookmark_name)
        
        # filter features to those with matching bookmark ids
        request = QgsFeatureRequest().setFilterExpression(f'"{LAYER_BOOKMARK_FIELD_ID}" = \'{id}\'')
        layer=self.coverage_layer()
        features = layer.getFeatures(request)
        
        #update extents and name of existing bookmark in layer or set to None if removed        
        field_idx1 = layer.fields().lookupField(LAYER_BOOKMARK_FIELD_NAME)
        field_idx2 = layer.fields().lookupField(LAYER_BOOKMARK_FIELD_ID)
        with edit(layer)
            for feature in features:
                layer.changeAttributeValue(feature.id(), field_idx1, bookmark_name)
                layer.changeAttributeValue(feature.id(), field_idx2, bookmark_id)
                layer.changeGeometryValues({feature.id(): geom}) 
                layer.updateFeature(feature)
                print(f"feature id {feature.id()} updated bookmark name and geometry")
        
        iface.mapCanvas().refresh()
        print(layer.commitErrors()) 

        #update combo box name
        self.populate()

    
    def bookmark_lookup(self,theme):
        layer=self.coverage_layer()
        lookup_field = LAYER_THEME_FIELD_NAME
        target_field = LAYER_BOOKMARK_FIELD_NAME

        # Create an in-memory key-value dictionary {lookup_value: target_value}
        # This loops through the features once and indexes them
        bookmark_lookup_dict = {feat[lookup_field]: feat[target_field] for feat in layer.getFeatures()}
        #finds bookmark corresponding to theme
        assoc_bmk = bookmark_lookup_dict.get(theme, None)  
        print(f"from fnc bookmark lookup:{bookmark_lookup_dict} returning '{assoc_bmk}' ")
        return assoc_bmk  

    def get_current_theme(self):
        """Retrieve the theme that matches current visibility map states ie active theme"""
        
        project = QgsProject.instance()
        theme_collection = project.mapThemeCollection()
        
        # 1. Capture the current layer tree layout state
        root = project.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        current_state = theme_collection.createThemeFromCurrentState(root, model)
        
        # 2. Loop through saved themes and check for a match
        for theme_name in theme_collection.mapThemes():
            if theme_collection.mapThemeState(theme_name) == current_state:
                return theme_name               
        return None

    def get_current_bookmark(self):
        """Retrieve the currently selected theme by name."""
        return self.dockwidget.BookmarkComboBox.currentText()    

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeDockWidget(self.dockwidget)

        # Save the size of the dock widget
        settings = QSettings()
        QSettings.setDefaultFormat(QSettings.IniFormat)
        saved_size = settings.value("ThemeSelector/size", QSize(300, 200))
        if isinstance(saved_size, QSize):
            self.dockwidget.resize(saved_size)
        elif isinstance(saved_size, str):  # Handle improperly serialized values
            try:
                width, height = map(int, saved_size.strip("()").split(","))
                self.dockwidget.resize(QSize(width, height))
            except ValueError:
                self.dockwidget.resize(QSize(300, 200))  # Default size
        settings = QSettings()
        settings.setValue("ThemeSelector/size", self.dockwidget.size())
    
    def disable_buttons(self):
        """Disable theme buttons."""
        self.dockwidget.pushButton_remove.setEnabled(False)
        self.dockwidget.pushButton_replace.setEnabled(False)
        self.dockwidget.pushButton_add.setEnabled(False)
        self.dockwidget.pushButton_rename.setEnabled(False)
       
    def enable_buttons(self):
        """Enable theme buttons."""
        self.dockwidget.pushButton_remove.setEnabled(True)
        self.dockwidget.pushButton_replace.setEnabled(True)
        self.dockwidget.pushButton_add.setEnabled(True)
        self.dockwidget.pushButton_rename.setEnabled(True)
        
