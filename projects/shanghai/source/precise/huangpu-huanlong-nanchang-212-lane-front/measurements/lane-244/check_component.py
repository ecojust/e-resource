"""Build both gate meshes and check visible materials on rays from the 2015 camera."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import trimesh

folder=Path(__file__).resolve().parent
site=folder.parents[1]
project=next(p for p in site.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(site/'source'),str(project/'source/precise/hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from lane_244 import add_244,PALETTE

def transform(station):
    d=json.loads((folder/'photogrammetry.json').read_text())
    q=d['source_views'][station]
    bearing,pitch=np.radians([q['az'],q['pitch']]);fx=q['width']*.5/np.tan(np.radians(q['hfov']*.5))
    right=np.array([np.cos(bearing),-np.sin(bearing),0.]);forward=np.array([np.sin(bearing)*np.cos(pitch),np.cos(bearing)*np.cos(pitch),np.sin(pitch)])
    image=np.array([[fx,0,q['width']*.5],[0,fx,q['height']*.5],[0,0,1.]])@np.array([right,-np.cross(right,forward),forward])
    t=np.radians(d['local_x_bearing_clockwise_from_true_north_deg'])
    local=np.array([[np.sin(t),np.cos(t),0],[-np.cos(t),np.sin(t),0],[0,0,1]])
    anchor=np.array(d['origin_mc'])
    camera=local@np.r_[(np.array(q['station']['mc'])-anchor)*d['metres_per_map_unit'],q['station']['height']]
    camera[2]-=d['local_floor_plane_above_camera_street_datum_m']
    return camera,image@local.T,q

def ray(mesh,eye,v):
    a,e1,e2=mesh[:,0],mesh[:,1]-mesh[:,0],mesh[:,2]-mesh[:,0]
    pp=np.cross(v,e2);den=np.einsum('ij,ij->i',e1,pp)
    with np.errstate(divide='ignore',invalid='ignore'):
        s=eye-a;u=np.einsum('ij,ij->i',s,pp)/den;qq=np.cross(s,e1);b=qq@v/den;t=np.einsum('ij,ij->i',e2,qq)/den
        good=(np.abs(den)>1e-10)&(u>=0)&(b>=0)&(u+b<=1)&(t>0)
    return int(np.argmin(np.where(good,t,np.inf))) if good.any() else None

def verify(lod,draw):
    b=Builder(PALETTE);add_244(b,lod)
    meshes=[trimesh.Trimesh(vertices=p['vertices'],faces=p['triangles'],process=False) for p in b.parts]
    assert all(m.is_volume and m.is_watertight for m in meshes)
    triangles=np.concatenate([m.triangles for m in meshes])
    indices=np.concatenate([np.full(len(m.faces),i)for i,m in enumerate(meshes)])
    result={'component_parts':len(meshes),'triangles':len(triangles),'positive_watertight_parts':len(meshes),'rays':[]}
    materials={'glass':'smoked window glass','wall':'warm lime-plastered courses','plate':'dark green number plate','base':'brown-grey stone plinth'}
    tests={'near-wall':{'glass':[[446,133],[489,135],[448,222],[493,222]],'wall':[[351,220],[552,220],[497,391]],'plate':[[390,135]],'base':[[416,586]]},
           'oblique-wall':{'glass':[[489,162],[550,170],[495,266],[560,267]],'wall':[[419,255],[433,395]],'plate':[[432,173]],'base':[[411,557]]}}
    for view,groups in tests.items():
        eye,camera,meta=transform(view)
        for expected,points in groups.items():
            for pixel in points:
                k=ray(triangles,eye,np.linalg.solve(camera,[*pixel,1.]))
                hit=b.parts[indices[k]] if k is not None else {}
                actual=hit.get('material','').split(' | ')[-1]
                result['rays'].append(dict(view=view,pixel=pixel,expected=materials[expected],actual=actual,part=hit.get('label')))
        if draw:
            from PIL import Image
            width,height=meta['width'],meta['height']
            rgb=np.empty((height,width,3),dtype=np.uint8);rgb[:]=(218,224,226)
            radial=np.full((height,width),np.inf)
            loc=(triangles-eye)@camera.T;xy=loc[:,:,:2]/loc[:,:,2,None]
            for k,t in enumerate(xy):
                depths=loc[k,:,2]
                if min(depths)<=0:continue
                x0,y0=np.maximum(0,np.floor(t.min(axis=0)).astype(int))
                x1,y1=np.minimum((width-1,height-1),np.ceil(t.max(axis=0)).astype(int))
                if x1<x0 or y1<y0:continue
                a,c,e=t;den=(c[1]-e[1])*(a[0]-e[0])+(e[0]-c[0])*(a[1]-e[1])
                if abs(den)<1e-9:continue
                ys,xs=np.ogrid[y0:y1+1,x0:x1+1]
                u=((c[1]-e[1])*(xs+.5-e[0])+(e[0]-c[0])*(ys+.5-e[1]))/den
                v=((e[1]-a[1])*(xs+.5-e[0])+(a[0]-e[0])*(ys+.5-e[1]))/den
                w=1.-u-v;mask=(u>=0)&(v>=0)&(w>=0)
                iz=u/depths[0]+v/depths[1]+w/depths[2];depth=np.full_like(iz,np.inf)
                np.divide(1.,iz,out=depth,where=mask);patch=radial[y0:y1+1,x0:x1+1]
                mask &= depth<patch
                if not mask.any():continue
                row=b.parts[indices[k]];material=np.array(PALETTE[row['material']]['color'])
                norm=np.cross(triangles[k,1]-triangles[k,0],triangles[k,2]-triangles[k,0]);norm/=np.linalg.norm(norm)
                color=np.clip((material*(.71+.21*abs(norm[1])+.08*norm[2]))**(1/2.2)*255,0,255).astype(int)
                patch[mask]=depth[mask];rgb[y0:y1+1,x0:x1+1][mask]=color
            im=Image.fromarray(rgb)
            im.save(draw/f'{view}-{"far" if lod else "full"}.png')
    result['matched']=sum(r['expected']==r['actual'] for r in result['rays'])
    assert result['matched']==len(result['rays']),result['rays']
    # The grille is through-open at eight measured intervals between its nine bars.
    result['gate_sections']=[]
    levels=(.385,.946,1.865,2.302)
    uprights=np.linspace(-.884,-.041,9)
    for z in levels:
        for y,solid in [(u,True)for u in uprights]+[(u,False)for u in (uprights[:-1]+uprights[1:])/2]:
            k=ray(triangles,np.array([3.00,y,z]),np.array([-1.,0.,0.]))
            material=b.parts[indices[k]]['material']if k is not None else None
            assert ('dark iron gate' in (material or ''))==solid,(y,z,material)
            result['gate_sections'].append(dict(y=float(y),z=z,expected='iron'if solid else 'opening',observed=material))
    return result

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--output',type=Path,required=True);cli.add_argument('--render',type=Path)
    args=cli.parse_args()
    if args.render:args.render.mkdir(parents=True,exist_ok=True)
    d={q:verify(l,args.render)for q,l in [('full',False),('lod',True)]}
    d['model_source_sha256']=hashlib.sha256((site/'source/lane_244.py').read_bytes()).hexdigest()
    d['measurements_sha256']=hashlib.sha256((folder/'photogrammetry.json').read_bytes()).hexdigest()
    args.output.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    print([(k,d[k]['matched'],len(d[k]['rays']))for k in ('full','lod')])
