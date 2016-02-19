from PyQt4.QtCore import QVariant
import flickrapi
#flickr_search
api_key='01ec364b7b79268dc9532ee6d57246c6'
api_secret='be42a860ecea8a87'
flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
lat = '46'
lon = '11'
radius = 1
#bbox = 'minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude'
has_geo = 1
radius_units = 'km'
json = flickr.photos.search(lon=lon, lat=lat, radius=radius, radius_units=radius_units)
#as we have all photos, let's add some data to each of it.
json['photos']['photo'][0]
#create link:
#https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}.jpg
thumb = 'https://farm' + str(json['photos']['photo'][0]['farm']) + '.staticflickr.com/' + str(json['photos']['photo'][0]['server']) + '/' + str(json['photos']['photo'][0]['id'])+ '_' + str(json['photos']['photo'][0]['secret'])+ '_t.jpg'
layer = QgsVectorLayer('Point?crs=EPSG:4326', 'Accessibility', "memory")
pr = layer.dataProvider()
pr.addAttributes([QgsField("thumbnail", QVariant.String)])
pr.addAttributes([QgsField("title", QVariant.String)])
pr.addAttributes([QgsField("owner", QVariant.String)])
pr.addAttributes([QgsField("link", QVariant.String)])
pr.addAttributes([QgsField("desc", QVariant.String)])
#pr.addAttributes([QgsField("lat", QVariant.Float)])
#pr.addAttributes([QgsField("lon", QVariant.Float)])
#pr.addAttributes([QgsField("country", QVariant.String)])
#pr.addAttributes([QgsField("county", QVariant.String)])
#pr.addAttributes([QgsField("region", QVariant.String)])
#pr.addAttributes([QgsField("locality", QVariant.String)])
#pr.addAttributes([QgsField("desc", QVariant.String)])
#pr.addAttributes([QgsField("date", QVariant.String)])
layer.updateFields()
for photo in json['photos']['photo']:
    fet = QgsFeature()
    #now read additional information:
    details = flickr.photos.getInfo(photo_id=photo['id'])
    thumb = 'https://farm' + str(json['photos']['photo'][0]['farm']) + '.staticflickr.com/' + str(json['photos']['photo'][0]['server']) + '/' + str(json['photos']['photo'][0]['id'])+ '_' + str(json['photos']['photo'][0]['secret'])+ '_t.jpg'
    details['photo']['dates']['taken']
    details['photo']['description']['_content']
    details['photo']['location']['latitude']
    details['photo']['location']['longitude']
    #details['photo']['location']['locality']['_content']
    details['photo']['location']['country']['_content']
    #details['photo']['location']['county']['_content']
    #details['photo']['location']['region']['_content']
    fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(details['photo']['location']['longitude']),float(details['photo']['location']['latitude']))))
    geom = fet.geometry()
    fet.setAttributes([details['photo']['dates']['taken'],details['photo']['description']['_content'],details['photo']['location']['longitude'],details['photo']['location']['latitude'],thumb])
    pr.addFeatures([fet])

QgsVectorFileWriter.writeAsVectorFormat(layer, "/tmp/access_berlin.shp", "CP1250", None, "ESRI Shapefile")
