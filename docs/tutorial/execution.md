Execution of the code is possible in two ways:

1. by executing a`.py` file or
2. by executing a jupyter notebook.

Case 1 is used for development and testing. Case 2 is the default for the EuroDataCube (EDC) environment.

### Execution in the EDC environemnt

Execution in the EDC environment is the default mode. Open the file `sat4ec/exe_runner.ipynb` and alter the settings if desired.

```
conf = Config(
    aoi_dir=Path(r"input/AOIs"),
    working_dir=Path.home().joinpath("sat4ec"),
    out_dir=Path(r"output"),
    orbit="both",  # ascending or descending orbit or both
    pol="VH",  # only use VH polarization
    aoi="porsche_leipzig",
    ext="geojson",
    start="2016-01-01",
    monthly=True,
    regression="spline",
    linear=True,
    aoi_split=True,
)
prod = Production(config=conf)
prod.workflow()
```

The parameters are described as follows:

| Parameter  | Description                                                                        | Required                                  |
|------------|------------------------------------------------------------------------------------|-------------------------------------------|
| aoi_dir    | Path to the directory with the AOI files                                           | Yes                                       |
| out_dir    | Path to the output directory. Will be created if not existing                      | Yes                                       |
| orbit      | Compute ascending or descending orbits or both, enter *asc*, *des* or *both*       | No, default *asc*                         |
| pol        | Polarization to use, VH is strongly recommended                                    | No, default VH                            |
| aoi        | Name of the AOI file                                                               | Yes                                       |
| ext        | Extension of the AOI file                                                          | Yes, default *.geojson*.                  |
| start      | Start date in the format YYYY-MM-DD                                                | No, default 2014-05-01                    |
| end        | End date in the format YYYY-MM-DD                                                  | No, default end of last month             |
| monthly    | Whether to aggregate monthly or semi-daily, enter *True* or *False*                | Yes, default *True*                       |
| regression | Name of the regression function, enter *spline*, *poly* or *rolling*               | No, default *spline*                      |
| linear     | Whether to compute linear regression or not, enter *True* or *False*               | Yes, default *True*                       |
| aoi_split  | Whether to compute on split or aggregated sub AOIs or not, enter *True* or *False* | Yes, default *False*: sub AOIs aggregated |                                                                         