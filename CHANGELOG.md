# Change Log

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
* Parsing SRTM DTED files
* CLI (including terminal plotting)
