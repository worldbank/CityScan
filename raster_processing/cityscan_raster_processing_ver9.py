import os
import sys
import math
import warnings
import yaml
import geopandas as gpd
from osgeo import gdal
import glob
import numpy as np
import rasterio.mask
import rasterio
import fiona

print('welcome to city scan 2')

print('note: You may add the -africa argument if you city is in Africa')
print('this flag will enable the higher resolution Africa ESACCI landcover')

print('note: Your input admin datasets should be using crs 4326')


# load configuration file, this files stores the file locations for the global data files
with open("./global_data_config_personal_windows.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

print('print cfg file')
print(cfg)

#print('Number of arguments:', len(sys.argv), 'arguments.')
#print('Argument List:', str(sys.argv))

admin_folder = './admin'

for file in os.listdir(admin_folder):
    if file.endswith("4326.shp"):
        print(file)

        print('attempt to read file')
        # 1. need to transform the input shp to correct prj
        admin_file = gpd.read_file(admin_folder + '/' + file)
        print('print admin_file crs')
        print(admin_file.crs)

        if not admin_file.crs == 'epsg:4326':
            sys.exit(
                'admin file crs is not 4326, provide an admin file with crs than 4326 and re-run')


prepend_file_text = '01_population'

output_folder = './output/'

###### getting file names #########################
# population
pop_file = 'test'

for name in glob.glob('./01_population/*.tif'):
    print('inside glob')
    print(name)
    pop_file = name

# urban_change
ghsl_urban_change_file = 'test'

for name in glob.glob('./02_urban_change/*evolution*.tif'):
    print('inside glob')
    print(name)
    ghsl_urban_change_file = name

# for name in glob.glob('../../GHS_BUILT_LDSMT_GLOBE_R2015B_3857_38_v1_0/*.vrt'):
# for name in glob.glob('../global_data_sets/02_urban_change/*.vrt'):
print('print urban change files')
print(cfg["02_urban_change"])


# land cover
# land_cover_file = 'test'

# tifCounter = len(glob.glob1('./03_landcover/', "*.tif"))

# print('tifCounter, land cover files:')
# print(tifCounter)

# if tifCounter == 1:
#     for name in glob.glob('./03_landcover/*.tif'):
#         print('inside land cover glob single')
#         print(name)
#         landcover_file = name
# elif tifCounter == 0:
#     warnings.warn("there are no land cover files")
# else:
#     for name in glob.glob('./03_landcover/*merged.tif'):
#         print('inside land cover glob multiple')
#         print(name)
#         landcover_file = name

# if landcover_file == 'test':
#     warnings.warn("Warning because there are multiple land cover files but no merged land cover file. Make sure to merge the land cover files and include the word 'merged' in the name of the file.")


# elevation

elevation_file = 'test'

tifCounter = len(glob.glob1('./04_elevation/', "*.tif"))

print('tifCounter, elevation files:')
print(tifCounter)

if tifCounter == 1:
    for name in glob.glob('./04_elevation/*.tif'):
        print('inside elevation glob single')
        print(name)
        elevation_file = name
elif tifCounter == 0:
    warnings.warn("there are no elevation files")
else:
    for name in glob.glob('./04_elevation/*merged.tif'):
        print('inside elevation glob multiple')
        print(name)
        elevation_file = name

if elevation_file == 'test':
    warnings.warn("Warning because there are multiple elevation files but no merged elevation file. Make sure to merge the elevation files and include the word 'merged' in the name of the file.")


# solar
solar_file = 'test'

print('go into solar glob')
for name in glob.glob('./06_solar/*/PVOUT.tif'):
    print('inside solar glob')
    print(name)
    solar_file = name

# imperviousness
imperv_file = 'test'

print('go into imperviousness glob')
for name in glob.glob('./13_imperviousness/*imperviousness*.tif'):
    print('inside imperviousness glob')
    print(name)
    imperv_file = name


# not used right now
def clipdata_urban_change(admin_folder, ghsl_urban_change_file, output_folder, prepend_file_text):
    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):
            print(file)

            # 1. need to transform the input shp to correct prj
            admin_file = gpd.read_file(admin_folder + '/' + file)
            print('print admin_file crs')
            print(admin_file.crs)

            admin_file_3857 = admin_file.to_crs('epsg:3857')
            print('print admin_file_3857 crs')
            print(admin_file_3857.crs)

            # save the admin_file_3857 as a temp file
            admin_file_3857_shp = output_folder + 'temp_admin_file_3857.shp'
            admin_file_3857.to_file(admin_file_3857_shp)

            with fiona.open(admin_file_3857_shp) as shapefile:
                features = [feature["geometry"] for feature in shapefile]

                # 2. need to clip the global ghsl by the input admin shape
                with rasterio.open(ghsl_urban_change_file) as src:

                    # shapely presumes all operations on two or more features exist in the same Cartesian plane.
                    out_image, out_transform = rasterio.mask.mask(
                        src, features, crop=True)
                    out_meta = src.meta.copy()

                    out_meta.update({"driver": "GTiff",
                                     "height": out_image.shape[1],
                                     "width": out_image.shape[2],
                                     "transform": out_transform})

                    output_3857_raster = output_folder + prepend_file_text + "_3857.tif"

                    with rasterio.open(output_3857_raster, "w", **out_meta) as dest:
                        dest.write(out_image)

                    # 3. need to transform the clipped ghsl to 4326

                    new_output_file_name = output_folder + prepend_file_text + "_4326.tif"

                    gdal.Warp(new_output_file_name,
                              output_3857_raster, dstSRS='EPSG:4326')

                    # remove temporary files
                    if os.path.exists(output_3857_raster):
                        os.remove(output_3857_raster)
            # remove temporary files
            print('admin_file_3857_shp keyword')
            print(admin_file_3857_shp[:-3])
            fileList = glob.glob(admin_file_3857_shp[:-3]+'*', recursive=True)
            admin_file_3857_shp_keyword = admin_file_3857_shp
            for filePath in fileList:
                try:
                    os.remove(filePath)
                except OSError as e:
                    print("Error while deleting file")
                    print("Failed with:", e.strerror)  # look what it says

