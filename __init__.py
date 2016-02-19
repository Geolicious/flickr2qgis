# -*- coding: utf-8 -*-
"""
/***************************************************************************
 flickr2qgis
                                 A QGIS plugin
 import photos as shapefile from flickr
                             -------------------
        begin                : 2016-02-19
        copyright            : (C) 2016 by Riccardo Klinger / Geolicious
        email                : riccardo.klinger@geolicious.de
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
    """Load flickr2qgis class from file flickr2qgis.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .flickr2qgis import flickr2qgis
    return flickr2qgis(iface)
