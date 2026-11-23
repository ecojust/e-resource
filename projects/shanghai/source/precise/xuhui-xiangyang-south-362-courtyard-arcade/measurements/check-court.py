"""Trace a photograph and check positive, closed solids in the two independently exported meshes."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
sys.path.insert(0,str(PRECISE/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
sys.path.insert(0,str(HERE.parent/'source'))
from glb_triangles import SerialScene
from court_arcade import SURVEY,WALL,TRIM,DARK,FRAME,GLASS,CIRCLE,add_court_arcade,PALETTE
sys.path.insert(0,str(PRECISE/'hongkou-general-post-office/source/common'))
from photo_architecture import Builder
P=np.asarray(SURVEY['P']);E=np.asarray(SURVEY['camera_eye'])
PIXELS={
 'left arch':[(269,312,GLASS),(290,310,GLASS),(270,293,WALL)],
 'middle arch':[(347,303,GLASS),(375,300,GLASS),(338,280,WALL)],
 'right arch':[(430,292,GLASS),(467,288,GLASS),(435,264,WALL)],
 'curved end':[(83,191,GLASS),(90,231,GLASS),(130,213,WALL),(164,190,WALL),(142,158,TRIM)],
 'open cut':[(298,194,None),(407,188,None)]}
def verify(p,lod):
    scene=SerialScene(p);b=Builder(PALETTE);add_court_arcade(b,lod);rows=[];closures=[]
    for part in b.parts:
        v=np.asarray(part['vertices']);tri=v[np.asarray(part['triangles'])];edges=Counter()
        for face in part['triangles']:
            for a,c in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,c)))]+=1
        volume=np.sum(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])))/6
        closures.append(dict(part=part['label'],closed=all(n==2 for n in edges.values()),volume_m3=volume))
    assert all(g['closed'] and g['volume_m3']>0 for g in closures)
    def trace(group,tag,eye,direction,wanted,pixel=None):
        hit=scene.ray(np.array(eye,float),np.asarray(direction,float),120.)
        got=hit['material'] if hit else None
        rows.append(dict(group=group,item=tag,pixel=pixel,wanted=wanted,first=hit,match=got==wanted))
    for group,pts in PIXELS.items():
        for i,(u,v,mat) in enumerate(pts):
            trace('photograph',group,E,np.linalg.solve(P[:,:3],[u,v,1]),mat,[u,v])
    for i,row in enumerate(SURVEY['axes'],1):
        x,r,h=row['x'],row['rx'],row['rise']
        for dx,dz,m in [(-.4,.36,GLASS),(.4,.36,GLASS),(0,.6,FRAME),(0,1.04,TRIM),(1.15,.55,WALL),(.4,-.015,FRAME)]:
            trace('construction',f'arch {i}',[x+dx*r,-2,dz*h],[0,1,0],m)
    for deg,z,m in [(-89,2.75,GLASS),(-82,2.75,FRAME),(-30,2.66,WALL),(-30,3.95,DARK),(-40,4.00,TRIM)]:
        u=np.array([np.cos(np.deg2rad(deg)),np.sin(np.deg2rad(deg))])
        trace('construction','bowed end',np.r_[np.asarray(CIRCLE)+u*3,z],np.r_[-u,0],m)
    return dict(asset=scene.asset,triangles=len(scene.tri),closed_solids=len(closures),solids=closures,groups={g:[sum(r['match'] for r in rows if r['group']==g),sum(r['group']==g for r in rows)]for g in ['photograph','construction']},checks=rows)
def board(mesh,photo,output):
    scene=SerialScene(mesh);im=Image.new('RGB',(1150,545),'#f3f0e7');draw=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
    draw.text((24,14),'Three arched lights and the curved cornice',font=font(29),fill='#2c3e36')
    draw.text((25,60),'No. 362, Xiangyang South Road  |  partial exterior, August 2018',font=font(18),fill='#526159')
    bounds=(20,135,510,360);size=(545,250);sample=Image.open(photo).resize((1000,562)).crop(bounds).resize(size)
    im.paste(sample,(24,117));screen=Image.new('RGB',(1000,562),'#d6ded8');d=ImageDraw.Draw(screen)
    colors={WALL:'#c8b78c',TRIM:'#dfcba4',DARK:'#565850',FRAME:'#505852',GLASS:'#748c93'}
    tri=scene.tri; eye_depth=np.mean(tri@P[2,:3]+P[2,3],axis=1)
    for k in np.argsort(-eye_depth):
        t=tri[k];px=t@P[:,:3].T+P[:,3];uv=px[:,:2]/px[:,2,None]
        d.polygon([tuple(x)for x in uv],fill=colors[scene.materials[scene.mi[k]]])
    im.paste(screen.crop(bounds).resize(size),(582,117))
    lines=['Left: crop from the original photograph by Antigng, 2 August 2018 (CC BY-SA 4.0).',
    'Right: original reconstruction projected through the fitted camera; three clear openings set the display scale.',
    'The photograph is titled No. 362. The municipal listing separately names No. 364. The shop canopy and gate obscure the lower sashes.',
    'Wikimedia Commons. Full source URL and image SHA-256 in courtyard-camera.json.  |  creativecommons.org/licenses/by-sa/4.0/']
    for i,line in enumerate(lines):draw.text((25,395+i*29),line,font=font(14),fill='#42544c')
    im.save(output,quality=90)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('near',type=Path);cli.add_argument('far',type=Path);cli.add_argument('out',type=Path);cli.add_argument('--photo',type=Path)
    a=cli.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    for name,p,lod in [('full',a.near,False),('lod',a.far,True)]:
        results=verify(p,lod);(a.out/(name+'-checks.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(name,results['groups'])
    if a.photo:
        assert hashlib.sha256(a.photo.read_bytes()).hexdigest()==SURVEY['source_sha256']
        board(a.near,a.photo,a.out/'photographic-comparison.jpg')
