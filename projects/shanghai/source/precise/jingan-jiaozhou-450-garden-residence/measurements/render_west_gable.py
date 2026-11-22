"""Render the west street end at the two registered panorama stations."""
import argparse,ctypes as ct,hashlib,json,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from photo_glb_raster import raster
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    h=Path(__file__).resolve().parent;src=h/'west-cameras.json';cams=json.loads(src.read_bytes())['cameras']
    sun=np.array([-.62,-.4,.70],dtype='float32');sun/=np.linalg.norm(sun)
    board=Image.new('RGB',(1200,589),(248,246,239));pen=ImageDraw.Draw(board)
    font=next(p for p in [Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')] if p.exists())
    title=ImageFont.truetype(str(font),34);small=ImageFont.truetype(str(font),19)
    pen.text((20,13),'胶州路450号住宅　西山墙',font=title,fill='#252522')
    rows=[]
    with tempfile.TemporaryDirectory()as tmp:
        sh=Path(tmp)/'photo-raster.so';subprocess.run(['cc','-O3','-fPIC','-shared',h/'photo_glb_raster.c','-lm','-o',sh],check=True)
        for i,(key,text) in enumerate([('2020-side','西面　中层三窗、上层两窗与烟道'),('2020-south','西南面　山墙和石栏下的短砖券')]):
            pic,r=raster(a.mesh,ct.CDLL(str(sh)),1160,np.asarray(cams[key]['P']),(0,0,1000,760),sun,(213,45))
            pic=pic.resize((576,438),Image.Resampling.LANCZOS);x=18+594*i;board.paste(pic,(x,76));pen.text((x,523),text,font=small,fill='#382f2b')
            rows.append({'station':key,'measurement':r})
    pen.text((19,553),'依据2020年2月两处街景机位绘制。树木、电线及街墙遮挡在测量记录中标示。',font=small,fill='#524c41')
    a.output.parent.mkdir(parents=True,exist_ok=True);board.save(a.output,quality=93)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    a.output.with_suffix('.json').write_text(json.dumps(dict(mesh_sha256=sha(a.mesh),camera_sha256=sha(src),image_sha256=sha(a.output),views=rows),indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
