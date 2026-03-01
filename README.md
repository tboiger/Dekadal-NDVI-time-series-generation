# Dekadal-NDVI-time-series-generation

HOW TO USE

The provided module generates a dekadal NDVI time series for a given time period in an automated pipeline.
An OAuth Client with Client ID and Client Secret is needed to access the data.
Based on this authentification data, a given start and end date, as well as a AOI as polygon, the pipeline produces a time series of .tifs.
The main file contains a function "main_pipeline()" that executes the pipeline.
Additionally, a function for plotting the .tifs is provided.


Notes:

Cloud Masking:
I tried to include could masking into the evalscript by adding "CLM" to the input bands. However, I always got an error message that CLM is not a possible layer of sentinel 2-l2a. For future, I would try to include this. So far, I only managed to set the maximum cloud coverage parameter.

Width and height definition:
Regarding the width and height definition in the output for the request, I tried to use the "bbox_to_dimensions" method to define width and height automatically. However, I only received wrong results (out of range, above 2500). Therefore, I set the width and height manually based on the Request Builder from Sentinel Hub. For future, I would include this that the width and height are set automatically based on the polygon and the resolution.


Output format:
Currently, I am not sure whether the output of the pipeline is a .tif or  Geotiff file. I tried to save the file that is given as a response, however, did not manage to save a file that contains georeferenced data.

Use of AI:
I did not use any generative AI tools to complete this task. I only used Google to obtain the information needed.
