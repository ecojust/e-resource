"""Small adversarial fixtures for the reviewer, NOT a building acceptance test."""
import unittest
import numpy as np
from modern_mesh import Part, Asset, oriented_position_hash
from audit_raw_structure import structure
from finite_checks import ray_intervals, contact_witness, aperture_check, section_check,ray_check,measure_check

FRAME={'origin_enu_m':[0,0,0],'axes_enu':[[1,0,0],[0,1,0],[0,0,1]]}

def box(lo=(0,0,0),hi=(1,1,1),label='box',reverse=False):
    v=np.array([[lo[0],lo[1],lo[2]],[hi[0],lo[1],lo[2]],
                [hi[0],hi[1],lo[2]],[lo[0],hi[1],lo[2]],
                [lo[0],lo[1],hi[2]],[hi[0],lo[1],hi[2]],
                [hi[0],hi[1],hi[2]],[lo[0],hi[1],hi[2]]],dtype=np.float32).astype(float)
    f=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
                [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
    if reverse:f=f[:,::-1]
    t=v[f]; n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
    return Part(label,label,'fixture',t,np.repeat(n[:,None,:],3,axis=1),0,0)

def asset(parts):return Asset({'raw':{'sha256':'synthetic-only','bytes':1}},parts,{}, {'id':'synthetic-only'})

class ReviewFixtures(unittest.TestCase):
    def test_hash_orientation(self):
        t=box().triangles_enu
        self.assertEqual(oriented_position_hash(t),oriented_position_hash(t[::-1][:,[1,2,0]]))
        self.assertNotEqual(oriented_position_hash(t),oriented_position_hash(t[:,::-1]))
    def test_structure_closed_and_negative_component(self):
        a=box();self.assertTrue(structure(asset([a]))['structure_passed'])
        a.triangles_enu=a.triangles_enu[:-1];a.normals_enu=a.normals_enu[:-1]
        self.assertFalse(structure(asset([a]))['structure_passed'])
        a,b=box(),box((3,0,0),(3.1,.1,.1),reverse=True)
        a.triangles_enu=np.concatenate([a.triangles_enu,b.triangles_enu]);a.normals_enu=np.concatenate([a.normals_enu,b.normals_enu])
        r=structure(asset([a]));self.assertFalse(r['structure_passed'])
        self.assertEqual(r['part_results'][0]['edge_component_count'],2)
    def test_separated_intervals(self):
        t=np.concatenate([box().triangles_enu,box((0,0,3),(1,1,4)).triangles_enu])
        self.assertEqual(ray_intervals(t,[.23,.37])['intervals_m'],[[0.,1.],[3.,4.]])
    def test_contact(self):
        a=box();b=box((.2,.2,.9),(.8,.8,2),'b')
        self.assertTrue(contact_witness(a,b,FRAME)['positive_volume_contact_found'])
        b=box((.2,.2,1.1),(.8,.8,2),'b')
        self.assertFalse(contact_witness(a,b,FRAME)['positive_volume_contact_found'])
        b=box((.2,.2,1.),(.8,.8,2),'b')
        self.assertFalse(contact_witness(a,b,FRAME)['contact_found'])
        self.assertTrue(contact_witness(a,b,FRAME,contact_mode='volume_or_exact_area')['positive_area_coincidence_found'])
        b=box((.2,.2,1.000001),(.8,.8,2),'b')
        self.assertFalse(contact_witness(a,b,FRAME,contact_mode='volume_or_exact_area')['contact_found'])
    def test_aperture_and_negative_controls(self):
        parts=[box((-2,-2,0),(-1,2,.2),'left'),box((1,-2,0),(2,2,.2),'right'),
               box((-1,-2,0),(1,-1,.2),'bottom'),box((-1,1,0),(1,2,.2),'top')]
        r={'wall_selectors':[{'label':p.label,'expected_count':1} for p in parts], 'frame':FRAME,
           'polygon_uv_m':[[-.9,-.9],[.9,-.9],[.9,.9],[-.9,.9]],'depth_range_m':[-.1,.3],
           'negative_controls_uv_m':[[-1.5,.2],[1.5,.3]],'maximum_blocked_area_m2':1e-12}
        self.assertTrue(aperture_check(asset(parts),r)['passed'])
        parts.append(box((-.5,-.5,0),(.5,.5,.2),'obstruction'))
        r['wall_selectors'].append({'label':'obstruction','expected_count':1})
        self.assertFalse(aperture_check(asset(parts),r)['passed'])
        r['depth_range_m']=[.05,.15]
        with self.assertRaises(ValueError):aperture_check(asset(parts),r)
    def test_section(self):
        r={'selectors':[{'label':'box','expected_count':1}],
           'frame':{**FRAME,'origin_enu_m':[0,0,.37]},'loop_count_range':[1,1]}
        self.assertTrue(section_check(asset([box()]),r)['passed'])
    def test_malformed_requests_cannot_pass(self):
        a=asset([box()]);r={'selectors':[{'label':'box','expected_count':1}], 'frame':FRAME,
                          'depth_range_m':[-1,2],'points_uv_m':[[2,2]],'expect':'solid'}
        self.assertFalse(ray_check(a,r)['passed'])
        for v in [0,-1,float('nan')]:
            with self.assertRaises(ValueError):ray_check(a,{**r,'minimum_single_interval_m':v})
        for points in [[],[[float('nan'),0]],[[0,float('inf')]]]:
            with self.assertRaises(ValueError):ray_check(a,{**r,'expect':'clear','points_uv_m':points})
        for ranges in [{},{'3':[0,1]},{'2':[float('nan'),2]}]:
            with self.assertRaises(ValueError):measure_check(a,{**r,'extent_ranges_m':ranges})

if __name__=='__main__':unittest.main()
