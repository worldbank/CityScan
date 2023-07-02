# CityScan Raster Processing

Collection of data processing scripts to generate the baseline raster data for the CityScan project

Processing a city scan first involves making sure you have the necessary source data downloaded and saved in the correct locations, as well as named appropiately. You also want to have the AOI shapefile of your region. Save the AOI in the epsg:4326 projection and inside the admin directory. The python city scan script can then be run to clip the source data to the appropiate AOI. All of the outputs will be saved in the 'output' directory. Note that for 08_uhi and 12_earthquakes, only screenshots of online viewers are taken.

Your City Scan directory should look like:

```bash
├── city_scan
    ├── 01_population
    ├── 02_urban_change
    ├── 03_landcover
    ├── 04_elevation
    ├── 06_solar
    ├── 07_air_quality
    ├── 08_uhi
    ├── 11_landslides
    ├── 12_earthquakes
    ├── admin
    ├── cityscan_raster_processing.py
    └── output
```

However, there are global data sets that can reside in different locations. The CityScan python script can read from a yaml configuration folder that specifies where the 02_urban_change, 03_Africa_20m_landcover, 03_landcover, 07_air_quality, and 11_landslides directories are located. There are two examples in this repo named 'global_data_config_personal.yml; and 'global_data_config_office.yml'.

```bash
├── global_data_sets
    ├── 02_urban_change
        ├── 12 (this directory contains many sub-directories with data)
       ├── GHS_BUILT_LDSMT_GLOBE_R2015B_3857_38_v1_0.vrt
       ├── GHS_BUILT_LDSMT_GLOBE_R2015B_3857_38_v1_0.vrt.clr
       ├── GHS_BUILT_LDSMT_GLOBE_R2015B_3857_38_v1_0.vrt.ovr
       ├── GHS_BUILT_LDSMT_GLOBE_R2015B_3857_38_v1_0.vrt.ovr.aux.xml
    ├── 03_Africa_20m_landcover
        ├── ESACCI-LC-L4-LC10-Map-20m-P1Y-2016-v1.0.tif
    ├── 03_landcover
        ├── ESACCI-LC-L4-LCCS-Map-300m-P1Y-2015-v2.0.7.tif
    ├── 07_air_quality
        ├── sdei-global-annual-gwr-pm2-5-modis-misr-seawifs-aod-2016-geotiff
            ├── gwr_pm25_2016.tfw
            ├── gwr_pm25_2016.tif
            ├── gwr_pm25_2016.tif.aux.xml
            ├── gwr_pm25_2016.tif.ovr
    ├── 11_landslides
        ├── global_landslides.tif
```

## How to retrieve datasets:

## 01_population

