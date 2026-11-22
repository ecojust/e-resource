"""Verify independent roof photograph pixels against a released, uncompressed GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0, str(ROOT / 'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'))
from glb_triangles import load_triangles
from render_riverfront_survey import load_raster, raster, perspective


def check(mesh):
    cameras = json.loads((HERE/'villa-three-cameras.json').read_bytes())
    control = json.loads((HERE/'independent-roof-samples.json').read_bytes())
    tris, ixmat, materials, sha = load_triangles(mesh)
    a = tris[:,0]
    e, f = tris[:,1]-a, tris[:,2]-a
    rows = []
    counts = {}
    for view in cameras['cameras']:
        name = view['source']
        projection = np.array(view['P'])
        inv = np.linalg.inv(projection[:,:3])
        eye = -inv @ projection[:,3]
        q = eye - a
        cross = np.cross(q,e)
        numer = np.einsum('ij,ij->i',cross,f)
        results = []
        for group, points in control['views'][name].items():
            for xy in points:
                direction = inv @ [*xy,1]
                direction /= np.linalg.norm(direction)
                h = np.cross(direction,f)
                det = np.einsum('ij,ij->i',e,h)
                safe = abs(det) > 1e-10
                divisor = np.where(safe,det,1)
                u = np.einsum('ij,ij->i',q,h)/divisor
                v, t = cross @ direction/divisor, numer/divisor
                choices = np.where(safe & (u>=0) & (v>=0) & (u+v<=1) & (t>1.e-4))[0]
                mat = None if len(choices)==0 else materials[ixmat[choices[np.argmin(t[choices])]]]
                results.append(dict(view=name,pixel=xy,expected=group,first_surface=mat,
                                    matches=bool(mat and any(k in mat for k in control['first_hit_expected_classes'][group]))))
        rows.extend(results)
        counts[name] = dict(hits=sum(r['matches'] for r in results),samples=len(results))
    return dict(sha256=sha['sha256'],bytes=sha['bytes'],triangles=len(tris),counts=counts,first_hits=rows,
                samples_sha256=hashlib.sha256((HERE/'independent-roof-samples.json').read_bytes()).hexdigest())


def board(mesh,path):
    data=json.loads((HERE/'villa-three-cameras.json').read_bytes())
    cameras={r['source']:np.array(r['P']) for r in data['cameras']}
    sun=np.array([-.46,-.70,.67],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    board=Image.new('RGB',(1290,920),'#f4f1e9');draw=ImageDraw.Draw(board)
    def label(x,y,t,size,bold=False):
        f='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
        draw.text((x,y),t,fill='#304641',font=ImageFont.truetype(f,size,index=2))
    label(42,20,'益民食品一厂复建小楼的红瓦屋顶',36,True)
    label(44,78,'两端山墙、三扇院前屋窗与左翼另三扇屋窗可从院内外照片辨认。',19)
    shots=[('district2018',cameras['district2018'],[0,0,967,435],(42,133),(1206,543)),
           ('visitor',cameras['visitor'],[148,122,861,454],(42,700),(385,179)),
           ('outer',perspective([-31,2,11.8],[-6.9,2,5.6],385,179,282),[0,0,385,179],(442,700),(385,179)),
           ('above',perspective([18,-29,25],[0,1.5,5],385,179,325),[0,0,385,179],(841,700),(385,179))]
    with tempfile.TemporaryDirectory() as temp:
        renderer=load_raster(temp)
        for _,P,crop,xy,wh in shots:
            img,_=raster(mesh,renderer,wh[0],P,crop,sun,angles)
            img.thumbnail(wh,Image.Resampling.LANCZOS);board.paste(img,xy)
    label(42,648,'2018 年区级资料照片的视角',18)
    label(42,880,'院内斜视',16);label(442,880,'左侧街面双窗',16);label(841,880,'屋脊、折谷与后坡',16)
    board.save(path,quality=91,subsampling=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path);parser.add_argument('report',type=Path)
    parser.add_argument('--board',type=Path)
    a=parser.parse_args()
    result=check(a.model)
    if a.board:
        board(a.model,a.board)
        result['board_sha256']=hashlib.sha256(a.board.read_bytes()).hexdigest()
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['counts'])
