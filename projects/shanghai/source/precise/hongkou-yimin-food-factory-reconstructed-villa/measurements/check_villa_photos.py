"""Measure the closest GLB surface at photo coordinates and render the model from the observed cameras."""
from pathlib import Path
import argparse,hashlib,json,math,sys,tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(HERE.parents[1]/'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'))
from glb_triangles import load_triangles
from render_riverfront_survey import load_raster,raster
sources=json.loads((HERE/'independent-wall-pixels.json').read_bytes())
observed=json.loads((HERE/'villa-three-cameras.json').read_bytes())
expected={'brick':['running-bond red brick'],'arch':['radial brick','arch lime mortar'],'glass':['window glass','pale glazing','dark stained frame'],
 'oriel_sill':['warm grey concrete','smooth grey sill'],'lintel':['smooth grey sill'],'landing':['entrance paving','warm grey concrete'],
 'plinth':['warm grey concrete'],'lower_door':['window glass','pale glazing','dark stained frame','portico smoked door glass','interior shadow']}
def check(mesh):
    tris,mat_id,mats,sha=load_triangles(mesh);a=tris[:,0];e=tris[:,1]-a;f=tris[:,2]-a
    result=[]
    for row in observed['cameras']:
        P=np.asarray(row['P']);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3];q=eye-a;cr=np.cross(q,e);dot=np.einsum('ij,ij->i',cr,f)
        for family,points in sources[row['source']].items():
            for uv in points:
                d=inv@[*uv,1];d/=np.linalg.norm(d);h=np.cross(d,f);det=np.einsum('ij,ij->i',e,h);ok=abs(det)>1.e-10
                ds=np.where(ok,det,1.);u=np.einsum('ij,ij->i',q,h)/ds;v=cr@d/ds;t=dot/ds
                ids=np.where(ok&(u>=0)&(v>=0)&(u+v<=1)&(t>.001))[0]
                label=None if not len(ids) else mats[mat_id[ids[np.argmin(t[ids])]]]
                result.append(dict(source=row['source'],pixel=uv,expected=family,first_material=label,match=bool(label and any(s in label for s in expected[family]))))
    return dict(asset_sha256=sha,triangles=len(tris),source_observations_sha256=hashlib.sha256((HERE/'independent-wall-pixels.json').read_bytes()).hexdigest(),photo_pixels_embedded=False,rays=result,counts={k:dict(test=sum(y['source']==k for y in result),first_hits=sum(y['source']==k and y['match']for y in result))for k in sources})
def board(mesh,path):
    out=Image.new('RGB',(1420,1030),'#f2eee5');draw=ImageDraw.Draw(out)
    def label(x,y,text,size,bold=False):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc',size,index=2)
        draw.text((x,y),text,fill='#263d3d',font=font)
    label(46,24,'香烟桥路13号 · 复建西班牙式小楼',39,True)
    label(47,90,'原楼1937年动工，1940年竣工，1985年拆除。展馆院内的小楼按原貌缩小并易地复建。',20)
    sun=np.array([-.48,-.67,.61],dtype=np.float32);sun/=np.linalg.norm(sun);ang=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))];stats={}
    frames=[('district2018',[0,0,944,649],(40,148),(820,564)),('visitor',[38,124,1070,719],(902,148),(468,270)),
            ('district2018',[348,382,649,554],(902,475),(468,267)),('tourism2023',[21,61,595,332],(46,755),(463,218))]
    with tempfile.TemporaryDirectory()as tmp:
        native=load_raster(tmp)
        for j,(station,crop,xy,wh) in enumerate(frames):
            P=np.array(next(v['P'] for v in observed['cameras']if v['source']==station))
            image,stat=raster(mesh,native,wh[0]*2,P,crop,sun,ang)
            image.thumbnail(wh,Image.Resampling.LANCZOS);out.paste(image,xy);stats[str(j+1)]=stat
    label(42,712,'虹口区2018年图 · 两端砖山墙与三券廊',20)
    label(902,420,'游客低角度 · 左侧窗列与屋顶',19)
    label(902,745,'券下的凹进门扇与地面',19)
    label(549,812,'旅游部门2023年图 · 院内正面',21,True)
    label(549,858,'三个视角均由成品模型按照照片机位渲染。',18)
    label(549,902,'图中尺度以中券净宽1.75米估算，未见原建施工尺寸。',18)
    out.save(path,quality=90,subsampling=0)
    return dict(photo_pixels_embedded=False,views=stats,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
if __name__=='__main__':
    arg=argparse.ArgumentParser(description=__doc__);arg.add_argument('model',type=Path);arg.add_argument('result',type=Path);arg.add_argument('--board',type=Path);a=arg.parse_args()
    r=check(a.model)
    if a.board:r['board']=board(a.model,a.board)
    a.result.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print(r['counts'])
