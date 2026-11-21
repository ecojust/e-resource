"""Test plausible locations of the photographed No. 3 porch against the unchanged garden mansion."""
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import ExitStack
from hashlib import sha256
from urllib.request import Request,urlopen
import argparse,gzip,json,math,os,runpy,subprocess,time
import numpy as np
from shapely.geometry import Polygon,Point,shape
from shapely.affinity import affine_transform
from shapely.ops import unary_union

parser=argparse.ArgumentParser(__doc__)
parser.add_argument('--project',type=Path,default=Path('.'))
parser.add_argument('--source-cache',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
home=Path(__file__).resolve().parent
p=args.project.resolve()
uid='xuhui-dingxiang-three-numbered-porch'
source=home.parent/'building-identity.json'
def read(f):return json.loads(f.read_bytes())
def h(f):return sha256(f.read_bytes()).hexdigest()
def put(f,d):f.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
def rr(v):return round(float(v),5)
def first(tri,o,d):
    origin,direction=np.array(o),np.array(d);e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
    cr=np.cross(direction,e2);det=(e1*cr).sum(axis=1);valid=np.abs(det)>1e-10
    inv=np.divide(1.,det,out=np.zeros_like(det),where=valid);delta=origin-tri[:,0];u=(delta*cr).sum(axis=1)*inv
    cross=np.cross(delta,e1);v=(cross*direction).sum(axis=1)*inv
    dist=(cross*e2).sum(axis=1)*inv;ok=valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1.0000001)&(dist>=0)&(dist<=32)
    return rr(12-dist[ok].min()) if ok.any() else None
def projected(tri):
    good=[Polygon(t[:,:2])for t in tri if abs(np.cross((t[1]-t[0]),(t[2]-t[0]))[2])>1e-8]
    return unary_union(good)
survey=read(source)
osm_record=read(home/'osm-building.json')
matching=next(v for v in osm_record['matches'] if v[1]=='1202309544')
outline=np.array(matching[3]);anchor=np.mean(outline[:-1],axis=0)
meter=np.array([6371008.8*math.cos(math.radians(anchor[1])),6371008.8])*math.pi/180
# Counterclockwise OSM coordinates give an inward normal to the left of each facade.
# The calibrated photographs resolve the stair and rail, but the courtyard trees hide
# their ends in the orthophotos. Test all four long faces, with physical inward offsets.
assert Polygon(outline).exterior.is_ccw
candidates={};edges={}
for i,(a,b) in enumerate(zip(outline,outline[1:])):
    ax=(b-a)*meter;length=np.linalg.norm(ax)
    if length<8:continue
    ax=ax/length;inward=np.array([-ax[1],ax[0]])
    edges[str(i)]={'endpoints':[a.tolist(),b.tolist()],'length_m':rr(length)}
    for fraction in (.32,.68):
        for offset in (-1.65,0.,1.65):
            pos=(a+fraction*(b-a)-anchor)*meter+offset*inward
            candidates[f'edge{i}_fraction{fraction}_offset{offset}']=(pos,ax,inward)
