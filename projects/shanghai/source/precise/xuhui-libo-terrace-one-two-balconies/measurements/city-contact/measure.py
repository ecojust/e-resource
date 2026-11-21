"""Compare the photographically located seam of Nos. 1 and 2 to both actual city meshes of the southern terrace."""
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
uid='xuhui-libo-terrace-one-two-balconies'
source=home.parent/'southern-pair-dimensions.json'
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

from scipy.spatial.transform import Rotation
survey=read(source)
addresses=read(home.parent/'eight-addresses.json')
eaves=read(home.parent/'two-eaves.json')
anchor=np.array([121.44032,31.20491])
# Keep the photographic solver's own east/north metric and calibrated 790×525 camera.
meter=np.array([111180*math.cos(math.radians(anchor[1])),111180])
p0,p1=[(np.array(a['wgs'])-anchor)*meter for a in eaves['points'][:2]]
east=(p1-p0)/np.linalg.norm(p1-p0)
inside=np.array([-east[1],east[0]])
nominal=np.array([[1,0,0],[0,0,-1],[0,1,0]])
uv=np.array(survey['points_xy']['eave_seam'])*[790/1080,525/718]
candidates={}
for i,fit in enumerate(eaves['fits']):
    sol=np.array(fit['sol']);rot=Rotation.from_rotvec(sol[:3]).as_matrix()@nominal;cam=-rot.T@sol[3:6]
    direction=rot.T@np.r_[(uv-[395.,262.5])/sol[-1],1.]
    for offset in (0.,.5,.9):
        base=p0+offset*inside
        distance=(base-cam[:2])@inside/(direction[:2]@inside)
        pos=cam[:2]+distance*direction[:2]
        assert distance>0 and -2<((pos-p0)@east)<36
        candidates[f'camera{i+1}_setback{offset}']=(pos,float(fit['fitted_focal']),offset)
