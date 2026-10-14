from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsPrintLayout,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutObject,
    QgsProperty,
    Qgis
)
from PyQt5.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QMessageBox
)

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
        
        # 2. Safely retrieve the map item using the helper method
        map_item = self.mapItem(layout)
        if not map_item:
            if feedback:
                feedback.reportError("Could not find a QgsLayoutItemMap in the layout.")
            return

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
        
