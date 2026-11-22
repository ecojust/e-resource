"""Rebuild the window comparison from two decoded GLBs and the original, openly licensed 2013 photograph."""
import argparse,ctypes,hashlib,io,json,subprocess,sys,tempfile
from pathlib import Path
from urllib.request import Request,urlopen
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
TOOLS=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(TOOLS),str(HERE)]
from photo_glb_raster import raster
from check_canteen_windows import cameras
from hall_coordinates import WIDTH

def synthetic_camera(eye,target,focus=900,center=(530.,330.)):
    eye=np.array(eye);forward=np.array(target)-eye;forward=forward/np.linalg.norm(forward)
    horizontal=np.cross(forward,[0.,0.,1.]);horizontal/=np.linalg.norm(horizontal)
    down=np.cross(forward,horizontal)
    R=np.array([horizontal,down,forward]);K=np.array([[focus,0,center[0]],[0,focus,center[1]],[0,0,1]])
    return K@np.column_stack([R,-R@eye])

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('near',type=Path);ap.add_argument('far',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--photo',type=Path)
    args=ap.parse_args();source=json.loads((HERE/'window-source-pixels.json').read_bytes());credit=next(f for f in source['frames']if f['id']=='street13')
    raw=args.photo.read_bytes() if args.photo else urlopen(Request(credit['image'],headers={'User-Agent':'ArchitecturalResearch/1.0'}),timeout=25).read()
    assert hashlib.sha256(raw).hexdigest()==credit['sha256']
    photo=Image.open(io.BytesIO(raw)).convert('RGB')
    sheet=Image.new('RGB',(1260,945),'#faf8f2');d=ImageDraw.Draw(sheet)
    font=Path('/usr/share/fonts/opentype/noto')
    def label(x,y,t,size=22,bold=False):
        f=ImageFont.truetype(str(font/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')),size,index=2)
        d.text((x,y),t,font=f,fill='#26333a')
    label(35,20,'益民食品一厂原食堂  ·  窗扇与门扇',36,True)
    label(35,79,'西北端的上窗保留浅弧形整片上亮，下方两扇各分三格。',22)
    cams=cameras(); nw_crop=(1165,528,1555,809);sz=(410,295)
    sheet.paste(photo.crop(nw_crop).resize(sz,Image.Resampling.LANCZOS),(36,125))
    records=[]
    with tempfile.TemporaryDirectory() as td:
        so=Path(td)/'paint.so';subprocess.run(['cc','-O2','-fPIC','-shared',TOOLS/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        def render(path,cam,crop,xy,dimensions,key,light):
            sun=np.array(light,dtype='float32');sun/=np.linalg.norm(sun)
            pic,r=raster(path,lib,round(dimensions[0]*1.3),cam,crop,sun,[])
            if r['zbuffer_foreground_pixels']<2000:raise ValueError('Empty image region')
            sheet.paste(pic.resize(dimensions,Image.Resampling.LANCZOS),xy)
            records.append(dict(scene_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),view=key,camera_P=cam.tolist(),**r))
        render(args.near,cams['street13'],nw_crop,(467,125),sz,'2013 northwest window match',[.4,-.7,.8])
        render(args.far,cams['long18'],(641,152,716,355),(961,125),(111,295),'2018 canal-side casement',[ -.8,-.4,.7])
        render(args.near,cams['end18'],(283,429,520,548),(35,519),(560,281),'2018 southeast paired glazed doors',[.28,.9,.7])
        rows=[o for o in json.loads((HERE.parent/'source/hall-layout.json').read_bytes())['faces']['street'] if o['kind']=='street-door']
        if len(rows)!=2:raise ValueError('Expected two street doors')
        ctr=sum(o['center'] for o in rows)/2
        c=synthetic_camera((WIDTH+11,ctr-1.4,2.40),(WIDTH,ctr,1.45))
        render(args.near,c,(222,203,840,514),(647,519),(572,281),'Street carved panel doors, model detail',[.84,-.28,.7])
    label(38,425,'2013年原照局部',20,True);label(468,425,'同机位近档',20,True);label(928,425,'临水长翼远档',20,True)
    label(36,470,'东南庭院，两樘宽玻璃门',25,True);label(646,470,'沿街第六、七轴，两樘木门',25,True)
    label(36,811,'每洞两扇，中缝旁各装一只拉手。',20)
    label(647,811,'四扇实木门共有十二块凸芯板。',20)
    label(36,866,'左上原照摄影 Coolmanjackey，2013年7月30日，CC BY-SA 3.0；本图裁切。其余均为导出模型实渲。',17)
    label(36,899,'东南端与临水长翼取景依据虹口区2018年刊图；沿街木门依据2015、2020年街景。',17)
    args.output.parent.mkdir(parents=True,exist_ok=True);sheet.save(args.output,quality=90,optimize=True)
    args.output.with_suffix('.json').write_text(json.dumps({'photo':credit,'photo_crop':nw_crop,'frames':records},indent=1,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
