# Change Log

## v1.3.0 -- 2025-02-21

Query sets of DTED tiles.
credit: [@westonCoder](https://github.com/westonCoder)

- Add a TileSet object to enable querying a collection of DTED file.
  This collection can be multiple, individual files and/or directories.
- Tile objects are now hashable and comparable.
  Metadata objects (acc/dsi/uhl) are now frozen.

## v1.2.0 -- 2025-01-23

Update project to support Python 3.13
credit: [@amclauth](https://github.com/amclauth)

- Drop support for Python 3.9
- Fix some type hints
- Add additional newly-discovered DTED source to README

## v1.1.0 -- 2024-04-16

Update minimum python version to 3.9 and refresh project.

- Remove now unnecessary <3.9 dependencies.
- Clean up typehinting for numpy arrays and their contents.
- Fix a numpy deprecation warning.

## v1.0.4 -- 2023-02-24

Improvement: VoidDataWarning can now be disabled with a keyword argument:

- dted.Tile(..., warn=False)
- dted.Tile.load_data(..., warn=False)

Bug Fix: Prevent unspecified, non-relevant metadata from causing errors
when parsing DTED files.
These fields will no longer cause errors:

- AccuracyDescription.absolute_horizontal
- AccuracyDescription.absolute_vertical
- AccuracyDescription.relative_horizontal
- AccuracyDescription.relative_vertical
- DataSetIdentification.edition
- DataSetIdentification.orientation
- DataSetIdentification.coverage
- UserHeaderLabel.vertical_accuracy

The following fields are now explicitly required:

- DataSetIdentification.latitude_interval
- DataSetIdentification.longitude_interval
- DataSetIdentification.shape
- UserHeaderLabel.latitude_interval
- UserHeaderLabel.longitude_interval
- UserHeaderLabel.shape

## v1.0.3 -- 2022-06-09

Bug Fix: incorrectly computing LatLon -> Tile Index conversion.
Caused `Tile.get_elevation` to give incorrect results for DTED
level 0 and 1 tiles.

## v1.0.2 -- 2021-11-17

Bug Fix: incorrectly parsed lat, long resolutions

## v1.0.1 -- 2021-11-15

Bug Fix: incorrectly parsed dataset shape

## v1.0.0 -- 2021-07-01

First Release!

#### Features

- Parsing SRTM DTED files
- CLI (including terminal plotting)
