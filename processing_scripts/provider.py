from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .layout_script import layoutScript

class CustomProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        # Instantiate and add your custom algorithm(s)
        self.addAlgorithm(layoutScript())

    def id(self):
        """Unique ID for your provider (no spaces, lowercase)."""
        return 'layout_script_provider'

    def name(self):
        """The display name seen in the Processing Toolbox."""
        return 'Atlas driven layout setup'

    def icon(self):
        """Optional: Return a QIcon object for your toolbox folder."""
        return QIcon()
