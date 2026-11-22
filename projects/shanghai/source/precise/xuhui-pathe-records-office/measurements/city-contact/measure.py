"""Measure the released house and both original city meshes in the north-wall survey frame."""
from argparse import ArgumentParser
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen
import gzip, json, math, os, subprocess, sys, time
import numpy as np
from shapely.geometry import MultiPoint, Polygon, box
from shapely.ops import polygonize, unary_union
from shapely import LineString
from glb_triangles import load_triangles

def load(f): return json.loads(f.read_bytes())
def digest(f): return sha256(f.read_bytes()).hexdigest()
def put(f, data): f.write_text(json.dumps(data, ensure_ascii=False, separators=(',',':'))+'\n')
def rnd(value): return round(float(value), 4)

def section(triangles, height):
    z = triangles[:,:,2]
    selected = triangles[(z.min(axis=1)<height) & (z.max(axis=1)>height)]
    lines = []
    for tri in selected:
        points = []
        for a,b in ((0,1),(1,2),(2,0)):
            left,right = tri[a],tri[b]
            if (left[2] < height) != (right[2] < height):
                fraction = (height-left[2])/(right[2]-left[2])
                points.append(tuple(np.round(left[:2]+fraction*(right[:2]-left[:2]), 5)))
        if len(points)==2 and points[0]!=points[1]:
            lines.append(LineString(points))
    if not lines: return Polygon()
    return unary_union(list(polygonize(unary_union(lines))))

def overhead(triangles, samples):
    # Vertical intersection of each actual upward/downward face, ignoring zero-area XY projections.
    a=triangles[:,0]; b=triangles[:,1]-a; c=triangles[:,2]-a
    det=b[:,0]*c[:,1]-b[:,1]*c[:,0]
    good=abs(det)>1e-8
    a,b,c,det=a[good],b[good],c[good],det[good]
    left=triangles[good,:,:2].min(axis=1);right=triangles[good,:,:2].max(axis=1)
    hits=[]
    for x,y in samples:
        idx=np.where((left[:,0]<=x)&(left[:,1]<=y)&(right[:,0]>=x)&(right[:,1]>=y))[0]
        aa,bb,cc,dd=a[idx],b[idx],c[idx],det[idx]
        dx=x-aa[:,0];dy=y-aa[:,1]
        u=(dx*cc[:,1]-dy*cc[:,0])/dd;v=(bb[:,0]*dy-bb[:,1]*dx)/dd
        ok=(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)
        heights=aa[:,2]+u*bb[:,2]+v*cc[:,2]
        hits.append(rnd(max(heights[ok])) if ok.any() else None)
    return hits

