#!/usr/bin/env python3
"""Actual raw navigation/camera screen with independent neighbor-screen binding.
All distances are finite probes, not a general walkability or surveyed-sidewalk proof.
"""
import argparse, hashlib, json, math, struct, sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point, LineString, shape
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ID='changning-hudec-residence'
def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text())
def desc(p):
    p=Path(p).resolve();h=hashlib.sha256()
    with p.open('rb') as f:
        while data:=f.read(1024*1024):h.update(data)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def save(p,d):
    with Path(p).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
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


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--metadata',type=Path,required=True);ap.add_argument('--navigation',type=Path,required=True);ap.add_argument('--camera-views',type=Path,required=True);ap.add_argument('--neighbor-report',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    need(a.output.resolve().is_relative_to(HERE) and not a.output.exists(),'New isolated output required')
    md=read(a.metadata);raw=md.get('assets',{}).get('raw',md.get('raw'));rp=Path(raw.get('path') or raw.get('file') or raw.get('source'));rp=rp if rp.is_absolute() else a.metadata.parent/rp
    raw_desc=desc(rp);need(all(raw_desc[k]==raw[k] for k in ('bytes','sha256')),'Raw bytes changed')
    gp=HERE/'source-owner-input-v1'/ID/'geometry-input.json';g=read(gp);need(md['id']==ID and md['anchor']==g['anchor'] and md.get('rotation_y',0)==0 and md['ground_base_m']==0,'Wrong raw model/frame')
    need(md.get('source_geometry_sha256')==desc(gp)['sha256'],'Raw source frame changed')
    parts,doc=raw_triangles(rp);tri=np.concatenate([p['triangles'] for p in parts]);points=tri.reshape(-1,3)
    need(len(tri)==raw['triangles'] and np.isfinite(points).all(),'Actual triangle count differs')
    parts_end=np.cumsum([len(p['triangles']) for p in parts]);tri_lo=tri.min(axis=1);tri_hi=tri.max(axis=1)
    def nearest(probe,radius,zrange=None):
        bb=probe.bounds;pad=10.;mask=(tri_hi[:,0]>=bb[0]-pad)&(tri_lo[:,0]<=bb[2]+pad)&(tri_hi[:,1]>=bb[1]-pad)&(tri_lo[:,1]<=bb[3]+pad)
        if zrange is not None:mask&=(tri_hi[:,2]>=zrange[0])&(tri_lo[:,2]<=zrange[1])
        ids=np.flatnonzero(mask)
        if not len(ids):return {'radius_clearance_lower_bound_m':pad-radius,'method':'No projected triangle bounding box within 10 m after stated height-band selection.','candidate_triangle_count':0,'height_band_m':zrange}
        xy=tri[ids,:,:2];areas=np.cross(xy[:,1]-xy[:,0],xy[:,2]-xy[:,0]);geoms=shapely.polygons(xy);flat=areas==0
        if flat.any():geoms[flat]=shapely.linestrings(xy[flat])
        distances=shapely.distance(geoms,probe);j=int(np.argmin(distances));tid=int(ids[j]);d=float(distances[j]);p=parts[int(np.searchsorted(parts_end,tid,side='right'))]
        return {'radius_clearance_lower_bound_m':min(d,pad)-radius,'method':'Minimum of actual transformed triangle projections after conservative triangle-height interval filtering; excluded XY boxes are at least 10 m away. No convex hull substitutes for a recess.','distance_to_nearest_selected_triangle_projection_m':d,'radius_m':radius,'height_band_m':zrange,'candidate_triangle_count':len(ids),'nearest_triangle_index':tid,'nearest_material':p['material'],'nearest_triangle_z_range_m':[float(tri_lo[tid,2]),float(tri_hi[tid,2])],'nearest_triangle_enu_m':tri[tid].tolist(),'height_filter_note':'A triangle crossing the height band is retained in full projection, so its clearance is conservative; this does not waive a low wall/column due to upper-floor projection overlap.'}
    npth=HERE/'source-neighborhood-v1.json';ctx=read(npth);need(len(ctx['features'])==44 and ctx['anchor']==g['anchor'],'Wrong source neighbors')
    for d in ctx['source_files']:need(all(desc(d['path'])[k]==d[k] for k in ('bytes','sha256')),'Source table changed')
    nei=[(r,shape(r['geometry_local_east_north_m'])) for r in ctx['features']]
    neighbor=read(a.neighbor_report);need(neighbor['raw_asset']['sha256']==raw_desc['sha256'] and neighbor['raw_asset']['bytes']==raw_desc['bytes'],'Independent neighbor screen differs from raw')
    seed=read(a.navigation);nav=seed['navigation'];lon0,lat0=g['anchor'];R=6378137;c=math.cos(math.radians(lat0));m0=math.asinh(math.tan(math.radians(lat0)))
    lon,lat=nav['walkStart'];start=np.array([R*math.radians(lon-lon0)*c,R*(math.asinh(math.tan(math.radians(lat)))-m0)*c]);b=math.radians(nav['bearing']);u=np.array([math.sin(b),math.cos(b)]);target=start+2.8*u;eye=target-14*math.sin(math.radians(82))*u;eye_alt=3+14*math.cos(math.radians(82))
    probes={'avatar_disc':(Point(start),.38,[-.10,2.30]),'first_5m_forward_swept_body':(LineString([start,start+5*u]),.38,[-.10,2.30]),'settled_camera_disc':(Point(eye),.12,[eye_alt-.12,eye_alt+.12]),'settled_camera_boom_projection':(LineString([target,eye]),.12,[3-.12,eye_alt+.12])}
    clear={}
    for name,(probe,r,zs) in probes.items():
        near=sorted([{'key':row['key'],'macro':row['macro'],'local_id':row['local_id'],'radius_clearance_m':geom.distance(probe)-r} for row,geom in nei],key=lambda x:x['radius_clearance_m'])
        clear[name]={'mesh_probe':nearest(probe,r,zs),'all_height_projection':nearest(probe,r),'source_neighbor_intersections':[x for x in near if x['radius_clearance_m']<=0],'nearest_source_neighbors':near[:4]}
    views=read(a.camera_views);need(set(views)=={'southwest','north-entry','west-facade-close'},'Need three actual camera views')
    checks={}
    for name,pose in views.items():
        e=np.array([pose['east'],pose['north'],pose['alt']],dtype=float);aim=np.array([pose['to_east'],pose['to_north'],pose['to_alt']],dtype=float);f=aim-e;f/=np.linalg.norm(f);right=np.cross(f,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,f)
        q=(points-e)@np.vstack([right,up,f]).T;depth=q[:,2];positive=depth>.1
        if name=='west-facade-close':
            roi=(points[:,0]>=-15.1)&(points[:,0]<=-7)&(points[:,1]>=-10.8)&(points[:,1]<=.8)&(points[:,2]>=1)&(points[:,2]<=11.5)
            need(roi.any(),'No actual west-facade ROI vertices');framing=q[roi];scope='Actual referenced vertices in stated west-facade ROI only. This close-up intentionally does not frame the entire building.'
        else:roi=np.ones(len(points),dtype=bool);framing=q;scope='Every referenced vertex of actual raw model, after transforms.'
        ndc=framing[:,:2]/(framing[:,2,None]*math.tan(math.radians(pose['fov']/2))*[1040/760,1]);frame_pass=bool(framing[:,2].min()>.1 and abs(ndc).max()<=.8)
        probe=Point(e[:2]);line=LineString([e[:2],aim[:2]])
        ns=sorted([{'key':r['key'],'local_id':r['local_id'],'camera_radius_clearance_m':geom.distance(probe)-.12,'sightline_radius_clearance_m':geom.distance(line)-.12} for r,geom in nei],key=lambda x:min(x['camera_radius_clearance_m'],x['sightline_radius_clearance_m']))
        camera_clear=nearest(probe,.12,[e[2]-.12,e[2]+.12])
        # Exact ray/actual-triangle intersection supports close-up targeting; it is not full rendered visibility.
        edge1=tri[:,1]-tri[:,0];edge2=tri[:,2]-tri[:,0];pv=np.cross(np.broadcast_to(f,edge2.shape),edge2);det=np.einsum('ij,ij->i',edge1,pv);tv=e-tri[:,0];inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-10);uu=np.einsum('ij,ij->i',tv,pv)*inv;qv=np.cross(tv,edge1);vv=np.einsum('j,ij->i',f,qv)*inv;tt=np.einsum('ij,ij->i',edge2,qv)*inv;hit=(abs(det)>1e-10)&(uu>=-1e-8)&(vv>=-1e-8)&(uu+vv<=1+1e-8)&(tt>.01)
        hid=np.flatnonzero(hit);first=None
        if len(hid):
            tid=int(hid[np.argmin(tt[hid])]);xyz=e+tt[tid]*f;p=parts[int(np.searchsorted(parts_end,tid,side='right'))];first={'triangle_index':tid,'material':p['material'],'distance_m':float(tt[tid]),'hit_enu_m':xyz.tolist()}
        checks[name]={'request':pose,'framing_scope':scope,'whole_model_referenced_vertices':len(points),'framed_actual_referenced_vertices':int(roi.sum()),'west_facade_roi_enu_m':{'min':[-15.1,-10.8,1],'max':[-7,.8,11.5]} if name=='west-facade-close' else None,'framing_ndc_min':ndc.min(axis=0).tolist(),'framing_ndc_max':ndc.max(axis=0).tolist(),'framed_positive_depth_range_m':[float(framing[:,2].min()),float(framing[:,2].max())],'inside_frame_with_10_percent_edge_margin':frame_pass,'camera_mesh_probe':camera_clear,'source_neighbors':{'nearest':ns[:5],'intersections':[x for x in ns if min(x['camera_radius_clearance_m'],x['sightline_radius_clearance_m'])<=0],'height_based_waiver_used':False},'actual_center_ray_first_hit':first,'rendered_visibility_accepted':False}
    nav_pass=all(r['mesh_probe']['radius_clearance_lower_bound_m']>0 and not r['source_neighbor_intersections'] for r in clear.values())
    camera_pass=all(r['inside_frame_with_10_percent_edge_margin'] and r['camera_mesh_probe']['radius_clearance_lower_bound_m']>0 and not r['source_neighbors']['intersections'] for r in checks.values())
    neighbor_pass=neighbor.get('passed_source_estimated_height_prism_screen') is True
    ground_path=HERE/'navigation-source-v1/source-ground-review.json';ground=read(ground_path);need(ground['candidate_navigation']=={k:nav[k] for k in ('walkStart','bearing')},'Ground candidate changed')
    limits=['Only the explicit exterior spawn, finite first 5 m and default camera are screened; arbitrary movement, interior access, arcade/stair/curb collision are not accepted.','Selected outdoor approach lies in imagery-indicated garden/court context; paving, exact terrain height, public access and walkable path width remain unverified. OSM road centerlines do not establish sidewalk edges.','Actual triangle height-band screening is conservative for these finite volumes; full-height projected cornices are reported separately, not automatically called ground collision.','Source-neighbor outlines and heights are mapped estimates, not surveyed architectural solids. Independent contact report remains authoritative for all neighbor overlaps.','Southwest and north-entry frame every referenced model vertex; west-facade-close frames only the explicitly bounded west-facade vertices. No full-building framing is claimed for the close-up.','Camera center ray and source-footprint line checks do not prove all-pixel visibility. Actual browser rendering and root visual review remain pending.']
    report={'schema':'hudec-v19-actual-raw-finite-navigation-camera-screen','building_id':ID,'geometry_screen_passed':nav_pass and camera_pass and neighbor_pass,'navigation_screen_passed':nav_pass,'camera_screen_passed':camera_pass,'independent_neighbor_screen_passed':neighbor_pass,'browser_passed':False,'root_visual_accepted':False,'source_owner_polygon_is_architectural_wall':False,'precise_public_sidewalk_membership_verified':False,'raw_asset':raw_desc,'metadata':desc(a.metadata),'geometry_input':desc(gp),'source_neighborhood':desc(npth),'source_files':ctx['source_files'],'independent_neighbor_report':desc(a.neighbor_report),'navigation_input':desc(a.navigation),'navigation':nav,'camera_requests':views,'camera_views_input':desc(a.camera_views),'screen_script':desc(__file__),'triangles':len(tri),'referenced_vertex_count':len(points),'actual_bounds_enu_m':[points.min(axis=0).tolist(),points.max(axis=0).tolist()],'controller_default':{'player_east_north_m':start.tolist(),'target_east_north_alt_m':[*target.tolist(),3],'camera_east_north_alt_m':[*eye.tolist(),eye_alt],'pitch_degrees':82,'camera_distance_m':14},'spawn_probe_clearance':clear,'views':checks,'limitations':limits}
    a.output.mkdir();save(a.output/'model-clearance.json',report);save(a.output/'camera-views.json',views)
    proposal=dict(seed);proposal.pop('draft_model',None);proposal['source_preliminary_proposal']=desc(a.navigation);proposal['status']='ACTUAL_RAW_GEOMETRY_SCREENED_MODEL_AND_BROWSER_PENDING' if report['geometry_screen_passed'] else 'ACTUAL_RAW_GEOMETRY_FAILED';proposal['raw_model']=raw_desc;proposal['source_ground_screen']=desc(ground_path);proposal['actual_model_screen']={'report':desc(a.output/'model-clearance.json'),'camera_views':desc(a.output/'camera-views.json'),'raw_asset_sha256':raw_desc['sha256'],'geometry_screen_passed':report['geometry_screen_passed'],'browser_passed':False,'root_visual_accepted':False};save(a.output/'navigation-proposal.json',proposal)
    print(json.dumps({'report':desc(a.output/'model-clearance.json'),'geometry_screen_passed':report['geometry_screen_passed'],'navigation_screen_passed':nav_pass,'camera_screen_passed':camera_pass,'neighbor_screen_passed':neighbor_pass,'probes':{k:v['mesh_probe']['radius_clearance_lower_bound_m'] for k,v in clear.items()},'views':{k:{'framing':v['inside_frame_with_10_percent_edge_margin'],'ndc_min':v['framing_ndc_min'],'ndc_max':v['framing_ndc_max'],'camera_clearance':v['camera_mesh_probe']['radius_clearance_lower_bound_m'],'source_intersections':v['source_neighbors']['intersections'],'center_hit':v['actual_center_ray_first_hit']} for k,v in checks.items()}},indent=2))
if __name__=='__main__':main()
