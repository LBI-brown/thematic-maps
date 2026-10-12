from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .layout_script import layoutScript

class CustomProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        # Instantiate and add your custom algorithm(s)
        self.addAlgorithm(layoutScript())

    def id(self):
        """Unique ID for your provider (no spaces, lowercase)."""
        return 'thematic_map_tools'

    def name(self):
        """The display name seen in the Processing Toolbox."""
        return 'Thematic maps scripts'

    def icon(self):
        """Dynamically loads and returns the custom icon from a subfolder."""
        # 1. Get the directory path of the current provider.py file
        current_dir = os.path.dirname(__file__)
        
        # 2. Navigate up one level to the main plugin root directory
        plugin_root = os.path.dirname(current_dir)
        
        # 3. Join paths: plugin root -> your subfolder -> your icon file name
        icon_path = os.path.join(plugin_root, 'img', 'thematic_maps.svg') 
        
        # 4. Return the QIcon object if the path is valid
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        
        return QIcon()
