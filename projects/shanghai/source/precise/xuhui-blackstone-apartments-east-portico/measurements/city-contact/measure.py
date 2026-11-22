"""Measure the photographed Blackstone portico against both meshes of the original street block."""
from argparse import ArgumentParser
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
import gzip
import json
import math
import os
import runpy
import subprocess

import numpy as np
from shapely.affinity import affine_transform
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union

parser=ArgumentParser(__doc__)
parser.add_argument('--project',type=Path,default=Path('.'))
parser.add_argument('--cache',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
home=Path(__file__).resolve().parent
project=args.project.resolve()
helpers=project/'source/precise/xuhui-anfu-284-timber-jetty/measurements/city-contact'
survey_file=home.parent.parent/'footprint-review.json'
uid='xuhui-blackstone-apartments-east-portico'
read=lambda f:json.loads(f.read_bytes())
digest=lambda f:sha256(f.read_bytes()).hexdigest()
round_m=lambda x:round(float(x),5)
survey=read(survey_file)
inputs=read(home/'signed-files.json')
anchor=np.array([survey['author_frame']['anchor'][k] for k in ('lng','lat')])
m_per_degree=np.array([math.cos(math.radians(anchor[1])),1.0])*math.pi/180*6371008.8
east_axis=(np.array(survey['registration']['physical_east_axis_wgs84'])-anchor)*m_per_degree
front_axis=(np.array(survey['registration']['physical_first_axis_wgs84'])-anchor)*m_per_degree
x_unit=(front_axis-east_axis)/np.linalg.norm(front_axis-east_axis)
y_unit=np.array([-x_unit[1],x_unit[0]])
assert abs(np.linalg.norm(front_axis-east_axis)-5.700312)<.005
assert np.linalg.norm(east_axis-.12*y_unit)<.012
matrix=np.stack((x_unit,y_unit))
timeline=[]
cache=args.cache.resolve() if args.cache else None

def run(cmd,env):
    child=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    stdout,stderr=child.communicate()
    timeline.append(dict(program=Path(cmd[1]).name,pid=child.pid,exit_code=child.returncode,
                         stdout_sha256=sha256(stdout).hexdigest(),stderr_sha256=sha256(stderr).hexdigest()))
    if child.returncode:raise RuntimeError(stderr.decode('utf-8',errors='replace')[-600:])

def plane_segments(tri,z):
    """Take the intersection of every non-horizontal face with one horizontal survey plane."""
    selected=tri[(tri[:,:,2].min(axis=1)<z)&(tri[:,:,2].max(axis=1)>z)]
    if not len(selected):return np.empty((0,2,2))
    a=selected;b=np.roll(selected,-1,axis=1)
    crosses=((a[:,:,2]<z)!=(b[:,:,2]<z))
    t=np.divide(z-a[:,:,2],b[:,:,2]-a[:,:,2],out=np.zeros_like(a[:,:,2]),where=b[:,:,2]!=a[:,:,2])
    return (a[:,:,:2]+(b[:,:,:2]-a[:,:,:2])*t[:,:,None])[crosses].reshape(-1,2,2)

def line_depth(segments,x):
    if not len(segments):return []
    edges=segments[(segments[:,0,0]<=x)!=(segments[:,1,0]<=x)]
    if not len(edges):return []
    a,b=edges[:,0,:],edges[:,1,:]
    vals=a[:,1]+(b[:,1]-a[:,1])*(x-a[:,0])/(b[:,0]-a[:,0])
    return sorted(set(round_m(y) for y in vals if -16<=y<=19))

def outline_at(segments):
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    if not len(segments):return Polygon()
    ls=[LineString(np.round(e,5)) for e in segments if np.linalg.norm(e[0]-e[1])>.00002]
    return unary_union(list(polygonize(unary_union(ls)))) if ls else Polygon()

def native_to_author(tri):
    converted=tri.copy()
    converted[:,:,:2]=converted[:,:,:2]@matrix.T
    return converted

with TemporaryDirectory() as temp,ExitStack() as resources:
    t=Path(temp)
    def anonymous(name):
        fd=os.memfd_create(name);f=t/name;f.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');resources.callback(os.close,fd);return f
    for name,row in inputs.items():
        basic=project/row['path'];options=[cache/name,basic] if cache else [basic]
        local=next((f for f in options if f.is_file() and digest(f)==row['sha256']),None)
        if local:(t/name).symlink_to(local.resolve())
        else:
            new=anonymous(name)
            with urlopen(row['url'],timeout=90) as response:new.write_bytes(response.read())
            assert digest(new)==row['sha256']
    (t/'initial-local-frame.json').write_text(json.dumps({'anchor':survey['author_frame']['anchor']}))
    (t/'context-features.json').write_text(json.dumps([{'localId':o} for o in survey['selection']['checked_neighbors']]))
    for level in ('near','far'):
        for suffix in ('owners.u32','triangles.f64'):anonymous(f'baseline-{level}-{suffix}')
    env=dict(os.environ,SHANGHAI_PROJECT=str(project),POSTAL_MAPPING_WORK=str(t),NODE_OPTIONS='--require='+str(helpers/'decode-texture.cjs'))
    run(['node',helpers/'decode-city.mjs'],env)
    table=json.loads(gzip.decompress((t/'feature-table.json.gz').read_bytes()))
    originals={row['localId']:row for row in table['features']}
    x,y=m_per_degree;ox,oy=anchor[0]*x,anchor[1]*y
    owners={}
    for owner in survey['selection']['checked_neighbors']:
        poly=affine_transform(shape(originals[owner]['geometry']),[x,0,0,y,-ox,-oy])
        owners[owner]=affine_transform(poly,[x_unit[0],x_unit[1],y_unit[0],y_unit[1],0,0])
    originals_out={k:{'area_m2':round_m(v.area),'height_m':originals[k]['height']} for k,v in owners.items()}
    old={level:native_to_author(np.fromfile(t/f'baseline-{level}-triangles.f64',dtype=np.float64).reshape(-1,3,3))for level in ('near','far')}
    far_ids=np.fromfile(t/'baseline-far-owners.u32',dtype=np.uint32)
    old['far']=old['far'][far_ids==2369]
    loader=runpy.run_path(str(helpers/'glb_triangles.py'))['load_triangles']
    mesh={};sections={};evidence={};casts=[]
    zlevels=[.175,.345,.925,2.225,3.335,3.605,3.815,4.033,4.283,4.675,4.913,5.259,6.927,12.317,16.945]
    for role,suffix in [('raw','raw'),('near','web'),('far','lod')]:
        name=f'{uid}-{suffix}.glb';f=t/name
        if role!='raw':
            d=anonymous('decoded-'+role+'.glb')
            run(['node',helpers/'decode-meshopt.mjs',f,d,project/'vendor/meshopt_decoder.module.js'],env)
            f=d
        tri=loader(f)[0];assert len(tri)==inputs[name]['triangles']
        mesh[role]=dict(triangles=len(tri),minimum=np.round(tri.min(axis=(0,1)),5).tolist(),maximum=np.round(tri.max(axis=(0,1)),5).tolist())
        reference='near' if role=='raw' else role
        level_rows=[];detail={}
        for z in zlevels:
            s=plane_segments(tri,z);b=plane_segments(old[reference],z)
            for xx in np.linspace(-1.302,7.194,89):
                new_hits=line_depth(s,xx);old_hits=line_depth(b,xx)
                level_rows.append(dict(x_m=round_m(xx),z_m=z,model_y_m=new_hits,original_y_m=old_hits))
            if z in (.345,2.225,4.033,4.913):
                shape_at=outline_at(s);detail[str(z)]=dict(area_m2=round_m(shape_at.area),intersect_owner2369_m2=round_m(shape_at.intersection(owners[2369]).area),
                    distance_to_1005_m=round_m(shape_at.distance(owners[1005])) if not shape_at.is_empty else None,
                    neighbors_touched=[k for k,v in owners.items() if k!=2369 and shape_at.intersection(v).area>1.e-5])
        sections[role]=detail
        evidence[role]=dict(rays=len(level_rows),portico_hits=sum(bool(v['model_y_m'])for v in level_rows),original_hits=sum(bool(v['original_y_m'])for v in level_rows),
            paired=sum(bool(v['model_y_m'] and v['original_y_m'])for v in level_rows),
            old_only_high=sum(bool(v['original_y_m']) and not v['model_y_m']and v['z_m']>6 for v in level_rows))
        casts.extend(dict(role=role,**v)for v in level_rows)
    assert all(e['rays']==1335 and e['portico_hits']>200 and e['original_hits']>100 for e in evidence.values())
    assert all(sections[role]['0.345']['area_m2']>.08 and sections[role]['4.033']['area_m2']>1 for role in sections)
    assert all(not point['neighbors_touched'] for row in sections.values()for point in row.values())
    body=json.dumps(casts,separators=(',',':')).encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    zipped=args.output.with_name('portico-and-street-rays.json.gz');zipped.write_bytes(gzip.compress(body,compresslevel=5,mtime=0))
    out=dict(order=361,id=uid,source_author_footprint_sha256=digest(survey_file),inputs_sha256=digest(home/'signed-files.json'),
              coordinate_system='X from east pair to front pair; +Y follows the right-handed horizontal perpendicular; Z up. Source city actual mesh matrices and Mercator scaling applied.',
              address='复兴中路1331号',anchor=anchor.tolist(),column_dist_m=round_m(np.linalg.norm(front_axis-east_axis)),retained_owners=originals_out,
              authored_meshes=mesh,model_cross_sections=sections,model_and_street_intersections=evidence,
              source_far_owner=2369,source_near_selection='Original near tile within 16 m of the registered two support pairs; the far model is filtered to owner 2369.',rays=len(casts),ray_gzip_sha256=digest(zipped),uncompressed_rays_sha256=sha256(body).hexdigest(),events=timeline,passed=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(evidence,sections,flush=True)
