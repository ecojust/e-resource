"""Measure independent sky-to-tile edges in a source photograph and three glTF meshes."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = {'left': [533,538,543,548,553,558,563], 'right': [578,581,584,587,590,593,596]}
TRAIN = [[526.8,109.8], [602.1,101.1], [573.6,65.0]]
LIMITS = {'rms_working_pixels': 2.0, 'max_working_pixels': 3.5}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def json_report(path, value):
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def photograph(path, camera):
    digest = sha(path.read_bytes())
    assert digest == camera['garden_photo_sha256']
    with Image.open(path) as image:
        width,height=image.size
        assert (width,height)==(4032,3024) and list(camera['working_size'])==[800,600]
        sx,sy=width/800,height/600
        left,top=2600,240
        source=np.asarray(image.crop((left,top,3050,600)).convert('RGB'),dtype=np.int16)
    def first(x):
        col=source[:,x-left]
        red,green,blue=col.T
        sky=(blue-red>25)&(blue-green>7)
        for y in range(5,len(col)-7):
            if np.all(sky[y-3:y]) and not np.any(sky[y:y+7]):
                return top+y
        # A soft colour boundary can straddle one pixel. In that case require
        # two blue sky samples in the three pixels preceding seven opaque ones.
        for y in range(5,len(col)-7):
            if np.sum(sky[y-3:y]) >= 2 and not np.any(sky[y:y+7]):
                return top+y
        raise ValueError(f'No sky-to-tile transition at source column {x}')
    rows=[]
    for side,columns in COLUMNS.items():
        for col in columns:
            u=round((col+.5)*sx-.5)
            ys=[first(x) for x in range(u-2,u+3)]
            boundary=float(np.median(ys))-.5
            cy=math.floor(boundary+.5)
            rows.append({'slope':side,'original_x':u,'first_tile_y_columns_minus2_to_plus2':ys,
                         'original_boundary_y':boundary,'working_uv':[(u+.5)/sx-.5,(boundary+.5)/sy-.5],
                         'sky_rgb_minus3':source[cy-3-top,u-left].tolist(),
                         'roof_rgb_plus4':source[cy+4-top,u-left].tolist()})
    return {'source_photo_sha256':digest,'source':'https://commons.wikimedia.org/wiki/File:Hongqiaolu_Baichongxi_Jiuju.jpg','author':'Fayhoo','date':'2018-07-14','license':'CC BY-SA 3.0','original_pixels':[width,height],
            'working_pixels':[800,600],'pixel_coordinates':'Top left pixel centre is (0,0). The boundary lies halfway between the last sky and first tile pixel. Five original columns give the median boundary.',
            'blue_sky_rule':'B-R>25 and B-G>7. Seven consecutive non-sky samples below, three blue above (two accepted if no fully blue transition).',
            'camera_calibration':'16 attic-glass corners in garden-camera.json. The roof slope sampling uses the same photograph and camera, at additional pixels.',
            'roof_construction_controls_working_uv':TRAIN,'selection':'Seven fixed interior columns on each upper slope. No chosen column was an endpoint used to construct the roof.',
            'limits':LIMITS,'measurements':rows}

def glb(data):
    if data[:4]!=b'glTF' or struct.unpack_from('<I',data,4)[0]!=2 or struct.unpack_from('<I',data,8)[0]!=len(data):
        raise ValueError('Invalid GLB header or byte length')
    size,kind=struct.unpack_from('<II',data,12)
    if kind!=0x4e4f534a: raise ValueError('GLB JSON chunk missing')
    doc=json.loads(data[20:20+size])
    length,kind=struct.unpack_from('<II',data,20+size)
    if kind!=0x004e4942: raise ValueError('GLB binary chunk missing')
    return doc,memoryview(data)[28+size:28+size+length]

def unpack(path):
    stored=path.read_bytes()
    if stored[:4] != bytes.fromhex('28b52ffd'):
        return stored,stored
    # The decoder writes to a Linux memory file. Nothing is expanded into the archive.
    with os.fdopen(os.memfd_create('garden-photo-check-glb'), 'w+b') as handle:
        subprocess.run(['zstd','--quiet','--decompress','--stdout'],input=stored,stdout=handle,check=True)
        handle.seek(0)
        return stored,handle.read()

def decode_meshopt(source,project):
    decoder=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    module=project/'vendor/meshopt_decoder.module.js'
    with os.fdopen(os.memfd_create('garden-packed-glb'),'w+b') as original, os.fdopen(os.memfd_create('garden-decoded-glb'),'w+b') as decoded:
        original.write(source);original.flush()
        fds=(original.fileno(),decoded.fileno())
        subprocess.run(['node',decoder,f'/proc/self/fd/{fds[0]}',f'/proc/self/fd/{fds[1]}',module],check=True,pass_fds=fds,stdout=subprocess.DEVNULL)
        decoded.seek(0)
        return decoded.read()

def geometry(path,project):
    stored,source=unpack(path)
    doc,buf=glb(source)
    compressed=any('EXT_meshopt_compression' in v.get('extensions',{}) for v in doc['bufferViews'])
    raw=source
    if compressed:
        raw=decode_meshopt(source,project)
        doc,buf=glb(raw)
    def accessor(index):
        a=doc['accessors'][index]
        assert 'sparse' not in a
        v=doc['bufferViews'][a['bufferView']]
        dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        size={'VEC3':3,'SCALAR':1}[a['type']]
        return np.ndarray((a['count'],size),dtype=dt,buffer=buf,offset=a.get('byteOffset',0)+v.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*size),dt.itemsize))
    triangles=[]; material_ids=[]
    def node(index,parent):
        n=doc['nodes'][index]
        if 'matrix' in n:
            local=np.asarray(n['matrix']).reshape(4,4).T
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1])
            rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                          [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                          [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            local=np.eye(4);local[:3,:3]=rot@np.diag(n.get('scale',[1.,1.,1.]));local[:3,3]=n.get('translation',[0.,0.,0.])
        world=parent@local
        if 'mesh' in n:
            for prim in doc['meshes'][n['mesh']]['primitives']:
                if prim.get('mode',4)!=4: raise ValueError('Unexpected non-triangle primitive')
                xyz=accessor(prim['attributes']['POSITION'])@world[:3,:3].T+world[:3,3]
                xyz=xyz[:,[0,2,1]].copy();xyz[:,1]*=-1
                indices=accessor(prim['indices']).ravel() if 'indices' in prim else np.arange(len(xyz))
                tri=xyz[indices.reshape(-1,3)]
                triangles.append(tri);material_ids.append(np.full(len(tri),prim['material'],dtype=np.int32))
        for child in n.get('children',[]): node(child,world)
    for index in doc['scenes'][doc.get('scene',0)]['nodes']: node(index,np.eye(4))
    return (np.concatenate(triangles),np.concatenate(material_ids),[m['name'] for m in doc['materials']],
            {'source_file':path.name,'source_sha256':sha(source),'source_bytes':len(source),'stored_sha256':sha(stored),'stored_bytes':len(stored),
             'meshopt_decoded':compressed,'decoded_sha256':sha(raw)})

def intersections(triangles,ids,eye,inv,uv):
    direction=inv@np.array([*uv,1.]);direction/=np.linalg.norm(direction)
    e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
    p=np.cross(direction,e2);det=np.einsum('ij,ij->i',p,e1)
    nonparallel=np.abs(det)>1e-11
    factor=np.divide(1.,det,out=np.zeros_like(det),where=nonparallel)
    s=eye-triangles[:,0];q=np.cross(s,e1)
    u=np.einsum('ij,ij->i',s,p)*factor
    v=(q@direction)*factor
    distance=np.einsum('ij,ij->i',e2,q)*factor
    valid=np.flatnonzero(nonparallel&(distance>0)&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9))
    if not len(valid): return None
    k=valid[np.argmin(distance[valid])]
    return {'triangle_index':int(ids[k]),'world_xyz':(eye+distance[k]*direction).tolist(),'ray_distance_m':float(distance[k])}

def check(path,project,photo,camera):
    tri,mats,names,result=geometry(path,project)
    M=np.asarray(camera['pinhole_3x4']);eye=np.asarray(camera['eye_xyz']);inv=np.linalg.inv(M[:,:3])
    assert np.linalg.norm(M[:,:3]@eye+M[:,3])<1e-5
    screen=tri@M[:,:3].T+M[:,3]
    if np.min(screen[:,:,2])<=0: raise ValueError('This checker requires all mesh triangles in front of this calibrated camera')
    pix=screen[:,:,:2]/screen[:,:,2,None]
    rows=[]
    for measured in photo['measurements']:
        x,y=measured['working_uv']
        ids=np.flatnonzero((pix[:,:,0].min(axis=1)<=x)&(pix[:,:,0].max(axis=1)>=x))
        g=pix[ids];cuts=[]
        for a,b in ((0,1),(1,2),(2,0)):
            dx=g[:,b,0]-g[:,a,0]
            t=np.divide(x-g[:,a,0],dx,out=np.full_like(dx,np.nan),where=np.abs(dx)>1e-12)
            keep=(0<=t)&(t<=1)
            cuts.extend((g[keep,a,1]+t[keep]*(g[keep,b,1]-g[keep,a,1])).tolist())
        edge=min(cuts)
        def cast(v):
            h=intersections(tri[ids],ids,eye,inv,[x,v])
            if h: h['material']=names[mats[h['triangle_index']]]
            return h
        above=cast(edge-.05);below=cast(edge+.05);below1=cast(edge+1.)
        residual=edge-y
        rows.append({'slope':measured['slope'],'original_x':measured['original_x'],'photo_working_y':y,
                     'mesh_working_edge_y':edge,'mesh_minus_photo_working_px':residual,'mesh_edge_original_y':(edge+.5)*photo['original_pixels'][1]/600-.5,
                     'above_first_hit':above,'below_first_hit':below,'one_pixel_inside':below1,
                     'roof_is_first':above is None and below is not None and below['material'].startswith('480 ')})
    residuals=np.array([r['mesh_minus_photo_working_px'] for r in rows])
    rms=float(np.sqrt((residuals**2).mean())); maximum=float(np.max(np.abs(residuals)))
    result.update(triangle_count=len(tri),columns=rows,rms_working_px=rms,max_abs_working_px=maximum,
                  mean_signed_working_px=float(residuals.mean()),passed=all(r['roof_is_first'] for r in rows) and rms<=LIMITS['rms_working_pixels'] and maximum<=LIMITS['max_working_pixels'])
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--photo',type=Path,default=ROOT/'garden-original.jpg')
    parser.add_argument('--camera',type=Path,default=ROOT/'measurements/garden-camera.json')
    parser.add_argument('--project',type=Path,default=Path.cwd(),help='Shanghai project root containing vendor and source if a model uses Meshopt')
    parser.add_argument('--delivery-dir',type=Path,help='Verify each GLB against the release manifest and independently decode the two delivered Meshopt files')
    parser.add_argument('--photo-only',action='store_true')
    for role in ('raw','full','lod'): parser.add_argument('--'+role,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();camera=json.loads(args.camera.read_bytes())
    photo=photograph(args.photo,camera)
    result={'photograph':photo,'camera_sha256':sha(args.camera.read_bytes()),'checker_sha256':sha(Path(__file__).read_bytes())}
    if not args.photo_only:
        if not all((args.raw,args.full,args.lod)):parser.error('supply all three delivery models')
        if len({p.resolve() for p in (args.raw,args.full,args.lod)})!=3:parser.error('three distinct delivery paths required')
        result['method']='Project the entire scene. Intersect each projected triangle with one fixed image column and find its earliest upper boundary. Independently cast camera rays 0.05 pixels above and below that boundary and one pixel inside to identify the nearest 3-D triangle.'
        result['roles']={role:check(getattr(args,role),args.project,photo,camera) for role in ('raw','full','lod')}
        if args.delivery_dir:
            manifest_file=args.delivery_dir/'manifest.json'
            manifest=json.loads(manifest_file.read_bytes())
            result['delivery_manifest_sha256']=sha(manifest_file.read_bytes())
            for role,measure in result['roles'].items():
                entry=manifest['assets'][role]
                file=args.delivery_dir/entry['file']
                if not file.is_file(): file=file.with_name(file.name+'.zst')
                archived,wire=unpack(file)
                assert len(wire)==entry['bytes'] and sha(wire)==entry['sha256']
                decoded=decode_meshopt(wire,args.project) if role!='raw' else wire
                assert sha(decoded)==measure['decoded_sha256'] and measure['triangle_count']==entry['triangles']
                measure['delivered_file']=entry['file'];measure['delivered_sha256']=sha(wire)
                measure['delivered_store_sha256']=sha(archived)
                measure['independent_decode_matches_measured_glb']=True
        result['passed']=all(r['passed'] for r in result['roles'].values())
    json_report(args.output,result)
    print(json.dumps({r:{k:v[k] for k in ('triangle_count','rms_working_px','max_abs_working_px','passed')} for r,v in result.get('roles',{}).items()}))
    if result.get('passed') is False: raise SystemExit(1)

if __name__=='__main__': main()
