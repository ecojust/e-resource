"""Join the garden portico to the actual source footprint and test open and closed French doors."""
from pathlib import Path
from hashlib import sha256
import json, math, os, runpy, sys
import numpy as np
import shapely as g
from shapely import geometry as G
from shapely.geometry import Point,box

project=Path(os.environ.get('COZY_PROJECT',str(next(a for a in Path(__file__).resolve().parents if (a/'tools/package_architectural_model.py').is_file()))))
w=Path(os.environ.get('COZY_WORK',Path(__file__).resolve().parent)); model_id='huangpu-cozy-apartments-494-lane-portal'
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
    m,scenes=make_scenes(assets);ref=ri(w/'footprint-review.json');o=next(r for r in ref['owners']if r['local_id']==2172);owner=g.transform(G.shape(o['geometry']),loc);sec=runpy.run_path(str(project/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']
    forms={r:sec(s.tri,.8123) for r,s in scenes.items()};collision=g.union_all(list(forms.values()),grid_size=.001).buffer(.007).simplify(.0029,preserve_topology=True)
    cut=box(-1.81,-.35,1.81,4.175);facade=box(-2.70,-.35,2.41,1.18);probes=[]
    def record(title,x,y,expected):
        pt=Point(x,y);new=collision.covers(pt);cutting=cut.covers(pt);old=owner.covers(pt) and not cutting
        assert (new or old)==expected,(title,x,y,new,old)
        probes.append(dict(name=title,xy=[x,y],wgs84=wgs(np.array([[x,y]]))[0].tolist(),model_obstacle=new,source_cut=cutting,expected_map='building' if expected else None))
    for x in [-.65,-.33,0,.33,.65]:
        for y in [-1,-.31,.03,.5,.96,1.6,2.1,3.2,4.04,4.15]:record('从公共人行道經两道开启铁门进入头段',x,y,False)
        record('登记范围以后的旧楼体',x,4.31,True)
    for x in [-2.15,2.045]:
        for y in [.08,.19,.272]:record('分块石柱',x,y,True)
    for x in [-1.875,1.875]:
        for y in [.48,1,2.2,3.05,4.10]:record('门弄两侧墙',x,y,True)
    for x in [-3.45,3.2]:
        for y in [-.92,.2]:record('临街旁侧行人空间',x,y,False)
        for y in [1.65,3.5]:record('两侧保留旧楼',x,y,True)
    # The wings of the open steel leaves and jamb intrados remain physical obstacles.
    for r,s in scenes.items():
        for x in [-.70,-.33,0,.33,.70]:
            for z in [.2,.8,1.55,2.1]:
                assert s.ray([x,-.60,z],[0,1,0],4.75005) is None,(r,x,z)
    roof=ri(w/'decoded-source-bounds.json');owner_ref={'macro_id':ref['frozen_macro'],'feature_local_id':2172};ids={'building':[o['key'].split(':',1)[1]],'building_part':[]};glb=m['assets']['raw']['bounds_gltf_m'];convert=lambda geo:G.mapping(g.transform(geo,wgs))
    site=dict(id=model_id+'-passage-first-span',geometry=convert(cut),owner=owner_ref,source_feature_ids=ids,min_height=-.12,max_height=3.24,height_reference=frame['macro_origin']);display=dict(id=model_id+'-stone-and-window-wall',geometry=convert(facade),owner=owner_ref,min_height=-.12,max_height=7.19,height_reference=frame['macro_origin'])
    contract=dict(id=model_id,owner=owner_ref,source_feature_ids=ids,site_replacement=site,display_height_clips=[display],replacement_geometry=None,collision_geometry=convert(collision),lng=lon,lat=lat,heading=heading,scale=1,altitude=0,model_geometry_sha256={k:m['assets'][r]['sha256']for k,r in [('raw','raw'),('web','full'),('lod','lod')]},bounds_glb=dict(min=glb[0],max=glb[1]),overviewBearing=334,overviewPitch=64,overviewZoom=20.25,maxDistance=400,lod_switch_in_m=610,lod_switch_out_m=745,navigation=dict(listed=False,status='从淮海中路经过题额下方，查看494弄前段及上方一对长窗。'),placement=dict(status='map-aligned',note='三处公共街面角度定门轴；4C002与w494956474@2、原城2172及2022年题额照片交会。低层门洞和二层窗按各自高度裁切，16米旧屋上部与两边均保留。'),partial_model=True,model_scope=m['scope'])
    save(w/'final-placement-contract.json',contract);save(w/'placement-geometry.json',dict(id=model_id,model_manifest_sha256=sha((assets/'manifest.json').read_bytes()),source_owner=2172,near_far=roof['levels'],source_height_clip=site,facade_height_clip=display,collision_m2=collision.area,collision_sections={r:t.area for r,t in forms.items()},cap_segments=0,why_no_seam_caps='实体没有切掉整屋屋顶。作者门洞两壁、上盖和窗后短返面形成实物收边，原屋屋顶与上墙仍在。',ground_probes=probes,center_passage_ray_count=60))
    print('ground',len(probes),'physical center rays',60,'collision',collision.area,'triangles',{r:len(t.tri)for r,t in scenes.items()})
if __name__=='__main__':main(Path(sys.argv[1]))
