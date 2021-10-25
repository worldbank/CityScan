## Author: Aijing Li aijingli@gsd.harvard.edu
## 2021-june-12 update:
## use ReplaceDataSource for layer (NOT findAndReplaceWorkspacePath) to support change of dataset name, with manual string match and replace to support parttial change of workpath
## work for stretched, classified and unique value raster & feature class, but might take long/memory space if on classified
## added a function to update legend labels for classified raster, in mainbody set to proceed only if classified raster with 2+ classes, but can be changed
## On workflow/file management:
## data workpath have EXACT folder structure
## dataset name must have EXACT naming logic, but can have city name changed inside, eg. Zinder_WSF.tif & Tillaberi_WSF.tif are okay
## city name in data workpath and dataset name is not case sensitive, but must match, eg. Zinder & Tillaberi, zinder & tillaberi, ZINDER & TILLABERI
## 2021-june-23 update:
## added coordinate system reprojection for each map, all invisible layers are removed before reprojection for speed-up
## round up legend labels, details see method reformulate_legend_labels()
## fixed extent default to AOI.shp + 8000(30000 for regional administrative map) for all maps after the first map containning AOI.shp
## 2021-july-03 update:
## add flood analysis, fathom data is cropped to a 50 km buffer around AOI
## flood mxds has to contain "fu pu comb" as key words for table calculation


########################################################SET UP############################################################
import arcpy, os
import numpy 
import pandas as pd
from arcpy.sa import *
from arcpy import env

try:
    arcpy.CheckOutExtension("Spatial")
except:
    arcpy.AddError("Didn't find license for spatial analyst extension")

arcpy.env.overwriteOutput = True
map_path = arcpy.GetParameterAsText(0)
mapOutFolder = arcpy.GetParameterAsText(1)
source_city_path = arcpy.GetParameterAsText(2)
new_city_path = arcpy.GetParameterAsText(3)
source_city = arcpy.GetParameterAsText(4)
new_city = arcpy.GetParameterAsText(5)

coordinate_sys_name = ""
coordinate_sys_name = arcpy.GetParameterAsText(6) #optional
zoomout = arcpy.GetParameterAsText(7) #optional
regionzoomout= arcpy.GetParameterAsText(8) #optional

depth_fu = arcpy.GetParameterAsText(9) #optional
depth_pu = arcpy.GetParameterAsText(10) #optional
if depth_fu == "":
    depth_fu = 0.15
else:
    depth_fu = float(depth_fu)
if depth_pu == "":
    depth_pu = 0.15
else:
    depth_pu = float(depth_pu)

contour_intv = arcpy.GetParameterAsText(11) #optional
if contour_intv != "":
    contour_intv = float(contour_intv)


logOutFile = mapOutFolder + "\\Execution_Log.txt"
replaceDictionary = mapOutFolder + "\\Replace_Dictionary .txt"
outFile = open(logOutFile,'w')
outDic = open(replaceDictionary,'w')
arcpy.env.workspace = map_path 

#############################################################  END OF SET UP  ################################################################

#############################################################START OF HELPER FUNCTIONS########################################################

def replace_name(old, source_city, new_city):
    new = ''
    multi = False
    multi = len(new_city.split(" ")) > 1 or len(new_city.split("_")) > 1
    if source_city in old:
        new = old.replace(source_city,new_city,100)[:]
    elif source_city.capitalize() in old and multi == False:        
        new = old.replace(source_city.capitalize(),new_city.capitalize(),100)[:]
    elif source_city.capitalize() in old and multi == True:        
        new = old.replace(source_city.title(),new_city.title(),100)[:]        
    elif source_city.upper() in old:
        new = old.replace(source_city.upper(),new_city.upper(),100)[:] 
    elif source_city.lower() in old:
        new = old.replace(source_city.lower(),new_city.lower(),100)[:] 
    else:
        return old
    return new

def round_up_breaklist(breaklist, tonum=10):
    last = -1000
    newlist = []
    raw = 0
    maxval = breaklist[-1]
    for i in range(0,len(breaklist)):        
        if i != 0:
            raw = round(breaklist[i]/tonum)*tonum
        else:
            raw = breaklist[i]
        while raw <= last:
            raw += tonum
        last = raw
        newlist.append(last)
    newlist[-1] = maxval
    return newlist 


