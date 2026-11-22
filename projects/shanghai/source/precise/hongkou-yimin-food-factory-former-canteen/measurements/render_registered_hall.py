"""Render two short ends, the long elevation and selected details using the three photo cameras."""
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
COMMON=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(COMMON))
from photo_glb_raster import raster

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    ends=json.loads((HERE/'two-terminal-cameras.json').read_text())['views']
    canal=json.loads((HERE/'canal-side-camera.json').read_text())
    ref={'northwest':np.asarray(ends[0]['P']),'southeast':np.asarray(ends[1]['P'])@np.array([[-1,0,0,18.7],[0,-1,0,56.5],[0,0,1,0],[0,0,0,1]]),'canal':np.asarray(canal['P'])}
    sun_angles={'northwest':[235,35],'southeast':[181,45],'canal':[67,39]}
    images=[('nw-end','northwest',[340,139,900,658],461,(24,101),'西北庭院端　2013年摄影位置'),('se-end','southeast',[70,193,686,566],600,(515,101),'东南近桥端　2018年区方刊图位置'),('canal-face','canal',[128,8,1005,613],607,(24,598),'临水长面　十四个开间与落水管'),('preserved-glass-doors','southeast',[290,428,513,547],372,(678,595),'东南端中央两道玻璃门'),('gable','southeast',[247,213,482,281],343,(677,889),'白色山花和下方的斜瓦坡')]
    canvas=Image.new('RGB',(1140,1110),'#f3f0e9');draw=ImageDraw.Draw(canvas)
    def label(x,y,txt,n,col='#303735'):
        draw.text((x,y),txt,font=ImageFont.truetype(str(args.font),n),fill=col)
    label(24,13,'益民食品一厂　旧食堂改建展厅',34)
    label(26,64,'香烟桥路13号　从三张公开照片的拍摄位置观察模型',18)
    views={}
    with tempfile.TemporaryDirectory()as temp:
        libname=Path(temp)/'raster.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(COMMON/'photo_glb_raster.c'),'-lm','-o',str(libname)],check=True)
        lib=ctypes.CDLL(str(libname));lib.paint.restype=lib.shadow_depth.restype=None
        for name,key,crop,width,(x,y),caption in images:
            az,alt=np.radians(sun_angles[key]);light=np.asarray([np.sin(az)*np.cos(alt),np.cos(az)*np.cos(alt),np.sin(alt)],np.float32)
            im,stats=raster(args.mesh,lib,width,ref[key],crop,light,sun_angles[key]);canvas.paste(im,(x,y));label(x,y+im.height+7,caption,18)
            views[name]=stats
    label(26,1067,'图中为原创模型渲染。窗位和各面独立核对，楼廓尺寸与屋脊退距均为影像估计。',17,'#555d58')
    plate=args.output/'former-canteen-three-views.jpg';canvas.save(plate,quality=92,subsampling=0)
    report=dict(mesh_sha256=sha(args.mesh),two_end_cameras_sha256=sha(HERE/'two-terminal-cameras.json'),canal_camera_sha256=sha(HERE/'canal-side-camera.json'),comparison_jpg_sha256=sha(plate),photographs_embedded=False,views=views)
    (args.output/'registered-former-canteen.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
