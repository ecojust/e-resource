"""Topology regressions: inner islands, disconnected water and thin channels."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, box

path = Path(__file__).resolve().parents[1] / 'source/surfaces/build.py'
spec = importlib.util.spec_from_file_location('surface_build', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SurfaceMeshTests(unittest.TestCase):
    def check_geometry(self, geometry):
        mesh = module.mesh_surface(geometry, 'mapped-water', [66,127,144,255], .42)
        points = mesh.vertices[:, [0,2]] * [1,-1]
        triangles = shapely.polygons(points[mesh.faces])
        union = shapely.union_all(triangles)
        # GLB positions are float32; permit sub-micrometre area rounding in these fixtures.
        self.assertLess(union.symmetric_difference(geometry).area, 1e-6)
        self.assertTrue((mesh.face_normals[:,1] > .99).all())
        return union

    def test_island_not_filled(self):
        water = Polygon([(0,0),(100,0),(100,100),(0,100)], holes=[[(30,30),(70,30),(70,70),(30,70)]])
        result = self.check_geometry(water)
        self.assertEqual(result.intersection(box(31,31,69,69)).area, 0)

    def test_disconnected_lakes_and_thin_channel(self):
        self.check_geometry(MultiPolygon([box(-20,-10,-10,0), box(0,0,100,.01)]))

    def test_tile_cut_is_not_a_bank(self):
        river = box(-100,-10,100,10).difference(box(-4,-4,4,4))
        tiles = [box(-100,-100,0,100),box(0,-100,100,100)]
        merged = module.polygonal(shapely.union_all([river.intersection(t) for t in tiles]))
        result = self.check_geometry(merged)
        self.assertEqual(result.symmetric_difference(river).area, 0)
        self.assertEqual(len(result.interiors),1)

    def test_ground_and_water_are_complementary(self):
        district=box(-100,-100,100,100)
        water=Polygon([(-100,-5),(100,-5),(100,5),(-100,5)],holes=[[(-2,-2),(2,-2),(2,2),(-2,2)]])
        land=self.check_geometry(district.difference(water))
        water_mesh=self.check_geometry(water)
        self.assertEqual(land.intersection(water_mesh).area,0)
        self.assertEqual(shapely.union_all([land,water_mesh]).symmetric_difference(district).area,0)

    def test_empty_surface(self):
        self.assertIsNone(module.mesh_surface(Polygon(), 'empty', [0,0,0,255], 1))

if __name__ == '__main__':
    unittest.main()
