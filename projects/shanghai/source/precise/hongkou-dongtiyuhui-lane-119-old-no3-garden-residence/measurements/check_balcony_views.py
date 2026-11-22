"""Compare the measured iron and the open spaces against the nearest actual GLB surface."""
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
CASES=HERE.parents[1]
sys.path.insert(0,str(CASES/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(CASES/'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'))
from glb_triangles import load_triangles
from render_riverfront_survey import load_raster,raster,perspective

def read(path):return json.loads(path.read_bytes())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def projected(P,xyz):
    p=np.atleast_2d(xyz)@P[:,:3].T+P[:,3]
    return p[:,:2]/p[:,2,None]

def homography(source,target):
    rows=[];values=[]
    for (x,y),(u,v) in zip(source,target,strict=True):
        rows.extend(([x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]))
        values.extend((u,v))
    return np.r_[np.linalg.solve(rows,values),1.].reshape(3,3)

def panel_camera(plate,p,geometry):
    corners=np.array([[x,geometry['railing_front_y'],z] for x,z in [
        (geometry['left_x'],geometry['top_z']),(geometry['right_x'],geometry['top_z']),
        (geometry['right_x'],geometry['base_z']),(geometry['left_x'],geometry['base_z'])]])
    target=plate['panel_rectification_native_uv']
    # Preserve camera centre and every 3-D occluder, recording a second, local four-corner image registration.
    return homography(projected(p,corners),target)@p

def observe(mesh):
    pts=read(HERE/'balcony-photographic-pixels.json')
    registered=read(HERE/'registered-courtyard-cameras.json')['cameras']
    tris,idx,materials,signature=load_triangles(mesh)
    n=len(tris);a=tris[:,0];e=tris[:,1]-a;f=tris[:,2]-a
    results={}
    for key,row in pts['views'].items():
        source=registered[key];P=np.array(source['P'])
        P[:2]*=max(row['native_size'])/max(source['working_size'])
        each={}
        for mode,camera in [('whole_facade',P),('four_corner_panel',panel_camera(row,P,pts['dimension_basis_m']))]:
            inv=np.linalg.inv(camera[:,:3]);eye=-inv@camera[:,3];q=eye-a
            cr=np.cross(q,e);dot=np.einsum('ij,ij->i',cr,f)
            triangles=projected(camera,tris.reshape(-1,3)).reshape(n,3,2)
            low=triangles.min(axis=1);high=triangles.max(axis=1)
            def first(uv):
                u,v=uv
                mask=np.flatnonzero((low[:,0]<=u)&(high[:,0]>=u)&(low[:,1]<=v)&(high[:,1]>=v))
                if len(mask)==0:return None
                direction=inv@[u,v,1];direction/=np.linalg.norm(direction)
                h=np.cross(direction,f[mask]);det=np.einsum('ij,ij->i',e[mask],h);ok=abs(det)>1e-10
                div=np.where(ok,det,1.);x=np.einsum('ij,ij->i',q[mask],h)/div;y=cr[mask]@direction/div;t=dot[mask]/div
                hit=np.flatnonzero(ok&(x>=0)&(y>=0)&(x+y<=1)&(t>.0001))
                return None if len(hit)==0 else materials[idx[mask[hit[np.argmin(t[hit])]]]]
            records=[]
            for mark in row['points']:
                pos=np.array(mark['native_uv']);material=first(pos);exp=mark['expect']
                def agrees(m):
                    rail=bool(m and m.startswith('Garden balcony |') and 'cement' not in m)
                    if exp=='opening':return not rail
                    if exp=='crest':return rail and 'handrail' in m
                    return rail
                ok=agrees(material);distance=0. if ok else None
                # Eight rays per radius, up to 2.5 pixels in the 910-wide working photograph.
                if not ok:
                    for pixels in (.5,1,1.5,2,2.5):
                        radius=pixels*max(row['native_size'])/910
                        if any(agrees(first(pos+radius*np.array([np.cos(t),np.sin(t)])))for t in np.arange(8)*np.pi/4):
                            distance=pixels;break
                records.append(dict(part=mark['part'],native_uv=pos.tolist(),expected=exp,first_material=material,
                                    centre_match=bool(ok),nearest_910px_radius=distance))
            each[mode]=dict(points=len(records),centre=sum(x['centre_match']for x in records),
                            within_2_5px=sum(x['nearest_910px_radius'] is not None for x in records),records=records)
        results[key]=each
    return dict(mesh=signature,triangles=n,camera_file_sha256=digest(HERE/'registered-courtyard-cameras.json'),
                point_file_sha256=digest(HERE/'balcony-photographic-pixels.json'),views=results)

def plate(mesh,output):
    data=read(HERE/'registered-courtyard-cameras.json')['cameras']
    board=Image.new('RGB',(1420,920),'#f7f4ed');d=ImageDraw.Draw(board)
    def label(x,y,text,size,bold=False):
        f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size,index=2)
        d.text((x,y),text,font=f,fill='#322e29')
    label(34,19,'旧3号花园住宅 · 庭面阳台铁栏',36,True)
    label(36,79,'两张2015年照片定出正面七格卷草、通透小菱形及栏顶。',20)
    A=data['front-a'];B=data['front-b'];sun=np.array([-.35,-.71,.61]);sun/=np.linalg.norm(sun)
    windows=[('front-a',[238,218,443,321],(36,136),740),('front-b',[38,284,216,354],(819,136),564)]
    with tempfile.TemporaryDirectory() as temp:
        lib=load_raster(temp);stats=[]
        for name,crop,at,width in windows:
            P=np.array(data[name]['P'])
            im,stat=raster(mesh,lib,width*2,P,crop,sun,(0,0))
            im=im.resize((width,round(im.height/2)),Image.Resampling.LANCZOS);board.paste(im,at)
            stats.append(stat)
        cam=perspective([6.4,-4.3,5.8],[2.83,-.43,4.40],750,400,600)
        im,stat=raster(mesh,lib,1040,cam,[145,89,609,311],sun,(0,0));im=im.resize((686,329),Image.Resampling.LANCZOS);board.paste(im,(36,546));stats.append(stat)
    label(36,510,'2015年横幅机位 · 两端水泥托座托住板底',19,True)
    label(818,382,'2015年竖幅机位 · 正栏与右回栏',19,True)
    label(799,550,'可辨的铁件',26,True)
    for j,t in enumerate(['圆弧冠盖下另有一道红色横杆。','七个立向卷草各有成对的弯折和小卷头。','两格间的窄立杆设透空小菱形。','右回栏的折角条、横杆和立柱可从两站对照。','左回栏可见一组卷草，其余部分有植物遮挡。']):
        label(800,611+42*j,t,17)
    label(35,877,'斜上方模型视角。三幅图均由成品模型生成。',17)
    board.save(output,quality=91,subsampling=0)
    return dict(sha256=digest(output),source_pixels_embedded=False,model_views=stats)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('out',type=Path)
    parser.add_argument('--board',type=Path);args=parser.parse_args()
    report=observe(args.mesh)
    if args.board:report['board']=plate(args.mesh,args.board)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print({k:{s:(v['centre'],v['within_2_5px'],v['points']) for s,v in row.items()} for k,row in report['views'].items()})
