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
    cameras = json.loads((HERE/'registered-courtyard-cameras.json').read_bytes())
    control = json.loads((HERE/'roof-independent-photo-pixels.json').read_bytes())
    tris, ixmat, materials, sha = load_triangles(mesh)
    a = tris[:,0]
    e, f = tris[:,1]-a, tris[:,2]-a
    rows = []
    counts = {}
    for name in control['views']:
        view = cameras['cameras'][name]
        projection = np.array(view['P'])
        if name == 'front-c': projection[:2] *= 1080/910
        if name == 'side-front': projection = np.array(json.loads((HERE/'roof-corner-registered-side-camera.json').read_bytes())['P'])
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
                samples_sha256=hashlib.sha256((HERE/'roof-independent-photo-pixels.json').read_bytes()).hexdigest())



def board(mesh,path):
    data=json.loads((HERE/'registered-courtyard-cameras.json').read_bytes())
    cameras={key:np.array(v['P']) for key,v in data['cameras'].items()}
    cameras['front-c'][:2] *= 1080/910
    cameras['side-front'] = np.array(json.loads((HERE/'roof-corner-registered-side-camera.json').read_bytes())['P'])
    sun=np.array([-.46,-.70,.67],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    plate=Image.new('RGB',(1390,854),'#f4f0e6');draw=ImageDraw.Draw(plate)
    def label(x,y,t,size):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',size)
        draw.text((x,y),t,font=font,fill='#302c28')
    label(45,21,'东体育会路老3号花园住宅｜红瓦、脊盖与老虎窗',32)
    label(46,73,'按已发表的刘恩惠图41及高参88实照相机投影；图面来自本件三维模型。',20)
    shots=[('front-c',(146,143,866,328),(48,120),1294),
           ('side-front',(170,165,345,269),(48,517),405),
           ('front-a',(175,32,633,148),(492,517),405),
           ('front-c',(406,154,582,267),(937,517),405)]
    with tempfile.TemporaryDirectory() as temp:
        renderer=load_raster(temp)
        for key,crop,(x,y),pixel_width in shots:
            img,_=raster(mesh,renderer,pixel_width,cameras[key],list(crop),sun,angles)
            plate.paste(img,(x,y))
    label(48,458,'图41视向可辨前坡转折、红瓦下口、棚檐、两侧灰板与中央两光。',20)
    label(48,763,'2015侧视，两巷角联合标定，坡顶仍有偏差',17)
    label(492,763,'2015庭面，实照右窗板下缘可见',17)
    label(937,790,'图41局部，两光中央仅一根中梃',17)
    label(48,807,'屋后高位受视角与树冠遮挡，顶面封口不据此增加屋窗。',17)
    plate.save(path,quality=92,subsampling=0)


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
