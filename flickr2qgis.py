# -*- coding: utf-8 -*-
"""
/***************************************************************************
 flickr2qgis
                                 A QGIS plugin
 import photos as shapefile from flickr
                              -------------------
        begin                : 2016-02-19
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Riccardo Klinger / Geolicious
        email                : riccardo.klinger@geolicious.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
#from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
#from PyQt4.QtGui import QAction, QIcon
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from flickr2qgis_dialog import flickr2qgisDialog
import flickrapi
from qgis.gui import * #for the click event tool
from xml.etree import ElementTree
import urllib2, os, qgis.utils, os.path, tempfile, urllib, requests, base64
from datetime import datetime, timedelta

class flickr2qgis:
    """QGIS Plugin Implementation."""
    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas() #CHANGE
        # this QGIS tool emits as QgsPoint after each click on the map canvas
        self.clickTool = QgsMapToolEmitPoint(self.canvas)
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'flickr2qgis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = flickr2qgisDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&flickr2qgis')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'flickr2qgis')
        self.toolbar.setObjectName(u'flickr2qgis')
        self.dlg.units.clear()
        self.dlg.units.addItem("km")
        self.dlg.units.addItem("miles")
        self.dlg.download.clear()
        self.dlg.download.addItem("download thumbs to tmp")
        self.dlg.download.addItem("download thumbs to folder")
        self.dlg.enddate.setDate(QDate.currentDate())
        today=QDate.currentDate()
        self.dlg.startdate.setDate(today.addDays(-14))
        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_output_file)
        self.dlg.address.clear()
        self.dlg.geocode.clicked.connect(self.geocodeAddress)
        #self.dlg.getlatlon.clicked.connect(self.clickTool)
        
        #result = QObject.connect(self.clickTool, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.handleMouseDown)

        self.settings = QSettings("api", "sec")
        self.dlg.secret_key.setText(self.settings.value("sec"))
        self.dlg.api_key.setText(self.settings.value("api"))

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('flickr2qgis', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/flickr2qgis/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'load photos from flickr'),
            callback=self.run,
            parent=self.iface.mainWindow())
        result = QObject.connect(self.clickTool, SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"), self.handleMouseDown)
    def handleMouseDown(self, point, button):
        test=self.dlg.address.text()
        crsSrc = qgis.utils.iface.mapCanvas().mapSettings().destinationCrs()
        crsDest = QgsCoordinateReferenceSystem(4326)
        xform = QgsCoordinateTransform(crsSrc, crsDest)
        pointwgs84 = xform.transform(point)
        self.dlg.lat.setValue(pointwgs84.y())
        self.dlg.lon.setValue(pointwgs84.x())

        #self.dlg.setTextBrowser( str(point.x()) + " , " +str(point.y()) )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&flickr2qgis'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.shp')
        self.dlg.lineEdit.setText(filename)


    def geocodeAddress(self):
        address = self.dlg.address.text().encode('utf-8')
        url = "http://openls.geog.uni-heidelberg.de/testing2015/geocoding?apikey=e2017639f5e987e6dc1f5f69a66d049c"
        text='<?xml version="1.0" encoding="UTF-8"?><xls:XLS xmlns:xls="http://www.opengis.net/xls" xmlns:sch="http://www.ascc.net/xml/schematron" xmlns:gml="http://www.opengis.net/gml" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/xls http://schemas.opengis.net/ols/1.1.0/LocationUtilityService.xsd" version="1.1"><xls:RequestHeader/><xls:Request methodName="GeocodeRequest" requestID="123456789" version="1.1"><xls:GeocodeRequest><xls:Address countryCode="DE"><xls:freeFormAddress>' + address + '</xls:freeFormAddress></xls:Address></xls:GeocodeRequest></xls:Request></xls:XLS>'
        req = urllib2.Request(url=url,
            data=text,
            headers={'Content-Type': 'application/xml'})
        response_start=urllib2.urlopen(req).read()
        #tidy up response
        newstr = response_start.replace("\n", "")
        response_start = newstr.replace("  ", "")
        print response_start
        xml = ElementTree.fromstring(response_start)
        start_point =""
        for child in xml[1][0]:
            numberOfHits_start = child.attrib["numberOfGeocodedAddresses"]
        if numberOfHits_start != "0":
            start_point=xml[1][0][0][0][0][0].text
            self.dlg.lon.setValue(float(start_point.split(" ")[0]))
            self.dlg.lat.setValue(float(start_point.split(" ")[1]))
        if start_point =="":
            QtGui.QMessageBox.about(self.dlg, "No Coordinates Found", "Check your start address!")

    #def handleMouseDown(self, point, button):
    #    QMessageBox.information( self.iface.mainWindow(),"Info", "X,Y = %s,%s" % (str(point.x()),str(point.y())) )#
    #    print str(point.x()), str(point.y())
    #    self.dlg.lat.setValue()
    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        self.canvas.setMapTool(self.clickTool)
        
            
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # a with your code.

            print self.dlg.lat.value()
            print self.dlg.lon.value()
            api = self.dlg.api_key.text().encode('utf-8')
            sec = self.dlg.secret_key.text().encode('utf-8')
            self.settings.setValue("api", api)
            self.settings.setValue("sec", sec)
            maxnum =self.dlg.maxnum.value()
            startdate = self.dlg.startdate.dateTime()
            enddate = self.dlg.enddate.dateTime()
            keywords = self.dlg.keywords.text()
            address = self.dlg.address.text()
            lat = self.dlg.lat.value()
            lon = self.dlg.lon.value()
            radius = self.dlg.radius.value()
            radius_units = self.dlg.units.currentText()
            flickr = flickrapi.FlickrAPI(api, sec, format='parsed-json')
            if self.dlg.disablegeo.checkState()==2:
                json = flickr.photos.search(per_page=maxnum, max_upload_date=enddate, min_upload_date=startdate, text=keywords, has_geo=1)
            if self.dlg.disablegeo.checkState()==0:
                json = flickr.photos.search(lon=lon, lat=lat, radius=radius, has_geo=1, radius_units=radius_units, per_page=maxnum, max_upload_date=enddate, min_upload_date=startdate, text=keywords)
            print json
            print startdate
            print enddate
            print(len(json['photos']['photo']))
            if len(json['photos']['photo'])>0:
#as we have all photos, let's add some data to each of it.
                print json['photos']['photo'][0]
                layer = QgsVectorLayer('Point?crs=EPSG:4326', 'Flickr', "memory")
                pr = layer.dataProvider()
                pr.addAttributes([QgsField("thumbnail", QVariant.String)])
                pr.addAttributes([QgsField("photoid", QVariant.String)])

                pr.addAttributes([QgsField("title", QVariant.String)])
                pr.addAttributes([QgsField("owner", QVariant.String)])
                pr.addAttributes([QgsField("link", QVariant.String)])
                pr.addAttributes([QgsField("desc", QVariant.String)])
                pr.addAttributes([QgsField("lat", QVariant.Double)])
                pr.addAttributes([QgsField("lon", QVariant.Double)])
                pr.addAttributes([QgsField("country", QVariant.String)])
                pr.addAttributes([QgsField("county", QVariant.String)])
                pr.addAttributes([QgsField("region", QVariant.String)])
                pr.addAttributes([QgsField("locality", QVariant.String)])
                pr.addAttributes([QgsField("posted", QVariant.String)])
                pr.addAttributes([QgsField("taken", QVariant.String)])
                
                layer.updateFields()
                categories = []
                renderer = QgsCategorizedSymbolRendererV2("photoid", categories)
                layer.setRendererV2(renderer)
                QgsMapLayerRegistry.instance().addMapLayer(layer)
                #sym.setColor(QColor(value))

                for photo in json['photos']['photo']:
                    fet = QgsFeature()
                #now read additional information:
                    details = flickr.photos.getInfo(photo_id=photo['id'])
                    thumb = 'https://farm' + str(photo['farm']) + '.staticflickr.com/' + str(photo['server']) + '/' + str(photo['id'])+ '_' + str(photo['secret'])+ '_t.jpg'
                    photoid = str(photo['id'])
                    try: taken = details['photo']['dates']['taken']
                    except: taken =""
                    try: posted = details['photo']['dates']['posted']
                    except: posted = ""
                    try: desc = details['photo']['description']['_content']
                    except: desc =""
                    try: latitude = details['photo']['location']['latitude']
                    except: latitude = ""
                    try: longitude = details['photo']['location']['longitude']
                    except: longitude =""
                    try: country = details['photo']['location']['country']['_content']
                    except: country =""
                    try: county = details['photo']['location']['county']['_content']
                    except: county = ""
                    try: region = details['photo']['location']['region']['_content']
                    except: region = ""
                    try: locality = details['photo']['location']['locality']['_content']
                    except: locality = ""
                    try: owner =  details['photo']['owner']['username']
                    except: owner = ""
                    try: title =  details['photo']['title']['_content']
                    except: title = ""
                    try: link = 'https://farm' + str(photo['farm']) + '.staticflickr.com/' + str(photo['server']) + '/' + str(photo['id'])+ '_' + str(photo['secret'])+ '_b.jpg'
                    except: link = ""
                    print([thumb, title, owner, link, desc, latitude, longitude, country, county, region, locality, posted, taken])
                    fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(details['photo']['location']['longitude']),float(details['photo']['location']['latitude']))))
                    geom = fet.geometry()
                    fet.setAttributes([thumb,photoid, title, owner, link, desc, latitude, longitude, country, county, region, locality, posted, taken])
                    pr.addFeatures([fet])
                    #sym = QgsSymbolV2.defaultSymbol(layer.geometryType())
                    #sym = QgsSymbolV2(QGis.Point)
                    #sym.setNamedPointSymbol("svg:/tmp/25059331595_t.jpg.svg")
                    #sym.setPointSize(30)
                    #symbollist = layer.rendererV2().symbols()
                    #symbol = symbollist[0]
                    #symbol.appendSymbolLayer(sl)
                    #self.canvas.refresh()  

                    #äsym.changeSymbolLayer(0,QgsSvgMarkerSymbolLayerV2(size=30).setPath("/tmp/25059331595_t.jpg.svg"))

                    #sym.appendSymbolLayer(QgsSvgMarkerSymbolLayerV2(size=30).setPath("/tmp/25059331595_t.jpg.svg"))
                    #sym.deleteSymbolLayer(0)
                    if self.dlg.download.currentText()=="download thumbs to tmp":
                        svg = """
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg>
  <g>
    <image xlink:href="data:image/jpeg;base64,{0}" height="256" width="320" />
  </g>
