Areas of interest (AOIs) are processed per orbit (ascending or descending). The general workflow is as follows.

#### Orbits

Depending on the settings (see [execution docs](execution.md)), either asending, descending or both orbits will be processed. The class `OrbitCollection()` in `main.py` registers the orbits to be processed:

``` python
orbit_collection = OrbitCollection(orbit="both")
```

Depending on the desired orbit, the object `orbit_collection.orbits` will be a list of one or two entries:

| `orbit_collection.orbits` | description                  |
|---------------------------|------------------------------|
| `["asc"]`                 | ascending orbit              |
| `["des"]`                 | descending orbit             |
| `["asc", des"]`           | ascending & descending orbit |

#### AOIs

Depending on the settings (see [execution docs](execution.md)), AOIs built from sub AOIs are either aggregated into a single AOI or being treated individually. The class `AOI()` in `main.py` registers the AOIs to be processed:

``` python
aoi_collection = AOI(data="/foo/bar/aoi.geojson", aoi_split=True)
```

#### Sub AOIs

Processing of sub AOIs is possible. If not desired, all of the existing sub AOIs will be aggregated to a main AOI and treated as a single sub AOI internally. The class `SubsetCollection()` in `main.py` is initialized as follows:

``` python
subset_collection = SubsetCollection(orbit=orbit)
```

The object `subset_collection` stores the results of each processed sub AOI.

#### Wrapping up

``` python
orbit_collection = OrbitCollection(orbit="both")  # register orbits

for orbit in orbit_collection.orbits:  # loop over orbits
    with AOI(data="/foo/bar/aoi.geojson", aoi_split=True) as aoi_collection:  # register AOIs
        subsets = Subsets(orbit=orbit)

        for index, feature in enumerate(aoi_collection.get_feature()):  # return sub AOI
            execute_data_retrieval()
```

#### Data retrieval