def reformulate_legend_labels(lyr): #update in place
    if lyr.symbologyType != "RASTER_CLASSIFIED" and lyr.symbologyType != "GRADUATED_COLORS":
        arcpy.AddWarning("WARNING: for map %s a file that is not classified raster is passed into symbology and legend updating function" % mapDoc)   
    ClsLabels = []
    i = 0
    Clsbreak = lyr.symbology.classBreakValues

    if type(Clsbreak[-1]) == "int":
        arcpy.AddWarning("WARNING: for map %s a file that is not float in datatype is passed into symbology and legend updating function" % mapDoc) 
        return None

    if lyr.symbology.classBreakValues[-1] >= 100:
        if Clsbreak[-1] - Clsbreak[0] >= 25:
            Clsbreak = round_up_breaklist(Clsbreak, 10)
        else:
            Clsbreak = round_up_breaklist(Clsbreak, 5)
        while i <= len(Clsbreak)-2:
            ClsLabels.append("{:.0f}".format(Clsbreak[i]) + " - " + "{:.0f}".format(Clsbreak[i+1]))
            i = i + 1
            
    elif lyr.symbology.classBreakValues[-1] >= 25:
        Clsbreak = round_up_breaklist(Clsbreak, 5)
        while i <= len(Clsbreak)-2:
            ClsLabels.append("{:.0f}".format(Clsbreak[i]) + " - " + "{:.0f}".format(Clsbreak[i+1]))
            i = i + 1
            
    elif lyr.symbology.classBreakValues[-1] >= 5:
        Clsbreak = round_up_breaklist(Clsbreak, 0.5)
        while i <= len(Clsbreak)-2:
            ClsLabels.append("{:.1f}".format(Clsbreak[i]) + " - " + "{:.1f}".format(Clsbreak[i+1]))
            i = i + 1 
            
    else:
        while i <= len(Clsbreak)-2:
            ClsLabels.append("{:.2f}".format(Clsbreak[i]) + " - " + "{:.2f}".format(Clsbreak[i+1]))
            i = i + 1     
    print >>outFile, "legend breaks:", Clsbreak 
    print >>outFile, "legend labels:", ClsLabels
    lyr.symbology.classBreakValues = Clsbreak
    lyr.symbology.classBreakLabels = ClsLabels
    
    return None

def record_file_dictionary(source_city_path, new_city_path, source_city, new_city):
    dic = {}
    dic_newpath = {}
    walk = []
    root = ""
    fu_datasource = ""
    pu_datasource = ""
    walk = arcpy.da.Walk(source_city_path)
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if filename not in dic:
                new_filename = replace_name(filename, source_city, new_city)
                dic[filename] = new_filename
                dic_newpath[new_filename] = ""
    
    new_walk = arcpy.da.Walk(new_city_path)
    for dirpath, dirnames, new_filenames in new_walk:
        for new_filename in new_filenames:
            if new_filename in dic_newpath:
                dic_newpath[new_filename] = dirpath
    

    print >>outFile, "finished walk through new and old data folders, find %s files" % len(dic_newpath)
    return dic, dic_newpath 

def find_prep_data(new_city_path):
    prep_dict = {}
    walk = []
    fu_datasource = ""
    pu_datasource = ""
    sol_list = []
    walk = arcpy.da.Walk(new_city_path)
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if "FU_1in5" in filename and filename.endswith(".tif"):
                prep_dict["fu_datasource"] = dirpath
            elif "P_1in5" in filename and filename.endswith(".tif"):               
                prep_dict["pu_datasource"] = dirpath
                prep_dict["root"] = os.path.dirname(prep_dict["pu_datasource"])
            elif "AOI" in filename and filename.endswith(".shp") and not "isochrone" in filename: 
                prep_dict["AOI_path"] = os.path.join(dirpath, filename)
            elif "elevation" in filename and filename.endswith(".tif"):
                prep_dict["elev_path"] = os.path.join(dirpath, filename)
            elif "SOL" in filename and filename.endswith(".tif"):
                sol_list.append(os.path.join(dirpath, filename) ) 
                prep_dict["sol_list"] = sol_list
            elif "air" in filename and filename.endswith(".tif"):
                prep_dict["air_path"] = os.path.join(dirpath, filename)
            elif "edge" in filename and filename.endswith(".shp"):
                prep_dict["edge"] = os.path.join(dirpath, filename)
            else:
                pass
        
    print >>outFile, "Pre-processing data:"
    print >>outFile, prep_dict

    return prep_dict

