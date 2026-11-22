"""Paint the two recorded winter views from an actual local GLB."""
from pathlib import Path
import json,sys,ctypes,hashlib,tempfile,subprocess,argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
CLIP=HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0]=[str(RASTER),str(CLIP)]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane

def draw(near,far,output):
    common=HERE/'gate-camera-registration.json'
    data=json.loads(common.read_text())
    board=Image.new('RGB',(1200,795),'#f1efe7')
    ink=ImageDraw.Draw(board)
    def typeface(size,bold=False):
        weight='Bold'if bold else 'Regular'
        return ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc',size,index=2)
    def label(x,y,s,size,bold=False):
        ink.text((x,y),s,font=typeface(size,bold),fill='#34322c')
    label(34,17,'归仁里过街楼的山花与弄名匾',38,True)
    label(35,76,'康定东路3弄　｜　冬季街面实拍机位的模型视图',20)
    views=[
        (near,'crown-winter20',[185,26,652,480],(34,132),595,'中央镜框、双侧花环与悬饰'),
        (near,'crown-east15',[508,70,655,240],(662,132),232,'椭圆镜心与下方垂饰'),
        (far,'crown-winter20',[545,112,640,412],(922,132),183,'右侧圆扣与叠鳞挂饰'),
        (near,'crown-winter20',[285,491,540,642],(663,448),288,'匾额从右向左读作“歸仁里”')]
    sun=np.array([-.58,-.49,.65],dtype=np.float32);sun/=np.linalg.norm(sun)
    angles=[round(float(np.rad2deg(np.arctan2(sun[0],sun[1]))%360),3),round(float(np.rad2deg(np.arcsin(sun[2]))),3)]
    reports=[]
    with tempfile.TemporaryDirectory()as tmp:
        t=Path(tmp);libfile=t/'render.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(libfile),'-lm'],check=True)
        lib=ctypes.CDLL(str(libfile));lib.paint.restype=lib.shadow_depth.restype=None
        previous={}
        for mesh,key,crop,(x,y),width,caption in views:
            P=np.array(data['views'][key]['xyz_to_image'])
            if (mesh,key)not in previous:
                g=t/f'clipped-{len(previous)}.glb';c=clip_near_plane(mesh,g,P);previous[mesh,key]=(g,c)
            g,c=previous[mesh,key]
            im,report=raster(g,lib,round(width*1.4),P,crop,sun,angles)
            height=round(width*im.height/im.width)
            board.paste(im.resize((width,height),Image.Resampling.LANCZOS),(x,y))
            label(x,y+height+4,caption,16,True)
            reports.append(dict(view=key,mesh=mesh.name,mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),clip=c,raster=report))
    label(34,747,'山花的细部依据2015、2016、2020及2021年街面影像；浮雕外凸深度按可见叠压关系估计。',17)
    output.parent.mkdir(parents=True,exist_ok=True)
    board.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(photo_pixels_in_board=False,views=reports,calibration_sha256=hashlib.sha256(common.read_bytes()).hexdigest(),image_sha256=hashlib.sha256(output.read_bytes()).hexdigest()),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('near',type=Path);parser.add_argument('far',type=Path);parser.add_argument('output',type=Path);a=parser.parse_args();draw(a.near,a.far,a.output)
