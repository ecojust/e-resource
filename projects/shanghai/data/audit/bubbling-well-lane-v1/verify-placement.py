"""Bind an independently modelled through-gate to a real gap in both providers and both city GLB levels."""
import argparse,gzip,hashlib,json,math,os,runpy,subprocess,sys
from pathlib import Path
import numpy as np,shapely as geo
from shapely.geometry import Point,LineString,Polygon,box,shape,mapping
from shapely.ops import polygonize,unary_union
import mapbox_vector_tile

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2];sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
ID='jingan-bubbling-well-lane-gate';FALLBACK='1fdad607f7b21b88e0ad7de7768cd646aba6c88aca481544ba3409575d5e2bb2'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py';SerialScene=runpy.run_path(str(READER))['SerialScene'];UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def section(tri,height):
    selected=tri[(tri[:,:,2].min(1)<height)&(tri[:,:,2].max(1)>height)]
    lines=[]
    for face in selected:
        pts=[]
        for a,b in zip(face,face[[1,2,0]]):
            if (a[2]<height)!=(b[2]<height):pts.append(a[:2]+(b[:2]-a[:2])*(height-a[2])/(b[2]-a[2]))
        if len(pts)==2 and np.linalg.norm(pts[0]-pts[1])>.0002:lines.append(LineString(np.round(pts,4)))
    return unary_union(list(polygonize(unary_union(lines)))).simplify(.021,preserve_topology=True)


def check_model(manifest,work,site):
    m=read(manifest);variants={};ground=[];bounds=[];assets={}
    for role in ['raw','full','lod']:
        a=m['assets'][role];source=manifest.parent/a['file'];assert sha(source)==a['sha256'];file=source
        if role!='raw':
            file=work/(role+'.glb');subprocess.run(['node',UNPACK,source,file,PROJECT/'vendor/meshopt_decoder.module.js'],check=True,stdout=subprocess.DEVNULL)
        scene=SerialScene(file);tri=scene.tri;bounds.append(np.array(a['bounds_gltf_m']));assets['web'if role=='full'else role]={'sha256':a['sha256'],'bytes':a['bytes'],'triangles':len(tri)}
        tests=[]
        def witness(name,o,v,maxdist,mat=None,distance=None):
            hit=scene.ray(o,v,maxdist);ok=hit is None if mat is None else hit is not None and hit['material']==mat and abs(hit['distance_m']-distance)<.055
            tests.append(dict(name=name,origin=o,direction=v,limit_m=maxdist,expected_material=mat,expected_m=distance,hit=hit,passed=ok))
        for x in [-1.03,0,1.03]:
            for z in [.39,1.38,1.88,2.72,3.65]:witness('visible clear passage from street to courtyard',[x,-1.2,z],[0,1,0],9.5)
        for y in [.8,3.35,6.8]:witness('centre overhead clearance',[0,y,.01],[0,0,1],9,'passage plaster',4.102)
        for sign in [-1,1]:
            witness('inner arcade column',[sign*1.99,-2.0,1.6],[0,1,0],8,'sandstone',1.662)
            witness('occupied side room',[0,3.55,1.6],[sign,0,0],6,'passage plaster',1.922)
            witness('side alcove shop glass',[sign*2.92+.22,-1.8,1.64],[0,1,0],7,'glazing',2.685)
        witness('middle bay glass',[-.90,-2.0,7.32],[0,1,0],8,'glazing',2.26)
        witness('upper arch glazing',[-.61,-2.0,10.56],[0,1,0],8,'glazing',2.26)
        # Same three pedestrian-body slices expose doorways rather than treating the roof projection as a solid block.
        slices=[section(tri,h) for h in [.13,.98,1.70]];foot=unary_union(slices).simplify(.025,preserve_topology=True);ground.append(foot)
        for pt,expected in [((0,3),False),((-3.0,3.4),True),((3.0,3.4),True),((1.99,-.09),True),((-1.99,-.09),True),((0,-2),False),((0,9.3),False)]:assert foot.covers(Point(pt))==expected,(role,pt)
        variants[role]=dict(triangles=len(tri),sha256=a['sha256'],section_area_m2=foot.area,rays=tests,passed=all(v['passed']for v in tests));
    return variants,assets,{'min':np.min(np.array(bounds)[:,0],axis=0).tolist(),'max':np.max(np.array(bounds)[:,1],axis=0).tolist()},unary_union(ground).simplify(.041,preserve_topology=True)