def classify_flood_risk(root, datasource, floodtype, depth, polygon):
    ras5 = ""
    ras10 = ""
    ras20 = ""
    ras50 = ""
    ras70 = ""
    ras100 = ""
    ras200 = ""
    ras250 = ""
    ras500 = ""
    ras1000 = ""
    arcpy.env.workspace = datasource
    rasList = arcpy.ListRasters("*","TIF")
    diff = ""
    if floodtype == "pu":
        diff = "P"
    elif floodtype == "fu":
        diff = "FU"

    
    for ras in rasList:
        rasname = "".join(ras.split(".")[:-1])
        
        if "1in5." in ras and diff in ras:
            ras5 = Raster(ras)
            ras5 = ExtractByMask(ras5, polygon)            
        elif "1in10." in ras and diff in ras:
            ras10 = Raster(ras)
            ras10 = ExtractByMask(ras10, polygon)
        elif "1in20." in ras and diff in ras:
            ras20 = Raster(ras)
            ras20 = ExtractByMask(ras20, polygon)
        elif "1in50." in ras and diff in ras:
            ras50 = Raster(ras)
            ras50 = ExtractByMask(ras50, polygon)
        elif "1in75." in ras and diff in ras:
            ras75 = Raster(ras)
            ras75 = ExtractByMask(ras75, polygon)
        elif "1in100." in ras and diff in ras:
            ras100 = Raster(ras)
            ras100 = ExtractByMask(ras100, polygon)
        elif "1in200." in ras and diff in ras:
            ras200 = Raster(ras)
            ras200 = ExtractByMask(ras200, polygon)
        elif "1in250." in ras and diff in ras:
            ras250 = Raster(ras)
            ras250 = ExtractByMask(ras250, polygon)
        elif "1in500." in ras and diff in ras:
            ras500 = Raster(ras)
            ras500 = ExtractByMask(ras500, polygon)
        elif "1in1000" in ras and diff in ras:
            ras1000 = Raster(ras)
            ras1000 = ExtractByMask(ras1000, polygon)
        else:
            pass
    
    try:
        class1 = Con(ras5 > depth, 1, 0)  |  Con(ras10  >  depth, 1, 0)
        class2 = Con(class1 <= 0,  1, 0)   &    (  Con(ras20  >  depth, 1, 0) |  Con(ras50  >  depth, 1, 0)  |  Con(ras75  >  depth, 1, 0) | Con(ras100  > depth, 1, 0))  
        class3 = (Con(class2 <= 0, 1, 0)    &  Con(class1  <= 0,  1, 0))  &  (  Con(ras200  >  depth, 1, 0) |  Con(ras250  >  depth, 1, 0) |  Con(ras500  >  depth, 1, 0)  |  Con(ras1000  > depth, 1, 0))
        arcpy.ProjectRaster_management(class1, root+"\\class1_"+floodtype+".tif", coordinate_sys_name)
        arcpy.ProjectRaster_management(class2, root+"\\class2_"+floodtype+".tif", coordinate_sys_name)
        arcpy.ProjectRaster_management(class3, root+"\\class3_"+floodtype+".tif", coordinate_sys_name)
        print >>outFile, "generated", root, floodtype, "classes"
    except Exception as e:
        print >>outFile, "Exception: ", e
        print >>outFile, "WARNING: One of the fathom raw raster for 1 in 5, 10, 20, ...1000 might be missing. Flood classification fails."        
        arcpy.AddWarning("WARNING: One of the fathom raw raster for 1 in 5, 10, 20, ...1000 might be missing. Flood classification fails.")
    
    return None

def generate_comb_rasters(root,fu_datasource,pu_datasource,depth_fu,depth_pu):
    InRas1 = ""
    InRas2 = "" 
    InRas3 = ""
    InRas4 = "" 
    InRas5 = ""
    InRas6 = "" 
    try:
        InRas1 = Raster(root+"\\class1_fu.tif")
        InRas2 = Raster(root+"\\class1_pu.tif")
        class1_comb = CellStatistics([InRas1, InRas2], "MAXIMUM", "DATA")
        class1_comb.save(root+"\\class1_comb.tif")

        InRas3 = Raster(root+"\\class2_fu.tif")
        InRas4 = Raster(root+"\\class2_pu.tif")
        class2_comb = CellStatistics([InRas3, InRas4], "MAXIMUM", "DATA")
        class2_comb.save(root+"\\class2_comb.tif")

        InRas5 = Raster(root+"\\class3_fu.tif")
        InRas6 = Raster(root+"\\class3_pu.tif")
        class3_comb = CellStatistics([InRas5, InRas6], "MAXIMUM", "DATA")
        class3_comb.save(root+"\\class3_comb.tif")

        class_all_fu = CellStatistics([InRas1, InRas3,InRas5], "MAXIMUM", "DATA")
        class_all_pu = CellStatistics([InRas2, InRas4,InRas6], "MAXIMUM", "DATA")
        class_all = CellStatistics([class_all_fu, class_all_pu], "MAXIMUM", "DATA")
        class_all_fu.save(root+"\\class_all_fu.tif")
        class_all_pu.save(root+"\\class_all_pu.tif")
        class_all.save(root+"\\class_all_comb.tif")
    except Exception as e:
        print >>outFile, "Exception: ", e 
        print >>outFile, "WARNING: One of the fathom raw raster for 1 in 5, 10, 20, ...1000 might be missing. Flood classification fails."
        arcpy.AddWarning("WARNING: One of the fathom raw raster for 1 in 5, 10, 20, ...1000 might be missing. Flood classification fails.")
    return None