# Different from clipdata because wsf needs to be bucketed by year
def clipdata_wsf(admin_folder, input_raster, output_folder, prepend_file_text):

    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):
            print(file)

            features_gdf = gpd.read_file(admin_folder + '/' + file)
            print('print admin_file crs')
            print(features_gdf.crs)

            # automatically find utm zone
            avg_lng = features_gdf["geometry"].unary_union.centroid.x

            # calculate UTM zone from avg longitude to define CRS to project to
            utm_zone = math.floor((avg_lng + 180) / 6) + 1
            utm_crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

            features = features_gdf['geometry'].tolist()

            # clip
            with rasterio.open(input_raster) as src:
                # shapely presumes all operations on two or more features exist in the same Cartesian plane.
                out_image, out_transform = rasterio.mask.mask(
                    src, features, crop=True)
                out_meta = src.meta.copy()

                out_meta.update({"driver": "GTiff",
                                 "height": out_image.shape[1],
                                 "width": out_image.shape[2],
                                 "transform": out_transform})

                output_4326_raster_clipped = output_folder + \
                    prepend_file_text + "_4326_clipped.tif"

                # save for stats
                with rasterio.open(output_4326_raster_clipped, "w", **out_meta) as dest:
                    dest.write(out_image)

                # 3. need to transform the clipped ghsl to utm
                output_utm_raster_clipped = output_folder + \
                    prepend_file_text + "_utm_clipped.tif"
                gdal.Warp(output_utm_raster_clipped,
                          output_4326_raster_clipped, dstSRS=utm_crs)

                with rasterio.open(output_utm_raster_clipped) as src:
                    pixelSizeX, pixelSizeY = src.res

                    array = src.read()

                    # Reclassify
                    #array[array < 1985] = 0
                    #print(np.count_nonzero(array == 2015))
                    year_dict = {}
                    for year in range(1985, 2016):
                        # print(year)
                        # resolution of each pixel about 30 sq meters. Multiply by pixelSize and Divide by 1,000,000 to get sq km
                        #year_dict[year] = np.count_nonzero(array == year)
                        if year == 1985:
                            year_dict[year] = np.count_nonzero(
                            array == year) * pixelSizeX * pixelSizeY / 1000000
                        else:
                            year_dict[year] = np.count_nonzero(
                                array == year) * pixelSizeX * pixelSizeY / 1000000 + year_dict[year-1]

                    # save CSV
                    import csv
                    with open(output_folder + '/' + prepend_file_text + "_stats_%s.csv" % file[:-4], 'w') as f:
                        f.write("year,cumulative sq km\n")
                        for key in year_dict.keys():
                            f.write("%s,%s\n" % (key, year_dict[key]))

                # Reclassify
                out_image[out_image < 1985] = 0
                out_image[(out_image <= 2015) & (out_image >= 2006)] = 4
                out_image[(out_image < 2006) & (out_image >= 1996)] = 3
                out_image[(out_image < 1996) & (out_image >= 1986)] = 2
                out_image[out_image == 1985] = 1

                output_4326_raster_clipped_reclass = output_folder + \
                    prepend_file_text + "_WSF_4326_reclass" + \
                    "_%s.tif" % file[:-4]

                # save for stats
                with rasterio.open(output_4326_raster_clipped_reclass, "w", **out_meta) as dest:
                    dest.write(out_image)

                # remove temporary clipped raster files
                # fileList = glob.glob(
                #     output_4326_raster_clipped[:-3]+'*', recursive=True)
                # for filePath in fileList:
                #     try:
                #         os.remove(filePath)
                #     except OSError as e:
                #         print("Error while deleting file")
                #         print("Failed with:", e.strerror)  # look what it says
                # fileList = glob.glob(
                #     output_utm_raster_clipped[:-3]+'*', recursive=True)
                # for filePath in fileList:
                #     try:
                #         os.remove(filePath)
                #     except OSError as e:
                #         print("Error while deleting file")
                #         print("Failed with:", e.strerror)  # look what it says