parser=ArgumentParser()
parser.add_argument('--project',type=Path,default=Path('.'))
parser.add_argument('--cache',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
project=args.project.resolve();home=Path(__file__).resolve().parent
inputs=load(home/'signed-files.json');survey=load(home.parent/'surveyed-plan-clearances.json')
anchor=np.array(survey['north_wall_midpoint_wgs84'])
coslat=math.cos(math.radians(anchor[1]));metres=np.array([math.pi*6371008.8/180*coslat,math.pi*6371008.8/180])
headings=np.deg2rad([survey['true_bearing_positive_x'],survey['true_bearing_positive_y']])
basis=np.array([np.sin(headings),np.cos(headings)])
samples=[(x/2,y/2)for x in range(-20,24)for y in range(-9,38)]
events=[]; summaries={};probe_rows={}
with TemporaryDirectory() as work,ExitStack() as resources:
    q=Path(work)
    def anonymous(name):
        fd=os.memfd_create('pathe-'+name);resources.callback(os.close,fd)
        dest=q/name;dest.symlink_to('/proc/'+str(os.getpid())+'/fd/'+str(fd));return dest
    for key,meta in inputs.items():
        choices=([args.cache/key]if args.cache else [])+[project/meta['path']]
        source=next((f for f in choices if f.is_file() and digest(f)==meta['sha256']),None)
        f=q/key
        if source: f.symlink_to(source.resolve())
        else:
            f=anonymous(key)
            with urlopen(Request(meta['url'],headers={'Accept-Encoding':'identity'}),timeout=60)as response: f.write_bytes(response.read())
        assert f.stat().st_size==meta['bytes'] and digest(f)==meta['sha256']
    ready=load(q/'macro-READY.json')
    tile=next(row for row in ready['tiles'] if 1982 in row['featureLocalIds'])
    assert ready['far']['sha256']==inputs['baseline-far.glb']['sha256'] and tile['sha256']==inputs['baseline-near.glb.gz']['sha256']
    table=json.loads(gzip.decompress((q/'feature-table.json.gz').read_bytes()))['features']
    owner=None;nearby={}
    for row in table:
        geom=row['geometry']
        if geom['type']!='Polygon':continue
        poly=Polygon(((np.array(geom['coordinates'][0])[:,:2]-anchor)*metres)@basis)
        if poly.is_valid and poly.distance(Polygon([(-9,-1),(10,-1),(10,17),(-9,17)]))<75:
            nearby[row['localId']]=poly
            if row['localId']==1982: owner=poly
    assert owner is not None and {1971,779}.issubset(nearby)
    put(q/'initial-local-frame.json',{'anchor':{'lng':anchor[0],'lat':anchor[1]}})
    put(q/'context-features.json',[{'localId':1982}])
    for level in ('near','far'):
        for kind in ('triangles.f64','owners.u32'):anonymous('baseline-'+level+'-'+kind)
    env=dict(os.environ,POSTAL_MAPPING_WORK=str(q),SHANGHAI_PROJECT=str(project),NODE_OPTIONS='--require='+str(home/'decode-texture.cjs'))
    def run(cmd):
        proc=subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL);code=proc.wait();events.append({'program':Path(cmd[1]).name,'pid':proc.pid,'exit':code});assert code==0
    run(['node',home/'decode-city.mjs'])
    groups={'main':box(-7,-.02,7,13.65),'south':box(-9,13.65,11,18),'west_wing':box(7,0,11,13.65),'north_steps_and_canopy':box(-9,-3,11,-.02)}
    for level in ('old_near','old_far','raw','full','lod'):
        if level.startswith('old_'):
            key=level[4:];tri=np.fromfile(q/('baseline-'+key+'-triangles.f64'),dtype='<f8').reshape(-1,3,3);tri[:,:,:2]=tri[:,:,:2]@basis
            if key=='near':
                # The near draw is grouped. Keep only triangles with centroids on the owner or its facade projections.
                centres=tri[:,:,:2].mean(axis=1);from shapely import intersects_xy
                tri=tri[intersects_xy(owner.buffer(1.0),centres[:,0],centres[:,1])]
        else:
            f=q/(level+'.glb')
            if level!='raw':
                target=anonymous('decoded-'+level+'.glb');run(['node',home/'decode-meshopt.mjs',f,target,project/'vendor/meshopt_decoder.module.js']);f=target
            tri=load_triangles(f)[0]
        pts=tri[:,:,:2].reshape(-1,2); hull=MultiPoint(np.unique(np.round(pts,5),axis=0)).convex_hull
        hts=overhead(tri,samples)
        s={}
        for z in (.24,1.20,2.70,5.20,7.91,9.53):
            plane=section(tri,z)
            s[str(z)]={'material_enclosed_m2':rnd(plane.area),'outside_owner_m2':rnd(plane.difference(owner).area),'by_zone_m2':{k:rnd(v.intersection(plane).area)for k,v in groups.items()}}
        summaries[level]={'triangles':len(tri),'z_range_m':[rnd(tri[:,:,2].min()),rnd(tri[:,:,2].max())],'sections':s,'hull_m2':rnd(hull.area),'hull_outside_owner_m2':rnd(hull.difference(owner).area),'neighbour_clearance_m':{str(k):rnd(hull.distance(v))for k,v in nearby.items()if k!=1982},'vertical_hits':sum(v is not None for v in hts)}
        probe_rows[level]=hts
        print(level,len(tri),summaries[level]['z_range_m'],s['1.2'],flush=True)
result={'order':380,'id':'xuhui-pathe-records-office','existing_owner':1982,'inputs':inputs,'source_frame_sha256':digest(home.parent/'surveyed-plan-clearances.json'),'directions_degrees':np.rad2deg(headings).tolist(),'north_wall_midpoint_wgs84':anchor.tolist(),'extent_of_original_m2':rnd(owner.area),'near_original_group':tile['featureLocalIds'],'neighbour_ids':sorted(k for k in nearby if k!=1982),'method':'Signed meshes decoded with their node transforms. Sections are unions of polygonized transverse face segments at 5 decimal places. A separate vertical ray grid at half-metre spacing records highest first triangle; empty courtyard samples are retained. Original near draw is spatially isolated with the source polygon plus one metre. Hull values are outer bounds, not masonry area.','summaries':summaries,'grid':samples,'first_roof_z':probe_rows,'processes':events}
args.output.parent.mkdir(parents=True,exist_ok=True);put(args.output,result)