def addsource(fc):    
    
    fc_view = fc.split(".")[0] + ".dbf"
    arcpy.AddField_management(fc_view,"source","TEXT")
    with arcpy.da.UpdateCursor(fc, "source") as cursor:
        for row in cursor:
            row[-1] = os.path.basename(fc).split(".")[0]
            cursor.updateRow(row)
    return None

def generate_slope(elev_path):
    ras_elev = arcpy.Raster(elev_path)
    ras_slope = Slope(ras_elev)
    out_path = os.path.dirname(elev_path)
    ras_slope.save(os.path.join(out_path,"slope.tif"))
    return None

def find_minmax_sol(sol_list):
    ras = ""
    maxv = 0
    minv = 1000
    valmax = 0
    valmin = 0
    for path in sol_list:
        ras = arcpy.Raster(path)
        ras = Float(ras)
        array = arcpy.RasterToNumPyArray(ras,nodata_to_value = numpy.nan)
        clean = array[~(numpy.isnan(array))]
        valmax = numpy.max(clean) 
        valmin = numpy.min(clean)
        if valmax > maxv:
            maxv = valmax
        if valmin < minv:
            minv = valmin      
    return maxv, minv

def generate_contour(elev_path,contour_intv):
    ras_elev = arcpy.Raster(elev_path)
    root_dir = os.path.dirname(elev_path)
    copy_elev = arcpy.CopyRaster_management(ras_elev,os.path.join(new_city_path,"copy_elev.tif"))
    foc = FocalStatistics(copy_elev, NbrCircle(3, "CELL"),"MEAN","NODATA")
    foc.save(os.path.join(new_city_path,"focstat_elev.tif"))
    Contour(foc, os.path.join(new_city_path,"contour1.shp"), contour_intv, 0)
    Contour(foc, os.path.join(new_city_path,"contour5.shp"), contour_intv*5, 0)
    return None 

def generate_air_legend(air_path):
    ras = arcpy.Raster(air_path)
    ras = Float(ras)
    array = arcpy.RasterToNumPyArray(ras,nodata_to_value = numpy.nan)
    clean = array[~(numpy.isnan(array))]
    valmax = numpy.max(clean) 
    valmin = numpy.min(clean)
    clsbreak = [5,10,15,20,30,40,50,100]
    # if valmax > 100:
    #     clsbreak.append(valmax)
    #     labels.append("{:.0f}".format(valmax) )
    return clsbreak

def select_major_road(edge_path):
    out_rd = os.path.join(os.path.dirname(edge_path),"major_road.shp")
    sql = """  "highway" = 'primary'  OR "highway" = 'trunk' OR "highway" = 'motorway' """
    arcpy.Select_analysis(edge_path, out_rd, sql)
    return out_rd

#############################################################END OF HELPER FUNCTIONS#############################################################

##########################################################  PRE-PROCESSING ######################################################################
            #############  GENERATE DERIVED DATA  ############
arcpy.AddMessage("Executing Pre-processing...")
sol_max = None
sol_min = None
con_max = 0
con_min = 0
prep_dict = find_prep_data(new_city_path)
AOI_path = prep_dict["AOI_path"]
elev_path = prep_dict["elev_path"]
air_path = prep_dict["air_path"]
edge_path = prep_dict["edge"]
try:
    # root = prep_dict["root"]
    root = new_city_path
    fu_datasource = prep_dict["fu_datasource"]
    pu_datasource = prep_dict["pu_datasource"]
except Exception as e:
    print >>outFile, "Exception: ", e
    arcpy.AddWarning("WARNING: flood data is missing")
    print >>outFile, "WARNING: flood data is missing"    

try:
    sol_list = prep_dict["sol_list"]
except Exception as e:
    print >>outFile, "Exception: ", e
    arcpy.AddWarning("WARNING: SOL data is missing")
    print >>outFile, "WARNING: SOL data is missing"       


ras_elev = arcpy.Raster(elev_path)
con_max = ras_elev.maximum
con_min = ras_elev.minimum

