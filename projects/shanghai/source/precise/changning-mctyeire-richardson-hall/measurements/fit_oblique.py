"""Register two 2022 district photographs against the lawn-face model.

Photo pixels use the original PNGs, before any thumbnail or crop. The training
corners are the stone edges of openings. Visibility determines the holdouts.
Pass --glb to physically intersect the source mesh with independent image rays.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import numpy as np
from scipy.optimize import least_squares
from frontage import SCALE, DORMERS, x, z

HERE = Path(__file__).resolve().parent
PAGE = 'https://www.shcn.gov.cn/col6991/20221017/1223835.html'
# Control syntax: label, horizontal and vertical coordinates on the measured
# rectified frontal reference, actual unrectified pixel, and fit/holdout.
SET = [
    dict(name='lawn-gathering', height_prior=1.65, frame=[640,426], file='d0ec9cc98e7a4798b6b749933a3cf484',
         sha='233d249a60a208e50ea38667c378571fd2a516d11a81cb7629fa59f5afedc482',
         crop=[207,204,562,392],
         points=[
          ('west-pavilion outer upper',51,239,210.5,322,True),('west-panel outer upper',199,239,243.8,318,True),
          ('west-panel inner upper',322,239,273.9,315,False),('second panel outer upper',355,239,282.7,312.9,True),
          ('second panel inner sill',478,275,317.2,321.6,True),('central upper left',518,239,328.7,306.3,False),
          ('central upper right',637,239,370.0,300.4,True),('fourth-panel upper left',675,239,383.4,298.0,True),
          ('fourth-panel upper right',796,239,434.9,291.4,False),('east-panel upper right',953,239,515.3,280.4,True),
          ('east-panel middle left',832,307,452.2,324.0,False),('east-panel ground right',953,376,517.1,357,True),
          ('fourth-panel ground right',796,376,436.4,361.0,False),('west panel ground left',199,376,244.2,365.7,True),
          ('west panel middle left',199,307,244.0,342.0,False)],
         ridge=[(181,269.3,271.4,True),(972,556.6,205.2,False)],
         dormers=[(0,261.5,295,False),(3,297,287.8,False),(4,334.8,283.5,False),
                  (6,369.5,277.6,False),(7,410.8,270.8,False),(10,485.0,257.7,False)],
         materials={'roof tile':[434,246],'wall between floors':[470,313],'upper sash pane':[481,290]}),
    dict(name='lawn-bench', height_prior=.85, frame=[1080,720], file='1d404ca92881404f9ebc9c92358a09bf',
         sha='ae67b8a66f021c137b7ed3a10cce9f60da4282236208b7a93f561e8839d61066',
         crop=[140,146,681,516],
         points=[
          ('west-pavilion outer upper',51,239,156.0,356.2,True),('west panel outer upper',199,239,224.0,348.5,True),
          ('west panel inner upper',322,239,282.6,342.0,False),('second panel outer upper',355,239,303.6,338.8,True),
          ('second panel inner sill',478,275,371.4,360.7,True),('central upper left',518,239,395.8,326.0,False),
          ('central upper right',637,239,474.8,316.1,True),('fourth panel outer upper',675,239,503.6,312.7,True),
          ('fourth panel inner sill',796,275,600.0,337.4,True),('east panel outer upper',832,239,633.5,294.0,False),
          ('west panel middle left',199,307,220.5,404.1,False),('west panel middle right sill',322,345,280.0,429.4,False),
          ('fourth panel middle right',796,307,600.2,373.1,True),('west panel ground left sill',199,421,216.0,491.5,True),
          ('west pavilion inner ground sill',146,421,187.8,491.0,False),('east panel ground left',832,376,632.2,446.2,False)],
         ridge=[(181,302.2,247.4,True)],
         dormers=[(0,265.4,307.2,False),(3,348.1,293.2,False),(4,412.6,282.8,False),
                  (6,481.5,270.9,False),(7,558,256.8,False),(9,648.4,240.9,False)],
         materials={'roof tile':[509,216],'wall between floors':[574,360],'upper sash pane':[442,340]})
]

def camera(params, size):
    eye=np.array(params[:3]); az,pitch,roll,focal,cx,cy=params[3:]
    right=np.array([np.cos(az), np.sin(az), 0])
    forward=np.array([-np.sin(az)*np.cos(pitch),np.cos(az)*np.cos(pitch),np.sin(pitch)])
    up=np.cross(right,forward)
    r=right*np.cos(roll)+up*np.sin(roll)
    u=-right*np.sin(roll)+up*np.cos(roll)
    a=np.stack([focal*r+cx*forward,-focal*u+cy*forward,forward])
    return np.column_stack([a,-a@eye])

def controls(spec):
    rows=[(name,[x(px),0.,z(py)],[u,v],fit) for name,px,py,u,v,fit in spec['points']]
    # The camera fit includes a true off-plane control at the west end of the ridge.
    # The east end in the first photograph and all dormer lights stay independent.
    distance=1685./SCALE
    ridge=(439.*distance+(439.-1.62*SCALE)*8.505-137.*(distance+8.505))/1685.
    rows.extend(('gable ridge '+str(px),[x(px),8.505,ridge+.27],[u,v],fit) for px,u,v,fit in spec['ridge'])
    centre_z=z(220)+.67+(.085+1.68-.16)/2
    rows.extend(('dormer light '+str(i+1),[x(DORMERS[i]),.815,centre_z],[u,v],fit) for i,u,v,fit in spec['dormers'])
    return rows

def project(m,p):
    t=m@np.r_[p,1.]
    return t[:2]/t[2]

def read_triangles(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);b=memoryview(raw)[28+n:]
    def values(i):
        a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
        dtype={5121:'<u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        k={'SCALAR':1,'VEC3':3}[a['type']];dt=np.dtype(dtype)
        arr=np.ndarray((a['count'],k),dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',k*dt.itemsize),dt.itemsize))
        return arr
    triangles=[];ids=[];names=[]
    for node in j['nodes']:
        if 'mesh' not in node: continue
        assert not any(v in node for v in ['matrix','rotation','scale','translation']), 'Provide baked, uncompressed source GLB'
        mesh=j['meshes'][node['mesh']]
        for prim in mesh['primitives']:
            pos=values(prim['attributes']['POSITION'])
            # GLTF is right handed and Y up. The source author works in Z up.
            v=np.stack([pos[:,0],-pos[:,2],pos[:,1]],axis=1)
            tri=v[values(prim['indices']).ravel().reshape(-1,3)]
            ids.extend([len(names)]*len(tri));triangles.append(tri)
            names.append([node.get('name',mesh.get('name')),j['materials'][prim['material']]['name']])
    return np.concatenate(triangles),np.asarray(ids),names,hashlib.sha256(raw).hexdigest()

def cast(p,eye,uv,mesh):
    t,ids,names,_=mesh
    direction=np.linalg.solve(p[:,:3],[*uv,1.]);direction/=np.linalg.norm(direction)
    e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h)
    ok=np.abs(det)>1e-8;inv=np.zeros_like(det);inv[ok]=1/det[ok]
    s=eye-t[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1)
    v=inv*(q@direction);length=inv*np.einsum('ij,ij->i',e2,q)
    valid=np.flatnonzero(ok&(u>=0)&(v>=0)&(u+v<=1)&(length>0))
    if not len(valid):return None
    i=valid[np.argmin(length[valid])]
    return dict(world=(eye+direction*length[i]).tolist(),object=names[ids[i]][0],material=names[ids[i]][1],distance_m=float(length[i]))

def facade_homography(points):
    """Report the independent projective fit on the wall plane (no roof depths)."""
    a=[]
    for _,pt,uv,used in points:
        if not used or pt[1]!=0:continue
        row=[pt[0],pt[2],1.];u,v=uv
        a.extend([[*row,0,0,0,*(-u*np.array(row))],[0,0,0,*row,*(-v*np.array(row))]])
    h=np.linalg.svd(np.array(a))[2][-1].reshape(3,3);h=h/h[2,2]
    held=[]
    for label,pt,uv,used in points:
        if used or pt[1]!=0:continue
        pixel=h@[pt[0],pt[2],1.]
        held.append(dict(feature=label,error_px=float(np.linalg.norm(pixel[:2]/pixel[2]-uv))))
    return dict(plane_y_m=0.0,input_order=['x','z','1'],matrix=h.tolist(),holdout=held,
                holdout_rms_px=float(np.sqrt(np.mean([item['error_px']**2 for item in held]))))

def fit(spec,mesh=None):
    w,h=spec['frame'];data=controls(spec)
    def err(params):
        p=camera(params,(w,h))
        residual=np.concatenate([project(p,pt)-np.asarray(uv) for _,pt,uv,train in data if train])
        # The published lawn views have corrected/shifted framing. Keep only weak
        # principal-point and camera-height priors, and disclose them in the report.
        return np.r_[residual,(params[2]-spec['height_prior'])/1.5,(params[7]-w*.5)/(w*.20),(params[8]-h*.58)/(h*.28)]
    initial=[31,-54,spec['height_prior'],.56,.06,0,w*.93,.5*w,.70*h]
    sol=least_squares(err,initial,bounds=([-20,-240,.1,-.3,-.45,-.20,.25*w,-.25*w,-.20*h],[160,-9,4,1.35,.70,.20,4*w,1.25*w,1.20*h]),
                      x_scale='jac',loss='soft_l1',f_scale=2)
    m=camera(sol.x,(w,h)); points=[]
    for nm,pt,uv,used in data:
        projected=project(m,pt);delta=projected-uv
        points.append(dict(feature=nm,model_xyz_m=pt,observed_px=uv,projected_px=projected.tolist(),dx_dy_px=delta.tolist(),used_in_fit=used,error_px=float(np.linalg.norm(delta))))
    def metrics(records):
        a=np.array([r['error_px'] for r in records])
        return dict(n=len(a),rms_px=float(np.sqrt(np.mean(a*a))),median_px=float(np.median(a)),max_px=float(np.max(a)))
    x0,y0,x1,y1=spec['crop'];crop_m=m.copy();crop_m[0]-=m[2]*x0;crop_m[1]-=m[2]*y0
    return dict(name=spec['name'],url='https://cn.storage.shmedia.tech/'+spec['file']+'.png',sha256=spec['sha'],
                frame=spec['frame'],principal_point_px=sol.x[7:9].tolist(),estimated_lawn_camera_height_prior_m=spec['height_prior'],focal_px=sol.x[6],eye_m=sol.x[:3].tolist(),projection=m.tolist(),
                native_crop_xyxy=spec['crop'],crop_frame=[x1-x0,y1-y0],crop_projection=crop_m.tolist(),
                front_plane=facade_homography(data),points=points,fit=metrics([r for r in points if r['used_in_fit']]),holdout=metrics([r for r in points if not r['used_in_fit']]),
                material_points=[dict(label=k,observed_px=uv,intersection=cast(m,sol.x[:3],uv,mesh) if mesh else None) for k,uv in spec['materials'].items()])

def reference_crop(station,mesh,path):
    """Draw the model alone in the measured native pixel crop. No source pixels reused."""
    from PIL import Image
    matrix=np.array(station['crop_projection'])
    tris,ids,names,_=mesh
    projected=tris@matrix[:,:3].T+matrix[:,3]
    xy=projected[:,:,:2]/projected[:,:,2,None]
    depth=projected[:,:,2].mean(axis=1)
    normal=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
    normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-12)
    diffuse=np.abs(normal@np.array([-.29,-.75,.59]))
    palette={'rust red pantile':(155,81,58),'grey ashlar':(179,174,163),'carved pale stone':(200,194,177),
             'smoky casement glass':(78,86,90),'charcoal lead and steel':(62,63,62),'dark oak':(102,70,50),
             'grey roof flashing':(137,137,129),'muted violet glazing':(108,96,119),'deep blue stained glass':(62,78,106)}
    rgb=np.array([palette.get(names[k][1],(137,124,105)) for k in ids])*(.72+.28*diffuse[:,None])
    width,height=station['crop_frame']
    colour=np.full((height,width,3),[229,232,231],dtype=np.uint8)
    depth_buffer=np.full((height,width),-np.inf)
    for k,tri in enumerate(xy):
        if np.any(projected[k,:,2]<=0):continue
        x0,y0=np.maximum(0,np.floor(tri.min(axis=0)).astype(int))
        x1,y1=np.minimum([width-1,height-1],np.ceil(tri.max(axis=0)).astype(int))
        if x0>x1 or y0>y1:continue
        a,b,c=tri
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-7:continue
        xpix=np.arange(x0,x1+1)[None,:]+.5;ypix=np.arange(y0,y1+1)[:,None]+.5
        wa=((b[1]-c[1])*(xpix-c[0])+(c[0]-b[0])*(ypix-c[1]))/den
        wb=((c[1]-a[1])*(xpix-c[0])+(a[0]-c[0])*(ypix-c[1]))/den
        wc=1-wa-wb
        z0,z1,z2=projected[k,:,2];inverse_z=wa/z0+wb/z1+wc/z2
        current=depth_buffer[y0:y1+1,x0:x1+1]
        visible=(wa>=0)&(wb>=0)&(wc>=0)&(inverse_z>current)
        current[visible]=inverse_z[visible]
        colour[y0:y1+1,x0:x1+1][visible]=rgb[k]
    Image.fromarray(colour).save(path)

def main():
    args=argparse.ArgumentParser()
    args.add_argument('--photos',type=Path,help='Optional folder with the two original PNGs, named original-official-0.png and original-official-1.png.')
    args.add_argument('--preview-dir',type=Path,help='Optional destination for model-only crop renderings.')
    args.add_argument('--glb',type=Path);args.add_argument('--output',type=Path,default=HERE/'oblique-stations.json')
    p=args.parse_args();mesh=read_triangles(p.glb) if p.glb else None
    report=dict(page=PAGE,publication='2022-10-17',building='上海市第三女子中学五四楼（景莲堂），江苏路155号',
       identification='Both photographs show the same south lawn façade. The central two-storey entrance, five recessed banks of classroom casements, roof dormers grouped four/three/four, stepped west flat-roof wing and tall later building at left match. Both viewpoints lie toward the eastern end of the lawn. The photographs do not locate the garden-side secondary door or the north auditorium walls.',
       station_scope='Independent manual pixel picks in each original. Coordinates in metres follow the model: X along the south frontage, Y toward the north, Z up. A pinhole camera with square pixels and a freely fitted shifted principal point and weak camera-height priors (1.65 and 0.85 m, uncertainty 1.5 m) is used. The 58.78 m source span and 17.01 m wing depth set working scale. Held-out dormer and ridge errors include approximate roof depth, façade dimensions, lens distortion and manual pixel uncertainty. Trees, people, bench and the newer tower are photographic occlusions or context outside the model.',
       glb_sha256=mesh[3] if mesh else None,stations=[fit(s,mesh) for s in SET])
    report['depth_qualification']='The projection along the lawn façade is directly constrained. One visible ridge end supplies the noncoplanar fit control per camera. Camera height, principal point, rear-wing depth and off-axis massing are coupled. The first camera reaches the search height bound of 4 m; neither estimated eye is a surveyed position. Use the separate frontal homography and held-out errors when measuring the flat wall.'
    if p.photos:
        from PIL import Image
        for i,station in enumerate(report['stations']):
            f=p.photos/('original-official-%s.png'%i)
            assert hashlib.sha256(f.read_bytes()).hexdigest()==station['sha256']
            im=Image.open(f).convert('RGB');assert list(im.size)==station['frame']
            for item in station['material_points']:
                u,v=item['observed_px'];patch=np.asarray(im.crop((u-1,v-1,u+2,v+2)))
                item['original_rgb_3x3_median']=np.median(patch.reshape(9,3),axis=0).astype(int).tolist()
    if p.preview_dir:
        assert mesh is not None
        p.preview_dir.mkdir(parents=True,exist_ok=True)
        for station in report['stations']:
            f=p.preview_dir/(station['name']+'-model.png')
            reference_crop(station,mesh,f)
            station['model_crop_sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
    p.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    for s in report['stations']:print(s['name'],s['fit'],s['holdout'],s['eye_m'],s['material_points'])
if __name__=='__main__':main()
