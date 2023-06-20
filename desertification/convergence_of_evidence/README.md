### Convergence of Evidence layer
The Convergence of Evidence layer (https://wad.jrc.ec.europa.eu/convergenceofevidence) from the World Atlas of Desertification is useful for viewing a convergence of reliable, global evidence of human environment interactions to identify local or regional areas of concern where land degradation processes may be underway.

### 1st Step
The first step is to simply view the Convergence of Evidence tile layer. Open QGIS and create a new XYZ connection. Input the following URL:

```
https://geospatial.jrc.ec.europa.eu/geoserver/gwc/service/tms/1.0.0/wad:sumKeyissues_14_20170428@EPSG:900913@png/{z}/{x}/{-y}.png
```

### Extracting tiles
If tiles exist for your area, then the next step is extracting the tiles from the TMS imagery service and converting them to a GeoTiff.

To do this you need to run the tms2geotiff.py file within the tms2geotiff directory. The directory itself is an embedded repo of the following forked repo: https://github.com/d3netxer/tiles-to-tiff

Here is an example command: 

```
python tiles_to_tiff https://geospatial.jrc.ec.europa.eu/geoserver/gwc/service/tms/1.0.0/wad:sumKeyissues_14_20170428@EPSG:900913@png/{z}/{x}/{-y}.png 38.465881 8.628545 39.061890 9.262069-o output -z 10
```