#get AOI extent for all map
AOI_lyr = arcpy.mapping.Layer(AOI_path)
ext = AOI_lyr.getExtent()
print >>outFile, "Get AOI extent", ext
print >>outFile, "original AOI extent sf is", ext.spatialReference
ext = ext.projectAs(coordinate_sys_name)
print >>outFile, "Project AOI extent in new sf:", ext

#generate major roads 
major_rd_path = select_major_road(edge_path)

#generate air legends
air_clsbreak = generate_air_legend(air_path)

#generate contour 
try:
    con_max-con_min
except Exception as e:
    print >>outFile, "Exception: ", e
    arcpy.CalculateStatistics_management(ras_elev)                       
    con_max = ras_elev.maximum
    con_min = ras_elev.minimum

if contour_intv == "":
    if con_max-con_min != 0:
        if con_max-con_min > 250:
            dif = (con_max-con_min)/500
            contour_intv = round(dif)*5
            if contour_intv == 0:
                contour_intv = 1
        elif con_max-con_min > 100:
            contour_intv = 2
        else:
            contour_intv = 1
    else:
        contour_intv = 1
else:
    pass

#generate slope raster
try:
    generate_slope(elev_path)
    generate_contour(elev_path,contour_intv)
except Exception as e:
    print >>outFile, "Exception: ", e
    arcpy.AddWarning("WARNING: elevation raster might be missing. Generate slope and contour skipped")
    print >>outFile, "WARNING: elevation raster might be missing. Generate slope and contour skipped"

# get max min for serial SOL
try:
    sol_max, sol_min = find_minmax_sol(sol_list)
    print >>outFile, "serial map SOL max is %s" % sol_max
    print >>outFile, "serial map SOL min is %s" % sol_min
except Exception as e:
    print >>outFile, "Exception: ", e
    print >>outFile, "WARNING: Monthly SOL might be missing. Calculate min and max for serial maps skipped"
    arcpy.AddWarning("WARNING: Monthly SOL might be missing. Calculate min and max for serial maps skipped")

#generate flood analysis data
try:
    aoi_poly_path = new_city_path+"\\aoi_poly.shp"
    arcpy.MinimumBoundingGeometry_management(AOI_path, aoi_poly_path,"ENVELOPE")
    aoi_poly = arcpy.mapping.Layer(aoi_poly_path)
    buffer_path = new_city_path + "\\buffer_aoi.shp"
    arcpy.analysis.Buffer(aoi_poly, new_city_path+"//buffer_aoi.shp", "50000 Meters")
    buffer = arcpy.mapping.Layer(buffer_path)

    classify_flood_risk(new_city_path, fu_datasource, "fu", depth_fu, buffer)
    classify_flood_risk(new_city_path, pu_datasource, "pu", depth_pu, buffer)
    generate_comb_rasters(new_city_path,fu_datasource,pu_datasource,depth_fu,depth_pu)

    flood_success = True
except Exception as e:
    print >>outFile, "Exception: ", e
    print >>outFile, "WARNING: Fail to generate derived data from fathom flood raw data"
    arcpy.AddWarning("WARNING: Fail to generate derived data from fathom flood raw data")
    flood_success = False

dic, dic_newpath = record_file_dictionary(source_city_path, new_city_path, source_city, new_city)

print >>outDic, "NAME REPLACEMENT"
print >>outDic, dic
print >>outDic, "FILE PATH REPLACEMENT"
print >>outDic, dic_newpath
            ########## END OF GENERATE DERIVED DATA ##########


            ##################### FLOOD AREA OVERLAP ANALYSIS ###################
pt_list = []
dic_full = {}

if flood_success == True:           
    for i in dic_newpath.keys():
        if "WSF" in i and "tif" in i and "reclass" in i:
            dic_full["wsf"] = os.path.join(dic_newpath[i],i)
        elif "population" in i and "tif" in i:
            dic_full["pop"] = os.path.join(dic_newpath[i],i)
        elif "health" in i and "shp" in i and "isochrone" not in i:
            dic_full["health"] = os.path.join(dic_newpath[i],i)
        elif "fire" in i and "shp" in i:
            dic_full["fire"] = os.path.join(dic_newpath[i],i)
        elif "police" in i and "shp" in i:
            dic_full["police"] = os.path.join(dic_newpath[i],i)
        elif "school" in i and "shp" in i and "isochrone" not in i:
            dic_full["school"] = os.path.join(dic_newpath[i],i)
        elif "class_all_comb" in i and "tif" in i:
            dic_full["comb"] = os.path.join(dic_newpath[i],i)
        elif "class_all_fu" in i and "tif" in i:
            dic_full["fu"] = os.path.join(dic_newpath[i],i)
        elif "class_all_pu" in i and "tif" in i:
            dic_full["pu"] = os.path.join(dic_newpath[i],i)
        else:
            pass
