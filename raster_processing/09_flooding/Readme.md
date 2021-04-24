## SSBN Data
The SSBN Global Flood Hazard dataset is a gridded product at 3 arcsecond resolution (approximately 90 m but varies slightly with latitude) that shows the maximum expected water depth in metres at 10 different return periods (between 1-in-5 and 1-in-1000 years). The data has global coverage between 56°S and 60°N.

SSBN flood raster layers for each country include the following:

-Type of flooding (3): Pluvial (flooding caused by extreme local rainfall), Fluvial (flooding caused by rivers overtopping their banks), Urban (show the combined risk from fluvial and pluvial flooding in urban areas)
-Flood defenses incorporated (2): yes (defended), no (undefended)
Return periods (10): 5, 10, 20, 50, 75, 100, 200, 250, 500, 1000

Sometimes, the country is split into two or more zones (large countries) indicated by 1, 2 and so on.
Classification  
The workflow will differ based on fluvial, pluvial and combined undefended inputs for the different return periods. Let's start with combined:

1. Download data and create environment work space for fluvial, pluvial and output folders.
2. Project rasters to appropriate UTM and change files names for both fluvial and pluvial datasets
3. Create a sorted list of both FU and PU and make sure that return periods are in the same order
4. Create ONE tif file for each return period independently using the maximum of FU and PU grid at each grid cell; this results in 10 maps with flood depths
5. Create an annual estimated flood depth based on the 10 flood depths for each grid cell; this consolidates the 10 previous maps into ONE map based on the following conditions:

class1 = 5 or 10 year raster shows positive depth ( > 10% probability)
class2 = 5 and 10 year show -999 (no flood) BUT 20...100 year show positive depth ( 1-10% probability) 
class3 = up to 100 year show  -999 BUT 200...1000 show positive depth ( <1% probability)

Legend on the map:
- < 1% in any given year 
- 1-10% in any given year 
- > 10% in any given year 

## How it looks in Python:

```
class1 = Con(Raster5 > 0, 1, 0)  |  Con(Raster10  >  0, 1, 0) 
class2 = Con(class1 <= 0,  1, 0)   &    (  Con(Raster20  >  0, 1, 0) |  Con(Raster50  >  0, 1, 0)  |  Con(Raster75  >  0, 1, 0) | Con(Raster100  >  0, 1, 0))  
class2 = class2 * 2 # the operation is needed to return the desired value, otherwise the ouput is binary 0-1
class3 = (Con(class2 <= 0, 1, 0)    &  Con(class1  <= 0,  1, 0))  &  (  Con(Raster200  >  0, 1, 0) |  Con(Raster250  >  0, 1, 0) |  Con(Raster500  >  0, 1, 0)  |  Con(Raster1000  >  0, 1, 0)) 
class3 = class3 * 3 # the operation is needed to return the desired value, otherwise the output is binary 0-1
```

For fluvial and pluvial layers, the classification is the same using projected rasters, no maximum value calculation is needed.

