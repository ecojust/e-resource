"""Recast fixed photo pixels and section rays on the actual release meshes."""
from pathlib import Path
import sys, json, math, argparse, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),str(HERE.parents[1]/'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements')]
import gongyi_frontage as f
from glb_triangles import SerialScene
from render_riverfront_survey import perspective,raster,load_raster

def cast(scene,origin,direction,length):return scene.ray(origin,direction,length)
def sections(scene):
 rows=[]
 def mark(name,origin,direction,allowed,length=3.):
  hit=cast(scene,origin,direction,length);rows.append({'element':name,'origin':origin,'direction':direction,'allowed':allowed,'first':hit,'match':bool(hit and hit['material'] in allowed)})
 u=lambda u:(u-162)*f.N/497;z=lambda v:(410.8-v)*f.N/497
 for level,base,top in [('L2',z(269.9)+.038,z(189)),('L3',z(144.3)+.038,z(70))]:
  for j,(a,c) in enumerate(f.DATA['north_photo']['leaf_u_intervals']):
   a=u(a);c=u(c);lab=f'North {level} door {j+1}'
   for q in [.14,.62,.85]:
    mark(lab+' glazed leaf',[a+(c-a)*q,.56,base+(top-base)*.60],[0,1,0],[f.GLASS,f.BLUE])
   mark(lab+' clear jamb',[a+.021,.56,base+(top-base)*.50],[0,1,0],[f.TIMBER])
   mark(lab+' stone side',[a-.09,.56,base+(top-base)*.60],[0,1,0],[f.STONE])
   mark(lab+' raised panel',[a+(c-a)*.36,.56,base+(top-base)*.155],[0,1,0],[f.TIMBER])
  for j,(a,c) in enumerate(zip([u(n) for n in (162,327,491)],[u(n) for n in (327,491,659)])):
   xx=(a+c)*.5;mark('Balcony handrail '+level,[xx,-.7,base-.038+1.060],[0,1,0],[f.LIGHTSTONE])
   xx=a+.7;mark('Gallery real cantilever '+level,[xx,.70,base+.32],[0,0,-1],[f.SHADE])
   xx=(a+c)*.5;mark('Cast iron centre wheel '+level,[xx,-.58,base-.038+.11+.56*(1.035-.11)],[0,1,0],[f.WROUGHT])
 g=[-f.S+(v-42)/447*f.S for v in [42,199,298,395,489]]
 widths=[[(.08,.245),(.37,.535),(.67,.835)],[(.13,.34),(.57,.78)],[(.17,.36),(.61,.80)],[(.16,.37),(.57,.78)]]
 for i,(a,c) in enumerate(zip(g,g[1:])):
  for lev,lo,hi in [('L2',5.18,7.30),('L3',9.02,11.09)]:
   for j,(l,r) in enumerate(widths[i]):
    s=a+(c-a)*l;end=a+(c-a)*r;name=f'South bay {i+1} {lev} window {j+1}'
    mark(name+' glazing',[s+.31*(end-s),-.34,lo+.29*(hi-lo)],[0,1,0],[f.GLASS,f.BLUE])
    mark(name+' meeting bar',[(s+end)/2,-.34,lo+.31*(hi-lo)],[0,1,0],[f.METAL])
   if i!=2:
    x=a+(c-a)*( (widths[i][0][1]+widths[i][1][0])/2 );mark('South buff window field',[x,-.34,lo+.66],[0,1,0],[f.LIGHT])
  mark('South shop glass',[a+.31*(c-a),-.70,1.6],[0,1,0],[f.SHOP])
 for x in [-20,-13,-8,-2]:
  for y in [2.8,9.4]:mark('South pitched roof',[x,y,16.5],[0,0,-1],[f.TILE],6.)
 for x in [2.8,8.0,12.1]:
  mark('North flat roof',[x,11.3,16.5],[0,0,-1],[f.COPING],8.)
 for x in [2.1,7.1,13.4]:
  mark('North shop glass',[x,-.6,1.71],[0,1,0],[f.SHOP])
 for y in [2.0,6.5,10.4]:
  for z0 in [5.9,9.5]:mark('North end inset brick panel',[f.N+.65,y,z0],[-1,0,0],[f.COURSE])
 for x in [3.0,7.0,11.0]:mark('Roof streetward glazed screen',[x,.88,z(43.5)-.24+.91],[0,1,0],[f.SCREEN],.8)
 return rows