else:
    pass

print >>outDic, "FLOOD DIC FULL"
print >>outDic, dic_full

try:
    ## analyse overlap with WSF & Population 
    for flood in ["fu","pu","comb"]:
        for t in ["wsf"]:  
            output_table = os.path.join(new_city_path, flood+"_"+t+"_"+"area.dbf")
            TabulateArea(arcpy.Raster(dic_full[flood]), "Value", arcpy.Raster(dic_full[t]), "Value", output_table) 
            out_excel = os.path.join(mapOutFolder, flood+"_"+t+"_"+"area.xls")
            arcpy.TableToExcel_conversion(output_table, out_excel)
        for t in ["pop"]:
            ras_pop = arcpy.Raster(dic_full["pop"])
            arcpy.CalculateStatistics_management(ras_pop)  
            ras_pop = Con(ras_pop > ras_pop.mean,1)
            output_table = os.path.join(new_city_path, flood+"_"+t+"_"+"area.dbf")
            TabulateArea(arcpy.Raster(dic_full[flood]), "Value", ras_pop, "Value", output_table) 
            out_excel = os.path.join(mapOutFolder, flood+"_"+t+"_"+"area.xls")
            arcpy.TableToExcel_conversion(output_table, out_excel)
except Exception as e:
    print >>outFile, "Exception: ", e
    arcpy.AddWarning("WARNING: Flood analysis with WSF & population tables generation encounters an error and is skipped")
    print >>outFile, "WARNING: Flood analysis with WSF & population tables generation encounters an error and is skipped"

try:
    ## analyse overlap with OSM infra
    ras_fu = arcpy.Raster(dic_full["fu"])
    ras_pu = arcpy.Raster(dic_full["pu"])
    ras_comb = arcpy.Raster(dic_full["comb"])

    dic_full["fu_fc"] = os.path.join(new_city_path, "fu_domain.shp")
    dic_full["pu_fc"] = os.path.join(new_city_path, "pu_domain.shp")
    dic_full["comb_fc"] = os.path.join(new_city_path, "comb_domain.shp")

    arcpy.RasterToPolygon_conversion(ras_fu, dic_full["fu_fc"], "NO_SIMPLIFY")
    arcpy.RasterToPolygon_conversion(ras_pu, dic_full["pu_fc"], "NO_SIMPLIFY")
    arcpy.RasterToPolygon_conversion(ras_comb, dic_full["comb_fc"], "NO_SIMPLIFY")


    pt_list = []
    for key in ["fire","school","health","police"]:
        try:
            dic_full[key]
            addsource(dic_full[key])
            pt_list.append(dic_full[key])
        except Exception as e:
            print >>outFile, "Exception: ", e
            print >>outFile, "WARNING: OSM SHP for %s is missing, calculation for flood area for this type of point shapefiles is skipped" % key
            arcpy.AddWarning("WARNING: OSM SHP for %s is missing, calculation for flood area for this type of point shapefiles is skipped" % key)


    try: 
        out_ptmerge = os.path.join(new_city_path, "osm_pt_merge.shp")
        arcpy.management.Merge(pt_list, out_ptmerge)
    except arcpy.ExecuteError: 
        arcpy.AddWarning("WARNING: Field length too long")
        print >>outFile, "WARNING: Field length too long"
        pt_list = []
        fieldlen = 200
        fieldname = "name"
        for key in ["fire","school","health","police"]:
            try:
                dic_full[key]
                addsource(dic_full[key])
                outloc = os.path.dirname(dic_full[key])
                outfc = key+"2"
                fms = arcpy.FieldMappings()
                infc = dic_full[key]
                fields = arcpy.ListFields(infc)
                skipfields = ["OBJECTID", "FID", "Shape"]
                fms = arcpy.FieldMappings()
                fields = arcpy.ListFields(infc)
                for field in fields:
                    if field.name in skipfields:
                        pass
                    else:
                        fm = arcpy.FieldMap()
                        fm.addInputField(infc, field.name)
                        if field.name == fieldname:
                            newfield = fm.outputField
                            newfield.length = fieldlen
                            fm.outputField = newfield
                        fms.addFieldMap(fm)
                arcpy.FeatureClassToFeatureClass_conversion(infc, outloc, outfc, field_mapping=fms)        
                pt_list.append(os.path.join(outloc,outfc+".shp"))
            except KeyError:
                pass
        out_ptmerge = os.path.join(new_city_path, "osm_pt_merge.shp")
        arcpy.management.Merge(pt_list, out_ptmerge)

    finally:
        for flood in ["fu","pu","comb"]:
            out_table_osmpt = os.path.join(new_city_path, flood+"_intersect_osm_pt.dbf")
            out_table_road = os.path.join(new_city_path, flood+"_intersect_majorroad.dbf")
            fc = flood + "_fc"
            arcpy.TabulateIntersection_analysis(dic_full[fc], "gridcode", out_ptmerge, out_table_osmpt, "source")
            arcpy.TabulateIntersection_analysis(dic_full[fc], "gridcode", major_rd_path, out_table_road)
            out_excel_osmpt = os.path.join(mapOutFolder, flood+"_osmpt.xls")
            out_excel_road = os.path.join(mapOutFolder, flood+"_majorroad.xls")
            arcpy.TableToExcel_conversion(out_table_osmpt, out_excel_osmpt)
            arcpy.TableToExcel_conversion(out_table_road, out_excel_road)

