from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsLayoutItemLabel,
    QgsPrintLayout,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsUnitTypes,
    QgsProperty,
    QgsLayoutObject,
    Qgis,
    QgsFillSymbol,
    QgsSingleSymbolRenderer,
    QgsProcessingParameterMapLayer,
    QgsProcessingParameterLayout,
    QgsProcessingParameterExtent,
    QgsProcessingFeedback, 
    QgsRectangle,
)

from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt


class layoutSetup:

    COVERAGE_LAYER = 'coverage layer'
    

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

    # ------------------------------------------------------------------
    def configureAtlas(self, parameters, context, feedback):
        # Always use the execution context project instance for thread safety
        project = context.project() if context.project() else QgsProject.instance()
        
        # --------------------------------------------------------------
        # Map settings
        # --------------------------------------------------------------
        map_item.setFollowVisibilityPreset(True)
        map_item.setFollowVisibilityPresetName(theme_name)
        # --------------------------------------------------------------
        # Atlas
        # --------------------------------------------------------------
        atlas = layout.atlas()
        atlas.setEnabled(True)
        atlas.setCoverageLayer(coverage_layer)
        atlas.setHideCoverage(True)
        atlas.setPageNameExpression('"theme_name"')

        
        
