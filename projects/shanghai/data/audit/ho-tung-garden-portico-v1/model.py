"""Join the garden portico to the actual source footprint and test open and closed French doors."""
from pathlib import Path
from hashlib import sha256
import json, math, os, runpy, sys
import numpy as np
import shapely as g
from shapely import geometry as G
from shapely.geometry import Point,box

project=Path(os.environ.get('HOTUNG_PROJECT',Path(__file__).resolve().parents[3]))
w=Path(os.environ.get('HOTUNG_WORK',Path(__file__).resolve().parent)); model_id='jingan-ho-tung-residence-garden-portico'
ri=lambda f:json.loads(f.read_bytes());sha=lambda b:sha256(b).hexdigest()
def save(file,value):
    file.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
frame=ri(w/'garden-face.json');lon,lat=frame['anchor'];heading=frame['runtime_heading_degrees'];h=math.radians(heading)
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
    m,scenes=make_scenes(assets);review=project/'source/precise'/model_id/'footprint-review.json';bind=ri(review)
    ref=next(v for v in bind['owners'] if v['local_id']==1292);owner=g.transform(G.shape(ref['geometry']),loc)
    cutinfo=ri(w/'proposed-source-cut.json');cut=G.shape(cutinfo['cut_local']);ids=frame['checked_neighbors']
    section=runpy.run_path(str(project/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']
    forms={role:section(s.tri,.614) for role,s in scenes.items()}
    # Exclude the unrecorded interior of the house. The middle threshold remains open through the whole photographed first door swing.
    interior=cut.intersection(owner).intersection(box(-8,3.90,8,10)).difference(box(-.61,3.85,.61,4.60))
    collide=g.union_all([interior,*forms.values()],grid_size=.001).buffer(.007).simplify(.003,preserve_topology=True)
    assert collide.is_valid
    probes=[];raychecks={}
    def check(name,x,y,solid):
        point=Point(x,y);hit=collide.covers(point);outside_source=not cut.covers(point) and owner.covers(point)
        assert (hit or outside_source)==solid,(name,x,y,hit,outside_source,solid)
        probes.append(dict(name=name,xy=[x,y],wgs84=wgs(np.array([[x,y]]))[0].tolist(),model_obstacle=hit,source_cut=cut.covers(point),expected_map='building' if solid else None))
    for x in (-.34,0,.34):
        for y in (-1.05,-.71,-.38,.30,1.6,2.6,3.55,3.79,4.05,4.25,4.50):check('花园经过弧阶、敞廊和中央门洞',x,y,False)
        check('中央开口内的保留原楼',x,4.72,True)
    for x in (-4.37444,-1.45815,1.45815,4.37444):
        for dx in (-.17,0,.17):check('爱奥尼柱柱基',x+dx,.30,True)
    for x in (-2.81344,2.81344):
        for dx in (-.40,.21):
            check('两侧券门前廊',x+dx,3.50,False);check('闭合侧扇后方',x+dx,4.03,True)
        check('侧门旁石墙',x+.82,3.96,True)
    for side in (-1,1):
        halfwidth=.586;hinge=side*.594
        xx=hinge-side*halfwidth*.5*math.cos(math.radians(70));yy=3.8636327+halfwidth*.5*math.sin(math.radians(70))
        check('向内开的实体门扇中央',xx,yy,True)
        check('门廊转角短返墙',side*5.01,2.48,True);check('未切原露肩侧翼',side*5.74,3.0,True)
    check('后方保留原屋',0,10,True)
    for role,scene in scenes.items():
        eye_data=[]
        for x in [-.34,0,.34]:
            for z in [.32,.79,1.35,1.89,2.13]:
                hit=scene.ray([x,3.35,z],[0,1,0],1.15)
                assert hit is None,(role,x,z,hit);eye_data.append(dict(x=x,z=z,start=3.35,end=4.50,hit=hit))
        for x in [-2.81344,2.81344]:
            for offset in [-.39,.18,.37]:
                a=scene.ray([x+offset,3.35,1.38],[0,1,0],1.15);assert a and 3.80<a['point_enu_m'][1]<3.93,(role,x,offset,a)
                eye_data.append(dict(x=x+offset,z=1.38,hit=a))
        raychecks[role]=eye_data
    glb=m['assets']['raw']['bounds_gltf_m'];far=next(q for q in bind['frozen_bindings'] if q['repository_path'].endswith('/far.glb'))
    caps=dict(geometry=G.mapping(g.transform(G.MultiLineString(cutinfo['geometry']['far']['seams']),wgs)),base_m=0,roof_m=cutinfo['geometry']['far']['height'],height_reference=frame['macro_origin'],far_sha256=far['sha256'])
    contract=dict(id=m['id'],owner=dict(macro_id=bind['frozen_macro'],feature_local_id=1292),source_feature_ids=dict(building=[ref['key'][9:]],building_part=[]),replacement_geometry=cutinfo['cut_wgs'],collision_geometry=G.mapping(g.transform(collide,wgs)),source_section_caps=caps,lng=lon,lat=lat,heading=heading,scale=1,altitude=0,model_geometry_sha256={k:m['assets'][r]['sha256']for k,r in [('raw','raw'),('web','full'),('lod','lod')]},bounds_glb=dict(min=glb[0],max=glb[1]),overviewBearing=335,overviewPitch=46,overviewZoom=20.00,maxDistance=400,lod_switch_in_m=610,lod_switch_out_m=745,navigation=dict(listed=False,status='从南偏东的花园看向四根石柱、内凹的铁栏阳台和三扇券门。'),placement=dict(status='map-aligned',note='与市表4B025、OSM 490280319及原城1292的花园侧立面相接。花园向154.30°，环绕门廊的原城两翼和后楼保留。'),partial_model=True,model_scope=m['scope'])
    sys.path.insert(0,str(project/'tools'));from build_candidate_city_integrations import checked_geometry
    checked_geometry(contract['collision_geometry'],'Ho Tung garden portico collision',collision=True);checked_geometry(contract['replacement_geometry'],'Ho Tung garden portico replacement')
    save(w/'final-placement-contract.json',contract);save(w/'placement-geometry.json',dict(id=m['id'],manifest_sha256=sha((assets/'manifest.json').read_bytes()),source_sha256=sha(review.read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),source_variants=cutinfo['geometry'],cap_segments=len(cutinfo['geometry']['far']['seams']),neighbors=cutinfo['other_owners'],assets={v:dict(triangles=len(s.tri),shape_area_m2=forms[v].area,asset_sha256=m['assets'][v]['sha256'],decoded_sha256=s.asset['sha256'])for v,s in scenes.items()},collision_m2=collide.area,collision_height_m=.614,ground_probes=probes,door_surface_rays_by_variant=raychecks))
    print(len(probes),'points;',sum(map(len,raychecks.values())),'rays;',round(collide.area,4),'m² collision')
if __name__=='__main__':main(Path(sys.argv[1]))
