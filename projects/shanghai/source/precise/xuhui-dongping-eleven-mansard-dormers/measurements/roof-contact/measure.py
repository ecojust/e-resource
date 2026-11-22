"""Sample the original roof and the surveyed dormer strip along perpendicular sections."""
from argparse import ArgumentParser
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from statistics import median
import gzip
import json
import math
import os
import runpy
import subprocess
import numpy as np
from shapely.affinity import affine_transform
from shapely.geometry import LineString, Point, shape

parser=ArgumentParser(description=__doc__)
parser.add_argument('--project', required=True,type=Path)
parser.add_argument('--cache',type=Path)
parser.add_argument('--output', required=True,type=Path)
args=parser.parse_args()
project=args.project.resolve()
home=Path(__file__).resolve().parent
src=home.parent.parent
helpers=project/'source/precise/xuhui-anfu-284-timber-jetty/measurements/city-contact'
def read(f):
    return json.loads(f.read_bytes())
def digest(f):
    return sha256(f.read_bytes()).hexdigest()
def rounded(value):
    return round(float(value),5)
files=read(home/'signed-files.json')
register=read(src/'footprint-review.json')
control=read(src/'reference-review.json')['photogrammetry']
recorded={key:register[key]['matched'][0] for key in ('historic_owner','north_auxiliary','east_neighbour')}
lon,lat=shape(recorded['historic_owner']['geometry']).centroid.coords[0]
scale=6371008.8*math.pi/180
mx=math.cos(math.radians(lat))*scale
parcel=affine_transform(shape(recorded['historic_owner']['geometry']),[mx,0,0,scale,-lon*mx,-lat*scale])
first,middle,last=np.array(control['axes_pixels'])
along=last-first
along[1]*=-1
along/=np.linalg.norm(along)
inward=np.array([-along[1],along[0]])
across=LineString([tuple(-40*inward),tuple(40*inward)])
ends=np.array(list(parcel.intersection(across).coords))
eave=ends[np.argmin(ends@inward)]

def intersections(triangles,x,y):
    a=triangles[:,0];b=triangles[:,1];c=triangles[:,2]
    ab=b-a;ac=c-a
    det=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0]
    keep=np.abs(det)>1e-8
    av=a[keep];ab=ab[keep];ac=ac[keep];det=det[keep]
    rx=x-av[:,0];ry=y-av[:,1]
    u=(rx*ac[:,1]-ry*ac[:,0])/det;v=(ab[:,0]*ry-ab[:,1]*rx)/det
    inside=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
    return sorted(set(rounded(z)for z in av[inside,2]+ab[inside,2]*u[inside]+ac[inside,2]*v[inside]))
def eligible(triangles):
    xy=triangles[:,:,:2]
    return triangles[(xy.max(axis=1)>-20).all(axis=1)&(xy.min(axis=1)<20).all(axis=1)]
timeline=[]
def run(cmd,env):
    with subprocess.Popen(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)as proc:
        out,err=proc.communicate()
        timeline.append(dict(program=Path(cmd[1]).name,pid=proc.pid,exit_code=proc.returncode,output_sha256=sha256(out).hexdigest(),stderr_sha256=sha256(err).hexdigest()))
        if proc.returncode:raise RuntimeError(err.decode()[-1200:])