Go to find the population datasets from WorldPop (https://www.worldpop.org/project/categories?id=3). Click on the Individual countries 2000-2020 link and find the country and year you are interested in. The dataset page has a preview of the data and a summary. Note that the summary states the mapping approach. We are interested in the mapping approach that uses Random Forest-based dasymetric redistribution. You can then download the dataset and save the .tif inside city_scan folder, within the 01_population folder. The default is to use the constrained version.

## 02_urban_change

The WSF-evolution dataset is now publically available and can be downloaded: https://geoservice.dlr.de/web/, https://download.geoservice.dlr.de/WSF_EVO/files/. WSF-evolution outlines the growth of settlements extent globally at 30m spatial resolution and high temporal frequency from 1985 to 2015. This file should be saved within the global_data_sets folder, within the 02_urban_change folder. 

If WSF-evolution is not available then GHS-built will be used. GHS-BUILT data contains a multitemporal information layer on built-up presence as derived from Landsat image collections (GLS1975, GLS1990, GLS2000, and ad-hoc Landsat 8 collection 2013/2014). Go to the download page (https://ghsl.jrc.ec.europa.eu/download.php?ds=bu) and download the global dataset. They now have the option to download tiles, so you can try just downloading a tile that covers your AOI as well. Choose the Multitemporal, 30m resolution, and Mercator projected dataset. This file should be saved within the global_data_sets folder, within the 02_urban_change folder.

## 03_landcover

ECA has a global world land cover map at 10 m resolution for 2020, based on both Sentinel-1 and Sentinel-2 data,
containing 11 land cover classes and independently validated with a global overall accuracy of 74.4%. More information here:
https://esa-worldcover.org/en/data-access 

By logging in with your account, WorldCover products can be accessed using the WorldCover viewer and downloaded: https://viewer.esa-worldcover.org/worldcover/

WorldCover classes:
- 10 Tree cover
- 20 Shrubland
- 30 Grassland
- 40 Cropland
- 50 Built-up
- 60 Bare / sparse vegetation
- 70 Snow and Ice
- 80 Permanent water bodies
- 90 Herbaceous wetland
- 95 Mangroves
- 100 Moss and lichen

Note: previously we used the ESA land cover maps that had lower resolution;
ECA has a global land cover maps at 300m spatial resolution (http://maps.elie.ucl.ac.be/CCI/viewer/download.php). Download the most recent 2015 Land Cover map in .tif form. The title of the file should be: ESACCI-LC-L4-LCCS-Map-300m-P1Y-2015-v2.0.7.tif. This file should be saved within the 03_landcover folder, which is inside the global_data_sets folder. If the city scan is in in Africa, then the higher resolution Africa 20m land cover dataset should be used, and this can be downloaded here (http://2016africalandcover20m.esrin.esa.int/). This title of this file should be: ESACCI-LC-L4-LC10-Map-20m-P1Y-2016-v1.0.tif. This file should be saved within the global_data_sets folder, within the 03_Africa_20m_landcover folder.

## 04_elevation

As of September 2022 we are now using the FABDEM data, which is a GLO-30 derived product with forests and buildings remove. Here is the link to ver 1.2:
https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn

We use the ESA Copernicus Digital Elevation Model (DEM) GLO-30 product (DGED version). It is available under the Panda catalogue (https://panda.copernicus.eu/web/cds-catalogue/panda), and it is required to register. Instructions on how to register: https://spacedata.copernicus.eu/web/cscda/data-access/discovery-and-download. For more information: https://www.usgs.gov/news/newly-released-elevation-dataset-highlights-value-importance-international-partnerships?qt-news_science_products=1#qt-news_science_products

note: previously we used the NASA SRTM GLobal 1 arc second rasters;
NASA Shuttle Radar Topography Mission (SRTM) Global 1 arc second rasters can be downloaded from https://earthexplorer.usgs.gov. Log into the site and zoom into your AOI. An easy way to do this is to upload a Shapefile. However, you need to limit the shapefile to less than 30 points and it needs to be compressed. We recommend to draw a new simplified AOI shapefile, compress it, and upload the file to earthexplorer and search. Now browse the datasets, open the digital elevation menu, then the srtm menu, and finally check the box for the SRTM 1 Arc-Second Global dataset. Hit the Results button and download SRTM or SRTMs as GeoTIFF. If you download multiple SRTMs, merge them into one include 'merged' as part of the file name. There is a preference for the merged raster to have borders that are transparent instead of black, and we achieve this by creating a transparent alpha band. In order to do this in QGIS 3, use the merge command, set the output data type to Int16, and assign the specified 'NoData' type to output as -32767 (both for "Input pixel value to treat as 'nodata' [optional]" and "Assign specified 'nodata' value to output [optional]"). As an alternative, you can do this with the following GDAL command from the command line:

```
gdalwarp -srcnodata 0 -dstalpha -ot Float32 input1.tif input2.tif input3.tif output.tif
```

Save the GeoTIFF inside the city_scan folder, within the 04_elevation folder.

## 06_solar

Solar resource and PV power potential data can be acquired from the Global Solar Atlas (https://globalsolaratlas.info/downloads/). Pick your country of interest and download the appropiate GIS data. You can download the GeoTIFF of the Longterm yearly/monthly average (YearlyMonthlyTotals) for consistency. Download this folder and unzip inside the city_scan folder, within the 06_solar folder.

## 07_air_quality

The Global Annual PM2.5 Grids from MODIS, MISR and SeaWiFS Aerosol Optical Depth (AOD) with GWR, 1998-2019 consist of annual concentrations (micrograms per cubic meter) of ground-level fine particulate matter (PM2.5), with dust and sea-salt removed. We are using the 2019 dataset. The dataset is downloaded from the following site: https://sedac.ciesin.columbia.edu/data/set/sdei-global-annual-gwr-pm2-5-modis-misr-seawifs-aod-v4-gl-03/data-download. This file should be saved within the global_data_sets folder, within the 07_air_quality folder.

## 08_uhi (depreciated, run a different way now)

The Global Surface UHI Explorer (https://yceo.users.earthengine.app/view/uhimap) is used to visualize urban heat islands. The UHI dataset was created based on the simplified urban-extent (SUE) algorithm detailed in Chakraborty and Lee, 2018. Screenshots are taken of the AOI using the Global Surface UHI Explorer. The screenshots can be used in reports and sourced appropriately.

## 11_landslides

A Global Landslide model and be downloaded from here: https://pmm.nasa.gov/applications/global-landslide-model. This file should be saved within the global_data_sets folder, within the 11_landslides folder.

## 12_earthquakes

An earthquake hazard viewer and earthquake risk viewer can be accessed from here: https://www.globalquakemodel.org/gem

Screenshots are taken of the AOI using these viewers and can be used in reports and sourced appropriately.