auth=read(p/'data/audit/dingxiang-three-numbered-porch-v1/preflight/model-review.json')
cfg=read(home/'signed-files.json');events=[]
with TemporaryDirectory()as work,ExitStack()as stack:
    q=Path(work)
    # Anonymous output prevents large transient decoded triangles being written to the project volume.
    def anon(n):
        path=q/n
        if hasattr(os,'memfd_create'):
            fd=os.memfd_create(n);stack.callback(os.close,fd);path.symlink_to('/proc/'+str(os.getpid())+'/fd/'+str(fd))
        return path
    for n,meta in cfg.items():
        items=[p/meta['path']]
        if args.source_cache:items.insert(0,args.source_cache/n)
        local=next((f for f in items if f.is_file() and h(f)==meta['sha256']),None)
        if local:(q/n).symlink_to(local.resolve())
        else:
            f=anon(n)
            with urlopen(Request(meta['url'],headers={'Accept-Encoding':'identity'}),timeout=60)as response:f.write_bytes(response.read())
            assert h(f)==meta['sha256'],n
    actual_near_tile=next(t for t in read(q/'macro-READY.json')['tiles'] if 1561 in t['featureLocalIds'])
    assert actual_near_tile['sha256']==cfg['baseline-near.glb.gz']['sha256']
    put(q/'initial-local-frame.json',{'anchor':{'lng':anchor[0],'lat':anchor[1]}})
    put(q/'context-features.json',[{'localId':1561}])
    for level in ('near','far'):
        for suffix in ('triangles.f64','owners.u32'):anon('baseline-'+level+'-'+suffix)
    def run(command):
        start=time.time();proc=subprocess.Popen(command,env=dict(os.environ,SHANGHAI_PROJECT=str(p),POSTAL_MAPPING_WORK=str(q),NODE_OPTIONS='--require='+str(home/'decode-texture.cjs')))
        code=proc.wait();events.append(dict(program=Path(command[1]).name,pid=proc.pid,exit=code,elapsed_seconds=round(time.time()-start,3)));assert code==0
    run(['node',home/'decode-city.mjs'])
    table=json.loads(gzip.decompress((q/'feature-table.json.gz').read_bytes()))['features']
    site=next(z for z in table if z['localId']==1561)
    shell=Polygon((np.array(site['geometry']['coordinates'][0])-anchor)*meter)
    osm={'outline':matching[3]}
    footprint=Polygon((np.array(osm['outline'])-anchor)*meter)
    matches=[]
    for row in sorted(table,key=lambda v:v['localId']!=1561):
        outline=shape(row['geometry'])
        if not outline.intersects(Polygon(osm['outline'])):continue
        geometry=affine_transform(outline,[meter[0],0,0,meter[1],-anchor[0]*meter[0],-anchor[1]*meter[1]])
        if geometry.is_valid and geometry.intersects(footprint):
            matches.append({'city_owner':row['localId'],'iou':rr(geometry.intersection(footprint).area/geometry.union(footprint).area)})
    assert matches[0]['city_owner']==1561 and matches[0]['iou']>.97
    loader=runpy.run_path(str(home/'glb_triangles.py'))['load_triangles']
    results={};shape_rows={}
    for name,asset in [('raw','raw'),('near','web'),('far','lod')]:
        f=q/(uid+'-'+asset+'.glb')
        if name!='raw':
            decoded=anon('decoded-'+name+'.glb');run(['node',home/'decode-meshopt.mjs',f,decoded,p/'vendor/meshopt_decoder.module.js']);f=decoded
        tri=loader(f)[0];expected=auth['assets'][{'raw':'raw','near':'full','far':'lod'}[name]]
        assert tri.shape==(expected['triangles'],3,3)
        v=tri.reshape(-1,3);shape_rows[name]=dict(triangles=len(tri),minimum=[rr(qv) for qv in v.min(axis=0)],maximum=[rr(qv)for qv in v.max(axis=0)])
        if name=='raw':continue
        old=np.fromfile(q/('baseline-'+name+'-triangles.f64'),dtype='float64').reshape(-1,3,3)
        info={}
        # Project the actual mesh, including both sashes, the timber jetty and its roof.
        top=projected(tri)
        for label,(ct,east,north) in candidates.items():
            from shapely.affinity import affine_transform
            piece=affine_transform(top,[east[0],north[0],east[1],north[1],ct[0],ct[1]])
            rows=[]
            for x in (-4.,-2.38,-1.77,-.92,0.,.89,1.52,2.33,4.):
                for z in (.15,.39,.68,.95,1.41,2.1,2.8,3.6,4.38,4.88,5.7,12.5,19.15):
                    orig=ct+east*x-north*12
                    oldhit=first(old,[*orig,z],[*north,0]);newhit=first(tri,[x,-12,z],[0,1,0])
                    rows.append(dict(x=x,z=z,old_surface_m=oldhit,model_surface_m=newhit,projection_ahead_m=rr(newhit-oldhit)if oldhit is not None and newhit is not None else None))
            both=[z['projection_ahead_m']for z in rows if z['projection_ahead_m']is not None]
            info[label]=dict(map_point_wgs84=(anchor+ct/meter).tolist(),projected_area_m2=rr(piece.area),inside_old_footprint_m2=rr(piece.intersection(shell).area),outside_old_footprint_m2=rr(piece.difference(shell).area),rays=rows,
              comparable=len(both),detail_ahead=sum(a>.025 for a in both),detail_behind=sum(a<-.025 for a in both),extrema_m=[min(both),max(both)]if both else [],
              old_extending_above_detail=sum(z['old_surface_m']is not None and z['model_surface_m']is None and z['z']>5.03 for z in rows),
              old_at_unmodeled_sides=sum(z['old_surface_m']is not None and z['model_surface_m']is None and abs(z['x'])>2.87 and z['z']<5.03 for z in rows))
        results[name]=dict(input_old_triangles=len(old),placements=info)
other=next(z for z in table if z['localId']==survey['no1_local_id'])
other_polygon=affine_transform(shape(other['geometry']),[meter[0],0,0,meter[1],-anchor[0]*meter[0],-anchor[1]*meter[1]])
out=dict(order=372,id=uid,source_sha256=h(source),osm_building_sha256=h(home/'osm-building.json'),register=survey['registration'],photographs=survey['gate_number_witnesses'],restaurant=survey['restaurant_witness'],registered_osm=1202309544,city_owner=1561,
  no1_existing_owner=survey['no1_local_id'],no1_distance_m=rr(shell.distance(other_polygon)),actual_near_tile_owners=actual_near_tile['featureLocalIds'],
  scope_of_old_meshes={'near':'All mesh triangles within sixteen metres in each horizontal axis of the measured local centroid.','far':'All far triangles tagged with original 1561.'},
  footprint_intersections=matches,source_footprint=site['geometry'],old_height_m=site['height'],old_area_m2=rr(shell.area),model_measurements=shape_rows,
  reference_test={'edge_endpoints':edges,'positions':{k:(anchor+v[0]/meter).tolist() for k,v in candidates.items()},'assumption':'The two photographs independently identify the No. 3 porch. Neither records ground control linking the posts to the aerial outline. Four distinct outward facade normals, two peripheral positions and three perpendicular offsets are compared. Values are sensitivity trials rather than a placement.'},results=results,processes=events)
args.output.parent.mkdir(parents=True,exist_ok=True)
put(args.output,out)
for name,row in results.items():
    widths=[q['inside_old_footprint_m2'] for q in row['placements'].values()]
    print(name,row['input_old_triangles'],len(widths),min(widths),max(widths),flush=True)
