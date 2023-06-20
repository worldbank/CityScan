var geometry = 
    /* color: #d63000 */
    /* shown: false */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[18.991221423828545, 18.023012127336703],
          [18.991221423828545, 17.794330684690713],
          [19.23154735156292, 17.794330684690713],
          [19.23154735156292, 18.023012127336703]]], null, false);


// https://developers.google.com/earth-engine/tutorials/community/introduction-to-dynamic-world-pt-1 



var startDate = '2015-06-23';
var endDate = '2015-12-31';

var dw_past = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
             .filterDate(startDate, endDate)
             .filterBounds(geometry);
             

var dwVisParams = {
  min: 0,
  max: 8,
  palette: ['#419BDF', '#397D49', '#88B053', '#7A87C6',
    '#E49635', '#DFC35A', '#C4281B', '#A59B8F', '#B39FE1']
};

// Create a Mode Composite.
var classification = dw_past.select('label');
var dwComposite_past = classification.reduce(ee.Reducer.mode());


// Classes

// 0	#419bdf	water
// 1	#397d49	trees
// 2	#88b053	grass
// 3	#7a87c6	flooded_vegetation
// 4	#e49635	crops
// 5	#dfc35a	shrub_and_scrub
// 6	#c4281b	built
// 7	#a59b8f	bare
// 8	#b39fe1	snow_and_ice


// Rename the band names.
var dwComposite_past = dwComposite_past.rename(['classification']);

var pixelCountStats = dwComposite_past.reduceRegion({
    reducer: ee.Reducer.frequencyHistogram().unweighted(),
    geometry: geometry,
    scale: 10,
    maxPixels: 1e10
    });

var pixelCounts = ee.Dictionary(pixelCountStats.get('classification'));
print(pixelCounts);

// // Format the results to make it more readable.
// var classLabels = ee.List([
//     'trees', 'flooded_vegetation', 'crops',
//     'shrub_and_scrub', 'built', 'bare',
//     ]);

// // Rename keys with class names.
// var pixelCountsFormatted = pixelCounts.rename(
//   pixelCounts.keys(), classLabels);
// print(pixelCountsFormatted);

// Remove the 'bare' key from the dictionary
//var withoutBare = pixelCountsFormatted.remove(['bare']);
var withoutBare = pixelCounts.remove(['7']);

// Get the values of the resulting dictionary as a list
var valuesList = withoutBare.values();

// Reduce the list to the sum of its elements
var sum = ee.Number(valuesList.reduce(ee.Reducer.sum()));

print(sum);


// *******
// present date

var startDate = '2022-06-23';
var endDate = '2022-12-21';

var dw_present = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
             .filterDate(startDate, endDate)
             .filterBounds(geometry);
             

// Create a Mode Composite.
var classification = dw_present.select('label');
var dwComposite_present = classification.reduce(ee.Reducer.mode());

// Rename the band names.
var dwComposite_present = dwComposite_present.rename(['classification']);

var pixelCountStats = dwComposite_present.reduceRegion({
    reducer: ee.Reducer.frequencyHistogram().unweighted(),
    geometry: geometry,
    scale: 10,
    maxPixels: 1e10
    });

var pixelCounts = ee.Dictionary(pixelCountStats.get('classification'));
print(pixelCounts);

// Format the results to make it more readable.
// var classLabels = ee.List([
//     'trees', 'flooded_vegetation', 'crops',
//     'shrub_and_scrub', 'built', 'bare',
//     ]);

// Rename keys with class names.
// var pixelCountsFormatted = pixelCounts.rename(
//   pixelCounts.keys(), classLabels);
// print(pixelCountsFormatted);

// Remove the 'bare' key from the dictionary
var withoutBare = pixelCounts.remove(['7']);

// Get the values of the resulting dictionary as a list
var valuesList = withoutBare.values();

// Reduce the list to the sum of its elements
var sum_present = ee.Number(valuesList.reduce(ee.Reducer.sum()));

print(sum_present);

var non_bare_percent_change = (ee.Number(sum_present).subtract(ee.Number(sum))).divide(ee.Number(sum)).multiply(100);
  
var bare_percent_change = non_bare_percent_change.multiply(-1);  // Make it negative;

print('Percentage Change in Bare Area', bare_percent_change.format('%.2f'));


Export.image.toDrive({
  image: dwComposite_past.clip(geometry),
  description: 'bareArea past',
  region: geometry,
  scale: 10,
  maxPixels: 1e10
});


Export.image.toDrive({
  image: dwComposite_present.clip(geometry),
  description: 'bareArea past',
  region: geometry,
  scale: 10,
  maxPixels: 1e10
});