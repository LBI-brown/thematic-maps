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


class layoutScript(QgsProcessingAlgorithm):

    EXISTING_LAYOUT = 'EXISTING_LAYOUT'
    NEW_LAYOUT_NAME = 'NEW_LAYOUT_NAME'
    EXISTING_LAYER = 'EXISTING_LAYER'
    NEW_LAYER_NAME = 'NEW_LAYER_NAME'
    EXTENT = 'EXTENT'

    def tr(self, string):
        return string

    def createInstance(self):
        return layoutScript()

    def name(self):
        return 'layout_script'

    def displayName(self):
        return self.tr('Atlas driven layout setup')

    def group(self):
        #return self.tr('Thematic maps')
        return ''

    def groupId(self):
        #return 'thematicMaps'
        return ''

    def shortHelpString(self):
        return self.tr(
            "Configures a new or existing layout to generate Atlas of thematic maps. "
            "Existing map and legend items are reused if found."
        )

    def flags(self):
        # Keeps processing operations synchronous on the main thread
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMapLayer(
                self.EXISTING_LAYER,
                self.tr(r"Existing coverage layer (with 'theme_name' field)"),
                optional=True,
                types=[QgsProcessing.SourceType.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                self.tr('New Coverage Extent (used if no existing layer selected)'),
                optional=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.NEW_LAYER_NAME,
                self.tr('New Coverage Layer Name'),
                defaultValue='Project Coverage layer'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterLayout(
                self.EXISTING_LAYOUT,
                self.tr('Existing Layout'),
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.NEW_LAYOUT_NAME,
                self.tr('New Layout Name (used if no existing layout selected)'),
                defaultValue='LBI thematic maps'
            )
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def findMapItem(self, layout):
        for item in layout.items():
            if isinstance(item, QgsLayoutItemMap):
                return item
        return None

    def findLegendItem(self, layout):
        for item in layout.items():
            if isinstance(item, QgsLayoutItemLegend):
                return item
        return None

    def findTitleItem(self, layout):
        for item in layout.items():
            if isinstance(item, QgsLayoutItemLabel):
                if item.displayName() == "AtlasTitle":
                    return item
        return None

    # ------------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):
        # Always use the execution context project instance for thread safety
        project = context.project() if context.project() else QgsProject.instance()
        
        # --------------------------------------------------------------
        # Extract map themes
        # --------------------------------------------------------------
        theme_collection = project.mapThemeCollection()
        theme_names = theme_collection.mapThemes()

        if not theme_names:
            feedback.reportError(
                "No map themes found! Please configure at least one map theme.",
                fatalError=True
            )
            return {}

        feedback.pushInfo(f"Found {len(theme_names)} map themes.")

        coverage_extent = self.parameterAsExtent(parameters, self.EXTENT, context)
        coverage_layer = self.parameterAsLayer(parameters, self.EXISTING_LAYER, context)
        
        # --------------------------------------------------------------
        # Use existing coverage layer
        # --------------------------------------------------------------    
        feature_names = []
        
        if coverage_layer:
            layer_name = coverage_layer.name()
            feedback.pushInfo(f"Using existing coverage layer '{layer_name}'")
            
            request = QgsFeatureRequest()
            for f in coverage_layer.getFeatures(request):
                # Guard against Null/None fields
                if f["theme_name"]:
                    feature_names.append(f["theme_name"])
                
            feedback.pushInfo(f"Using existing feature names '{feature_names}'")
        else:
            # --------------------------------------------------------------
            # create new coverage layer
            # --------------------------------------------------------------
            layer_name = self.parameterAsString(parameters, self.NEW_LAYER_NAME, context)
            
            # FIXED: Avoid using iface.mapCanvas(). Fetch target project CRS securely.
            crs_auth_id = project.crs().authid()

            layer_uri = (
                f"Polygon?crs={crs_auth_id}"
                "&field=id:integer"
                "&field=theme_name:string(100)"
            )

            coverage_layer = QgsVectorLayer(layer_uri, layer_name, "memory")
            project.addMapLayer(coverage_layer)
            feedback.pushInfo(f"New Coverage layer created: {layer_name}")

        # --------------------------------------------------------------
        # generate / update features in coverage layer based on themes and extent
        # --------------------------------------------------------------
        provider = coverage_layer.dataProvider()
        geom = QgsGeometry.fromRect(coverage_extent)
        new_features = []
        
        for theme_name in theme_names:
            if feedback.isCanceled():
                return {}
                
            if theme_name not in feature_names:
                feat = QgsFeature(coverage_layer.fields())
                feat.setAttribute("theme_name", theme_name)
                feat.setGeometry(geom)
                new_features.append(feat)
                
        provider.addFeatures(new_features)
        coverage_layer.updateExtents()

        symbol = QgsFillSymbol.createSimple({
            'color': '255,255,255,0',
            'outline_color': '225,25,25,200'
        })

        coverage_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        coverage_layer.triggerRepaint()

        # --------------------------------------------------------------
        # Layout handling
        # --------------------------------------------------------------
        layout_manager = project.layoutManager()
        layout = self.parameterAsLayout(parameters, self.EXISTING_LAYOUT, context)

        if layout:
            layout_name = layout.name()
            feedback.pushInfo(f"Using existing layout '{layout_name}'")
        else:
            layout_name = self.parameterAsString(parameters, self.NEW_LAYOUT_NAME, context)
            layout = layout_manager.layoutByName(layout_name)

            if layout:
                feedback.pushInfo(f"Using existing layout '{layout_name}'")
            else:
                feedback.pushInfo(f"Creating layout '{layout_name}'")
                layout = QgsPrintLayout(project)
                layout.initializeDefaults()
                layout.setName(layout_name)
                layout_manager.addLayout(layout)

        # --------------------------------------------------------------
        # Atlas
        # --------------------------------------------------------------
        atlas = layout.atlas()
        atlas.setEnabled(True)
        atlas.setCoverageLayer(coverage_layer)
        atlas.setHideCoverage(True)
        atlas.setPageNameExpression('"theme_name"')

        # --------------------------------------------------------------
        # Page settings
        # --------------------------------------------------------------
        margin = 10.0
        title_height = 15.0
        page_w = 297
        page_h = 210

        # --------------------------------------------------------------
        # Title
        # --------------------------------------------------------------
        title_item = self.findTitleItem(layout)

        if title_item:
            feedback.pushInfo("Existing atlas title found.")
        else:
            feedback.pushInfo("Creating atlas title.")
            title_item = QgsLayoutItemLabel(layout)
            title_item.setText("AtlasTitle")

            title_w = page_w - (margin * 2)
            title_item.attemptMove(
                QgsLayoutPoint(margin, page_h - 20, QgsUnitTypes.LayoutMillimeters)
            )
            title_item.attemptResize(
                QgsLayoutSize(title_w, title_height, QgsUnitTypes.LayoutMillimeters)
            )
            layout.addLayoutItem(title_item)

        title_item.setText('[% "theme_name" %]')

        font = QFont("Poppins", 18)
        font.setBold(True)
        title_item.setFont(font)
