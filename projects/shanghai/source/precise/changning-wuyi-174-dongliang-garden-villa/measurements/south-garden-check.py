"""Read a decoded architectural mesh back in house coordinates and test the photographed storefront."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np

SOURCE = Path(__file__).resolve().parents[1]
PROJECT = next(p for p in SOURCE.parents if (p / 'tools/package_architectural_model.py').is_file())
helper = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
SerialScene = runpy.run_path(str(helper))['SerialScene']
sys.path.insert(0, str(SOURCE / 'source'))
from wuyi_fabric import (CrownBuilder, PALETTE as FINISH, STONE, SOFFIT, FABRIC, DOOR,
                         FRAME, WALL, IRON)
from south_garden_bay import add_south_bay, DOOR_GLASS, SHOP_GLASS, FASCIA_FINISH, PALETTE as BAY
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def surface_closure(builder):
    volumes = []
    open_parts = []
    for part in builder.parts:
        points = np.array(part['vertices'])
        cells = np.array(part['triangles'], dtype=int)
        unique, ids = np.unique(points.round(6), axis=0, return_inverse=True)
        triangles = ids[cells]
        directed = Counter((a,b) for a,b,c in triangles for a,b in [(a,b),(b,c),(c,a)])
        edges = [pair for pair,n in directed.items() if n != directed.get(pair[::-1],0)]
        pts = points[cells]
        volume = np.einsum('ij,ij->i',pts[:,0],np.cross(pts[:,1],pts[:,2])).sum()/6
        volumes.append(volume)
        if edges or volume <= 0:
            open_parts.append({'label':part['label'],'unpaired_edges':len(edges),'signed_volume':float(volume)})
    return {'parts':len(volumes),'min_volume':min(volumes),'triangles':sum(len(p['triangles']) for p in builder.parts),'nonclosed_or_inverted':open_parts}


def matrix(coefficients):
    u,v,s,k,dv,ds,yaw,r=coefficients[:8]
    vertical,convergence=coefficients[8:] if len(coefficients)>8 else (1.,0.)
    centered=np.array([[s,ds,r,0],[-r,dv,-s*vertical,0],[yaw,-k,convergence,1.]])
    centered[0]+=u*centered[2]
    centered[1]+=v*centered[2]
    local=centered.copy()
    local[:,3]-=2.96*centered[:,2]
    return local @ np.array([[-1,0,0,9.55],[0,1,0,-13.60],[0,0,1,0],[0,0,0,1]])


# Coordinates below were read in the native photographs. Trees and retail furnishings
# conceal parts of the glass. The source point registers remain fixed for every export.
PHOTO_PROBES = {
    '8': [(310,142,FABRIC),(522,143,FABRIC),(735,154,FABRIC),
          (680,220,DOOR_GLASS),(752,265,DOOR_GLASS),(782,352,DOOR_GLASS),
          (530,440,IRON),(319,431,IRON),(735,431,IRON),(735,434,IRON),
          (530,674,FASCIA_FINISH),(414,667,FASCIA_FINISH),(720,663,FASCIA_FINISH),
          (430,789,SHOP_GLASS),(575,918,SHOP_GLASS),(623,1015,SHOP_GLASS),
          (400,838,FRAME),(530,890,FRAME),(251,787,STONE),(819,775,STONE)],
    '0': [(551,295,FASCIA_FINISH),(512,297,FASCIA_FINISH),(601,294,FASCIA_FINISH),(552,234,IRON),
          (439,248,IRON),(658,239,IRON),(550,329,SHOP_GLASS),(516,328,FRAME)]
}


def photo_ray(scene,P,eye,uv):
    ray=np.linalg.solve(P[:,:3],[*uv,1.])
    if ray[1]>0: ray=-ray
    return scene.ray(eye,ray,100.)


def nearby_visible(scene,P,eye,uv,material,budget):
    """The nearest projected target still has to pass an unfiltered sightline."""
    indices=[i for i,name in enumerate(scene.materials) if name==material]
    if not indices:return None
    tr=scene.tri[np.isin(scene.mi,indices)]
    plane=tr@P[:,:3].T+P[:,3]
    positive=(plane[:,:,2]>1e-6).all(axis=1)
    projected=plane[positive,:,:2]/plane[positive,:,2:]
    sel=(projected.min(axis=1)<=uv+budget).all(axis=1)&(projected.max(axis=1)>=uv-budget).all(axis=1)
    candidates=[]
    p=Point(uv)
    for tri in projected[sel]:
        face=Polygon(tri)
        if face.area<1e-7:continue
        near=nearest_points(p,face)[1]
        # A point just inside the triangle avoids arbitrary first-hit ties along a shared edge.
        sample=.989*np.asarray(near.coords[0])+.011*tri.mean(axis=0)
        delta=float(np.linalg.norm(sample-uv))
        if delta<=budget:candidates.append((delta,sample))
    for delta,sample in sorted(candidates,key=lambda pair:pair[0]):
        hit=photo_ray(scene,P,eye,sample)
        if hit and hit['material']==material:
            return {'native_px':sample.round(3).tolist(),'distance_px':round(delta,3),'first_material':material}
    return None


def rear_wall_clearance(scene):
    results=[]
    for x,z in [(-1.82,4.09),(-1.50,4.22),(-.13,4.06),(.20,4.30),(1.59,4.09),(1.91,4.22),(-.43,1.09),(.28,1.50)]:
        eye=[9.55-x,13.60-.265,z]
        h=scene.ray(eye,[0,1,0],.30)
        results.append({'local_xz':[x,z],'material':h['material'] if h else None,
                        'free_of_roughcast':not h or h['material']!=WALL})
    return results


def shoot(mesh,camera_file):
    scene=SerialScene(mesh);s=json.loads(camera_file.read_bytes())
    results = {}
    for name,rows in PHOTO_PROBES.items():
        P=matrix(s['views'][name]['camera_coefficients'])
        eye=np.linalg.solve(P[:,:3], -P[:,3])
        results[name]={'eye_house_m':eye.tolist(),'probes':[]}
        for u,v,mat in rows:
            hit=photo_ray(scene,P,eye,[u,v])
            matches=bool(hit and hit['material']==mat)
            record={'uv':[u,v],'target':mat,'hit':hit,'matches':matches}
            if not matches:
                budget=s['views'][name]['max_px']
                record['nearby_budget_px']=budget
                record['nearby_visible']=nearby_visible(scene,P,eye,np.asarray([u,v]),mat,budget)
            results[name]['probes'].append(record)
        result=results[name]
        result['matched']=sum(x['matches'] for x in result['probes'])
        result['count']=len(rows)
        datum=s['depth_control']['measured_roof_drip']
        edge_points=datum['photo_08_uv' if name=='8' else 'photo_00_uv']
        result['tile_lip_at_native_coordinates']=[]
        for u,v in edge_points:
            # These are boundary pixels. Record the exposed materials above, on and below the edge.
            readings=[]
            for offset in (-4,0,4):
                hit=photo_ray(scene,P,eye,[u,v+offset])
                readings.append({'delta_v':offset,'hit':hit})
            result['tile_lip_at_native_coordinates'].append({'native_px':[u,v],'samples':readings})
    return {'mesh_sha256':sha(mesh),'mesh_bytes':mesh.stat().st_size,'cameras':results,
            'threshold_wall_clearance':rear_wall_clearance(scene)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('out',type=Path)
    parser.add_argument('--components',action='store_true')
    parser.add_argument('--camera-file',type=Path,default=SOURCE/'measurements/south-garden-two-photographs.json')
    parser.add_argument('meshes',type=Path,nargs='*')
    args=parser.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
    meshes=list(args.meshes);closure={}
    if args.components:
        for lod,tag in [(False,'full'),(True,'lod')]:
            obj=CrownBuilder({**FINISH,**BAY});add_south_bay(obj,lod)
            close=surface_closure(obj)
            if close['nonclosed_or_inverted']:raise ValueError(close)
            mesh=args.out.parent/f'{tag}-bay.glb'
            obj.save(mesh,{'name':'武夷路174号南园弧形阳台、三门与折面玻璃','photos_embedded':False})
            closure[tag]=close;meshes.append(mesh)
    if not meshes:parser.error('Supply a mesh or --components')
    doc={'camera_file':args.camera_file.name,'camera_sha256':sha(args.camera_file),
         'component_closure':closure,'reads':{mesh.name:shoot(mesh,args.camera_file) for mesh in meshes}}
    args.out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    for mesh,row in doc['reads'].items():
        print(mesh,row['mesh_sha256'][:12],[(k,x['matched'],x['count']) for k,x in row['cameras'].items()])
    print(closure)


if __name__=='__main__':main()