def observed(scene,info):
 results={}
 for key,view in info['views'].items():
  inv=np.linalg.inv(np.array(view['street_plane_xz_to_working_pixels']))
  rows=[]
  for _,label,(u,v) in view['samples']:
   loc=inv@[u,v,1.];x,z=(loc[:2]/loc[2]).tolist()
   back=key=='post-repair-north' and label in ('glass','wood','brick')
   yy=.56 if back else -.60;wanted=[getattr(f,k) for k in info['material_aliases'][label]]
   if key=='northeast-project-view':
    hit=cast(scene,[f.N+.8,x,z],[-1,0,0],3.0);outer=hit
   else:
    hit=cast(scene,[x,yy,z],[0,1,0],4.0);outer=cast(scene,[x,-.60,z],[0,1,0],4.0)
   rows.append(dict(pixel=[u,v],feature=label,sample_plane_prefix_y=yy,point_xz=[x,z],expected_materials=wanted,first_on_sample=hit,outermost=outer,match=bool(hit and hit['material'] in wanted)))
  results[key]={'hits':sum(q['match'] for q in rows),'samples':len(rows),'registration_rms_px':view['control_rms_px'],'rows':rows}
 return results
def board(mesh,target):
 canvas=Image.new('RGB',(1380,1220),'#f6f3ed');d=ImageDraw.Draw(canvas)
 def title(x,y,s,n=21):d.text((x,y),s,font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n,index=2),fill='#302c28')
 title(37,14,'公益坊一号楼 · 四川北路1297–1311号',35)
 title(37,71,'南段的四个店面与北段的三跨连续阳台；正面轮廓与两段屋顶来自不同年份的照片和计划图。',20)
 scene=[('front',(-3.65,-83,9.5),(-3.65,0,7),(1300,410),2100,(40,111)),('wheel',(3.10,-6.3,9.8),(2.73,.15,9.02),(550,300),660,(43,575)),('above',(0,-71,42),(-4.2,4,7),(650,300),1100,(673,575))]
 sun=np.array([-.43,-.54,.81]);sun/=np.linalg.norm(sun);angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
 stats={}
 with tempfile.TemporaryDirectory() as tmp:
  linker=load_raster(tmp)
  for key,eye,look,(nx,ny),fl,xy in scene:
   P=perspective(eye,look,nx,ny,fl);im,st=raster(mesh,linker,nx,P,[0,0,nx,ny],sun,angles);canvas.paste(im,xy);stats[key]=st
 title(45,526,'修缮后街面。左为南段，右为北段；南段两排各九扇窗，北段两层各六樘阳台门。',20)
 title(45,899,'北段三楼 · 中部六辐铁轮与方折卷纹',21);title(677,899,'南段红瓦双坡与北段平顶',21)
 with tempfile.TemporaryDirectory() as tmp:
  linker=load_raster(tmp);P=perspective([45,-24,30],[6,5,8.3],660,232,775);im,st=raster(mesh,linker,660,P,[0,0,660,232],sun,angles);canvas.paste(im,(40,962));stats['north_end']=st
 title(758,998,'从东北角看两层六块嵌砖墙面。',22);title(758,1045,'青绿挡屏和上方格架据天华2024年鸟瞰。',22);title(758,1093,'平台后侧的矮壳体只表示可见外形。',21)
 canvas.save(target,quality=88,optimize=True);return stats
if __name__=='__main__':
 arg=argparse.ArgumentParser(description=__doc__);arg.add_argument('mesh',type=Path);arg.add_argument('output',type=Path);arg.add_argument('--board',type=Path);a=arg.parse_args()
 sc=SerialScene(a.mesh);meta=json.loads((HERE/'independent-image-probes.json').read_bytes())
 sec=sections(sc);obs=observed(sc,meta);data={'asset':sc.asset,'triangle_count':len(sc.mi),'sections':{'hits':sum(q['match'] for q in sec),'samples':len(sec),'rows':sec},'archival_photos':obs}
 if a.board:data['drawings']=board(a.mesh,a.board)
 a.output.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n');print(data['asset']['sha256'],data['sections']['hits'],len(sec),{k:(v['hits'],v['samples'])for k,v in obs.items()})
