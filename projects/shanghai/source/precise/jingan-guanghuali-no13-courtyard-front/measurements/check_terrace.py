"""Intersect serialized roof geometry from the photographed rail pixels and across physical sections."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'source'), str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import terrace_roof as roof


def inspect(asset, placement=None):
    scene = SerialScene(asset)
    survey = json.loads((HERE/'terrace-reconstruction.json').read_text())
    controls = json.loads((HERE/'photographed-rail-centres.json').read_text())
    data = json.loads(placement.read_text()) if placement else dict(origin=[0,0,0],yaw_degrees=0)
    a = np.radians(data['yaw_degrees'])
    r = np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    origin = np.array(data['origin'])
    physical,photo = [],[]
    def cast(title, eye, direction, limit, materials, rows, **context):
        hit = scene.ray(r @ np.asarray(eye)+origin, r @ np.asarray(direction), limit)
        mat = hit['material'] if hit else None
        rows.append(dict(feature=title,passed=mat in materials,actual=mat,expected=materials,**context))

    path = np.array(survey['handrail_path_m'])[:, :2]
    for index,(u,v) in enumerate(zip(path,path[1:])):
        tangent=(v-u) / np.linalg.norm(v-u)
        normal=np.array([tangent[1],-tangent[0],0])
        for f in [.12,.32,.53,.73,.89]:
            xy=(1-f)*u+f*v
            for level,(z,_) in enumerate(roof.RAIL_LEVELS):
                rail = roof.rail_path(path,roof.RAIL_OFFSETS[level])
                sample = rail[index]*(1-f)+rail[index+1]*f
                cast(f'rail {level+1}, run {index+1}',np.r_[sample,z]+.07*normal,-normal,.12,[roof.IRON],physical)
            for z in [-.125,-.350,-.577]:
                cast('clear slot between rails',np.r_[xy,z]+.055*normal,-normal,.10,[None],physical)
    for idx,pt in enumerate(path):
        for z in [-.13,-.34,-.57,-.80]:
            foot = roof.rail_path(path,-.034)[idx]
            center = pt+(z/roof.DECK_Z)*(foot-pt)
            cast(f'anchored upright {idx+1}',np.r_[center,z]+[0,-.042,0],[0,1,0],.08,[roof.IRON],physical)
    corners=np.array(survey['masonry_corners_m'])[:,:2]
    for u,v in zip(corners,corners[1:]):
        t=(v-u)/np.linalg.norm(v-u)
        n=np.array([t[1],-t[0],0])
        for f in [.21,.50,.78]:
            xy=(1-f)*u+f*v
            for z,mat in [(-1.277,roof.CAP),(-1.182,roof.RECESS),(-1.150,roof.CAP),(-1.071,roof.CAP),(-.966,roof.CAP)]:
                cast('stepped coping section',np.r_[xy,z]+.135*n,-n,.20,[mat],physical)

    left,right,rear=[np.array(survey[k]) for k in
                     ('eave_lower_left_front_m','eave_lower_right_front_m','eave_lower_right_occlusion_m')]
    width=np.linalg.norm((right-left)[:2]);ex=(right-left)[:2]/width;ey=np.array([-ex[1],ex[0]])
    depth=np.dot(rear[:2]-right[:2],ey)
    def xyz(x,y,z):return np.r_[left[:2]+ex*x+ey*y,z]
    for x in [.25,width/2,width-.24]:
        for y in [.12,.47,.86]:
            z=left[2]+x*(right[2]-left[2])/width+y*(rear[2]-right[2])/depth
            cast('single-pitch grey covering',xyz(x,y,z+.29),[0,0,-1],.3,[roof.METAL],physical)
        for dz,m in [(.065,roof.WHITE),(.13,roof.METAL)]:
            z=left[2]+x*(right[2]-left[2])/width
            cast('two levels of eave fascia',xyz(x,-.13,z+dz),[*ey,0],.20,[m],physical)
    for x,m in [(.7,roof.GLASS_DARK),(1.45,roof.GLASS_DARK),(2.80,roof.GLASS)]:
        for z in [-.15,.40,.78]:
            cast('three recessed rooftop lights',xyz(x,.22,z),[*ey,0],.3,[m],physical)
    for tag,group in controls.items():
        P=np.array(survey['cameras'][tag]);eye=-np.linalg.solve(P[:,:3],P[:,3])
        for q in group['controls']:
            uv=q['uv']
            cast('original steel silhouette',eye,np.linalg.solve(P[:,:3],[*uv,1]),40,[roof.IRON],photo,
                 station=tag,uv=uv,run=q['side'],rail_index=q['level'])
            row=photo[-1]
            row['observed_band_y']=q['observed_dark_band_y']
            row['band_intersects_metal']=row['passed']
            if not row['passed']:
                lo,hi=row['observed_band_y']
                for y in range(lo,hi+1):
                    direction=np.linalg.solve(P[:,:3],[uv[0],y,1])
                    hit=scene.ray(r@eye+origin,r@direction,40)
                    if hit and hit['material']==roof.IRON:
                        row['band_intersects_metal']=True
                        row['first_matching_native_y']=y
                        break
    def tally(results):
        return dict(total=len(results),passed=sum(q['passed'] for q in results),rays=results)
    return dict(asset=scene.asset,placement=data,physical=tally(physical),photographs=dict(**tally(photo),bands_overlapping=sum(row['band_intersects_metal'] for row in photo)))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('--placement',type=Path)
    a=ap.parse_args()
    doc=inspect(a.mesh,a.placement)
    a.output.write_text(json.dumps(doc,ensure_ascii=False,indent=1)+'\n')
    for k in ['physical','photographs']:
        group=doc[k]
        print(k,group['passed'],group['total'],[(q['feature'],q.get('station'),q.get('uv'),q['actual']) for q in group['rays'] if not q['passed']][:10])
    raise SystemExit(int(doc['physical']['passed'] != doc['physical']['total']))
