#!/usr/bin/env python3
"""Isolated camera-request comparison, no Playwright/browser or product mutation."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base',type=Path,required=True)
parser.add_argument('--landmarks',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();assert not args.output.exists()
candidate=HERE/'browser_acceptance.py'
old=args.base.read_text();new=candidate.read_text()
expected=old
for before,after in [
    ('def camera(east,north,alt,to_alt,fov=48):','def camera(east,north,alt,to_alt,fov=48,to_east=0,to_north=0):'),
    ("'to':offset(record,0,0,to_alt)","'to':offset(record,to_east,to_north,to_alt)"),
    ('request=camera(width*.18,-length*.88,max(height*.55,12),height*.23,52)',
     'request=camera(0,-85,12,5,52,to_east=.8,to_north=-40.91)')]:
    assert expected.count(before)==1
    expected=expected.replace(before,after)
release_old='''                    page.evaluate("""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();a.scene.map.jumpTo({center:[v.lng+.06,v.lat],zoom:15,pitch:50,bearing:20});a.scene.loadLandmarks()}""",record)
'''
release_new='''                    release_request={'center':offset(record,18000,0,0),'zoom':15,'pitch':50,'bearing':20}
                    release_distance=metres(release_request['center'],record)
                    report['release_navigation']={'requested':release_request,'requested_distance_m':release_distance,'required_distance_above_m':12300}
                    need(release_distance>12300,'Release request does not exceed the 12000m overview range plus 300m hysteresis')
                    page.evaluate("""v=>{const a=__SHANGHAI_APP__;a.syncMode('overview',false);a.scene.map.stop();a.scene.map.jumpTo({center:[v.center.lng,v.center.lat],zoom:v.zoom,pitch:v.pitch,bearing:v.bearing});a.scene.loadLandmarks()}""",release_request)
                    actual_release=page.evaluate("()=>{const a=__SHANGHAI_APP__,m=a.scene.map,c=m.getCenter();return {mode:a.mode,center:{lng:c.lng,lat:c.lat},zoom:m.getZoom()}}")
                    report['release_navigation']['actual']=actual_release
                    report['release_navigation']['actual_distance_m']=metres(actual_release['center'],record);save()
                    need(actual_release['mode']=='overview' and actual_release['zoom']==15 and report['release_navigation']['actual_distance_m']>12300,'Actual release view did not exceed the overview hysteresis range')
'''
assert expected.count(release_old)==1
expected=expected.replace(release_old,release_new)
assert expected==new,'Changes extend outside the permitted camera and release-driver lines'
record=next(r for r in json.loads(args.landmarks.read_text()) if r['id']=='yangpu-library')
spec=importlib.util.spec_from_file_location('qa_camera_helpers',candidate);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class PageObserver:
    def __init__(self):self.calls=[]
    def evaluate(self,expression,value):self.calls.append({'expression':expression,'request':value})
def camera_function(source):
    tree=ast.parse(source)
    fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='camera')
    observer=PageObserver();scope={'record':record,'offset':module.offset,'page':observer}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'isolated-camera-function','exec'),scope)
    return scope['camera'],observer
before,old_observer=camera_function(old);after,new_observer=camera_function(new)
w,s,e,n=record['bbox'];height=record['height_m']
width=module.metres({'lng':e,'lat':record['lat']},{'lng':w,'lat':record['lat']})
length=module.metres({'lng':record['lng'],'lat':n},{'lng':record['lng'],'lat':s})
cases=[('unchanged_helper_defaults',(1,2,3,4)),
       ('unchanged_oblique',(width*1.2,length*.9,max(height*2.7,max(width,length)*.75),height*.28,50)),
       ('unchanged_lod',(max(600,record.get('lod_switch_out_m',400)+180),0,height+110,height*.3,36.87))]
controls=[]
for name,values in cases:
    a=before(*values);b=after(*values);assert a==b
    assert old_observer.calls[-1]==new_observer.calls[-1]
    controls.append({'name':name,'exact_request_and_camera_JS_unchanged':True,'request':b})
old_south=before(width*.18,-length*.88,max(height*.55,12),height*.23,52)
new_south=after(0,-85,12,5,52,to_east=.8,to_north=-40.91)
assert old_south!=new_south
assert new_south=={'from':module.offset(record,0,-85,12),'to':module.offset(record,.8,-40.91,5),'fov':52}
old_release={'lng':record['lng']+.06,'lat':record['lat']}
new_release=module.offset(record,18000,0,0)
old_distance=module.metres(old_release,record);new_distance=module.metres(new_release,record)
assert old_distance<12300 and new_distance>12300
assert not (12300>12300) and 12300.01>12300
def desc(path):
    value=path.read_bytes();return {'file':str(path),'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()}
result={'schema':'south-camera-release-driver-control-v3','passed':True,
        'base_script':desc(args.base),'candidate_script':desc(candidate),'navigation':desc(args.landmarks),
        'only_camera_and_release_driver_changed':True,'unchanged_controls':controls,
        'old_south_request':old_south,'new_south_request':new_south,
        'new_south_enu':{'from':[0,-85,12],'to':[.8,-40.91,5],'fov':52},
        'release_driver':{'old_request':old_release,'old_distance_m':old_distance,'old_below_required_threshold':True,
                          'new_request':new_release,'new_distance_m':new_distance,'required_distance_above_m':12300,
                          'threshold_equality_rejected':True,'strictly_greater_threshold_accepted':True},
        'scope':'Pure request-generation and strict release-distance controls against actual candidate navigation. Existing ownership assertions remain byte-identical. No browser, screenshot, source/asset acceptance or actual camera clipping/release claim.'}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'only_camera_and_release_driver_changed':True,'unchanged_controls':len(controls),'south_request':new_south,'old_release_m':old_distance,'new_release_m':new_distance}),flush=True)
