"""Draw two Chinese plates from the central-sash GLBs and the measured camera matrices.

python render_central_steel_views.py --full windows-full.glb --lod windows-lod.glb --out boards
Requires Python 3, NumPy, Pillow, and Noto Sans/Serif CJK SC or --font-dir.
This program reads only meshes and numerical observations. No panorama bitmap is an input.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
PAPER=(252,249,242); PANEL=(237,233,223); INK='#262d2a'; MUTED='#505e56'; GREEN='#276953'; RUST='#9a5538'; RULE='#b9bbac'
def load_json(p):return json.loads(p.read_bytes())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def read_triangles(path):
    data=path.read_bytes()
    magic,version,n=struct.unpack_from('<4sII',data,0);assert magic==b'glTF' and version==2 and n==len(data)
    length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);buf=memoryview(data)[28+length:]
    def accessor(i):
        acc=doc['accessors'][i];view=doc['bufferViews'][acc['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[acc['componentType']]);dim={'VEC3':3,'SCALAR':1}[acc['type']]
        return np.ndarray((acc['count'],dim),dtype=dtype,buffer=buf,offset=view.get('byteOffset',0)+acc.get('byteOffset',0),strides=(view.get('byteStride',dim*dtype.itemsize),dtype.itemsize))
    tri=[];materials=[]
    for idx in doc['scenes'][doc.get('scene',0)]['nodes']:
        node=doc['nodes'][idx];assert set(node)<=set(('name','mesh'))
        for prim in doc['meshes'][node['mesh']]['primitives']:
            if not doc['materials'][prim['material']]['name'].startswith('JKK central | '):
                continue
            v=accessor(prim['attributes']['POSITION'])[:,[0,2,1]]*[1.,-1.,1.]
            faces=accessor(prim['indices']).reshape(-1,3);tri.extend(v[faces]);materials.extend([prim['material']]*len(faces))
    mats=doc['materials'];rgba=np.array([m['pbrMetallicRoughness'].get('baseColorFactor',[1,1,1,1]) for m in mats])
    blend=np.array([m.get('alphaMode')=='BLEND' for m in mats])
    assert blend.any() and np.all((rgba[blend,3]>0)&(rgba[blend,3]<1))
    return np.array(tri),np.array(materials),rgba,blend

def srgb(x):return np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
def linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def draw_mesh(mesh,camera,rects,size,scope):
    tri,mi,rgba,blend=mesh
    z=tri.mean(axis=1)[:,2]
    if scope!='all':
        _,bottom,_,top=rects[scope]['rect_xz_m'];keep=(z>bottom-.12)&(z<top+.12);tri,mi=tri[keep],mi[keep]
    eye=-np.linalg.solve(camera[:,:3],camera[:,3]);direction=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normal=direction/np.maximum(np.linalg.norm(direction,axis=1)[:,None],1e-12)
    selected=(normal*(eye-tri.mean(axis=1))).sum(axis=1)>0
    tri,mi,normal=tri[selected],mi[selected],normal[selected]
    v=tri@camera[:,:3].T+camera[:,3];assert (v[:,:,2]>0).all()
    xy=v[:,:,:2]/v[:,:,2,None];flat=xy.reshape(-1,2);lo=flat.min(axis=0);hi=flat.max(axis=0)
    w,h=size;scale=.925*min(w/(hi[0]-lo[0]),h/(hi[1]-lo[1]))
    xy=(xy-(hi+lo)/2)*scale+[w/2,h/2];inv=1/v[:,:,2]
    background=linear(np.array(PANEL)/255);canvas=np.full((h,w,3),background,dtype=np.float32)
    depth=np.full((h,w),-np.inf);touched=np.zeros((h,w),bool);through=np.zeros_like(touched)
    sun=np.array([-.26,-.67,.69]);sun/=np.linalg.norm(sun);light=.72+.38*np.maximum(0,normal@sun)
    colors=rgba[mi,:3]*light[:,None]
    # Close opaque geometry first. Blended glass is drawn from far to near with
    # depth testing against its opaque frames and its true glTF alpha in linear light.
    order=np.r_[np.flatnonzero(~blend[mi]),np.flatnonzero(blend[mi])[np.argsort(inv[blend[mi]].mean(axis=1))]]
    for i in order:
        pts=xy[i];a,b,c=pts
        x0,y0=np.maximum(0,np.floor(pts.min(axis=0)).astype(int))
        x1,y1=np.minimum([w,h],np.ceil(pts.max(axis=0)).astype(int))
        if x1<=x0 or y1<=y0:continue
        ux,uy=a-c;vx,vy=b-c;den=ux*vy-uy*vx
        if abs(den)<1e-7:continue
        px=np.arange(x0,x1)[None,:]+.5-c[0];py=np.arange(y0,y1)[:,None]+.5-c[1]
        s=(px*vy-py*vx)/den;t=(ux*py-uy*px)/den;l=1-s-t
        area=(s>=0)&(t>=0)&(l>=0)
        dz=inv[i,0]*s+inv[i,1]*t+inv[i,2]*l
        sl=np.s_[y0:y1,x0:x1];zb=depth[sl];mask=area&(dz>zb+1e-9)
        if not mask.any():continue
        out=canvas[sl]
        if blend[mi[i]]:
            mix=rgba[mi[i],3];out[mask]=colors[i]*mix+out[mask]*(1-mix);through[sl][mask]=True
        else:
            out[mask]=colors[i];zb[mask]=dz[mask]
        touched[sl][mask]=True
    im=Image.fromarray(np.rint(np.clip(srgb(canvas),0,1)*255).astype('uint8'))
    assert touched.sum()>300
    return im,{'camera_eye_m':eye.tolist(),'original_pixel_bounds':[lo.tolist(),hi.tolist()],'painted_pixels':int(touched.sum()),'glass_blended_pixels':int(through.sum()),'triangle_faces_considered':len(tri)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('full','lod','out'):parser.add_argument('--'+flag,type=Path,required=True)
    parser.add_argument('--font-dir',type=Path,default=Path('/usr/share/fonts/opentype/noto'))
    opt=parser.parse_args();opt.out.mkdir(exist_ok=True,parents=True)
    @lru_cache(None)
    def font(size,weight='regular'):
        family='NotoSerifCJK' if weight=='title' else 'NotoSansCJK'
        style='Bold' if weight in ('bold','title') else 'Regular'
        return ImageFont.truetype(str(opt.font_dir/f'{family}-{style}.ttc'),size,index=2)
    def label(d,xy,msg,size=22,color=INK,weight='regular',anchor='la'):
        d.text(xy,msg,font=font(size,weight),fill=color,anchor=anchor)
    def rule(d,x0,x1,y):d.line((x0,y,x1,y),fill=RULE,width=2)
    def stock(title,subtitle):
        img=Image.new('RGB',(1440,1024),PAPER);d=ImageDraw.Draw(img)
        label(d,(58,34),'长乐路962弄1—4号  /  J.K.K. 公寓',23,GREEN,'bold')
        label(d,(55,69),title,52,INK,'title');label(d,(58,148),subtitle,22,MUTED)
        rule(d,58,1382,204);return img,d
    def foot(d,text):
        rule(d,58,1382,939);label(d,(58,956),text,18,MUTED)
    rects_file=HERE/'central-steel-reconstruction.json';rects={r['id']:r for r in load_json(rects_file)['openings']}
    cameras_file=HERE/'jkk-street-camera-fit.json';camera=load_json(cameras_file)['camera_matrices']
    models={'full':read_triangles(opt.full),'lod':read_triangles(opt.lod)}
    captures=[]
    def mesh_panel(plate,role,frame,scope,xy,size):
        target=(size[0]*2,size[1]*2);im,info=draw_mesh(models[role],np.array(camera[frame]),rects,target,scope)
        plate.paste(im.resize(size,Image.Resampling.LANCZOS),xy)
        captures.append({'file_role':role,'camera':frame,'scope':scope,'projection':camera[frame],**info})
    p,d=stock('中央凹间的四处钢窗','由街面向北望。为看清钢框，图中单列窗洞及内侧退口。上窗与横亮窗之间原有实墙。')
    mesh_panel(p,'full','centre-stack-20','all',(58,241),(337,646))
    label(d,(58,892),'2020年2月机位  ·  近档全列',20,MUTED)
    cells=[('upper-transom','横亮窗','固定六列两层，位于上窗之上。','centre-upper-20'),('upper-main','上窗','西扇向外打开，面向街侧。','e20-high'),('middle','中窗','东扇外开，中排上亮向外翻。','w20-mid'),('low','下窗','两旁的竖扇外开，中扇留在框内。','centre-lower-20')]
    for i,(tag,name,desc,view) in enumerate(cells):
        x=430+480*(i%2);y=225+354*(i//2)
        left,bottom,right,top=rects[tag]['rect_xz_m']
        label(d,(x,y),name,28,INK,'bold');label(d,(x+438,y+4),f'{right-left:.2f} × {top-bottom:.2f} 米',20,GREEN,anchor='ra')
        mesh_panel(p,'full',view,tag,(x,y+52),(438,213))
        label(d,(x,y+275),desc,21,MUTED)
    foot(d,'尺寸按窗洞外缘估算，比例约有5%—10%误差。图中钢框、透光扇与玻璃均由实际近档网格绘制。')
    p.save(opt.out/'central-steel-measured-views.png',optimize=True)
    p,d=stock('两次记录中的窗扇开合','2015年4月与2020年2月的街面记录。模型采用2020年的可见状态，角度由多机位拟合。')
    label(d,(58,221),'2015年4月',32,INK,'bold');label(d,(727,221),'2020年2月',32,INK,'bold')
    label(d,(58,276),'下窗两侧均有外开扇；中窗东列可辨玻璃格。',22)
    label(d,(58,316),'上窗处被树枝及线缆遮挡，仅能确认窗洞分开。',22)
    label(d,(727,276),'下窗西扇约116°、东扇约123°；中窗东扇约90°。',21)
    label(d,(727,316),'上窗西扇约78°；中窗上亮向外翻约23°。',22)
    rule(d,58,1382,378)
    label(d,(58,399),'下窗俯视开扇示意',28,INK,'bold')
    label(d,(734,399),'中窗在两个街面机位的投影',28,INK,'bold')
    mesh_panel(p,'lod','spr15-mid','middle',(734,462),(309,321))
    mesh_panel(p,'lod','w20-mid','middle',(1057,462),(325,321))
    label(d,(734,793),'2015年4月 · 正面机位',19,MUTED)
    label(d,(1057,793),'2020年2月 · 西侧机位',19,MUTED)
    # View from above, room at top and street below. Orient each symbol from
    # its true hinge towards the free steel stile.
    dr=ImageDraw.Draw(p);ox,oy=174,579
    width=120;dr.line((ox-24,oy,ox+3*width+26,oy),fill=MUTED,width=5)
    for hix in (ox,ox+3*width):
        dr.ellipse((hix-7,oy-7,hix+7,oy+7),fill=GREEN)
    for hinge,sign,angle,text in [(ox,1,rects['low']['lower_leaf_angles_deg'][0],'西扇 116°'),(ox+3*width,-1,rects['low']['lower_leaf_angles_deg'][2],'东扇 123°')]:
        a=math.radians(angle);u=hinge+sign*width*math.cos(a);v=oy+width*math.sin(a)
        dr.line((hinge,oy,u,v),fill=GREEN,width=7)
        arc=[(hinge+sign*46*math.cos(a*t/30),oy+46*math.sin(a*t/30)) for t in range(31)]
        dr.line(arc,fill=RUST,width=3)
        label(dr,(u,v+14),text,21,GREEN,anchor='ma')
    label(dr,(ox+1.5*width,oy-72),'室内侧',19,MUTED,anchor='ma')
    label(dr,(ox+1.5*width,oy-36),'中扇关闭',19,MUTED,anchor='ma')
    label(dr,(ox+1.5*width,oy+152),'街面',20,MUTED,anchor='ma')
    label(dr,(58,848),'平面图按2020年数据绘制，圆点为转轴。',20,MUTED)
    label(dr,(734,848),'两图均显示2020年远档网格及外开扇的透光效果。',20,MUTED)
    foot(d,'2015年4月只记录可辨特征，未为遮挡的窗扇推算角度。2020年两面斜照与正视共同约束开角。')
    p.save(opt.out/'central-steel-opening-states.png',optimize=True)
    result={'source_camera_sha256':digest(cameras_file),'reconstruction_sha256':digest(rects_file),'mesh_sha256':{'full':digest(opt.full),'lod':digest(opt.lod)},'sash_triangles':{k:len(v[0]) for k,v in models.items()},'illustrator_sha256':digest(Path(__file__)),'illustration_inputs':'实际三角网、相机矩阵、测量值和文字观察','views':captures,'images':{f.name:{'bytes':f.stat().st_size,'sha256':digest(f)} for f in sorted(opt.out.glob('central-steel-*.png'))}}
    assert all(q['glass_blended_pixels']>0 for q in captures if q['scope']!='upper-transom')
    (opt.out/'central-steel-boards.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