auth=read(p/'data/audit/libo-terrace-one-two-balconies-v1/preflight/model-review.json')
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
    actual_near_tile=next(t for t in read(q/'macro-READY.json')['tiles'] if 3347 in t['featureLocalIds'])
    assert actual_near_tile['sha256']==cfg['baseline-near.glb.gz']['sha256']
    put(q/'initial-local-frame.json',{'anchor':{'lng':anchor[0],'lat':anchor[1]}})
    put(q/'context-features.json',[{'localId':3347}])
    for level in ('near','far'):
        for suffix in ('triangles.f64','owners.u32'):anon('baseline-'+level+'-'+suffix)
    def run(command):
        start=time.time();proc=subprocess.Popen(command,env=dict(os.environ,SHANGHAI_PROJECT=str(p),POSTAL_MAPPING_WORK=str(q),NODE_OPTIONS='--require='+str(home/'decode-texture.cjs')))
        code=proc.wait();events.append(dict(program=Path(command[1]).name,pid=proc.pid,exit=code,elapsed_seconds=round(time.time()-start,3)));assert code==0
    run(['node',home/'decode-city.mjs'])
    table=json.loads(gzip.decompress((q/'feature-table.json.gz').read_bytes()))['features']
    site=next(z for z in table if z['localId']==3347)

    polygons={}
    for row in table:
        if row['localId'] in (3347,2656,343):
            identifier=str(row['localId']);geom=row['geometry'];prior=addresses['source_footprints'][identifier]
            assert prior['geometry']==geom and abs(prior['height']-row['height'])<.0001
            poly=Polygon((np.array(geom['coordinates'][0])-anchor)*meter)
            polygons[identifier]=(row,poly)
    assert len(polygons)==3
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
        top=projected(tri)
        old=np.fromfile(q/f'baseline-{"near" if name=="near" else "far"}-triangles.f64',dtype='<f8').reshape(-1,3,3)
        # Extract only triangles that can actually intersect each sample line in X/Z.
        xs=(-3.65,-3.0,-2.31,-1.87,-1.27,-.72,-.26,0.,.31,.81,1.26,1.77,2.31,2.94,3.65)
        zs=(.20,.92,1.55,2.36,3.18,3.86,4.72,5.56,6.45,7.32,8.47,9.62,10.71,11.49,12.25,16.11)
        def projected_bounds(t):
            return (t[:,:,0].min(axis=1)-1e-7,t[:,:,0].max(axis=1)+1e-7,t[:,:,2].min(axis=1)-1e-7,t[:,:,2].max(axis=1)+1e-7)
        def probe(t,bounds,x,z):
            xmin,xmax,zmin,zmax=bounds
            mask=(xmin<=x)&(xmax>=x)&(zmin<=z)&(zmax>=z)
            return first(t[mask],[x,-12,z],[0.,1.,0.]) if np.any(mask) else None
        model_bounds=projected_bounds(tri)
        hits={(x,z):probe(tri,model_bounds,x,z)for x in xs for z in zs}
        info={}
        for label,(pos,focal,offset) in candidates.items():
            footprint=affine_transform(top,[east[0],inside[0],east[1],inside[1],*pos])
            local=old.copy();local[:,:,0]=(old[:,:,:2]-pos)@east;local[:,:,1]=(old[:,:,:2]-pos)@inside
            bounds=projected_bounds(local)
            pairs=[]
            for (x,z),newhit in hits.items():
                oldhit=probe(local,bounds,x,z)
                pairs.append(dict(x=x,z=z,original_towards_street_m=oldhit,model_towards_street_m=newhit,ahead_m=rr(newhit-oldhit)if oldhit is not None and newhit is not None else None))
            cmp=[r['ahead_m']for r in pairs if r['ahead_m']is not None]
            region={k:rr(footprint.intersection(v[1]).area)for k,v in polygons.items()}
            info[label]=dict(fitted_focal=focal,setback_m=offset,seam_wgs=(anchor+pos/meter).tolist(),projected_area_m2=rr(footprint.area),overlap_m2=region,rays=pairs,compared=len(cmp),ahead=sum(v>.025 for v in cmp),behind=sum(v<-.025 for v in cmp),coincident=sum(abs(v)<=.025 for v in cmp),covering_above=sum(r['original_towards_street_m']is not None and r['model_towards_street_m']is None and r['z']>11.75 for r in pairs),covering_beside=sum(r['original_towards_street_m']is not None and r['model_towards_street_m']is None and abs(r['x'])>3.20 for r in pairs),depth_range_m=[min(cmp),max(cmp)]if cmp else [])
        results[name]=dict(original_triangles=len(old),sample_points_per_case=len(hits),cases=info)
out=dict(order=376,id=uid,author_review_sha256=h(p/'data/audit/libo-terrace-one-two-balconies-v1/preflight/model-review.json'),existing_city_source=cfg,source_files={f:h(home.parent/f)for f in ('eight-addresses.json','two-eaves.json','southern-pair-dimensions.json','photographs-and-road-bearing.json')},address_pois=addresses['registered_eight_addresses'],two_rows=addresses['rows'],original_footprints={k:dict(height_m=v[0]['height'],area_m2=rr(v[1].area),outline=v[0]['geometry']) for k,v in polygons.items()},model=shape_rows,calibrated_road_image=survey['source'],image_sha256=survey['photo_sha256'],picked_eave_seam_px=survey['points_xy']['eave_seam'],test='Six independent focal solutions constrained by four cornice points in the courtyard view. Test each reported 0, 0.5 and 0.9 metre setback on the southern row. Street-projection distances use the native ground zero as the original city base. The previous model on 343 and the other four residences on 2656 are included in the projected-footprint comparison.',actual_near_tile_owners=actual_near_tile['featureLocalIds'],results=results,events=events)
args.output.parent.mkdir(parents=True,exist_ok=True);put(args.output,out)
for level,row in results.items():
    print(level,row['original_triangles'],len(row['cases']),row['sample_points_per_case'],min(r['overlap_m2']['3347']for r in row['cases'].values()),max(r['overlap_m2']['3347']for r in row['cases'].values()),flush=True)
