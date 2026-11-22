"""Read the first real GLB surface at every pane and at photographic observations."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
S=HERE.parent/'source'
sys.path[:0]=[str(S),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from hall_coordinates import WIDTH,LENGTH,point
from hall_windows import FRAME, LEAF, SEAL, SKY, UPPER, GROUND, DOOR, PULL, WOOD, RAISED_WOOD

END_18={
    'EU1':[(184,327,SKY),(182,343,UPPER),(201,359,UPPER),(183,376,UPPER)],
    'EU2':[(339,332,SKY),(330,349,UPPER),(348,365,UPPER),(330,379,UPPER)],
    'EU3':[(472,338,SKY),(466,352,UPPER),(483,366,UPPER),(467,383,UPPER)],
    'EU4':[(587,357,UPPER),(586,385,UPPER)],
    'EG1':[(202,459,GROUND)],
    'EG2':[(317,477,DOOR),(357,478,DOOR),(321,505,DOOR),(356,528,DOOR)],
    'EG3':[(455,475,DOOR),(489,499,DOOR),(455,524,DOOR)],
    'EG4':[(570,458,GROUND),(587,474,GROUND)]}
END_13={
    'EU1':[(845,758,UPPER),(843,842,UPPER)],
    'EU2':[(988,711,UPPER),(1017,749,UPPER),(986,797,UPPER)],
    'EU3':[(1250,630,SKY),(1233,668,UPPER),(1265,703,UPPER),(1234,764,UPPER)],
    'EU4':[(1508,556,SKY),(1482,620,UPPER),(1520,612,UPPER),(1482,675,UPPER),(1521,714,UPPER)]}
CANAL_18={
    'EU1':[(684,183,SKY),(670,232,UPPER),(693,222,UPPER),(669,277,UPPER),(694,265,UPPER),(669,322,UPPER)],
    'EU2':[(523,257,SKY),(515,291,UPPER),(526,324,UPPER),(514,360,UPPER)],
    'EU3':[(430,329,UPPER),(439,348,UPPER),(431,386,UPPER)]}

def read(path):
    return json.loads(path.read_bytes())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def cameras():
    a=read(HERE/'two-terminal-cameras.json')['views']
    nw=np.array(a[0]['P']);nw[:2]*=2
    # The southeast calibration is expressed in its own front-facing coordinate frame.
    reflect=np.array([[-1.,0,0,WIDTH],[0,-1.,0,LENGTH],[0,0,1,0],[0,0,0,1.]])
    return {'street13':nw,'end18':np.array(a[1]['P'])@reflect,'long18':np.array(read(HERE/'canal-side-camera.json')['P'])}
def audit(path):
    scene=SerialScene(path)
    rows=[]; image=[]
    def ray(origin, vec, length, target, label):
        raw=scene.ray(origin,vec,length)
        return {**label,'expected':target,'first':raw['material'] if raw else None,
                'point':np.round(raw['point_enu_m'],5).tolist() if raw else None,
                'triangle':raw['triangle_index'] if raw else None,'matched':bool(raw and raw['material']==target)}
    for face,openings in read(S/'hall-layout.json')['faces'].items():
        for o in openings:
            c,w,z0,top=(o[k] for k in ('center','width','sill','crown'))
            door=o['kind']=='double-door'; upper=o['level']=='upper'
            h=top-z0
            bulb=DOOR if door else UPPER if upper else GROUND
            arched=SKY if upper else DOOR if door else GROUND
            mid=z0+h*(.838 if door else .795)
            frame=w*(.029 if door else .034);rim=w*(.044 if door else .018)
            low_clear=z0+frame+w*(.046 if door else .024)
            top_clear=mid-w*(.052 if door else .050)/2-rim
            points=[(c,top-.55*(top-mid),arched,'arched light'),(c+.20*w,mid,FRAME,'fixed transom'),
                    (c-w*.014,mid-.10*h,LEAF,'left meeting stile'),(c+w*.014,mid-.10*h,LEAF,'right meeting stile'),
                    (c-.5*w+.48*frame,z0+.21*h,FRAME,'fixed jamb')]
            for side in (-1,1):
                u=c+side*.256*w
                for n,f in enumerate((1/6,.5,5/6)):
                    points.append((u,low_clear+(top_clear-low_clear)*f,bulb,f'leaf {side:+d} pane {n+1}'))
                for n,f in enumerate((1/3,2/3)):
                    points.append((u,low_clear+(top_clear-low_clear)*f,LEAF,f'leaf {side:+d} bar {n+1}'))
                if door:
                    points.append((c+side*.039*w,z0+.348*h,PULL,f'pull {side:+d}'))
            if o['kind']=='street-door':
                points=[(c-.5*w+.018*w,z0+.21*h,FRAME,'fixed wooden-door jamb'),
                        (c+.025*w,z0+.58*h,WOOD,'solid wood at the meeting joint'),
                        (c,z0+.72*h,SEAL,'dark meeting seam')]
                for side in (-1,1):
                    for index,f in enumerate((.20,.485,.76)):
                        points.append((c+side*.235*w,z0+f*h,RAISED_WOOD,f'{side:+d} wooden panel {index+1}'))
                    points.append((c+side*.044*w,z0+.488*h,PULL,f'{side:+d} long return pull'))
            for u,z,expected,feature in points:
                origin=np.array(point(face,u,-1.15,z))
                direction=np.array(point(face,u,0,z))-origin
                rows.append(ray(origin,direction,1.52,expected,dict(face=face,number=o['number'],level=o['level'],feature=feature,u=round(u,5),z=round(z,5))))
    for r in rows:
        if (r['face']=='canal' and r['number']==11 and r['feature'] in
            ('arched light','left meeting stile','right meeting stile') and
            r['first']=='Yimin canteen | painted iron rainwater pipe' and
            -0.30<r['point'][0]<-0.10):
            r['visible_occluder']='Documented downpipe in front of canal axis 11, also seen in district image 05.'
            r['matched_including_measured_occlusion']=True
        else:
            r['matched_including_measured_occlusion']=r['matched']
    for key,samples in [('end18',END_18),('long18',CANAL_18),('street13',END_13)]:
        p=cameras()[key];origin=-np.linalg.solve(p[:,:3],p[:,3])
        for bay,ss in samples.items():
            for u,v,target in ss:
                direction=np.linalg.solve(p[:,:3],[u,v,1.])
                image.append(ray(origin,direction,130.,target,dict(view=key,bay=bay,uv=[u,v])))
    # Keep every original location and preliminary reading. Three labelled regions
    # are resolved by the enlarged source crop; one lies at a narrow image edge.
    revisions={('street13',845,758):([FRAME,LEAF],'Boundary at the top of the rectangular sash, touching the head/transom.'),
               ('street13',988,711):([SKY],'Inside the full-width arched upper light.'),
               ('street13',986,797):([LEAF],'A narrow horizontal glazing bar crosses the source pixel.')}
    for r in image:
        notes=revisions.get((r['view'],*r['uv']))
        if notes:
            r['initially_expected']=r['expected']
            r['expected_after_photo_review'],r['photo_review']=notes
            r['matched_after_photo_review']=r['first'] in notes[0]
        else:
            r['matched_after_photo_review']=r['matched']
        if r['view']=='long18' and r['uv']==[439,348]:
            r['photo_review']='The source pixel is in a sky reflection immediately to the right of the centre stile. Retained residual at a material boundary.'
    return dict(asset_sha256=sha(path),layout_sha256=sha(S/'hall-layout.json'),mesh_rays=len(rows),
                mesh_matches=sum(x['matched'] for x in rows),mesh_matches_including_occlusion=sum(x['matched_including_measured_occlusion'] for x in rows),photo_rays=len(image),
                photo_matches=sum(x['matched'] for x in image),photo_matches_after_review=sum(x['matched_after_photo_review'] for x in image),mesh_points=rows,photo_points=image)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('asset',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();result=audit(args.asset)
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print('mesh',result['mesh_matches'],result['mesh_rays'],'photo',result['photo_matches'],result['photo_rays'])
