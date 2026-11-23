"""Render two photographic viewpoints and a garden overview directly from the supplied model."""
import argparse,hashlib,json,runpy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
raster=runpy.run_path(str(PROJECT/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'))['raster']
def render(model,out):
    out.mkdir(parents=True,exist_ok=True)
    cams=json.loads((HERE/'two-stations.json').read_bytes())
    view=json.loads((HERE.parent/'source/cameras.json').read_bytes())[0]
    c=np.array(view['eye']);target=np.array(view['target']);direction=target-c;distance=np.linalg.norm(direction);direction/=distance
    right=np.cross(direction,[0,0,1]);right/=np.linalg.norm(right);focal=1080*distance/view['width_m']
    cams['independent-overview']=dict(size=[1080,780],C=c.tolist(),R=[right.tolist(),np.cross(direction,right).tolist(),direction.tolist()],K=[[focal,0,540],[0,focal,390],[0,0,1]])
    sheet=Image.new('RGB',(1250,640),'#f4f1e9');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',18,index=2)
    records={};head=['18号山墙 · 2018年街道照片的机位','室外石阶 · 照片局部条件配准','三道券廊与山墙 · 全景']
    for i,(name,q)in enumerate(cams.items()):
        w,h=q['size'];ratio=min(1000/w,1060/h)
        frame=raster(model,q,(0,0,w,h),round(w*ratio))
        fname=name+('-model.jpg'if name!='independent-overview'else'.jpg')
        frame.save(out/fname,quality=93,subsampling=0)
        records[name]={'file':fname,'pixels':frame.size,'sha256':hashlib.sha256((out/fname).read_bytes()).hexdigest()}
        frame.thumbnail((395,538));sheet.paste(frame,(i*415+(415-frame.width)//2,(546-frame.height)//2+12));draw.text((16+i*415,578),head[i],font=font,fill='#29382a')
    sheet.save(out/'registered-views.jpg',quality=92)
    (out/'rendered-views.json').write_text(json.dumps({'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'views':records,'combined_sha256':hashlib.sha256((out/'registered-views.jpg').read_bytes()).hexdigest()},indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args();render(a.mesh,a.out)
