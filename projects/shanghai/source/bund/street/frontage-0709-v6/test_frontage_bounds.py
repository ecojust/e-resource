"""Road-junction regression: a closer side street is not the public front."""
import importlib.util
from pathlib import Path
import unittest
from shapely.geometry import Point,box
from shapely.ops import unary_union

spec=importlib.util.spec_from_file_location('append_frontage',Path(__file__).with_name('append_frontage.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ForwardBoundary(unittest.TestCase):
    def test_nearer_side_street_does_not_replace_forward_road(self):
        road=unary_union([box(8,-4,14,20),box(-10,-3,14,-2)])
        point=Point(0,0)
        self.assertEqual(point.distance(road),2)
        hit=module.forward_road_point(road,point,(1,0))
        self.assertEqual((hit.x,hit.y),(8,0))

    def test_no_road_in_confirmed_direction_rejects_fill(self):
        with self.assertRaisesRegex(AssertionError,'No actual road boundary'):
            module.forward_road_point(box(-10,-5,-3,5),Point(0,0),(1,0))

    def test_width_cap_and_facade_inside_asphalt_are_rejected(self):
        with self.assertRaises(AssertionError):module.forward_road_point(box(25,-5,30,5),Point(0,0),(1,0))
        with self.assertRaisesRegex(AssertionError,'inside asphalt'):module.forward_road_point(box(-1,-1,2,2),Point(0,0),(1,0))

if __name__=='__main__':unittest.main()
