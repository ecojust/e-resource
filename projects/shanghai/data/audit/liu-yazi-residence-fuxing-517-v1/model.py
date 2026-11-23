"""Evaluate the exported Wutopia Lab villa exterior against the ordinary city collision polygons."""
import os as _author_os
from pathlib import Path as _AuthorPath
_author_project = next(p for p in _AuthorPath(__file__).resolve().parents if p.name == 'shanghai')
_author_data = _AuthorPath(_author_os.environ.get('LIUYAZI_EVIDENCE_ROOT', _author_project / 'data' / 'surveys'))
from pathlib import Path
from hashlib import sha256
import json, math, os, runpy, sys
import numpy as np
import shapely as g
from shapely import geometry as G
from shapely.geometry import Point,box

project=Path(os.environ.get('LIUYAZI_PROJECT',str(_author_project)))
w=Path(os.environ.get('LIUYAZI_WORK',Path(__file__).resolve().parent)); model_id='huangpu-liu-yazi-residence-fuxing-517'
ri=lambda f:json.loads(f.read_bytes());sha=lambda b:sha256(b).hexdigest()
def save(file,value):
    data=(json.dumps(value,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n').encode()
    if file.is_file() and file.read_bytes()==data:return
    temporary=file.with_suffix(file.suffix+'.staged')
    temporary.write_bytes(data);os.replace(temporary,file)
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


WIDTH=8.854035
DEPTH=5.451995
GALLERY=3.48
GARDEN_FACE=-7.13
GARDEN_BACK=-3.42
EAST_Y=4.19

def entrance_geometry():
    """Open walking surfaces in the digital street scene, including the low garden rails."""
    # The floor plan terminates at the glazing of the sheltered porch and the top of the entrance flight.
    interior=box(-WIDTH,-DEPTH,WIDTH,DEPTH).difference(box(-GALLERY-.007,-DEPTH-.1,GALLERY+.007,GARDEN_BACK))
    passage=box(5.551,EAST_Y-.566,WIDTH+.35,EAST_Y+.566)
    blocks=[interior.difference(passage)]
    # Wall returns beside the porch, including the closed study-wall side under the garden stair.
    blocks.extend([box(-3.59,-7.145,-3.37,-3.42),box(3.37,-5.49,3.59,-3.42),
                   box(3.37,-7.13,3.59,-6.92),box(3.37,-5.65,3.59,-5.41)])
    for a,b in [(-3.48,-3.21),(-.34,.34),(3.21,3.48)]:
        blocks.append(box(a,GARDEN_FACE,b,GARDEN_FACE+.27))
    for a,b in [(-3.20,-.34),(.34,3.20)]:
        blocks.append(box(a,GARDEN_FACE-.170,b,GARDEN_FACE-.128))
    # The game map uses planar collisions. Treads stay open; the curved cheek and the garden stair's iron rail remain solid.
    blocks.append(box(-8.45,-7.14+.062,-3.51,-7.14+.122))
    from shapely.geometry import Polygon
    def arc(r0,r1):
        a=np.linspace(0,-math.pi/2,33)
        return Polygon([(WIDTH+r*math.cos(t),5.18+r*math.sin(t))for r,seq in [(r0,a),(r1,reversed(a))]for t in seq])
    blocks.append(arc(1.790,2.030))
    return g.union_all(blocks,grid_size=.001).simplify(.003,preserve_topology=True)

def samples():
    checks=[]
    def add(label,x,y,blocked):checks.append((label,x,y,blocked))
    for x in [-2.4,-1.45,1.17,2.5]:
        for y in [-7.55,-7.28,-6.68,-5.87,-4.32,-3.55,-3.16]:
            add('南面花廊正面铁栏、廊内空腔及后墙',x,y,y==-7.28 or y==-3.16)
    for x in [-3.39,0,3.395]:
        add('花廊前墙与中央实墩',x,-7.038,True)
    for x in [3.45,3.6,3.93]:
        add('花廊东返墙的实拍侧开口',x,-6.23,False)
    add('南院花廊西侧书房侧墙',-3.47,-6.24,True)
    add('西侧室外梯临园铁栏',-6.1,-7.05,True)
    for x in [-8.3,-7.4,-6.4,-5.5,-4.3,-3.71]:
        add('南花园西侧室外梯踏面',x,-6.40,False)
    for y in [6.23,6.04,5.78,5.53,5.29]:
        for x in [WIDTH+.30,WIDTH+.94,WIDTH+1.53]:
            add('东门街口及坡脚石台',x,y,False)
    for i in range(7):
        a=-(i+.5)*math.pi/14
        for r in [.42,1.05,1.64,1.93,2.14]:
            add('东侧弧形石阶与外侧弧墙',WIDTH+r*math.cos(a),5.18+r*math.sin(a),r==1.93)
    for dy in [-.38,0,.38]:
        for x in [9.02,8.71,8.02,7.55,6.31,5.71,5.39]:
            add('砖券甬道的踏面、门框与尽端',x,EAST_Y+dy,x==5.39)
    for x,y in [(0,0),(-7.8,-5.21),(8.58,3.44),(8.57,4.95),(-8.62,4.89),(0,5.13)]:
        add('主楼外壳与封闭部分',x,y,True)
    for x,y in [(0,6.1),(-9.25,2),(-6.4,-7.73),(2.6,-8.08),(11.4,4.74)]:
        add('既有庭院地面',x,y,False)
    return checks

def measure_surfaces(scene):
    rows=[]
    def ray(label,origin,direction,length,axis,expected,tolerance):
        a=scene.ray(origin,direction,length)
        assert a and abs(a['point_enu_m'][axis]-expected)<=tolerance,(label,origin,a,expected)
        rows.append(dict(measurement=label,from_local=origin,direction=direction,expected=expected,axis=axis,tolerance=tolerance,result=a))
    def empty(label,origin,direction,length):
        result=scene.ray(origin,direction,length);assert result is None,(label,origin,result)
        rows.append(dict(measurement=label,from_local=origin,direction=direction,tested_length=length,result=None))
    # The low rail is geometrically real. Verify that the apparent opening exists above it, and glass closes the end of the recess.
    for x in (-2.21,-1.78,1.86,2.1):
        for z in [1.15,1.65,2.23]:
            empty('南花廊正孔上部与后退面之间', [x,-7.52,z],[0,1,0],3.78)
        ray('花廊前铁栏上道',[x,-7.58,.965],[0,1,0],.75,1,-7.28,.04)
        ray('带玻璃的退进后墙',[x,-3.71,1.63],[0,1,0],.68,1,-3.42,.24)
    # Trace onto the interior of the individual stone slabs from below the roofs.
    # Their joints have different spacing in the full model and in the distant model.
    for x in (-2.65,-1.78,1.83,2.63):
        for y in (-6.81,-5.56,-4.31):
            ray('南花廊铺地石板',[x,y,.34],[0,0,-1],.47,2,.065,.004)
            assert rows[-1]['result']['material'] in ('Light grey cast stone','Weathered cement sill'),rows[-1]
    for y in (-6.73,-6.21,-5.91):
        empty('东侧廊口', [3.81,y,1.42],[-1,0,0],1.03)
    # Floor elevations are measured locally. Overhead roofs do not intercept the downward sample.
    for y,z in [(5.99,.068),(5.52,.155),(5.30,.310)]:
        ray('东入口台基与直踏步',[WIDTH+.9,y,.75],[0,0,-1],.85,2,z,.022)
    for i in range(7):
        a=-(i+.5)*math.pi/14;z=.31+(1.41-.31)*(i+1)/7
        for rad in [.63,1.48]:
            ray('东门弧阶踏面',[WIDTH+rad*math.cos(a),5.18+rad*math.sin(a),z+.37],[0,0,-1],.66,2,z,.025)
        ray('弧墙压顶',[WIDTH+1.92*math.cos(a),5.18+1.92*math.sin(a),z+1.24],[0,0,-1],.65,2,.31+(1.41-.31)*(i+.5)/7+.98,.045)
    for i in range(10):
        x=WIDTH-.13-i*.258;z=1.41+1.6*(i+1)/10
        ray('东券内石踏步',[x,EAST_Y,z+.34],[0,0,-1],.55,2,z,.025)
    ray('券内平台',[5.84,EAST_Y,3.64],[0,0,-1],1.00,2,3.01,.03)
    for y in [3.88,4.19,4.49]:
        empty('券内上段净空',[8.93,y,4.39],[-1,0,0],3.28)
        ray('台阶尽头实门',[5.73,y,4.39],[-1,0,0],.57,0,WIDTH-3.31,.095)
    for i in [0,4,8,12,16]:
        x=-8.51+(i+.5)*(8.51-GALLERY)/17;z=3.01*(i+1)/17
        ray('南侧室外直梯',[x,-6.26,z+.36],[0,0,-1],.61,2,z,.026)
    return rows

def main(assets):
    manifest,scenes=make_scenes(assets)
    ref=ri(w/'footprint-review.json');old=ri(w/'source-owner-selection.json');vector=ri(w/'vector-scope.json')
    cut=G.shape(old['proposed_cut_local']);owner=ref['selection']['owner']
    polygons={v['local_id']:g.transform(G.shape(v['geometry']),loc)for v in ref['owners']}
    collision=entrance_geometry()
    assert collision.is_valid and all(collision.disjoint(polygons[i]) for i in ref['checked_neighbors'])
    probes=[]
    for label,x,y,expected in samples():
        pt=Point(x,y);blocked=collision.covers(pt)
        assert blocked==expected,(label,x,y,expected,blocked)
        probes.append(dict(name=label,xy=[x,y],wgs84=wgs(np.array([[x,y]]))[0].tolist(),expected_map='building' if blocked else None,source_cut=cut.covers(pt),model_obstacle=blocked))
    raychecks={role:measure_surfaces(scene) for role,scene in scenes.items()}
    b=manifest['assets']['raw']['bounds_gltf_m']
    contract=dict(id=model_id,owner=dict(macro_id=ref['frozen_macro'],feature_local_id=owner),
                  lng=lon,lat=lat,heading=heading,altitude=0,scale=1,overviewBearing=305,overviewPitch=32,overviewZoom=19.6,maxDistance=425,lod_switch_in_m=610,lod_switch_out_m=745,
                  model_geometry_sha256={key:manifest['assets'][role]['sha256']for key,role in [('raw','raw'),('web','full'),('lod','lod')]},
                  source_feature_ids=dict(building=[vector['selected_source_id']],building_part=[]),
                  osm_replacement_geometry=vector['selected_ground_wgs'],replacement_geometry=old['proposed_cut_wgs84'],
                  collision_geometry=G.mapping(g.transform(collision,wgs)),bounds_glb=dict(min=b[0],max=b[1]),
                  placement=dict(status='map-aligned',note='2018年修缮总图与南北立面、两张剖面定位复兴中路517号主楼。按完整新外壳替换原模型2849，保留周边庭院与相邻楼栋。'),
                  navigation=dict(listed=False,status='从花园侧查看玻璃花廊、交叉屋脊和东侧砖券。'),model_scope=manifest['scope'],partial_model=False)
    sys.path.insert(0,str(project/'tools'));from build_candidate_city_integrations import checked_geometry
    checked_geometry(contract['replacement_geometry'],'Villa 517 owner clip');checked_geometry(contract['collision_geometry'],'Villa 517 ground',collision=True)
    heights={role:float(s.tri[:,:,2].max()) for role,s in scenes.items()}
    assert all(15.9<v<17.1 for v in heights.values())
    save(w/'final-placement-contract.json',contract)
    save(w/'placement-geometry.json',dict(id=model_id,model_manifest_sha256=sha((assets/'manifest.json').read_bytes()),source_owner=owner,source_height_m=old['source_height_m'],model_height_m=heights,
         source_tiers_and_neighbors=old['actual_owner_meshes_and_neighbors'],collision_m2=collision.area,ground_probes=probes,
         additional_neighbor_ids=ref['checked_neighbors'],cap_segments=0,cut_boundary='核实原2849完整体积位于影像重建的新范围内；裁去全部旧三角后无跨接原楼的截断边线。',surface_rays_by_variant=raychecks))
    save(w/'model-assets.json',dict(id=model_id,assets={k:{'bytes':v['bytes'],'sha256':v['sha256'],'file':v['file']} for k,v in manifest['assets'].items() if k in ('raw','full','lod')}))
    print('ground',len(probes),len(ref['checked_neighbors']),'triangle probes', {role:len(rows)for role,rows in raychecks.items()},'actual heights',heights)

if __name__=='__main__':main(Path(sys.argv[1]))
