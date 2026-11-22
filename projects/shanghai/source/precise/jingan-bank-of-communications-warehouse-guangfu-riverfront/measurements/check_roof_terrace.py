"""Read the terrace from an uncompressed actual GLB and test its roof-photo projections."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
HERE = Path(__file__).resolve().parent
SHANGHAI = HERE.parents[3]
sys.path[:0] = [str(HERE.parent/'source'),
    str(SHANGHAI/'source/precise/xuhui-pathe-records-office/measurements/city-contact'),
    str(SHANGHAI/'source/precise/hongkou-general-post-office/source/common')]
from glb_triangles import SerialScene
from photo_architecture import Builder
from roof_terrace import add_terrace, terrace_layout, STEEL, LENS, LAMP, PAVING


def export(path, z, far):
    b = Builder()
    add_terrace(b, far, {'roof_deck_z':z})
    for part in b.parts:
        vs = np.asarray(part['vertices'])
        tris = np.asarray(part['triangles'])
        directions = Counter((i,j) for tri in tris for i,j in zip(tri,np.roll(tri,-1)))
        assert all(i!=j and n==directions[j,i]==1 for (i,j),n in directions.items()),part['label']
        a,c,d=(vs-vs.mean(axis=0))[tris].transpose(1,0,2)
        assert np.sum(a*np.cross(c,d))>0,part['label']
    b.save(path,{'name':'Guangfu Road warehouse south roof terrace'})
    return {'closed_outward_parts':len(b.parts),'actual_triangles':sum(len(p['triangles']) for p in b.parts)}


def camera_ray(camera, uv, deck_z):
    cx,cy,cz,yaw,pitch,roll,f,u0,v0=camera
    co,si=np.cos,np.sin
    right=np.array([co(yaw),-si(yaw),0.])
    forward=np.array([si(yaw)*co(pitch),co(yaw)*co(pitch),si(pitch)])
    up=np.cross(right,forward)
    horizontal=right*co(roll)+up*si(roll)
    vertical=up*co(roll)-right*si(roll)
    return [cx,cy,cz+deck_z],forward+horizontal*(uv[0]-u0)/f-vertical*(uv[1]-v0)/f


def check(path,z):
    field,inner,fit=terrace_layout({'roof_deck_z':z})
    scene=SerialScene(path)
    rows=[]
    for family,uvs,allowed in [
        ('rail_head',fit['bracket_head_pixels'],{STEEL}),
        ('rail_lower_bracket',fit['bracket_base_pixels'],{STEEL}),
        ('flush_light',fit['light_centres_photo38_uv'],{LENS,LAMP}),
    ]:
        for uv in uvs:
            direct=None;best=None
            # Published native pixels and radii. Search only up to 3 px where
            # the documented handrail is thinner than a pixel at the far end.
            offsets=sorted(((x,y)for x in range(-3,4)for y in range(-3,4)if x*x+y*y<=9),key=lambda p:p[0]**2+p[1]**2)
            for du,dv in offsets:
                origin,ray=camera_ray(fit['camera_xyz_yaw_pitch_roll_f_cx_cy'],[uv[0]+du,uv[1]+dv],z)
                hit=scene.ray(origin,ray,82.)
                if (du,dv)==(0,0):direct=hit['material'] if hit else None
                if hit and hit['material'] in allowed:
                    best={'offset_native_px':[du,dv],'actual_first_hit':hit['material']};break
            rows.append({'feature':family,'native_uv':uv,'central_first_material':direct,'within_3px':best})
    vertical=[]
    for key,xy in enumerate(fit['light_centres_xy'],1):
        a=scene.ray([*xy,z+.28],[0.,0.,-1.],.8)
        vertical.append({'light':key,'first_material':a['material']if a else None,'pass':bool(a and a['material']==LAMP)})
    for x in np.linspace(-25,25,9):
        xy=[float(x),float(np.interp(x,inner[:,0],inner[:,1])+1.5)]
        a=scene.ray([*xy,z+.3],[0.,0.,-1.],1.)
        vertical.append({'pavement_xy':xy,'first_material':a['material'] if a else None,'pass':bool(a and a['material']==PAVING)})
    return {'model_sha256':sha256(path.read_bytes()).hexdigest(),'roof_deck_z_m':z,
            'southern_paved_area_m2':round(field.area,3),'native_photo_38':rows,
            'model_sections':vertical,'sections_passing':sum(i['pass'] for i in vertical),
            'photo_direct':sum(r['within_3px'] is not None and r['within_3px']['offset_native_px']==[0,0] for r in rows),
            'photo_within_3px':sum(r['within_3px'] is not None for r in rows)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);p.add_argument('--deck-z',type=float,required=True)
    p.add_argument('--export',choices=('full','lod'))
    args=p.parse_args()
    closed=export(args.mesh,args.deck_z,args.export=='lod') if args.export else None
    doc=check(args.mesh,args.deck_z)
    if closed:doc.update(closed)
    args.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(doc['photo_direct'],doc['photo_within_3px'],len(doc['native_photo_38']),doc['sections_passing'],doc['southern_paved_area_m2'])
    if doc['sections_passing']!=len(doc['model_sections']):sys.exit(1)