def clipdata(admin_folder, input_raster, output_folder, prepend_file_text):

    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):
            print(file)
            with fiona.open(admin_folder + '/' + file, "r") as shapefile:
                features = [feature["geometry"] for feature in shapefile]

                with rasterio.open(input_raster) as src:
                    # shapely presumes all operations on two or more features exist in the same Cartesian plane.
                    out_image, out_transform = rasterio.mask.mask(
                        src, features, crop=True)
                    out_meta = src.meta.copy()

                out_meta.update({"driver": "GTiff",
                                 "height": out_image.shape[1],
                                 "width": out_image.shape[2],
                                 "transform": out_transform})

                with rasterio.open(output_folder + '/' + prepend_file_text + "_%s.tif" % file[:-4], "w", **out_meta) as dest:
                    dest.write(out_image)

# Same as clipdata(), but set the nodata value to -99999
def clipdata_elev(admin_folder, input_raster, output_folder, prepend_file_text):

    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):
            print(file)
            with fiona.open(admin_folder + '/' + file, "r") as shapefile:
                features = [feature["geometry"] for feature in shapefile]

                with rasterio.open(input_raster) as src:
                    out_image, out_transform = rasterio.mask.mask(src, features, crop = True, nodata = -99999)
                    out_meta = src.meta.copy()

                out_meta.update({"driver": "GTiff",
                                "height": out_image.shape[1],
                                "width": out_image.shape[2],
                                "transform": out_transform,
                                'nodata': -99999})

                with rasterio.open(output_folder + '/' + prepend_file_text + "_%s.tif" % file[:-4], "w", **out_meta) as dest:
                    dest.write(out_image)


print('starting processing')

# 01 population
clipdata(admin_folder, pop_file, output_folder, prepend_file_text)

# 02 urban change
# clipdata_urban_change(admin_folder, ghsl_urban_change_file, output_folder, '02_urban_change')
clipdata_wsf(admin_folder, ghsl_urban_change_file,
             output_folder, '02_urban_change')

# 03 land cover
# if tifCounter > 0:
#     clipdata(admin_folder, landcover_file, output_folder, '03_landcover')

# 04 elevation
if tifCounter > 0:
    clipdata_elev(admin_folder, elevation_file, output_folder, '04_elevation')

# 06 solar
clipdata(admin_folder, solar_file, output_folder, '06_solar')

# 07 air quality
clipdata(admin_folder, cfg["07_air_quality"] +
         'sdei-global-annual-gwr-pm2-5-modis-misr-seawifs-aod-2016-geotiff/gwr_pm25_2016.tif', output_folder, '07_air_quality')

# 11 landslides
clipdata(admin_folder, cfg["11_landslides"] +
         'suscV1_1.tif', output_folder, '11_landslides')

# 13 imperviousness
clipdata(admin_folder, imperv_file, output_folder, '13_imperviousness')


# NOT done by this script
# 08 uhi: GEE
# 09 flooding: toolbox
# 12 earthquakes: screenshot