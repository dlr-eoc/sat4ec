# Sat4Ec

## Usage

Build the docker image.

```
docker build -f sat4ec.Dockerfile -t sat4ec .
```

Execute the docker container.

```
docker run
-v /PATH/TO/INPUT/DIR/:/scratch/in/
-v /PATH/TO/OUTDIR/:/scratch/out/
--rm sat4ec
--aoi_data <Path to AOI file or AOI as POLYGON or AOI as WKT>
--start_date <Begin of the time series, as YYYY-MM-DD>
--end_date <End of the time series, as YYYY-MM-DD>
--anomalies : Use anomaly detection to list scenes of high or low backscatter
            invert : Invert the anomaly detection
--save_plot <Wether or not to save the results as a plot, boolean>
```

Call with `--anomalies` without further sub options to perform a simple anomaly detection. The default parameters are listed here. **DEFAULT PARAMETERS MISSING**

Call with `--anomalies invert` to invert the anomaly detection.

An exemplarily docker call looks like this:

```
docker run
-v /PATH/TO/INPUT/DIR/:/scratch/in/
-v /PATH/TO/OUTDIR/:/scratch/out/
--rm sat4ec
--aoi_data /path/to/aoi.geojson
--start_date 2020-01-01
--end_date 2020-12-31
--anomalies invert
--save_plot False
```

## Development

```
conda create -n sat4ec Python=3.11
conda install matplotlib jupyterlab
conda install gdal fiona shapely geopandas pandas seaborn
conda install sentinelhub
pip install adtk
```