except Exception as e:
    print >>outFile, "Exception: ", e
    arcpy.AddWarning("WARNING: Flood analysis with OSM tables generation encounters an error and is skipped")
    print >>outFile, "WARNING: Flood analysis with OSM tables generation encounters an error and is skipped"


            ################## END OF FLOOD AREA OVERLAP ANALYSIS #################   

################################################## END OF PRE-PROCESSING ###################################################


########################################  MAIN BODY: ITERATE THROUGH MAPS & REPLACE ########################################
arcpy.AddMessage("Executing Main Loop...")
arcpy.env.workspace = map_path 
mapList = arcpy.ListFiles("*.mxd")
runtime_flag = 0
wsf_flag = 0
pop_flag = 0

for mapDoc in mapList:
    print >>outFile,  "_" * 25
    print >>outFile, mapDoc
    mxd = arcpy.mapping.MapDocument(os.path.join(map_path, mapDoc))
    for df in arcpy.mapping.ListDataFrames(mxd):
        for lyr in arcpy.mapping.ListLayers(mxd):            
            if lyr.supports("DATASOURCE") and lyr.visible == True:
                print >>outFile," Enter replacement"
                print >>outFile, " processing layer: ", lyr
                print >>outFile,"        lyr.workspacePath is： ",lyr.workspacePath
                print >>outFile,"        lyr.dataSource is:  ",lyr.dataSource

                workpath = lyr.workspacePath[:]
                filename = os.path.basename(lyr.dataSource)
                try:
                    new_filename = dic[filename]
                
                    #If the layer is vector
                    if new_filename[-3:] == "shp":   
                        try:
                            new_path = dic_newpath[new_filename]    
                            new_filename = "".join(new_filename.split(".")[:-1])  
                            lyr.replaceDataSource(new_path, "SHAPEFILE_WORKSPACE", dataset_name = new_filename)
                        except ValueError as ve:
                            print >>outFile,"       Value Error", ve
                            print >>outFile,"       File infomration for SHP:", new_filename, new_path
                            print >>outFile,"       WARNING: Fail to replace file link for map %s, layer %s might be unmatched/invalid, please check the database" % (mapDoc,lyr.name)
                            arcpy.AddWarning("       WARNING: Fail to replace file link for map %s, layer %s might be unmatched/invalid, please check the database" % (mapDoc, lyr.name))
                            pass      
                    #the layer is raster  
                    elif lyr.isRasterLayer == True:                             
                        try:
                            new_path = dic_newpath[new_filename]        
                            lyr.replaceDataSource(new_path, "NONE", dataset_name = new_filename)
                        except ValueError as ve:
                            print >>outFile,"       Value Error", ve
                            print >>outFile,"       File infomration:", new_filename, new_path
                            print >>outFile,"       WARNING Value Error: Fail to replace file link for map %s, layer %s might be unmatched/invalid, please check the database" % (mapDoc,lyr.name)
                            arcpy.AddWarning("       WARNING Value Error: Fail to replace file link for map %s, layer %s might be unmatched/invalid, please check the database" % (mapDoc,lyr.name))
                            pass 
                        raster = arcpy.Raster(lyr.dataSource)
                        arcpy.CalculateStatistics_management(raster)
                    else:
                        pass
                    
                    lyr.name = replace_name(lyr.name, source_city, new_city)
                
                except KeyError as ke:
                    print >>outFile,"       Key Error", ke  
                    arcpy.AddWarning("WARNING: Didn't find file %s in the new city data folder" % filename)
                    print >>outFile, "WARNING: Didn't find file %s in the new city data folder" % filename

                                
                ## update symbology for classfied raster
                if (lyr.symbologyType == "RASTER_CLASSIFIED" or lyr.symbologyType == "GRADUATED_COLORS") and lyr.symbology.numClasses != 2:
                    if lyr.symbologyType == "RASTER_CLASSIFIED":
                        if "SOL" in lyr.datasetName and sol_max != None:
                            valmax = sol_max
                            valmin = sol_min
                            numCls = 5
                        elif "air" in lyr.datasetName:
                            pass
                        else:                                
                            valmax = raster.maximum
                            valmin = raster.minimum
                            print >>outFile, "raster.minimum is:", raster.minimum
                            print >>outFile, "raster.maximum is:", raster.maximum
                            numCls = lyr.symbology.numClasses                   
                            testcon = False
                            con1 = raster.minimum == raster.noDataValue
                            con2 = raster.minimum == None 
                            con3 = pd.isnull(raster.minimum) == True
                            testcon = con1 or con2 or con3
                            print >>outFile, "test condition:", testcon
                            
                            if testcon == True: 
                                raster = Float(raster)
                                array = arcpy.RasterToNumPyArray(raster,nodata_to_value = numpy.nan)
                                clean = array[~(numpy.isnan(array))]
                                print >>outFile, "array isnan", clean
                                valmax = numpy.max(clean) 
                                valmin = numpy.min(clean)                                
                                print >>outFile, "updated min is: ", valmin, "max is:", valmax
                    
                    elif lyr.symbologyType == "GRADUATED_COLORS": # this is only for feature class
                        arr = arcpy.da.FeatureClassToNumPyArray(lyr, lyr.symbology.valueField) 
                        valmax = numpy.max(arr[lyr.symbology.valueField])
                        valmin = numpy.min(arr[lyr.symbology.valueField])
                        numCls = lyr.symbology.numClasses 
                    
                    # for both "GRADUATED_COLORS"& "RASTER_CLASSIFIED"
                    if "air" in lyr.datasetName:                        
                        lyr.symbology.classBreakValues = air_clsbreak
                        reformulate_legend_labels(lyr)
                    
                    else:
                        try:
                            step = float(valmax-valmin)/numCls
                            i = 0
                            Clsbreak = [valmin]
                            while i < numCls:
                                Clsbreak.append(Clsbreak[-1]+step)
                                i = i + 1
    
                            lyr.symbology.classBreakValues = Clsbreak
                        except TypeError:
                            print >>outFile,"     WARNING: fail to access values for legend update"
                            arcpy.AddWarning("     WARNING: fail to access values for legend update for map %s" % mapDoc)


                        try:
                            reformulate_legend_labels(lyr)
                            print >>outFile,"       legend labels updated"
                        except Exception as e:
                            print >>outFile, "Exception: ", e
                            print >>outFile, "       WARNING: failed to update legend labels for this classified data"
                            arcpy.AddWarning("     WARNING: fail to change the legend labels for layer %s in %s" % (lyr.name, mapDoc))
                
            

            elif lyr.visible == False:
                arcpy.mapping.RemoveLayer(df, lyr)
            else:
                pass
            del lyr

        ## update extent of mxd from AOI ext obtained above
        print >>outFile, "before move ext scale:", df.scale  
        df.spatialReference = coordinate_sys_name
        df.extent = ext
        print >>outFile, "updated ext:", ext
        print >>outFile, "after move ext scale:", df.scale  
        if not "admin" in mapDoc:
            if zoomout == "":
                zoomout = 0.2
            df.scale = df.scale * (1+ float(zoomout))
            print >>outFile, "updated scale:", df.scale  
        elif "admin" in mapDoc:
            if regionzoomout == "":
                regionzoomout = 0.4
            df.scale =  df.scale * (1+ float(regionzoomout))
            print >>outFile, "updated scale for admin:", df.scale
      
        ## update coordinate system
        

        
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
                
        del df
            #################  END OF ITERATE THROUGH MAPS & REPLACE ############
     
            ############### OUTPUT FINISHED MAPS ##############    
    tempPath = mxd.filePath
    fileName = os.path.basename(tempPath)
    length = -(len(fileName.split("_"))-1)
    fileName = "_".join(fileName.split("_")[length:])
    print >>outFile,"New map name: ", new_city + "_"+ fileName
    
    new_map_path = mapOutFolder +"\\"+ new_city + "_" + fileName
    mxd.saveACopy(new_map_path)
    out_png = mapOutFolder+"\\"+new_city + "_" + fileName.split(".")[0]+".png"
    arcpy.mapping.ExportToPNG(mxd, out_png, resolution = 300)
    del mxd
            ########### END OF OUTPUT FINISHED MAPS ###########

