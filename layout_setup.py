from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsPrintLayout,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutObject,
    QgsProperty,
    QgsLayoutPoint, 
    QgsLayoutSize, 
    QgsUnitTypes,
    Qgis
)
from PyQt5.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QMessageBox
)
from qgis.utils import iface



class layoutSetup:

    LAYER_THEME_FIELD_NAME = "theme_name"

    def __init__(self, layout, coverage_layer):
        print("layoutsetup script called")
        self.coverage_layer = coverage_layer
        self.layout = layout

        designer = iface.openLayoutDesigner(layout)
        
        self.configureAtlas(layout, coverage_layer)

    def mapItem(self, layout):
        for item in layout.items():
            if isinstance(item, QgsLayoutItemMap):
                return item
        return None

    def legendItem(self, layout):
        for item in layout.items():
            if isinstance(item, QgsLayoutItemLegend):
                return item
        return None

    def configureAtlas(self, layout, coverage_layer):
        # Always use the execution context project instance for thread safety
        project = QgsProject.instance()

        layout_name = layout.name()

        # 1. Initialize Atlas
        atlas = layout.atlas()
        atlas.setEnabled(True)
        atlas.setCoverageLayer(self.coverage_layer)
        atlas.setHideCoverage(True)
        
        # Format field name properly inside the expression quotes
        atlas.setPageNameExpression(f'"{self.LAYER_THEME_FIELD_NAME}"')
        
        # 2. Safely retrieve the map item using the helper method or create new map
        map_item = self.mapItem(layout) or self.add_map_to_layout(layout)
        
        # 3. Boot up the atlas preview to load the first feature into memory
        atlas.first()
        
        # Assign dynamic map theme based on the current feature attribute
        expression_string = f"attribute(@atlas_feature, '{self.LAYER_THEME_FIELD_NAME}')"
        map_item.dataDefinedProperties().setProperty(
            QgsLayoutObject.DataDefinedProperty.MapStylePreset, 
            QgsProperty.fromExpression(expression_string)
        )
        
        # Control map extents by atlas
        map_item.setAtlasDriven(True)

        # Set the margin around the feature (e.g., 5% margin)
        map_item.setAtlasMargin(0.05)

        # 4. Set the scaling mode (FIXED: Corrected enum path)
        map_item.setAtlasScalingMode(QgsLayoutItemMap.Auto)

        # FIXED: Removed map_item.setFollowVisibilityPreset(True) 
        # because it conflicts with the dynamic DataDefinedProperty MapStylePreset
        
        # Commit layout map parameters and refresh bounding dimensions
        map_item.refresh()
        layout.refresh()
        
        # Example processing task: Print the layout name
        print(f"Executing script using layout: {layout_name}")
                
        QMessageBox.information(
            iface.mainWindow(), 
            "Success", 
            f"Successfully setup layout: {layout_name}"
        )

    # Create map if none found in layout
    def add_map_to_layout(self, layout):
        
        # 2. Instantiate and INITIALISE defaults
        map_item = QgsLayoutItemMap(layout)
        map_item.initializeDefaults() 
        
        # 3. Commit it to the layout tree before setting coordinates
        layout.addLayoutItem(map_item)
        
        # 4. Set sizing coordinates
        map_item.attemptMove(QgsLayoutPoint(10, 10, QgsUnitTypes.LayoutMillimeters))
        map_item.attemptResize(QgsLayoutSize(200, 150, QgsUnitTypes.LayoutMillimeters))
        
        # 5. Force geographic scope alignment
        map_item.zoomToExtent(iface.mapCanvas().extent())
        
        # 6. Select the item to populate the Properties Panel
        layout.setSelectedItem(map_item)
        
        # 7. Force a rendering refresh cycle across both systems
        map_item.refresh()
        if designer:
            designer.view().addRefreshRegion(map_item.rect()) # Direct view update

        print(f"map item added to layout")
        
        return map_item
