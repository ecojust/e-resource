"""Sample openly licensed building-height estimates for WGS84 footprints.

CNBH-10m 2020 is preferred. The median uses positive raster pixels whose
centers lie inside the footprint, including its boundary. A narrow footprint
with no enclosed pixel centers uses its representative point. Missing cells
are never filled from neighboring cells. GHSL ANBH 2018 is the final fallback.

Keep one instance per worker: arrays are loaded once, not once per building.
The shipped CNBH UInt16 array occupies about 295 MB of RAM. Raster scale and
offset metadata are read explicitly; rasterio does not apply them on read.

Example:
    sampler = RasterHeightSampler()
    result = sampler.sample_geometry(feature['geometry'])
    if result:
        print(result['height_m'], result['height_quality'])

These estimates must follow source building heights and documented floors.
Neither dataset represents a surveyed individual building roof height.
Requires numpy, rasterio, pyproj and shapely >= 2.0.
"""
from pathlib import Path
import math
import numpy as np
import rasterio
from pyproj import Transformer
import shapely
from shapely.geometry import shape


HERE = Path(__file__).resolve().parent
DEFAULT_CNBH = HERE / 'alternatives' / 'cnbh_2020_shanghai_core_dm.tif'
DEFAULT_GHSL = HERE / 'shanghai_ghsl_anbh_2018_3arcsec.tif'


class _CachedRaster:
    def __init__(self, path):
        with rasterio.open(path) as dataset:
            self.data = dataset.read(1)
            self.transform = dataset.transform
            self.inverse = ~self.transform
            self.scale = float(dataset.scales[0])
            self.offset = float(dataset.offsets[0])
            self.nodata = dataset.nodata
            self.crs = dataset.crs
            self.resolution = dataset.res
        if self.transform.b or self.transform.d:
            raise ValueError('This sampler requires a north-up raster')
        if self.transform.a <= 0 or self.transform.e >= 0:
            raise ValueError('Unexpected raster axis direction')
        self.project = Transformer.from_crs('EPSG:4326', self.crs, always_xy=True)
        self.rows, self.cols = self.data.shape

    def positive_meters(self, values):
        values = np.asarray(values)
        valid = np.isfinite(values)
        if self.nodata is not None:
            valid &= values != self.nodata
        meters = values[valid].astype(np.float64) * self.scale + self.offset
        return meters[np.isfinite(meters) & (meters > 0)]

    def point_value(self, x, y):
        col, row = self.inverse * (x, y)
        col, row = math.floor(col), math.floor(row)
        if 0 <= row < self.rows and 0 <= col < self.cols:
            values = self.positive_meters(self.data[row:row+1, col:col+1])
            if values.size:
                return float(values[0])
        return None

    def footprint_value(self, geometry):
        """Return (median height in m, positive count, method) or None."""
        geom = shapely.transform(geometry, self.project.transform, interleaved=False)
        if geom.is_empty:
            return None
        if geom.geom_type == 'Point':
            value = self.point_value(geom.x, geom.y)
            return (value, 1, 'representative-point-cell') if value is not None else None
        minx, miny, maxx, maxy = geom.bounds
        col_min, row_min = self.inverse * (minx, maxy)
        col_max, row_max = self.inverse * (maxx, miny)
        c0 = max(0, math.ceil(col_min - 0.5))
        c1 = min(self.cols, math.floor(col_max - 0.5) + 1)
        r0 = max(0, math.ceil(row_min - 0.5))
        r1 = min(self.rows, math.floor(row_max - 0.5) + 1)
        enclosed_centers = 0
        positive_chunks = []
        if c0 < c1 and r0 < r1:
            xs = self.transform.c + (np.arange(c0, c1) + 0.5) * self.transform.a
            # Small windows dominate building workloads. Row chunks also keep
            # anomalously large footprints from allocating city-sized grids.
            for start_row in range(r0, r1, 256):
                stop_row = min(r1, start_row + 256)
                ys = self.transform.f + (np.arange(start_row, stop_row) + 0.5) * self.transform.e
                inside = shapely.intersects_xy(geom, xs[None, :], ys[:, None])
                count = int(np.count_nonzero(inside))
                enclosed_centers += count
                if count:
                    values = self.positive_meters(self.data[start_row:stop_row, c0:c1][inside])
                    if values.size:
                        positive_chunks.append(values)
        if positive_chunks:
            values = np.concatenate(positive_chunks)
            return float(np.median(values)), int(values.size), 'footprint-pixel-center-positive-median'
        if enclosed_centers:
            # There were raster centers inside the footprint but they had no
            # estimate. Do not quietly substitute some other CNBH cell.
            return None
        point = geom.representative_point()
        value = self.point_value(point.x, point.y)
        return (value, 1, 'representative-point-cell') if value is not None else None


class RasterHeightSampler:
    """Cached CNBH 2020 footprint median, followed by GHSL 2018 cell mean."""
    def __init__(self, cnbh_path=None, ghsl_path=None):
        cnbh_path = DEFAULT_CNBH if cnbh_path is None else Path(cnbh_path)
        ghsl_path = DEFAULT_GHSL if ghsl_path is None else Path(ghsl_path)
        self.cnbh = _CachedRaster(cnbh_path) if cnbh_path.exists() else None
        self.ghsl = _CachedRaster(ghsl_path) if ghsl_path.exists() else None
        if self.cnbh is None and self.ghsl is None:
            raise FileNotFoundError('Neither CNBH nor GHSL raster is available')

    def sample_geometry(self, geometry):
        """Return provenance-bearing estimated height, or None if unavailable.

        ``geometry`` is a GeoJSON geometry in EPSG:4326 (longitude, latitude).
        A Shapely geometry is also accepted. ``resolution`` is nominal meters;
        the GHSL 3-arcsecond cells are about 80 x 93 m at Shanghai's latitude.
        ``count`` counts positive contributing pixels, not surveyed buildings.
        """
        geom = shape(geometry) if isinstance(geometry, dict) else geometry
        if geom is None or geom.is_empty:
            return None
        if self.cnbh is not None:
            estimate = self.cnbh.footprint_value(geom)
            if estimate is not None:
                value, count, method = estimate
                return {
                    'height_m': round(value, 3),
                    'height_source': 'cnbh-10m-2020',
                    'height_quality': 'cnbh_estimate_10m',
                    'height_epoch': 2020,
                    'resolution': 10,
                    'estimated': True,
                    'license': 'CC-BY-4.0',
                    'method': method,
                    'count': count,
                }
        if self.ghsl is not None:
            point = geom.representative_point()
            x, y = self.ghsl.project.transform(point.x, point.y)
            value = self.ghsl.point_value(x, y)
            if value is not None:
                return {
                    'height_m': round(value, 3),
                    'height_source': 'ghsl-anbh-2018-cell-mean',
                    'height_quality': 'raster_estimate_2018',
                    'height_epoch': 2018,
                    'resolution': 100,
                    'estimated': True,
                    'license': 'CC-BY-4.0',
                    'method': 'representative-point-cell-average',
                    'count': 1,
                }
        return None

    def sample_point(self, longitude, latitude):
        return self.sample_geometry({'type': 'Point', 'coordinates': [longitude, latitude]})

    def height_at(self, longitude, latitude):
        result = self.sample_point(longitude, latitude)
        return result['height_m'] if result else None
