# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThematicMaps
                                 A QGIS plugin
 This plugin maintains a thematic coverage layer for use in print layout
                             -------------------
        begin                : 2026-09-01
        copyright            : (C) 2026 by Nick Brown
        email                : nick@browndesign.co.uk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    from .thematic_maps import ThematicMaps
    return ThematicMaps(iface)
