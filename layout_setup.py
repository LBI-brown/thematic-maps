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

class layoutSetup:

    COVERAGE_LAYER = 'coverage layer'
    LAYER_THEME_FIELD_NAME = "theme_name"

    def __init__(self, coverage_layer, layout):
        self.coverage_layer = coverage_layer
        self.layout = layout

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

    def configureAtlas(self, layout, coverage_layer, context, feedback):
        # Always use the execution context project instance for thread safety
        project = context.project() if (context and context.project()) else QgsProject.instance()

        # 1. Initialize Atlas
        atlas = layout.atlas()
        atlas.setEnabled(True)
        atlas.setCoverageLayer(coverage_layer)
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
        expression_string = f"attribute(@atlas_feature, '{self.LAYER_THEME_FIELD_NAME}')"
        map_item.dataDefinedProperties().setProperty(
        QgsLayoutObject.MapFollowVisibilityPresetName, 
        QgsProperty.fromExpression(expression_string)
        )
        map_item.setFollowVisibilityPreset(True)
        map_item.refresh()

    def my_custom_processing_logic(self, layout):
        """
        Place your custom script execution logic inside this method.
        """
        layout_name = layout.name()
        
        # Example processing task: Print the layout name
        print(f"Executing script using layout: {layout_name}")
        
        # Example modification: Find a map item inside the layout
        # map_item = layout.itemByById("Map 1")
        
        QMessageBox.information(self, "Success", f"Successfully processed layout: {layout_name}")
        
