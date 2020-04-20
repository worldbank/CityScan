print('welcome to city scan 2')

print('note: You may add the -africa argument if you city is in Africa')
print('this flag will enable the higher resolution Africa ESACCI landcover')

print('note: Your input admin datasets should be using crs 4326')

import sys, os

import fiona
import rasterio
import rasterio.mask

import glob

from osgeo import gdal
import geopandas as gpd

import yaml

# load configuration file, this files stores the file locations for the global data files
with open("./global_data_config_personal.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

print(cfg)

#print('Number of arguments:', len(sys.argv), 'arguments.')
#print('Argument List:', str(sys.argv))

africa = 0
if any("africa" in s for s in sys.argv):
  print('africa argument exists')
  africa = 1
else:
  print('africa argument does not exist')

admin_folder = './admin'

for file in os.listdir(admin_folder):
        if file.endswith(".shp"):  
            print(file)

            print('attempt to read file')
            # 1. need to transform the input shp to correct prj
            admin_file = gpd.read_file(admin_folder + '/' + file)
            print('print admin_file crs')
            print(admin_file.crs)

            if not admin_file.crs == 'epsg:4326':
              sys.exit('admin file crs is not 4326, provide an admin file with crs than 4326 and re-run')


prepend_file_text = '01_population'

output_folder = './output/'

#population
pop_file = 'test'

for name in glob.glob('./01_population/*.tif'):
    print('inside glob')
    print(name)
    pop_file = name

#urban_change
ghsl_urban_change_file = 'test'

# for name in glob.glob('./02_urban_change/*.tif'):
#     print('inside glob')
#     print(name)
#     urban_change_file = name

#for name in glob.glob('../../GHS_BUILT_LDSMT_GLOBE_R2015B_3857_38_v1_0/*.vrt'):
#for name in glob.glob('../global_data_sets/02_urban_change/*.vrt'):
for name in glob.glob(cfg.02_urban_change + '*.vrt'):
    print('inside glob')
    print(name)
    ghsl_urban_change_file = name

#elevation
elevation_file = 'test'

tifCounter = len(glob.glob1('./04_elevation/',"*.tif"))

print('tifCounter, elevation files:')
print(tifCounter)

if tifCounter == 1:
  for name in glob.glob('./04_elevation/*.tif'):
    print('inside elevation glob single')
    print(name)
    elevation_file = name
elif tifCounter == 0:
  sys.exit('exiting because there are no elevation files')
else:
  for name in glob.glob('./04_elevation/*merged.tif'):
    print('inside elevation glob multiple')
    print(name)
    elevation_file = name

#solar
solar_file = 'test'

for name in glob.glob('./06_solar/*/PVOUT.tif'):
    print('inside solar glob')
    print(name)
    solar_file = name

def clipdata_urban_change(admin_folder, ghsl_urban_change_file, output_folder, prepend_file_text):
    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):  
            print(file)

            # 1. need to transform the input shp to correct prj
            admin_file = gpd.read_file(admin_folder + '/' + file)
            print('print admin_file crs')
            print(admin_file.crs)
            
            admin_file_3857 = admin_file.to_crs({'init': 'epsg:3857'})
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
                  out_image, out_transform = rasterio.mask.mask(src, features, crop=True)
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

                  gdal.Warp(new_output_file_name, output_3857_raster, dstSRS='EPSG:4326')

                  #remove temporary files
                  if os.path.exists(output_3857_raster):
                    os.remove(output_3857_raster)
                #remove temporary files
                print('admin_file_3857_shp keyword')
                print(admin_file_3857_shp[:-3])
                fileList = glob.glob(admin_file_3857_shp[:-3]+'*', recursive = True)
                admin_file_3857_shp_keyword = admin_file_3857_shp
                for filePath in fileList:
                  try:
                      os.remove(filePath)
                  except OSError:
                      print("Error while deleting file")

def clipdata(admin_folder, input_raster, output_folder, prepend_file_text):

    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):  
            print(file)
            with fiona.open(admin_folder + '/' + file, "r") as shapefile:
                features = [feature["geometry"] for feature in shapefile]

                with rasterio.open(input_raster) as src:
                    # shapely presumes all operations on two or more features exist in the same Cartesian plane.
                    out_image, out_transform = rasterio.mask.mask(src, features, crop=True)
                    out_meta = src.meta.copy()

                out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

                with rasterio.open(output_folder + '/' + prepend_file_text + "_%s.tif" % file[:-4], "w", **out_meta) as dest:
                    dest.write(out_image)

print('starting processing')

#01 population
clipdata(admin_folder, pop_file, output_folder, prepend_file_text)

#02 urban change
clipdata_urban_change(admin_folder, ghsl_urban_change_file, output_folder, '02_urban_change')

#03 land cover
if africa == 1:
  clipdata(admin_folder, cfg.03_Africa_20m_landcover + 'ESACCI-LC-L4-LC10-Map-20m-P1Y-2016-v1.0.tif', output_folder, '03_landcover')
else:
  clipdata(admin_folder, cfg.03_landcover + 'ESACCI-LC-L4-LCCS-Map-300m-P1Y-2015-v2.0.7.tif', output_folder, '03_landcover')

#04 elevation
clipdata(admin_folder, elevation_file, output_folder, '04_elevation')

#06 solar
clipdata(admin_folder, solar_file, output_folder, '06_solar')

#07 air quality
clipdata(admin_folder, cfg.07_air_quality + 'sdei-global-annual-gwr-pm2-5-modis-misr-seawifs-aod-2016-geotiff/gwr_pm25_2016.tif', output_folder, '07_air_quality')

#11 landslides
clipdata(admin_folder, cfg.11_landslides + 'global_landslides.tif', output_folder, '11_landslides')

