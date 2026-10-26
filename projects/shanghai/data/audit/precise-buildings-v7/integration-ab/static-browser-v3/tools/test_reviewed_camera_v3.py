import copy
import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
def module(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=module('old_browser_next','browser-next.py')
new=module('new_browser_next','browser-next-v3.py')

class Page:
    def __init__(self):self.calls=[]
    def evaluate(self,source,arg):self.calls.append((source,copy.deepcopy(arg)))

REQUEST={'from':{'lng':121.05101715900082,'lat':31.112928210976463,'alt':4.9030108060378},
 'to':{'lng':121.0510433170166,'lat':31.113007658612247,'alt':4.1},'fov':50}
VIEW={'scope':'root-reviewed-actual-camera-v1','request':REQUEST,
 'evidence':{'diagnostic_sha256':'a'*64,'visual_review_sha256':'b'*64,'image_sha256':'c'*64}}
RECORD={'id':'synthetic-ordinary','kind':'building','lng':121.0510057,'lat':31.1130536,'height_m':8.2,
 'navigation':{'listed':True,'walkStart':[121.0510491,31.1129678],'bearing':352.87},'lod_switch_out_m':400}

class ReviewedCameraTests(unittest.TestCase):
    def setUp(self):new.TARGET_PROFILES={};old.TARGET_PROFILES={}
    def test_original_readonly_probes_are_byte_identical(self):
        for name in ['INSTALL_PROBE','FETCH_JSON','AUDIT_ASSET']:
            self.assertEqual(getattr(new,name),getattr(old,name))
    def test_unbound_target_uses_original_camera_request_and_operation(self):
        a,b=Page(),Page();self.assertEqual(new.camera_view(a,RECORD),old.camera_view(b,RECORD));self.assertEqual(a.calls,b.calls)
    def test_bound_target_lod_is_still_original_camera(self):
        new.TARGET_PROFILES={RECORD['id']:{'reviewed_oblique':VIEW}};a,b=Page(),Page()
        self.assertEqual(new.camera_view(a,RECORD,True),old.camera_view(b,RECORD,True));self.assertEqual(a.calls,b.calls)
    def test_reviewed_near_uses_normalized_actual_eye(self):
        new.TARGET_PROFILES={RECORD['id']:{'reviewed_oblique':VIEW}};p=Page()
        self.assertEqual(new.camera_view(p,RECORD),REQUEST);self.assertEqual(p.calls[0][1],REQUEST)
        self.assertIn('setVerticalFieldOfView(v.fov)',p.calls[0][0])
    def test_camera_evidence_and_finite_coordinates_required(self):
        for change in ['evidence','scope','coordinate']:
            v=copy.deepcopy(VIEW)
            if change=='evidence':v['evidence'].pop('image_sha256')
            elif change=='scope':v['scope']='unreviewed'
            else:v['request']['from']['lng']=float('nan')
            with self.assertRaises(Exception):new.reviewed_oblique({'reviewed_oblique':v})
    def test_actual_fov_and_eye_are_checked_not_only_profile_flags(self):
        camera={'eye':copy.deepcopy(REQUEST['from']),'fov':50}
        self.assertTrue(new.check_reviewed_camera_state(camera,REQUEST)['passed'])
        bad=copy.deepcopy(camera);bad['fov']=36.87
        with self.assertRaises(Exception):new.check_reviewed_camera_state(bad,REQUEST)
        bad=copy.deepcopy(camera);bad['eye']['alt']=4.5
        with self.assertRaises(Exception):new.check_reviewed_camera_state(bad,REQUEST)
        bad=copy.deepcopy(camera);bad['eye']['lng']+=.00001
        with self.assertRaises(Exception):new.check_reviewed_camera_state(bad,REQUEST)

if __name__=='__main__':unittest.main()