def city_sources(site,review,model):
    work=site.work;scratch=[];nearfar=[];site.link('macro-READY.json',site.files['READY.json']);site.link('baseline-far.glb',site.files['far.glb']);
    for row in review['near_tiles']:
        site.link('baseline-near.glb.gz',site.files[Path(row['file']).name]);write(work/'context-features.json',[{'localId':i}for i in row['feature_local_ids']]);subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ['near','far']:
            tri=np.fromfile(work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3);xy=tri[:,:,:2]@site.axes.T
            # An axis-aligned triangle envelope gives a conservative lower bound for each exact native triangle.
            footprint=geo.box(xy[:,:,0].min(1),xy[:,:,1].min(1),xy[:,:,0].max(1),xy[:,:,1].max(1));dist=geo.distance(footprint,model);i=int(np.argmin(dist));nearfar.append({'tile':row['id'],'variant':variant,'triangles':len(tri),'min_triangle_envelope_distance_m':float(dist[i]),'nearest_triangle_local_xy_m':xy[i].tolist()});assert dist[i]>5
    return nearfar


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json');ap.add_argument('--work',type=Path,required=True);ap.add_argument('--pbf',type=Path,required=True);ap.add_argument('--out',type=Path,default=HERE);args=ap.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    src=PROJECT/'source/precise'/ID/'footprint-review.json';review=read(src);site=PlacementMeshes(PROJECT,args.work,review);model=geo.transform(shape(review['model_footprint']),site.to_xy);variants,assets,bounds,collision=check_model(args.manifest,args.work,site)
    clearance=LineString([(0,-4),(0,11)]).buffer(.38);assert clearance.disjoint(collision)
    ov=sorted((g.distance(model),i)for i,g in site.footprints.items());assert ov[0][0]>15;raw=args.pbf.read_bytes();assert hashlib.sha256(raw).hexdigest()==FALLBACK
    layer=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building'];extent=layer['extent']
    def project_tile(v):
        ll=np.column_stack(((v[:,0]/extent+13718)/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(v[:,1]/extent+6694)/16384))))));return site.to_xy(ll)
    osm=sorted((geo.transform(shape(v['geometry']),project_tile).distance(model),v['id'])for v in layer['features']);assert osm[0][0]>15
    native=city_sources(site,review,model);frame=review['author_frame'];contract={'id':ID,'lng':site.lon,'lat':site.lat,'heading':frame['runtime_heading_deg'],'altitude':0,'scale':1,'replacement_geometry':None,'source_feature_ids':{'building':[],'building_part':[]},'collision_geometry':site.wgs(collision),'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'overviewBearing':153,'overviewPitch':58,'overviewZoom':20,'maxDistance':450,'lod_switch_in_m':500,'lod_switch_out_m':640,'navigation':{'listed':False,'status':'单列门楼的建筑复原；自由漫游可实际穿过门洞。'},'placement':{'status':'estimated','note':'愚园路南侧过街楼中央通道对齐19级屋顶及保护地块边；距最近源面约15米，独立追加。'},'partial_model':True,'model_scope':read(args.manifest)['scope']}
    write(args.out/'final-placement-contract.json',contract);g=[{'name':name,'local_xy_m':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),'blocked':collision.covers(Point(x,y))}for x,y,name in [(0,-3,'street'),(0,.8,'entrance'),(0,3.55,'passage'),(0,6.9,'back threshold'),(0,9.3,'courtyard side'),(-3,3.4,'left side room'),(3,3.4,'right side room'),(-1.99,-.09,'left pier'),(1.99,-.09,'right pier')]]
    write(args.out/'placement-geometry.json',{'id':ID,'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),'references_sha256':sha(src),'contract_sha256':sha(args.out/'final-placement-contract.json'),'model_assets':assets,'variants':variants,'source_native':native,'vector_sources':{'overture_nearby_checked':len(site.footprints),'overture_nearest_ids_and_distances_m':[[i,d]for d,i in ov[:6]],'openmaptiles_url':'https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13718/6694.pbf','openmaptiles_sha256':FALLBACK,'openmaptiles_building_features_checked':len(osm),'openmaptiles_nearest_id':osm[0][1],'openmaptiles_min_distance_m':osm[0][0]},'model_ground':{'source_planes_m':[.13,.98,1.70],'collision_area_m2':collision.area,'centreline_buffer_radius_m':.38,'centreline_interior_clearance_m':LineString([(0,-4),(0,11)]).distance(collision),'ground_probes':g},'passed':all(v['passed']for v in variants.values())});print([(k,[u['name'] for u in v['rays']if not u['passed']]) for k,v in variants.items()]);assert all(v['passed']for v in variants.values())
if __name__=='__main__':main()
