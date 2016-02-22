# flickr2qgis
flickr2qgis- a plugin for search and downloading flickr images

##Prerequisites
For a proper usage you need to install the [flickrapi](https://stuvel.eu/flickrapi). And you need to get a flickr API key / secret key. This can be obtained easily at [flickr](https://www.flickr.com/services/api/misc.api_keys.html).
###flickrapi installation Windows
For Windows make sure to use the [correct location](http://gis.stackexchange.com/questions/141320/how-to-install-3rd-party-python-libraries-for-qgis-on-windows) of your QGIS Python version 
So Open up the OSGeo4W Shell and type
``easy_install flickrapi``
###flickrapi installation Ubuntu
Just install the easiest Python module installer [Setuptools](https://pypi.python.org/pypi/setuptools):
``sudo apt-get install python-setuptools``
and install flickrapi with:
``easy_install flickrapi``
