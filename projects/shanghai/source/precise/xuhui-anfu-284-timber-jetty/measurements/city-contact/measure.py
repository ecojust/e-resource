"""Compare three possible south arcade positions with the original south wall and courtyard."""
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
uid='xuhui-anfu-284-timber-jetty'
source=home.parent/'parcel-and-roof.json'
def read(f):return json.loads(f.read_bytes())
def h(f):return sha256(f.read_bytes()).hexdigest()
def put(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
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
outline=np.array(survey['garden_roof']['footprint']);west,east_end=outline[1],outline[0]
anchor=(west+east_end)/2
meter=np.array([6371008.8*math.cos(math.radians(anchor[1])),6371008.8])*math.pi/180
east=(east_end-west)*meter
east/=np.linalg.norm(east)
north=np.array([-east[1],east[0]])
# Three along-wall positions and three perpendicular offsets test the historic roof edge.
# Foliage in the source photography hides the actual position of the brackets on the ground.
candidates={f'{part}_{offset}':((west+fraction*(east_end-west)-anchor)*meter+north*distance)
    for part,fraction in [('west',.25),('middle',.50),('east',.75)]
    for offset,distance in [('garden',-1.10),('footprint',0.),('inward',1.10)]}
auth=read(p/'data/audit/anfu-284-timber-jetty-v1/preflight/model-review.json')
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
    actual_near_tile=next(t for t in read(q/'macro-READY.json')['tiles'] if 3868 in t['featureLocalIds'])
    assert actual_near_tile['sha256']==cfg['baseline-near.glb.gz']['sha256']
    put(q/'initial-local-frame.json',{'anchor':{'lng':anchor[0],'lat':anchor[1]}})
    put(q/'context-features.json',[{'localId':3868}])
    for level in ('near','far'):
        for suffix in ('triangles.f64','owners.u32'):anon('baseline-'+level+'-'+suffix)
    def run(command):
        start=time.time();proc=subprocess.Popen(command,env=dict(os.environ,SHANGHAI_PROJECT=str(p),POSTAL_MAPPING_WORK=str(q),NODE_OPTIONS='--require='+str(home/'decode-texture.cjs')))
        code=proc.wait();events.append(dict(program=Path(command[1]).name,pid=proc.pid,exit=code,elapsed_seconds=round(time.time()-start,3)));assert code==0
    run(['node',home/'decode-city.mjs'])
    table=json.loads(gzip.decompress((q/'feature-table.json.gz').read_bytes()))['features']
    site=next(z for z in table if z['localId']==3868)
    shell=Polygon((np.array(site['geometry']['coordinates'][0])-anchor)*meter)
    osm={'outline':survey['garden_roof']['footprint']}
    footprint=Polygon((np.array(osm['outline'])-anchor)*meter)
    matches=[]
    for row in sorted(table,key=lambda v:v['localId']!=3868):
        outline=shape(row['geometry'])
        if not outline.intersects(Polygon(osm['outline'])):continue
        geometry=affine_transform(outline,[meter[0],0,0,meter[1],-anchor[0]*meter[0],-anchor[1]*meter[1]])
        if geometry.is_valid and geometry.intersects(footprint):
            matches.append({'city_owner':row['localId'],'iou':rr(geometry.intersection(footprint).area/geometry.union(footprint).area)})
    assert matches[0]['city_owner']==3868 and matches[0]['iou']>.97
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
        for label,ct in candidates.items():
            from shapely.affinity import affine_transform
            piece=affine_transform(top,[east[0],north[0],east[1],north[1],ct[0],ct[1]])
            rows=[]
            for x in (-4.,-2.1,-1.20,-.75,-.05,.55,1.13,1.92,2.61,3.25,4.8):
                for z in (.31,1.52,2.72,3.43,4.61,5.85,6.57,7.79,8.94,9.73,10.46,12.5,19.15,27.8):
                    orig=ct+east*x-north*12
                    oldhit=first(old,[*orig,z],[*north,0]);newhit=first(tri,[x,-12,z],[0,1,0])
                    rows.append(dict(x=x,z=z,old_surface_m=oldhit,model_surface_m=newhit,projection_ahead_m=rr(newhit-oldhit)if oldhit is not None and newhit is not None else None))
            both=[z['projection_ahead_m']for z in rows if z['projection_ahead_m']is not None]
            info[label]=dict(map_point_wgs84=(anchor+ct/meter).tolist(),projected_area_m2=rr(piece.area),inside_old_footprint_m2=rr(piece.intersection(shell).area),outside_old_footprint_m2=rr(piece.difference(shell).area),rays=rows,
              comparable=len(both),detail_ahead=sum(a>.025 for a in both),detail_behind=sum(a<-.025 for a in both),extrema_m=[min(both),max(both)]if both else [],
              old_extending_above_detail=sum(z['old_surface_m']is not None and z['model_surface_m']is None and z['z']>10.65 for z in rows),
              old_at_unmodeled_sides=sum(z['old_surface_m']is not None and z['model_surface_m']is None and (z['x'] < -1.34 or z['x'] > 3.37) and z['z']<10.64 for z in rows))
        results[name]=dict(input_old_triangles=len(old),placements=info)
out=dict(order=368,id=uid,parcel_survey_sha256=h(source),historic_parcel=survey['historic_parcel'],garden_photograph=survey['current_elevated_garden_view'],registered_osm=1204087454,city_owner=3868,actual_near_tile_owners=actual_near_tile['featureLocalIds'],scope_of_old_meshes={'near':'All original triangles within 16 metres of the garden edge in its near tile.','far':'The actual feature-ID triangles for original building 3868.'},footprint_intersections=matches,source_footprint=site['geometry'],old_height_m=site['height'],old_area_m2=rr(shell.area),model_measurements=shape_rows,reference_test={'edge_endpoints':[west.tolist(),east_end.tolist()],'positions':{k:(anchor+ct/meter).tolist()for k,ct in candidates.items()},'assumption':'The southern edge of the OSM garden house is compatible with the two gables in archival and garden views. Nine trial origins cover its central length and either side of the visible footprint. Foliage hides the exact ground projection of the brackets.'},results=results,processes=events)
args.output.parent.mkdir(parents=True,exist_ok=True)
put(args.output,out)
for name,row in results.items():
 print(name,row['input_old_triangles'],[(k,v['inside_old_footprint_m2'],v['comparable']) for k,v in row['placements'].items()])
