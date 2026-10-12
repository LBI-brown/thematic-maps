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

from qgis.utils import iface

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
        return ThemeAtlasGeneratorAlgorithm()

    def name(self):
        return 'layout_script'

    def displayName(self):
        return self.tr('Generate/ Update Theme-Driven Atlas Layout v2')

    def group(self):
        return self.tr('LBI processes')

    def groupId(self):
        return 'lbi'

    def shortHelpString(self):
        return self.tr(
            "Creates a coverage layer with polygons the size of the canvas extent and named after each theme." 
            " Then configures a new or existing layout to generate Atlas of thematic maps."
            " Existing map and legend items are reused if found."
        )

    def flags(self):
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
        
        project = QgsProject.instance()
        
        project_base_name = project.baseName()
        
        project = QgsProject.instance()
        
        
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

        feedback.pushInfo(
            f"Found {len(theme_names)} map themes."
        )

        
        
        coverage_extent = self.parameterAsExtent(
                parameters,
                self.EXTENT,
                context
            )
        
        coverage_layer = self.parameterAsLayer(
            parameters,
            self.EXISTING_LAYER,
            context
        )
        
    # --------------------------------------------------------------
        # Use existing coverage layer
        # --------------------------------------------------------------    
        feature_names = []
        
        if coverage_layer:

            layer_name = coverage_layer.name()

            feedback.pushInfo(
                f"Using existing coverage layer '{layer_name}'"
            )
            
            # construct array of features names in existing layer to check against theme names
            
            request = QgsFeatureRequest()
            for f in coverage_layer.getFeatures(request):
                feature_names.append(f["theme_name"])
                
            feedback.pushInfo(
                f"Using existing feature names '{feature_names}'"
            )

        else:
 
            # --------------------------------------------------------------
            # create new coverage layer
            # --------------------------------------------------------------
            layer_name = self.parameterAsString(
            parameters,
            self.NEW_LAYER_NAME,
            context
            )
            
            canvas = iface.mapCanvas()

            crs_auth_id = canvas.mapSettings().destinationCrs().authid()

            layer_uri = (
                f"Polygon?crs={crs_auth_id}"
                "&field=id:integer"
                "&field=theme_name:string(100)"
            )

            coverage_layer = QgsVectorLayer(
                layer_uri,
                layer_name,
                "memory"
            )
            
            project.addMapLayer(coverage_layer)
            
            feedback.pushInfo(
                f"New Coverage layer created: {layer_name}"
            )

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

        coverage_layer.setRenderer(
            QgsSingleSymbolRenderer(symbol)
        )

        coverage_layer.triggerRepaint()

        # --------------------------------------------------------------
        # Layout handling
        # --------------------------------------------------------------

        layout_manager = project.layoutManager()
        
        layout = self.parameterAsLayout(
            parameters,
            self.EXISTING_LAYOUT,
            context
        )

        if layout:

            layout_name = layout.name()

            feedback.pushInfo(
                f"Using existing layout '{layout_name}'"
            )

        else:

            layout_name = self.parameterAsString(
                parameters,
                self.NEW_LAYOUT_NAME,
                context
            )

            layout = layout_manager.layoutByName(layout_name)

            if layout:

                feedback.pushInfo(
                    f"Using existing layout '{layout_name}'"
                )

            else:

                feedback.pushInfo(
                    f"Creating layout '{layout_name}'"
                )

                layout = QgsPrintLayout(project)
                layout.initializeDefaults()
                layout.setName(layout_name)

                layout_manager.addLayout(layout)

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

            feedback.pushInfo(
                "Existing atlas title found."
            )

        else:

            feedback.pushInfo(
                "Creating atlas title."
            )

            title_item = QgsLayoutItemLabel(layout)

            title_item.setText("AtlasTitle")

            title_w = page_w - (margin * 2)

            title_item.attemptMove(
                QgsLayoutPoint(
                    margin,
                    page_h - 20,
                    QgsUnitTypes.LayoutMillimeters
                )
            )

            title_item.attemptResize(
                QgsLayoutSize(
                    title_w,
                    title_height,
                    QgsUnitTypes.LayoutMillimeters
                )
            )

            layout.addLayoutItem(title_item)

        title_item.setText('[% "theme_name" %]')

        font = QFont("Poppins", 18)
        font.setBold(True)

        title_item.setFont(font)
        title_item.setFontColor(QColor(0, 0, 0))
        title_item.setHAlign(Qt.AlignLeft)
        title_item.setVAlign(Qt.AlignVCenter)

        # --------------------------------------------------------------
        # Map Item
        # --------------------------------------------------------------

        map_item = self.findMapItem(layout)

        if map_item:

            feedback.pushInfo(
                "Existing map item found."
            )

        else:

            feedback.pushInfo(
                "Creating map item."
            )

            map_item = QgsLayoutItemMap(layout)

            map_item.attemptMove(
                QgsLayoutPoint(
                    margin,
                    margin,
                    QgsUnitTypes.LayoutMillimeters
                )
            )

            map_item.attemptResize(
                QgsLayoutSize(
                    200,
                    180,
                    QgsUnitTypes.LayoutMillimeters
                )
            )

            layout.addLayoutItem(map_item)

        map_item.setExtent(coverage_extent)
        map_item.setAtlasScalingMode(QgsLayoutItemMap.Auto)      

        map_item.setAtlasDriven(True)

        map_item.setFollowVisibilityPreset(True)

        theme_property = QgsProperty.fromExpression(
            '"theme_name"'
        )

        map_item.dataDefinedProperties().setProperty(
            QgsLayoutObject.MapStylePreset,
            theme_property
        )

        map_item.refreshDataDefinedProperty(
            QgsLayoutObject.MapStylePreset
        )

        # --------------------------------------------------------------
        # Legend
        # --------------------------------------------------------------

        legend_item = self.findLegendItem(layout)

        if legend_item:

            feedback.pushInfo(
                "Existing legend item found."
            )

        else:

            feedback.pushInfo(
                "Creating legend item."
            )

            legend_item = QgsLayoutItemLegend(layout)

            legend_w = 60.0
            legend_h = page_h - (2 * margin)

            legend_x = (
                (page_w - (2 * margin))
                - legend_w
            )

            legend_y = margin

            legend_item.attemptMove(
                QgsLayoutPoint(
                    legend_x,
                    legend_y,
                    QgsUnitTypes.LayoutMillimeters
                )
            )

            legend_item.attemptResize(
                QgsLayoutSize(
                    legend_w,
                    legend_h,
                    QgsUnitTypes.LayoutMillimeters
                )
            )

            layout.addLayoutItem(legend_item)

        legend_item.setTitle("Legend")

        legend_item.setLinkedMap(map_item)

        legend_item.setAutoUpdateModel(False)

        legend_item.setLegendFilterByMapEnabled(True)

        legend_item.setLegendFilterOutAtlas(True)

        legend_item.setAutoWrapLinesAfter(60)

        # --------------------------------------------------------------
        # Refresh layout
        # --------------------------------------------------------------

        layout.refresh()
        
        feedback.setProgress(int(100))

        feedback.pushInfo(
            "Atlas successfully configured."
        )

        feedback.pushInfo(
            f"Layout '{layout_name}' is ready."
        )
        
        

        return {
            self.NEW_LAYER_NAME: coverage_layer
        }
