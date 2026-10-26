#!/usr/bin/env python3
"""Actual raw-GLB void, glass-fit, coordinates and conditional projection audit."""
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    out=HERE/'output';file=out/'xuhui-wukang-129-raw.glb';data=file.read_bytes()
    assert len(data)<100_000_000 and data[:4]==b'glTF'
    jslen=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+jslen]);binary=data[28+jslen:]
    def acc(i):
        a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
        count={'SCALAR':1,'VEC3':3}[a['type']];dtype={5126:'<f4',5125:'<u4'}[a['componentType']]
        assert not v.get('byteStride')
        return np.frombuffer(binary,dtype=dtype,count=a['count']*count,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,count)
    meshes={};tris=0;normalerrors=[]
    for prim in g['meshes'][0]['primitives']:
        v=acc(prim['attributes']['POSITION']).astype(float);n=acc(prim['attributes']['NORMAL']).astype(float);ii=acc(prim['indices']).ravel()
        assert np.isfinite(v).all() and np.isfinite(n).all()
        tt=v[ii.reshape(-1,3)];nn=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);lens=np.linalg.norm(nn,axis=1)
        assert np.min(lens)>1e-12;nn/=lens[:,None]
        stored=n[ii.reshape(-1,3)[:,0]];stored/=np.linalg.norm(stored,axis=1)[:,None]
        errors=np.degrees(np.arccos(np.clip(np.sum(nn*stored,axis=1),-1,1)));normalerrors.append(float(errors.max()))
        assert errors.max()<1e-3
        # Convert serialized east/up/-north back into ENU.
        name=g['materials'][prim['material']]['name'];meshes[name]=(v[:,[0,2,1]]*[1,-1,1],ii.reshape(-1,3));tris+=len(ii)//3
    source=json.loads((HERE/'geometry-input.json').read_text());model=json.loads((HERE/'calibration-model.json').read_text());metric=json.loads((HERE/'calibration/calibration-independent.json').read_text())
    assert g['extras']['geometry_input_sha256']==sha(HERE/'geometry-input.json')==model['frozen_source_geometry_sha256']
    assert source['replacement']['feature_local_ids']==[3733] and len(source['replacement']['retained_same_near_feature_local_ids'])==17
    assert not g.get('images')
    wp,wi=meshes['cream plaster'];wall=wp[wi]
    def ray(origin,direction,limit=.70):
        edge1=wall[:,1]-wall[:,0];edge2=wall[:,2]-wall[:,0]
        h=np.cross(np.broadcast_to(direction,edge2.shape),edge2);det=np.einsum('ij,ij->i',edge1,h)
        ok=np.abs(det)>1e-10;inv=np.zeros(len(det));inv[ok]=1/det[ok]
        s=origin-wall[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,edge1)
        v=inv*np.einsum('ij,j->i',q,direction);t=inv*np.einsum('ij,ij->i',edge2,q)
        good=ok&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>0)&(t<limit)
        return int(np.count_nonzero(good))
    voids=[];glass=[]
    for w in model['windows']:
        O=np.asarray(w['facade_origin_enu']);T=np.asarray(w['facade_u_enu']);N=np.asarray(w['facade_outward_enu']);x0,z0,x1,z1=w['opening_bounds']
        center=O+T*((x0+x1)/2)+[0,0,(z0+z1)/2]
        holes=ray(center+N*.40,-N)
        solid=ray(center+T*(-(x1-x0)/2-.13)+N*.40,-N)
        assert holes==0,(w['label'],'opening obstructed',holes)
        assert solid>0,(w['label'],'outside opening lacks wall')
        voids.append({'label':w['label'],'actual_plaster_ray_hits_in_opening':holes,'negative_control_adjacent_wall_hits':solid})
        candidates=[]
        for name in ['dark reflection glass','interior shadow']:
            if name not in meshes:continue
            pts=meshes[name][0];offset=pts-O;u=offset@T;d=offset@N;z=pts[:,2]
            select=(u>x0-1e-5)&(u<x1+1e-5)&(z>z0-1e-5)&(z<z1+1e-5)&(d>-.2)&(d<.05)
            candidates.extend(d[select].tolist())
        assert candidates,w['label']
        lo,hi=min(candidates),max(candidates)
        assert abs(lo+.08)<5e-6 and abs(hi+.06)<5e-6,(w['label'],lo,hi)
        glass.append({'label':w['label'],'actual_depth_m':[lo,hi],'front_setback_m':-.04-hi,'thickness_m':hi-lo})
    # Conditional camera projection of named real opening corners, not image resizing.
    P=np.asarray(metric['facade_u_z_d_to_oriented_pixel_projection_3x4']);origin=np.asarray(source['front_edge']['center_local_east_north_m']);X=-np.asarray(source['front_edge']['tangent_east_north']);Y=-np.asarray(source['front_edge']['outward_normal_east_north'])
    def project_enu(pts):
        pts=np.asarray(pts);off=pts[:,:2]-origin
        world=np.column_stack((off@X,pts[:,2],-off@Y,np.ones(len(pts))))
        q=world@P.T;return q[:,:2]/q[:,2,None]
    obs=json.loads((HERE/'references/review/observation-independent.json').read_text());lookup={}
    for z in obs['zones']:
        for k,v in z['2026_controls'].items():
            if 'quad' in k:lookup[(z['plane'],k)]=v
    match={'upper-narrow':('A','narrow_window_outer_quad_TL_TR_BR_BL'),'upper-wide':('A','wide_window_outer_quad'),'lower-wide':('C','lower_window_outer_quad')}
    checks=[]
    for w in model['windows']:
        key=match.get(w['label'])
        if key is None:
            plane=w['facade_label'][0];key=(plane,w['label'])
        if key not in lookup:continue
        O=np.asarray(w['facade_origin_enu']);T=np.asarray(w['facade_u_enu']);x0,z0,x1,z1=w['opening_bounds']
        points=[O+T*u+[0,0,z] for u,z in [(x0,z1),(x1,z1),(x1,z0),(x0,z0)]]
        predicted=project_enu(points);actual=np.asarray(lookup[key]);error=np.linalg.norm(predicted-actual,axis=1)
        checks.append({'label':w['label'],'source_pixels':actual.tolist(),'model_projected_pixels':predicted.tolist(),'corner_rms_px':float(np.sqrt(np.mean(error**2))),'maximum_corner_error_px':float(error.max())})
        assert error.max()<6.,(w['label'],error)
    roof=[]
    for label,uzd,pixel in [('left-front-gable',[-4.453,6.516,0.],[354,245]),('right-offset-cap-apex',[6.14,7.03,-1.67],[1410,232])]:
        q=P@np.r_[uzd,1.];q=q[:2]/q[2];error=float(np.linalg.norm(q-pixel));assert error<5.
        roof.append({'label':label,'model_u_z_d':uzd,'photo_pixel':pixel,'predicted':q.tolist(),'error_px':error,'depth_is_estimated':True})
    result={'schema':'wukang129-independent-raw-check-v1','passed':True,'raw_sha256':sha(file),'raw_bytes':len(data),'triangles':tris,'finite_positions_normals':True,'maximum_normal_deviation_deg':max(normalerrors),
        'frozen_geometry_sha256':sha(HERE/'geometry-input.json'),'unique_target_local_id':3733,'retained_neighbors':17,'actual_glb_opening_rays':voids,'actual_glb_glass_inset':glass,'conditional_photo_opening_checks':checks,'conditional_photo_roof_checks':roof,
        'not_a_survey':'Subpixel/low-pixel conditional fitting does not validate inferred facade depth, envelope scale or lens corrections. Source/model uncertainty remains in calibration reports.',
        'browser_blender_visual_acceptance':False,'checker_sha256':sha(Path(__file__))}
    (out/'independent-model-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'raw_bytes':len(data),'triangles':tris,'openings':len(voids),'projection_controls':len(checks),'max_corner_px':max(r['maximum_corner_error_px'] for r in checks),'roof':roof},indent=2))


if __name__=='__main__':main()
