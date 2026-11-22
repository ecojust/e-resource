"""Sample the published mesh at the two measured elevations and render its actual surfaces."""
import argparse
import json
import math
from pathlib import Path
import sys
import tempfile
import struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'camera-fit'))
sys.path.insert(0,str(ROOT/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(ROOT/'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'))
sys.path.insert(0,str(HERE.parent/'source'))
import registered as street
import court_registered as court
from glb_triangles import SerialScene
from render_riverfront_survey import load_raster,raster,perspective
from hospital_roof import LIP,SOFFIT,TURNED,BRICK,VENT,STREET_PIERS

CAMS={'street':street,'court':court}
MATERIAL_FAMILY={BRICK:'brick',VENT:'vent',LIP:'stone',SOFFIT:'stone',TURNED:'stone'}


def family(hit):
    if hit is None:return 'sky'
    return MATERIAL_FAMILY.get(hit['material'], 'other building surface')


def camera_probes(scene,obs):
    out=[]
    for view,branches in obs['image_probes'].items():
        camera=CAMS[view]
        for part,uvs in branches.items():
            target=part.split('_')[0]
            for uv in uvs:
                r=camera.R.T@np.linalg.solve(camera.K,[*uv,1.])
                first=scene.ray(camera.eye,r,115)
                material=family(first)
                matched=target==material if part!='shaft_background' else material=='sky'
                out.append(dict(view=view,feature=part,pixel=uv,observed=material,
                                match=matched,returned=first))
    return out


def section_probes(scene):
    rows=[]
    z,w,d=23.69,44.62,11.33
    scale=w/46.5
    def cast(part,o,r,material):
        hit=scene.ray(o,r,2.3)
        rows.append(dict(part=part,origin=o,direction=r,expected=material,returned=hit,
                         match=bool(hit and hit['material']==material)))
    for tag,span,start,sign,tangent in [('street',w,(0,0),-1,1),
                                           ('court',w-1.14,(w,d),1,-1)]:
        n=round(span/(.58*scale))
        for i in np.linspace(0,n-1,11).round().astype(int):
            x=start[0]+tangent*span*(i+.5)/n
            cast(tag+' profiled modillion',[x,start[1]+sign*1.6,z-.846*scale],[0,-sign,0],LIP)
        for i in (2,4,6,8):
            if tag=='street':
                a,c=[STREET_PIERS[j]*w for j in (i,i+1)]
                seat=.32
            else:
                south=(1.14,6.97,12.22,17.45,22.73,28.16,32.68,39.32,44.62)
                if i>=len(south)-1:continue
                a,c=south[i:i+2]
                seat=.71
                if i==6:continue
            lo,hi=a+.38*scale,c-.38*scale
            pieces=round((hi-lo)/(.233*scale))
            if tag=='court' and i==7:continue
            for j in (1,pieces//2):
                x=lo+(j+.5)*(hi-lo)/pieces
                cast(tag+' turned spindle',[x,start[1]+sign*1.6,z+(seat+.33)*scale],[0,-sign,0],TURNED)
    return rows


def raised_brick_uv(mesh):
    """Check UV area against the actual rooftop triangles in all three brick masses."""
    with mesh.open('rb') as f:
        f.seek(12)
        length,_=struct.unpack('<II',f.read(8))
        doc=json.loads(f.read(length))
        length,_=struct.unpack('<II',f.read(8));binary=f.read(length)
    types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
    def read(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        dt=np.dtype(types[a['componentType']])
        columns={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        offset=a.get('byteOffset',0)+v.get('byteOffset',0)
        data=np.ndarray((a['count'],columns),dtype=dt,buffer=binary,offset=offset,
                        strides=(v.get('byteStride',dt.itemsize*columns),dt.itemsize))
        if a.get('normalized'):
            data=data.astype(float)/np.iinfo(dt).max
            if dt.kind=='i':data=np.maximum(data,-1)
        return data
    material=next(i for i,m in enumerate(doc['materials']) if m['name']==BRICK)
    coat=doc['materials'][material]['pbrMetallicRoughness']
    # A roof-only study assembled with the minimal palette can still be
    # compared spatially. Released building files require the fired-brick image.
    if 'baseColorTexture' not in coat:return {'embedded_brick_texture':False}
    tex=doc['textures'][coat['baseColorTexture']['index']]
    image=doc['images'][tex['source']]
    import hashlib
    view=doc['bufferViews'][image['bufferView']]
    k=view.get('byteOffset',0)
    result={'embedded_brick_texture':True,
            'image_sha256':hashlib.sha256(binary[k:k+view['byteLength']]).hexdigest(),
            'texture_repeat_m':[1.92,1.056], 'masses':{}}
    all_ratios={}
    for node in doc['nodes']:
        if 'mesh' not in node:continue
        local=np.eye(4)
        if 'matrix' in node:local=np.asarray(node['matrix']).reshape(4,4).T
        else:
            if 'rotation' in node:
                x,y,z,w=node['rotation']
                local[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                              [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                              [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
            local[:3,:3]=local[:3,:3]@np.diag(node.get('scale',[1.,1.,1.]))
            local[:3,3]=node.get('translation',[0.,0.,0.])
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            if primitive.get('material')!=material:continue
            attrs=primitive['attributes']
            pos=read(attrs['POSITION'])@local[:3,:3].T+local[:3,3]
            pos=pos[:,[0,2,1]]*np.array([1.,-1.,1.])
            ix=read(primitive['indices']).reshape(-1,3)
            geom=pos[ix];centre=geom.mean(axis=1)
            x,y,z=centre.T
            uv=read(attrs['TEXCOORD_0'])[ix]*np.array([1.92,1.056])
            first,second=uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]
            uv_area=np.abs(first[:,0]*second[:,1]-first[:,1]*second[:,0])
            xyz_area=np.linalg.norm(np.cross(geom[:,1]-geom[:,0],geom[:,2]-geom[:,0]),axis=1)
            for label,mask in [('corner',(x<7)&(y<5.3)&(z>24.82)),
                               ('shaft',(x>17)&(x<23)&(y<3)&(z>24.9)),
                               ('court',(x>30)&(x<41)&(y>8)&(z>24.8))]:
                if np.any(mask):
                    all_ratios.setdefault(label,[]).extend((uv_area[mask]/xyz_area[mask]).tolist())
    for label,ratios in all_ratios.items():
        result['masses'][label]={'triangles':len(ratios),'minimum_area_ratio':min(ratios),
                         'maximum_area_ratio':max(ratios),'nonzero_uv_faces':sum(r>1e-6 for r in ratios)}
    assert set(result['masses'])=={'corner','shaft','court'}
    assert all(v['triangles']==v['nonzero_uv_faces'] for v in result['masses'].values())
    return result


def board(mesh,report,dest):
    image=Image.new('RGB',(1400,928),'#f4f0e8')
    pen=ImageDraw.Draw(image)
    def label(x,y,txt,sz,bold=False):
        name='Bold' if bold else 'Regular'
        f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+name+'.ttc',sz,index=2)
        pen.text((x,y),txt,font=f,fill='#342f2b')
    label(35,13,'公济医院后勤楼的屋顶与檐口',36,True)
    label(38,70,'天潼路、乍浦路街角　｜　北面与院侧两张 2020 年公开照片的原模型投影',21)
    sun=np.array([-.54,-.40,.74],dtype=np.float32)
    sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    rendered=[]
    with tempfile.TemporaryDirectory() as tmp:
        lib=load_raster(tmp)
        for cam,crop,(x,y,ww,hh),title in [
              (street,[195,-7,721,232],(38,114,820,373),'Street cornice'),
              (court,[132,-3,655,148],(38,550,820,237),'Courtyard and recessed roof room')]:
            P=cam.K@np.column_stack([cam.R,-cam.R@cam.eye])
            view,stats=raster(mesh,lib,ww,P,crop,sun,angles)
            image.paste(view.resize((ww,hh),Image.Resampling.LANCZOS),(x,y))
            rendered.append(dict(view=title,crop=crop,stats=stats))
        for eye,look,xy,title in [
              ([-1.4,-5.2,22.2],[1.15,-.08,23.4],(891,135),'Projected brackets'),
              ([10.,-3.1,23.96],[10.4,.05,24.34],(891,500),'Pierced stone balustrade')]:
            iw,ih=460,248
            # Keep the entire building in front of the camera, also for
            # the low street-facing section. The longer lens retains the crop.
            eye=np.asarray(look)+4.5*(np.asarray(eye)-np.asarray(look))
            P=perspective(eye,look,iw,ih,372*4.5)
            view,stats=raster(mesh,lib,iw,P,[0,0,iw,ih],sun,angles)
            image.paste(view.resize((iw,ih),Image.Resampling.LANCZOS),xy)
            rendered.append(dict(view=title,stats=stats))
    label(38,487,'街角的厚石檐、红砖角部高体与有两重石束带的方形竖体。',19)
    label(891,389,'檐下石牛腿的前头与逐级收细的下部。',17)
    label(891,752,'瓶栏逐根成形，凹腰与上、下石栏座分开。',17)
    label(38,800,'院侧仍见开敞的石瓶栏和屋上带方窗的砖房。三面被遮的屋面进深据可见边缘估算。',18)
    label(38,862,'测读依据　乔争月（2020）与戴走军（2020）。图中只绘本模型，未转载原照。',17)
    image.save(dest,quality=90,subsampling=0)
    return rendered


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mesh',type=Path);p.add_argument('report',type=Path);p.add_argument('--board',type=Path)
    a=p.parse_args()
    obs=json.loads((HERE/'roof-photo-observations.json').read_bytes())
    scene=SerialScene(a.mesh)
    photo=camera_probes(scene,obs);physical=section_probes(scene)
    counts={}
    for view in CAMS:
        hits=[p for p in photo if p['view']==view]
        counts[view]=[sum(int(p['match']) for p in hits),len(hits)]
    counts['component_sections']=[sum(int(p['match']) for p in physical),len(physical)]
    result=dict(asset=scene.asset,counts=counts,photo_pixels=photo,physical_sections=physical,
                notes='The image probes are fixed readings from the original photographs. The 3D section samples measure the constructed geometry independently of the camera fit. Unresolved photograph samples are retained.')
    result['roof_brick_uv']=raised_brick_uv(a.mesh)
    if a.board:result['views']=board(a.mesh,result,a.board)
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print(result['asset']['sha256'],counts)
