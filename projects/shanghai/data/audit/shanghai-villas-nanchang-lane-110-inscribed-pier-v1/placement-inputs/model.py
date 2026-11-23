"""Join the garden portico to the actual source footprint and test open and closed French doors."""
from pathlib import Path
from hashlib import sha256
import json, math, os, runpy, sys
import numpy as np
import shapely as g
from shapely import geometry as G
from shapely.geometry import Point,box

project=Path(os.environ.get('VILLA_PROJECT') or next(p for p in Path(__file__).resolve().parents if (p/'tools/package_architectural_model.py').is_file()))
w=Path(os.environ.get('VILLA_WORK',Path(__file__).resolve().parent)); model_id='huangpu-shanghai-villas-nanchang-lane-110-inscribed-pier'
ri=lambda f:json.loads(f.read_bytes());sha=lambda b:sha256(b).hexdigest()
def save(file,value):
    file.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
frame=ri(w/'portal-frame.json');lon,lat=frame['anchor'];heading=frame['runtime_heading_degrees'];h=math.radians(heading)
axes=np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]]);k=6371008.8*math.cos(math.radians(lat));loglat=math.asinh(math.tan(math.radians(lat)))
def loc(x):return np.column_stack((np.radians(x[:,0]-lon)*k,(np.arcsinh(np.tan(np.radians(x[:,1])))-loglat)*k))@axes.T
def wgs(x):
    east,north=(x@axes).T
    return np.column_stack((lon+np.degrees(east/k),np.degrees(np.arctan(np.sinh(loglat+north/k)))))
class Asset:
    def __init__(self,name,b):self.name,self.content=name,b
    def read_bytes(self):return self.content

def make_scenes(assets):
    import zstandard
    manifest=ri(assets/'manifest.json');files=ri(assets/'six-source-backed-exports.json')
    scene=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
    def get(n):
        path=assets/n
        if path.is_file():data=path.read_bytes()
        else:
            packed=(assets/(n+'.zst')).read_bytes();assert sha(packed)==files[n]['archive_sha256']
            data=zstandard.ZstdDecompressor().decompress(packed)
        assert sha(data)==files[n]['sha256'] and len(data)==files[n]['bytes']
        return data
    assert manifest['id']==model_id
    scenes={}
    for role in ('raw','full','lod'):
        meta=manifest['assets'][role];data=get(meta['file']);assert sha(data)==meta['sha256'] and len(data)==meta['bytes']
        name=meta['file'] if role=='raw' else 'decoded-'+role+'.glb';data=data if role=='raw' else get(name)
        scenes[role]=scene(Asset(name,data));assert len(scenes[role].tri)==meta['triangles']
    return manifest,scenes


def main(assets):
    m,scenes=make_scenes(assets);ref=ri(w/'footprint-review.json')
    owner=next(r for r in ref['owners']if r['local_id']==3695)
    old={r['local_id']:g.transform(G.shape(r['geometry']),loc) for r in ref['owners']}
    sec=runpy.run_path(str(project/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']
    sections={role:sec(scene.tri,.29) for role,scene in scenes.items()}
    # The bases and both iron wings are represented by the horizontal section; the left wall and posts have unchanged footprints higher up.
    collision=g.union_all(list(sections.values()),grid_size=.001).buffer(.006).simplify(.001,preserve_topology=True)
    print('original clearances',collision.distance(old[3695]),collision.distance(old[214]),flush=True);assert collision.disjoint(old[3695]) and collision.disjoint(old[214])
    eps=1e-6
    tests=[]
    def probe(label,x,y,hit):
        pt=Point(x,y);model=collision.covers(pt);sources=[k for k,s in old.items() if s.covers(pt)];assert (bool(model or sources))==hit,(x,y,model,sources)
        tests.append({'name':label,'xy':[x,y],'wgs84':wgs(np.array([[x,y]]))[0].tolist(),'model_obstacle':model,'old_owners':sources,'expected_map':'building' if hit else None})
    for px in [-1.835,1.835]:
        for xx in [px-.19,px,px+.19]:
            for yy in [.07,.34,.58]:probe('题名柱柱座',xx,yy,True)
    for x in [-.7,-.48,-.25]:
        for y in [-1,-.7,-.35,0,.25,.5,.8,1.15,1.5,1.92]:probe('两柱间街侧与门后有限前段',x,y,False)
    for geom_owner in ref['checked_neighbors']:
        q=old[geom_owner].representative_point();probe('原城邻栋'+str(geom_owner),q.x,q.y,True)
    for x in [-5,-3.7,0,3.4,5]:
        for y in [-1.25,-.9]:probe('沿南昌路人行道',x,y,False)
    glb=m['assets']['raw']['bounds_gltf_m']; owner_ref={'macro_id':ref['frozen_macro'],'feature_local_id':3695}
    c=dict(id=model_id,lng=lon,lat=lat,heading=heading,scale=1,altitude=0,owner=owner_ref,source_feature_ids={'building':[],'building_part':[]},replacement_geometry=None,collision_geometry=G.mapping(g.transform(collision,wgs)),bounds_glb={'min':glb[0],'max':glb[1]},model_geometry_sha256={k:m['assets'][v]['sha256']for k,v in [('raw','raw'),('web','full'),('lod','lod')]},overviewBearing=340,overviewPitch=65,overviewZoom=20.6,maxDistance=400,lod_switch_in_m=610,lod_switch_out_m=745,navigation={'listed':False,'status':'从南昌路人行道查看110弄两侧的题名石柱与112号院墙。'},placement={'status':'map-aligned','note':'门两侧题名以同年街景交会定位，原临街排屋3695、东侧214和两保护范围原轮廓均保留。'})
    save(w/'final-placement-contract.json',c);save(w/'placement-geometry.json',dict(id=model_id,manifest_sha256=sha((assets/'manifest.json').read_bytes()),model_hashes=c['model_geometry_sha256'],original_geometry_cut=False,original_owner=3695,checked_neighbors=ref['checked_neighbors'],source_clips_added=0,original_to_new_clearances_m={str(k):old[k].distance(collision)for k in (3695,214)},probe_count=len(tests),ground_probes=tests,source_bounds=glb,collision_section_height_m=.29,near_far_source_same=True))
    print('ground',len(tests),collision.area,collision.bounds,c['bounds_glb'],scenes['full'].materials,flush=True)
if __name__=='__main__':main(Path(sys.argv[1]))