with TemporaryDirectory()as tmp,ExitStack()as stack:
    work=Path(tmp)
    def anonymous(name):
        fd=os.memfd_create(name);stack.callback(os.close,fd)
        f=work/name;f.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');return f
    for name,d in files.items():
        options=[project/d['path']]
        if args.cache:options.insert(0,args.cache/name)
        f=next((p for p in options if p.is_file() and digest(p)==d['sha256']),None)
        if f:(work/name).symlink_to(f.resolve())
        else:
            f=anonymous(name)
            with urlopen(d['url'],timeout=60)as resp:f.write_bytes(resp.read())
            assert digest(f)==d['sha256']
    (work/'initial-local-frame.json').write_text(json.dumps({'anchor':{'lng':lon,'lat':lat}}))
    (work/'context-features.json').write_text(json.dumps([{'localId':r['local_id']}for r in recorded.values()]))
    for level in ('near','far'):
        for suffix in ('triangles.f64','owners.u32'):anonymous(f'baseline-{level}-{suffix}')
    env=dict(os.environ,SHANGHAI_PROJECT=str(project),POSTAL_MAPPING_WORK=str(work),NODE_OPTIONS='--require='+str(helpers/'decode-texture.cjs'))
    run(['node',helpers/'decode-city.mjs'],env)
    cities={}
    for level in ('near','far'):
        tri=np.fromfile(work/f'baseline-{level}-triangles.f64',dtype=np.float64).reshape(-1,3,3)
        if level=='far':
            ids=np.fromfile(work/'baseline-far-owners.u32',dtype=np.uint32)
            tri=tri[ids==recorded['historic_owner']['local_id']]
        cities[level]=eligible(tri)
    load=runpy.run_path(str(helpers/'glb_triangles.py'))['load_triangles']
    rows=[];metrics={};meshes={};retained={}
    for label,record in recorded.items():
        polygon=affine_transform(shape(record['geometry']),[mx,0,0,scale,-lon*mx,-lat*scale])
        retained[label]=dict(owner=record['local_id'],height_m=record['height'],iou=record['iou'],study_centroid_distance_m=rounded(polygon.centroid.distance(Point(eave))))
    for role,key in [('raw','raw'),('near','web'),('far','lod')]:
        name=f'xuhui-dongping-eleven-mansard-dormers-{key}.glb';file=work/name
        if key!='raw':
            dest=anonymous('decoded-'+role+'.glb');run(['node',helpers/'decode-meshopt.mjs',file,dest,project/'vendor/meshopt_decoder.module.js'],env);file=dest
        model=load(file)[0];assert len(model)==files[name]['triangles']
        meshes[role]=dict(triangles=len(model),minimum=np.round(model.min(axis=(0,1)),5).tolist(),maximum=np.round(model.max(axis=(0,1)),5).tolist())
        original=cities['far'if role=='far'else'near'];metrics[role]={}
        for shift in (0.65,1.65,2.65):
            runrows=[]
            for x in np.linspace(-5.32,5.32,71):
                for y in (.035,.135,.235,.335,.435,.535,.635,.735,.825):
                    xy=eave+along*x+inward*(y+shift);old=intersections(original,*xy)
                    fresh=intersections(model,x,y)
                    runrows.append(dict(model_x=rounded(x),model_y=y,old_z=old,model_z=fresh,inside_owner=bool(parcel.covers(Point(xy)))))
            paired=[r for r in runrows if r['old_z']and r['model_z']and r['inside_owner']]
            pitch_away=[r for r in paired if min(abs(r['model_x']-a)for a in (-3.8,0,3.8))>0.84]
            offsets=[max(r['old_z'])-max(r['model_z'])for r in pitch_away]
            fitted=median(offsets)
            def distribution(vals):
                return [rounded(x)for x in np.percentile(vals,[0,10,50,90,100])]
            metrics[role][str(shift)]=dict(traces=len(runrows),paired=len(paired),roof_strip_outside_window_heads=len(offsets),best_constant_offset_m=rounded(fitted),original_roof_m=distribution([max(r['old_z'])for r in pitch_away]),mismatch_m=distribution([v-fitted for v in offsets]),authored_roof_span_m=distribution([max(r['model_z'])for r in pitch_away]))
            rows.extend(dict(role=role,inset_m=shift,**r)for r in runrows)
    assert len(rows)==5751 and all(d['roof_strip_outside_window_heads']>140 for m in metrics.values()for d in m.values())
    body=json.dumps(rows,separators=(',',':')).encode();out=args.output;out.parent.mkdir(parents=True,exist_ok=True)
    casts=out.parent/'roof-and-dormer-rays.json.gz';casts.write_bytes(gzip.compress(body,compresslevel=5,mtime=0))
    report=dict(order=365,id=register['id'],passed=True,site_evidence_sha256=digest(src/'footprint-review.json'),photograph_review_sha256=digest(src/'reference-review.json'),inputs_sha256=digest(home/'signed-files.json'),old_shells=retained,
                registration={'description':'Origin at the centroid of historic shell 336. Study eave is its southern intersection with the perpendicular to the three photographed heads. Compare three insets as alternatives. The published photograph does not set absolute eave elevation.','origin_wgs84':[lon,lat],'source_axes_pixels':control['axes_pixels'],'along_east_north':along.tolist(),'garden_eave_local_m':eave.tolist()},
                models=meshes,vertical_sections=metrics,signed_probe_count=len(rows),uncompressed_probes_sha256=sha256(body).hexdigest(),probes_gzip_sha256=digest(casts),events=timeline)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(metrics,ensure_ascii=False))
