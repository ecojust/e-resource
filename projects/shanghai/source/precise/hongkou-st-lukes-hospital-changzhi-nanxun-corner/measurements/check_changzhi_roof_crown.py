"""Check the submitted roof mesh against source photographs and perpendicular section rays."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE.parent/'source'),
              str(ROOT/'xuhui-pathe-records-office/measurements/city-contact'),
              str(ROOT/'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements')]
from changzhi_roof_crown import CAP, PANE, PLASTER, REVEAL, SASH, SOFFIT, face_basis
from glb_triangles import SerialScene
from render_riverfront_survey import load_raster, raster

CLASSES={'sky':{None},'pediment':{PLASTER},'drum':{PLASTER},'rake':{CAP,SOFFIT},
         'sash':{PANE,SASH,REVEAL},'oculus':{PANE,SASH,REVEAL,CAP},'coping':{CAP,SOFFIT}}

def photo_rays(scene,records):
    rows=[]
    for view,source in records['views'].items():
        eye=np.array(source['eye']); inv=np.array(source['R']).T@np.linalg.inv(source['K'])
        for feature,pixels in source['probes'].items():
            for u,v in pixels:
                ray=inv@[u,v,1.]
                hit=scene.ray(eye,ray,100)
                material=hit['material'] if hit else None
                rows.append(dict(view=view,feature=feature,pixel=[u,v],match=material in CLASSES[feature],first=hit))
    return rows

def physical_sections(scene,layout,config):
    rows=[]
    def cast(name,point,out,s,z,expected):
        eye=point(s,z,.85)
        hit=scene.ray(eye,[-out[0],-out[1],0],1.6)
        rows.append(dict(feature=name,origin=eye,axis=[-out[0],-out[1],0],
                         expected=expected,first=hit,match=bool(hit and hit['material']==expected)))
    face=next(f for f in layout['faces'] if f['id']=='changzhi')
    _,pt=face_basis(face)
    g=config['gable'];x,z,r=g['oculus']
    for angle in np.linspace(0,2*np.pi,12,endpoint=False):
        for name,rad,mat in [('oculus glazing',.74*r,PANE),('recessed circular frame',r-.037,SASH),
                             ('pale stone edge',r+.015,CAP),('perforated tympanum',r+.115,PLASTER)]:
            xx=x+rad*np.cos(angle);zz=z+rad*np.sin(angle)
            if name=='perforated tympanum' and abs(xx-x)<.15 and zz>z+r:continue
            cast(name,pt,face['out'],xx,zz,mat)
    t=config['lantern'];outline=t['face_vertices']+t['roofward_vertices']
    for i,(a,b) in enumerate(zip(outline,outline[1:]+outline[:1])):
        delta=np.subtract(b,a);length=np.linalg.norm(delta);normal=[delta[1]/length,-delta[0]/length]
        _,pt=face_basis({'a':a,'b':b,'out':normal})
        cast('facet %d below head'%(i+1),pt,normal,.31*length,t['head_z']-.24,PLASTER)
        cast('facet %d top cap'%(i+1),pt,normal,.42*length,t['head_z']+.07,CAP)
        if i not in (0,2):continue
        id=('corner-changzhi' if i==0 else 'corner-nanxun')
        u,v,lo,hi=t['openings'][id];x0=u*length;x1=v*length
        for fracx in (.27,.74):
            for fracz in (.18,.5,.81):
                cast(id+' glass',pt,normal,x0+(x1-x0)*fracx,lo+(hi-lo)*fracz,PANE)
        for ss in (x0+.025,x1-.025):cast(id+' upright',pt,normal,ss,(lo+hi)/2,SASH)
        cast(id+' projecting sill',pt,normal,(x0+x1)/2,lo-.044,CAP)
        if i==2:
            cast(id+' central bar',pt,normal,(x0+x1)/2,lo+(hi-lo)*.25,SASH)
            for frac in (1/3,2/3):cast(id+' glazing bar',pt,normal,x0+(x1-x0)*.25,lo+(hi-lo)*frac,SASH)
    return rows

def board(mesh,records,path):
    img=Image.new('RGB',(1200,777),'#f5f2e9')
    draw=ImageDraw.Draw(img)
    def txt(pt,s,size,bold=False):
        wt='Bold' if bold else 'Regular'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+wt+'.ttc',size,index=2)
        draw.text(pt,s,font=font,fill='#332e27')
    txt((32,12),'长治路159号的八面塔冠与圆眼山花',34,True)
    txt((34,63),'三组朝街塔面与两处小窗据两张街照，后部折角据三期卫星影像。',20)
    sun=np.array([-.38,-.54,.74]);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    tiles=[('district_2023',[175,-3,564,400],(33,117,559,499)),('toutiao_2021',[156,4,344,165],(618,117,551,472))]
    draws={}
    with tempfile.TemporaryDirectory() as tmp:
        lib=load_raster(tmp)
        for key,box,(x,y,width,height) in tiles:
            rec=records['views'][key];R=np.array(rec['R']);eye=np.array(rec['eye']);P=np.array(rec['K'])@np.column_stack([R,-R@eye])
            a,stats=raster(mesh,lib,width,P,box,sun,angles)
            # Fit the complete camera crop without changing its aspect ratio.
            a.thumbnail((width,height),Image.Resampling.LANCZOS)
            img.paste(a,(x+(width-a.width)//2,y));draws[key]=dict(crop=box,source_image=rec['source_sha256'],render=stats)
    txt((42,624),'虹口区公开照片所见的三角山花、凹入圆眼及塔窗。',18)
    txt((619,624),'从长治路另一侧观察三面灯楼及檐口折线。',18)
    txt((35,697),'左据 2023 年虹口区照片，右据老房子爱好者 2021 年刊图。图板使用交付模型渲染。',17)
    img.save(path,quality=88)
    return draws

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('report',type=Path);p.add_argument('--board',type=Path)
    args=p.parse_args();data=json.loads((HERE/'roof-crown-photo-study.json').read_bytes());geom=json.loads((HERE/'roof-crown-geometry.json').read_bytes())
    layout=json.loads((HERE.parent/'source/street-layout.json').read_bytes())
    scene=SerialScene(args.mesh);photo=photo_rays(scene,data);sections=physical_sections(scene,layout,geom)
    counts={v:[sum(r['match'] for r in photo if r['view']==v),sum(r['view']==v for r in photo)] for v in data['views']}
    counts['component_sections']=[sum(x['match'] for x in sections),len(sections)]
    result=dict(asset=scene.asset,counts=counts,fixed_source_pixels=photo,constructed_sections=sections,
                scope='Photo rays use fixed coordinates in the actual source photographs. Each perpendicular section tests the first material hit. Real model occlusions, including disagreements at edge pixels, are retained.')
    if args.board:result['drawings']=board(args.mesh,data,args.board)
    args.report.parent.mkdir(exist_ok=True,parents=True);args.report.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print(scene.asset['sha256'],counts)