</svg>
"""
                        
                        data2 = requests.get(thumb, stream=True).content
                        nameim = str(photo['id'])+'_t.jpg'
                        b64response = base64.b64encode(data2)
                        newsvg = svg.format(b64response).replace('\n','')
                        path = tempfile.gettempdir() + os.sep + photo['id'] + '_t.jpg.svg'
                        with open(path, 'w') as f:
                            f.write(newsvg)
                    svgStyle = {}
                    svgStyle['fill'] = '#0000ff'
                    svgStyle['name'] = tempfile.gettempdir() + os.sep + photo['id'] + '_t.jpg.svg'
                    svgStyle['outline'] = '#000000'
                    svgStyle['size'] = '30'
                    symLyr1 = QgsSvgMarkerSymbolLayerV2.create(svgStyle)
                    print symLyr1
                    sym = QgsSymbolV2.defaultSymbol(layer.geometryType())
                    sym.changeSymbolLayer(0, symLyr1)
                    category = QgsRendererCategoryV2(str(photo['id']), sym, str(photo['id']))
                    categories.append(category)
                    renderer = QgsCategorizedSymbolRendererV2("photoid", categories)
                    layer.setRendererV2(renderer)
                    layer.updateExtents()
                    layer.triggerRepaint()

                QgsVectorFileWriter.writeAsVectorFormat(layer, "/tmp/access_berlin.shp", "CP1250", None, "ESRI Shapefile")





