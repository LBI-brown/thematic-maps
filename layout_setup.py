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
        self.coverage_layer = coverage_layer
        self.layout = layout
        self.configureAtlas(self.layout, self.coverage_layer)

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
        # assign theme
        expression_string = f"attribute(@atlas_feature, '{self.LAYER_THEME_FIELD_NAME}')"
        map_item.dataDefinedProperties().setProperty(
        QgsLayoutObject.DataDefinedProperty.MapStylePreset, 
        QgsProperty.fromExpression(expression_string)
        )
        # control by atlas
        map_item.setAtlasDriven(True)

        # (Optional) Set the margin around the feature (e.g., 5% margin)
        # This mimics checking the "Margin around feature" option in the QGIS UI
        map_item.setAtlasMargin(0.05)

        # 3. (Optional) Set the scaling mode
        # Options: Auto (0), FixedScale (1), PredefinedScale (2)
        map_item.setAtlasScalingMode(QgsLayoutItemMap.AtlasScalingMode.Auto)

        map_item.setFollowVisibilityPreset(True)
        map_item.refresh()
        
        # Example processing task: Print the layout name
        print(f"Executing script using layout: {layout_name}")
                
        QMessageBox.information(
            iface.mainWindow(), 
            "Success", 
            f"Successfully setup layout: {layout_name}"
        )

    #create map if none found in layout
    def add_map_to_layout(self,layout):
        # 1. Instantiate the map item linked to your layout
        map_item = QgsLayoutItemMap(layout)
        
        # 2. Set the map's default background canvas and extents
        map_item.setToCanvasExtent()
        
        # 3. Position the map on the page (X, Y coordinates from top-left)
        # Places the map 20mm from the left edge and 20mm from the top edge
        map_item.attemptMove(QgsLayoutPoint(20, 20, QgsUnitTypes.LayoutMillimeters))
        
        # 4. Set the map's width and height (e.g., 200mm wide by 150mm high)
        map_item.attemptResize(QgsLayoutSize(200, 150, QgsUnitTypes.LayoutMillimeters))
        
        # 5. Add the item to the layout's item manager
        layout.addLayoutItem(map_item)

        print(f"map item added to layout")
        
        return map_item
        
