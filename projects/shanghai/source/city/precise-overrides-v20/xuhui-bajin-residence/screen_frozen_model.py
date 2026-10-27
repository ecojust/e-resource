#!/usr/bin/env python3
"""Actual raw navigation/camera screen with independent neighbor-screen binding.
All distances are finite probes, not a general walkability or surveyed-sidewalk proof.
"""
import argparse, hashlib, json, math, shutil, struct, sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point, LineString, shape
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ID='xuhui-bajin-residence'
VIEW_NAMES={'garden-front','north-entry','north-oblique'}
def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text())
def desc(p):
    p=Path(p).resolve();h=hashlib.sha256()
    with p.open('rb') as f:
        while data:=f.read(1024*1024):h.update(data)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def save(p,d):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def raw_triangles(path):
    blob=Path(path).read_bytes();need(struct.unpack_from('<4sII',blob)==(b'glTF',2,len(blob)),'Invalid raw GLB header')
    offset=12;chunks={}
    while offset<len(blob):
        length,kind=struct.unpack_from('<II',blob,offset);offset+=8
        need(kind not in chunks and length%4==0 and offset+length<=len(blob),'Invalid raw GLB chunk')
        chunks[kind]=memoryview(blob)[offset:offset+length];offset+=length
    need(set(chunks)=={0x4E4F534A,0x004E4942},'Expected JSON and BIN chunks')
    doc=json.loads(bytes(chunks[0x4E4F534A]));binary=chunks[0x004E4942]
    need(len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0],'Expected embedded raw geometry')
    need(not doc.get('skins') and not doc.get('animations'),'Skins or animations require a separate screen')
    dtype={5121:'<u1',5123:'<u2',5125:'<u4',5126:'<f4'};size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def accessor(index):
        a=doc['accessors'][index];need(not a.get('sparse') and not a.get('normalized') and a['count']>0,'Unsupported raw accessor')
        v=doc['bufferViews'][a['bufferView']];need(v['buffer']==0 and not v.get('extensions'),'Compressed or external view is not a raw geometry input')
        dt=np.dtype(dtype[a['componentType']]);width=size[a['type']];stride=v.get('byteStride',width*dt.itemsize)
        start=v.get('byteOffset',0)+a.get('byteOffset',0);end=start+(a['count']-1)*stride+width*dt.itemsize
        need(stride>=width*dt.itemsize and end<=v.get('byteOffset',0)+v['byteLength']<=len(binary),'Accessor outside its bufferView')
        return np.ndarray((a['count'],width),dtype=dt,buffer=binary,offset=start,strides=(stride,dt.itemsize))
    def matrix(node):
        need(not node.get('extensions'),'Raw node extensions/instancing require explicit decode support')
        if 'matrix' in node:
            need(not any(k in node for k in ('translation','rotation','scale')),'Ambiguous node transform')
            result=np.array(node['matrix'],dtype=float).reshape(4,4).T
        else:
            x,y,z,w=node.get('rotation',[0,0,0,1]);need(abs(x*x+y*y+z*z+w*w-1)<1e-5,'Nonunit quaternion')
            rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                          [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                          [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            result=np.eye(4);result[:3,:3]=rot@np.diag(node.get('scale',[1,1,1]));result[:3,3]=node.get('translation',[0,0,0])
        need(np.isfinite(result).all() and np.allclose(result[3],[0,0,0,1]),'Invalid node transform')
        return result
    visited=set();parts=[]
    def visit(index,parent):
        need(index not in visited,'Repeated or cyclic active node');visited.add(index)
        node=doc['nodes'][index];world=parent@matrix(node)
        if 'mesh' in node:
            mesh=doc['meshes'][node['mesh']]
            for pi,primitive in enumerate(mesh['primitives']):
                need(primitive.get('mode',4)==4 and not primitive.get('targets'),'Only static triangle primitives are screened')
                positions=accessor(primitive['attributes']['POSITION']);need(positions.shape[1]==3 and np.isfinite(positions).all(),'Invalid position buffer')
                indices=accessor(primitive['indices']).ravel() if 'indices' in primitive else np.arange(len(positions))
                need(len(indices)%3==0 and indices.min()>=0 and indices.max()<len(positions),'Invalid triangle indices')
                points=np.asarray(positions,dtype=float)@world[:3,:3].T+world[:3,3]
                enu=points[:,[0,2,1]]*[1,-1,1]
                material=doc.get('materials',[])[primitive['material']].get('name') if 'material' in primitive else None
                parts.append({'node':node.get('name',str(index)),'mesh':mesh.get('name',str(node['mesh'])),'primitive':pi,'material':material,
                              'triangles':enu[indices].reshape(-1,3,3)})
        for child in node.get('children',[]):visit(child,world)
    for index in doc['scenes'][doc.get('scene',0)]['nodes']:visit(index,np.eye(4))
    need(parts,'No active triangles')
    return parts,doc


def navigation_value(seed, geometry, expected_schema=None):
    need(isinstance(seed,dict) and seed.get('building_id')==ID,'Navigation target differs')
    if expected_schema is not None:
        need(seed.get('schema')==expected_schema,'Navigation request schema differs')
    nav=seed.get('navigation')
    need(isinstance(nav,dict) and set(nav)=={'listed','overviewZoom','walkStart','bearing'},'Explicit navigation fields required')
    need(nav['listed'] is True and type(nav['overviewZoom']) is int and nav['overviewZoom']==18,'Wrong listed/overviewZoom')
    start=nav['walkStart'];bearing=nav['bearing']
    finite=lambda x:type(x) in (int,float) and math.isfinite(x)
    need(isinstance(start,list) and len(start)==2 and all(finite(x) for x in start),'Finite geographic walkStart required')
    need(-180<start[0]<180 and -85<start[1]<85 and finite(bearing) and 0<=bearing<360,'Invalid walkStart/bearing range')
    need(seed.get('route_scope')=='exterior_only','Only an actual exterior route may be screened')
    need(isinstance(seed.get('candidate_id'),str) and seed['candidate_id'].strip() and len(seed['candidate_id'])<=128,'Actual candidate id of at most 128 characters required')
    need(isinstance(seed.get('ground_access_note'),str) and seed['ground_access_note'].strip() and len(seed['ground_access_note'])<=8000,'Explicit ground/access uncertainty note of at most 8000 characters required')
    return nav


def validate_views(views):
    need(isinstance(views,dict) and set(views)==VIEW_NAMES,'Need garden-front, north-entry and north-oblique camera views')
    fields={'east','north','alt','to_east','to_north','to_alt','fov'}
    for name,pose in views.items():
        need(isinstance(pose,dict) and set(pose)==fields,'Exact explicit ENU camera fields required: '+name)
        need(all(type(x) in (int,float) and math.isfinite(x) for x in pose.values()),'Camera values must be finite: '+name)
        need(.12<pose['alt']<80 and 0<=pose['to_alt']<60 and 5<=pose['fov']<=100,'Camera altitude/FOV outside screening range: '+name)
        need(math.hypot(pose['east'],pose['north'])<=100 and math.hypot(pose['to_east'],pose['to_north'])<=100,'Camera/aim outside bounded frozen neighborhood context: '+name)
        need(math.hypot(pose['to_east']-pose['east'],pose['to_north']-pose['north'])>1e-6,'Camera aim must not be zero or vertical: '+name)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for flag in ('navigation','camera-views','neighbor-report','ground-report','root-model-review','output'):
        ap.add_argument('--'+flag,type=Path,required=True)
    ap.add_argument('--root-model-review-sha256',required=True)
    modes=ap.add_mutually_exclusive_group()
    modes.add_argument('--check-only',dest='execute_screen',action='store_false')
    modes.add_argument('--execute-screen',action='store_true')
    ap.set_defaults(execute_screen=False)
    a=ap.parse_args()
    import integration_contract as contract
    contract.fresh_output(a.output,create=False,budget_bytes=2_000_000)
    binding=contract.validate_root_review(a.root_model_review,a.root_model_review_sha256)
    contract.check_baseline();g,ctx=contract.check_frozen_inputs()
    raw_desc=binding['assets']['raw'];rp=Path(raw_desc['path'])
    need(raw_desc==contract.descriptor(rp),'Root-bound actual raw differs')
    need(g['id']==ID and g['anchor']==contract.ANCHOR,'Wrong frozen raw frame')
    need(len(ctx['features'])==80 and ctx['anchor']==g['anchor'],'Wrong frozen source neighbors')
    seed=contract.read(a.navigation);nav=navigation_value(seed,g)
    views=contract.read(a.camera_views);validate_views(views)
    neighbor=contract.read(a.neighbor_report);ground=contract.read(a.ground_report)
    need(neighbor.get('raw_asset')==raw_desc and neighbor.get('source_neighborhood')==contract.NEIGHBORHOOD,'Independent neighbor input differs')
    need(neighbor.get('passed_source_estimated_height_prism_screen') is True,'Actual independent source-height prism screen must pass first')
    need(neighbor.get('root_source_owner_authorization')==binding,'Independent neighbor root binding differs')
    need(ground.get('root_source_owner_authorization')==binding,'Source-ground root binding differs')
    need(ground.get('passed_source_screen_only') is True and ground.get('candidate_navigation')=={k:nav[k] for k in ('walkStart','bearing')},'Matching successful source-ground screen required')
    need(ground.get('candidate_binding')==contract.descriptor(a.navigation),'Source-ground must bind the exact navigation input')
    need(ground.get('coordinate_contract')==contract.GEOMETRY and ground.get('effective_neighborhood')==contract.NEIGHBORHOOD,'Source-ground frame or neighborhood differs')
    for d in ctx['source_files']:
        need(contract.descriptor(d['path'])==d,'Frozen source table changed')
    watched=[a.navigation,a.camera_views,a.neighbor_report,a.ground_report,Path(__file__)]
    before=[contract.descriptor(p) for p in watched]
    if not a.execute_screen:
        print(json.dumps({'status':'REAL_INPUTS_CHECKED_NO_NAVIGATION_SCREEN_EXECUTED','root_source_owner_authorization':binding,'input_descriptors':before,'output_created':False,'screen_executed':False,'browser_passed':False},indent=2))
        return
    parts,doc=raw_triangles(rp);tri=np.concatenate([p['triangles'] for p in parts]);points=tri.reshape(-1,3)
    need(np.isfinite(points).all() and len(tri)>0,'Actual raw triangles must be finite')
    need(neighbor.get('actual_triangle_count')==len(tri),'Neighbor screen triangle count differs')
    parts_end=np.cumsum([len(p['triangles']) for p in parts]);tri_lo=tri.min(axis=1);tri_hi=tri.max(axis=1)
    def nearest(probe,radius,zrange=None):
        bb=probe.bounds;pad=10.;mask=(tri_hi[:,0]>=bb[0]-pad)&(tri_lo[:,0]<=bb[2]+pad)&(tri_hi[:,1]>=bb[1]-pad)&(tri_lo[:,1]<=bb[3]+pad)
        if zrange is not None:mask&=(tri_hi[:,2]>=zrange[0])&(tri_lo[:,2]<=zrange[1])
        ids=np.flatnonzero(mask)
        if not len(ids):return {'radius_clearance_lower_bound_m':pad-radius,'method':'No projected triangle bounding box within 10 m after stated height-band selection.','candidate_triangle_count':0,'height_band_m':zrange}
        xy=tri[ids,:,:2];areas=np.cross(xy[:,1]-xy[:,0],xy[:,2]-xy[:,0]);geoms=shapely.polygons(xy);flat=areas==0
        if flat.any():geoms[flat]=shapely.linestrings(xy[flat])
        distances=shapely.distance(geoms,probe);j=int(np.argmin(distances));tid=int(ids[j]);d=float(distances[j]);part=parts[int(np.searchsorted(parts_end,tid,side='right'))]
        return {'radius_clearance_lower_bound_m':min(d,pad)-radius,'method':'Minimum of actual transformed triangle projections after conservative triangle-height interval filtering; excluded XY boxes are at least 10 m away.','distance_to_nearest_selected_triangle_projection_m':d,'radius_m':radius,'height_band_m':zrange,'candidate_triangle_count':len(ids),'nearest_triangle_index':tid,'nearest_material':part['material'],'nearest_triangle_z_range_m':[float(tri_lo[tid,2]),float(tri_hi[tid,2])],'nearest_triangle_enu_m':tri[tid].tolist(),'height_filter_note':'Every triangle crossing the height band is retained in full projection; low walls/columns are not waived by upper-floor projection overlap.'}
    nei=[(row,shape(row['geometry_local_east_north_m'])) for row in ctx['features']]
    lon0,lat0=g['anchor'];R=6378137;c=math.cos(math.radians(lat0));m0=math.asinh(math.tan(math.radians(lat0)))
    lon,lat=nav['walkStart'];start=np.array([R*math.radians(lon-lon0)*c,R*(math.asinh(math.tan(math.radians(lat)))-m0)*c]);b=math.radians(nav['bearing']);u=np.array([math.sin(b),math.cos(b)]);target=start+2.8*u;eye=target-14*math.sin(math.radians(82))*u;eye_alt=3+14*math.cos(math.radians(82))
    probes={'avatar_disc':(Point(start),.38,[-.10,2.30]),'first_5m_forward_swept_body':(LineString([start,start+5*u]),.38,[-.10,2.30]),'settled_camera_disc':(Point(eye),.12,[eye_alt-.12,eye_alt+.12]),'settled_camera_boom_projection':(LineString([target,eye]),.12,[3-.12,eye_alt+.12])}
    clear={}
    for name,(probe,r,zs) in probes.items():
        near=sorted([{'key':row['key'],'macro':row['macro'],'local_id':row['local_id'],'radius_clearance_m':geom.distance(probe)-r} for row,geom in nei],key=lambda x:x['radius_clearance_m'])
        clear[name]={'mesh_probe':nearest(probe,r,zs),'all_height_projection':nearest(probe,r),'source_neighbor_intersections':[x for x in near if x['radius_clearance_m']<=0],'nearest_source_neighbors':near[:4]}
    checks={}
    for name,pose in views.items():
        e=np.array([pose['east'],pose['north'],pose['alt']],dtype=float);aim=np.array([pose['to_east'],pose['to_north'],pose['to_alt']],dtype=float);f=aim-e;f/=np.linalg.norm(f);right=np.cross(f,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,f)
        framing=(points-e)@np.vstack([right,up,f]).T
        # All three Ba Jin views screen the complete actual model; no inherited Hudec ROI.
        depth=framing[:,2];positive=depth>.1
        ndc=np.divide(framing[:,:2],depth[:,None]*math.tan(math.radians(pose['fov']/2))*[1040/760,1],out=np.full_like(framing[:,:2],np.inf),where=depth[:,None]>.1)
        frame_pass=bool(positive.all() and np.isfinite(ndc).all() and abs(ndc).max()<=.8)
        probe=Point(e[:2]);line=LineString([e[:2],aim[:2]])
        ns=sorted([{'key':row['key'],'macro':row['macro'],'local_id':row['local_id'],'camera_radius_clearance_m':geom.distance(probe)-.12,'sightline_radius_clearance_m':geom.distance(line)-.12} for row,geom in nei],key=lambda x:min(x['camera_radius_clearance_m'],x['sightline_radius_clearance_m']))
        camera_clear=nearest(probe,.12,[e[2]-.12,e[2]+.12])
        edge1=tri[:,1]-tri[:,0];edge2=tri[:,2]-tri[:,0];pv=np.cross(np.broadcast_to(f,edge2.shape),edge2);det=np.einsum('ij,ij->i',edge1,pv);tv=e-tri[:,0];inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-10);uu=np.einsum('ij,ij->i',tv,pv)*inv;qv=np.cross(tv,edge1);vv=np.einsum('j,ij->i',f,qv)*inv;tt=np.einsum('ij,ij->i',edge2,qv)*inv;hit=(abs(det)>1e-10)&(uu>=-1e-8)&(vv>=-1e-8)&(uu+vv<=1+1e-8)&(tt>.01)
        hid=np.flatnonzero(hit);first=None
        if len(hid):
            tid=int(hid[np.argmin(tt[hid])]);xyz=e+tt[tid]*f;part=parts[int(np.searchsorted(parts_end,tid,side='right'))];first={'triangle_index':tid,'material':part['material'],'distance_m':float(tt[tid]),'hit_enu_m':xyz.tolist()}
        checks[name]={'request':pose,'framing_scope':'Every referenced vertex of actual raw model after node transforms; authored ENU is not rotated again.','whole_model_referenced_vertices':len(points),'framed_actual_referenced_vertices':len(points),'framing_ndc_min':ndc.min(axis=0).tolist() if np.isfinite(ndc).all() else None,'framing_ndc_max':ndc.max(axis=0).tolist() if np.isfinite(ndc).all() else None,'framed_positive_depth_range_m':[float(depth.min()),float(depth.max())],'inside_frame_with_10_percent_edge_margin':frame_pass,'camera_mesh_probe':camera_clear,'source_neighbors':{'nearest':ns[:5],'intersections':[x for x in ns if min(x['camera_radius_clearance_m'],x['sightline_radius_clearance_m'])<=0],'height_based_waiver_used':False},'actual_center_ray_first_hit':first,'rendered_visibility_accepted':False}
    nav_pass=all(row['mesh_probe']['radius_clearance_lower_bound_m']>0 and not row['source_neighbor_intersections'] for row in clear.values())
    camera_pass=all(row['inside_frame_with_10_percent_edge_margin'] and row['camera_mesh_probe']['radius_clearance_lower_bound_m']>0 and not row['source_neighbors']['intersections'] for row in checks.values())
    limits=['Only the supplied outdoor spawn, first 5 m and default camera are screened. Arbitrary movement, interiors, stairs, curbs and public access are not accepted.','Source-neighbor geometry/heights and the unmeasured main-house envelope are context estimates, not surveyed solids.','The 2.2 m door-leaf prior and hidden 4.5 m northern roof transition remain estimates; neither validates a ground route.','The courtyard, annexes, gate and interiors are excluded from this authored model. Geometry clearance cannot establish their physical accessibility.','All three views conservatively frame every referenced model vertex. Center rays and footprint lines do not prove all-pixel visibility; browser rendering and visual review remain pending.']
    report={'schema':'bajin-v20-actual-raw-finite-navigation-camera-screen','building_id':ID,'geometry_screen_passed':nav_pass and camera_pass,'navigation_screen_passed':nav_pass,'camera_screen_passed':camera_pass,'independent_neighbor_screen_passed':True,'source_ground_screen_passed':True,'browser_passed':False,'root_visual_accepted':False,'source_owner_polygon_is_architectural_wall':False,'precise_public_sidewalk_membership_verified':False,'root_source_owner_authorization':binding,'raw_asset':raw_desc,'geometry_input':contract.GEOMETRY,'source_neighborhood':contract.NEIGHBORHOOD,'source_files':ctx['source_files'],'independent_neighbor_report':contract.descriptor(a.neighbor_report),'source_ground_report':contract.descriptor(a.ground_report),'navigation_input':contract.descriptor(a.navigation),'navigation':nav,'camera_requests':views,'camera_views_input':contract.descriptor(a.camera_views),'screen_script':contract.descriptor(__file__),'triangles':len(tri),'referenced_vertex_count':len(points),'actual_bounds_enu_m':[points.min(axis=0).tolist(),points.max(axis=0).tolist()],'controller_default':{'player_east_north_m':start.tolist(),'target_east_north_alt_m':[*target.tolist(),3],'camera_east_north_alt_m':[*eye.tolist(),eye_alt],'pitch_degrees':82,'camera_distance_m':14},'spawn_probe_clearance':clear,'views':checks,'limitations':limits}
    need(before==[contract.descriptor(p) for p in watched],'Screen input changed during execution')
    need(binding==contract.validate_root_review(a.root_model_review,a.root_model_review_sha256),'Root-bound inputs changed during execution')
    contract.check_baseline();contract.check_frozen_inputs()
    out=a.output.resolve()
    encode=lambda value:(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    planned=lambda path,content:{'path':str(path),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
    report_bytes=encode(report);view_bytes=encode(views)
    proposal={key:seed[key] for key in ('schema','building_id','navigation','route_scope','candidate_id','ground_access_note')};proposal['source_preliminary_proposal']=contract.descriptor(a.navigation);proposal['status']='ACTUAL_RAW_GEOMETRY_SCREENED_BROWSER_PENDING' if report['geometry_screen_passed'] else 'ACTUAL_RAW_GEOMETRY_FAILED';proposal['raw_model']=raw_desc;proposal['root_source_owner_authorization']=binding;proposal['source_ground_screen']=contract.descriptor(a.ground_report);proposal['actual_model_screen']={'report':planned(out/'model-clearance.json',report_bytes),'camera_views':planned(out/'camera-views.json',view_bytes),'raw_asset_sha256':raw_desc['sha256'],'geometry_screen_passed':report['geometry_screen_passed'],'browser_passed':False,'root_visual_accepted':False}
    payload={'model-clearance.json':report_bytes,'camera-views.json':view_bytes,'navigation-proposal.json':encode(proposal)}
    total=sum(map(len,payload.values()));need(total<2_000_000,'Navigation-screen output exceeds 2MB budget')
    need(shutil.disk_usage(HERE).free>=300_000_000+total,'Navigation-screen output would breach 300MB reserve')
    contract.fresh_output(a.output,create=True,budget_bytes=2_000_000)
    for name,content in payload.items():
        with (out/name).open('xb') as handle:handle.write(content)
    need(shutil.disk_usage(HERE).free>=300_000_000,'Navigation-screen output breached 300MB reserve')
    print(json.dumps({'report':contract.descriptor(out/'model-clearance.json'),'geometry_screen_passed':report['geometry_screen_passed'],'navigation_screen_passed':nav_pass,'camera_screen_passed':camera_pass,'browser_passed':False},indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,TypeError,OSError) as error:
        print('BAJIN_NAVIGATION_SCREEN_REJECTED: '+str(error),file=sys.stderr);sys.exit(2)


