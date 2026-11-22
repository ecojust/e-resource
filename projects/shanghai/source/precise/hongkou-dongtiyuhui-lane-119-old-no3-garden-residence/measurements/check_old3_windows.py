"""Check unfiltered first surfaces for the photographed sashes, door and twisted columns."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'source'
sys.path[:0]=[str(SRC),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from old3_windows import BRASS, CASE, DARK, EDGE, IRON, PANEL, SKY, STONE, TREE, WOOD

def read(path):
    return json.loads(path.read_bytes())

def calculate(path):
    scene=SerialScene(path)
    front=read(SRC/'front-layout.json')
    ret=read(SRC/'return-layout.json')
    dep=ret['depth']
    faces={'front':front,**ret['faces']}
    mesh=[];photo=[]
    def cast(origin,direction,expected,meta,end):
        hit=scene.ray(origin,direction,end)
        mat=hit['material'] if hit else None
        return {**meta,'expected':expected,'first':mat,'hit_m':np.round(hit['point_enu_m'],4).tolist() if hit else None,'triangle':hit['triangle_index'] if hit else None,'matched':mat in expected}
    def model(face,u,v,z):
        if face=='front':return np.array([u,v,z])
        if face=='lane':return np.array([v,u,z])
        return np.array([u,dep-v,z])
    def normal_ray(face,item,u,z,expected,name):
        eye=model(face,u,-1.15,z)
        mesh.append(cast(eye,model(face,u,0,z)-eye,[expected],{'face':face,'piece':item,'feature':name,'u':round(u,4),'z':round(z,4)},2.))
    for face,data in faces.items():
        for o in data['openings']:
            c,w,lo,hi=[o[k]for k in ('center','width','sill','head')]
            k=o['kind'];rounded=k in ('arch','door');rim=w*(.043 if rounded else .049)
            def add(u,z,mat,label):
                normal_ray(face,o['id'],u,z,mat,label)
            add(c-w/2+rim/2,lo+.81*(hi-lo),CASE,'fixed outer jamb') if not rounded else add(c-w/2+rim/2,lo+.77*(o['spring']-lo),CASE,'fixed outer jamb')
            if not rounded:
                bottom=lo+rim+(.32*(hi-lo-2*rim)if k=='balcony'else 0)+.044*w
                top=hi-rim-.044*w
                n=o.get('lights_per_leaf',3)
                for j in range(n):
                    z=bottom+(j+.49)*(top-bottom)/n
                    for sign in (-1,1):add(c+w*sign*.25,z,SKY if k=='balcony'else TREE,f'leaf {sign:+} light {j+1}')
                for j in range(1,n):add(c-w*.26,bottom+j*(top-bottom)/n,WOOD,f'horizontal bar {j}')
                add(c,(top+bottom)/2,WOOD,'meeting stile')
                if k=='balcony':
                    for sign in (-1,1):add(c+sign*w*.24,lo+(hi-lo)*.19,PANEL,f'lower panel {sign:+}')
                continue
            spring=o['spring'];rise=hi-spring
            add(c+w*.22,spring+.28*rise,DARK,'fanlight clear segment')
            add(c,spring+.68*rise,WOOD,'vertical fanlight spoke')
            add(c+w*.24,spring,WOOD,'transom')
            if k=='arch':
                gw=w-2*rim
                for i in (1,2,4,5):
                    add(c-gw/2+i*gw/6,lo+rim+(spring-lo-rim)*.36,IRON,f'grille upright {i}')
                for j,level in enumerate((.11,.51,.88)):
                    add(c+.21*gw,lo+rim+level*(spring-lo-rim),IRON,f'grille horizontal {j+1}')
                add(c+.231*gw,lo+rim+(spring-lo-rim)*.255,TREE,'glass through ironwork')
            else:
                g=.075*w;pw=(w-2*rim-3*g)/2;ph=(spring-lo-rim-5*g)/4
                for j in range(4):
                    for i in range(2):
                        x=c-w/2+rim+g+(pw+g)*i;z=lo+rim+g+(ph+g)*j
                        add(x+.5*pw,z+.5*ph,PANEL,f'panel field {j+1}.{i+1}')
                        add(x+.012*w,z+.5*ph,WOOD,f'panel surround {j+1}.{i+1}')
                add(c-.33*w,lo+rim+.47*(spring-lo-rim),BRASS,'handle')
        for o in data['columns']:
            lo,hi,c=o['sill'],o['head'],o['center']
            for j,f in enumerate((.13,.26,.39,.53,.67,.79,.87)):
                normal_ray(face,o['id'],c,lo+f*(hi-lo),STONE,f'visible spiral {j+1}')
            normal_ray(face,o['id'],c,hi-.028*o['width'],EDGE,'top moulding')
    cameras=read(HERE/'registered-courtyard-cameras.json')['cameras']
    p2=np.array(cameras['front-b']['P']);p2[:2]*=950/cameras['front-b']['working_size'][1]
    returns=read(HERE/'lane-and-rear-cameras.json')['sources']
    p4=np.array(returns['04']['P'])
    p5=np.array(returns['05']['P'])
    p5[:2]*=950/returns['05']['working_height']
    # Independent reads at visible points on the dated exposures, in 950-pixel working images.
    samples={'02':(p2,[(141,353,SKY),(164,381,SKY),(220,350,SKY),(245,375,SKY),(185,373,STONE),(187,342,STONE),
        (385,336,TREE),(413,350,TREE),(387,382,TREE),(415,381,TREE),(399,358,WOOD),
        (180,625,STONE),(222,539,DARK),(212,549,DARK),(236,550,DARK),(392,551,DARK),(425,551,DARK),
        (393,673,PANEL),(424,674,PANEL),(393,705,PANEL),(427,705,PANEL)]),
      '04':(p4,[(124,645,STONE),(122,679,STONE),(119,720,STONE),(411,655,STONE),(412,692,STONE),(412,727,STONE),
        (82,589,DARK),(170,578,DARK),(376,585,DARK),(441,599,DARK),(529,616,DARK),
        (337,343,TREE),(355,359,TREE),(346,348,WOOD),(448,351,TREE)]),
      '05':(p5,[(125,599,DARK),(140,596,DARK),(134,621,STONE),(134,642,STONE)])}
    for camera,(p,s)in samples.items():
        for u,v,mat in s:
            eye=-np.linalg.solve(p[:,:3],p[:,3]); direction=np.linalg.solve(p[:,:3],[u,v,1])
            photo.append(cast(eye,direction,[mat],{'photo':camera,'uv_working':[u,v],'uv_native':np.round(np.array([u,v])*4912/950,1).tolist()},40))
    # Retain the first interpretation. Re-read these unaltered coordinates on native crops.
    shaded_wall='Old No 3 | grey groove shadow'
    reread={
        ('04',82,589):([shaded_wall,CASE],'Touches the outside of the dark sash where the grey arch reveal meets it.'),
        ('04',170,578):([WOOD,DARK],'The oblique edge follows a narrow radial wood bar on its left.'),
        ('04',376,585):([WOOD],'This is a dark radial glazing bar, visible diagonally across the centre.'),
        ('04',441,599):([CASE,WOOD],'The sampled dark brown band is the outer sash frame.'),
        ('04',529,616):([shaded_wall,CASE],'A reveal/outer frame transition in the strongly oblique opening.'),
        ('05',125,599):([shaded_wall],'Shaded plaster soffit above the short twisted column.'),
        ('05',140,596):([shaded_wall,CASE],'Shaded reveal immediately inside the thin brown jamb edge.')}
    for r in photo:
        notes=reread.get((r['photo'],*r['uv_working']))
        if notes:
            r['native_crop_reread']=notes[1]
            r['reread_materials']=notes[0]
        r['matched_after_reread']=r['first'] in r.get('reread_materials',r['expected'])
    for r in mesh:
        if r['piece']=='courtyard upper twisted shaft' and r['feature']=='visible spiral 2' and r['first']=='Garden balcony | red oxide iron':
            r['visible_occluder']='The garden balcony railing crosses this part of the upper column.'
        if r['piece']=='lane twin arch towards rear' and r['feature']=='fixed outer jamb' and r['first']==STONE:
            r['visible_occluder']='The outer jamb meets the twisted stone column shared by these two arches.'
        r['matched_with_photographed_foreground']=r['matched'] or 'visible_occluder' in r
    return {'asset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'plan_sha256':{n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['return-layout.json','front-layout.json','old3_windows.py']},'mesh_samples':len(mesh),'mesh_matches':sum(x['matched']for x in mesh),'photo_samples':len(photo),'photo_matches':sum(x['matched']for x in photo),'photo_matches_after_native_reread':sum(x['matched_after_reread']for x in photo),'mesh_matches_with_foreground':sum(x['matched_with_photographed_foreground']for x in mesh),'mesh':mesh,'photos':photo}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('scene',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    out=calculate(a.scene);raw=json.dumps(out,ensure_ascii=False,separators=(',',':')).encode()+b'\n'
    a.output.write_bytes(gzip.compress(raw,mtime=0)if a.output.suffix=='.gz'else raw)
    print(out['asset_sha256'],out['mesh_matches'],out['mesh_samples'],out['photo_matches'],out['photo_samples'])
