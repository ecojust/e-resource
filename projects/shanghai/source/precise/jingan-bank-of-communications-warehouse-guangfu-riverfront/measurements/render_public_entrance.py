"""Render the public river entrance, its two inscriptions, and the measured passage directly from the released mesh."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from scipy.optimize import least_squares
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
CLIP=HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0]=[str(RASTER),str(CLIP),str(HERE.parent/'source')]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane
from south_entrance import image_frame


def fit_homography(source,destination):
    rows=[]
    for (x,y),(u,v) in zip(source,destination):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
    _,_,v=np.linalg.svd(rows)
    h=v[-1].reshape(3,3)
    return h/h[2,2]


def front_camera(region,oblique=False):
    xz,_,_=image_frame()
    u0,v0,u1,v1=region
    pairs=np.array([(u,v)for u in np.linspace(u0,u1,7)for v in np.linspace(v0,v1,7)])
    h=fit_homography([xz(x)for x in pairs],pairs)
    if oblique:
        r=json.loads((HERE/'portal-relative-depth.json').read_bytes());h=np.array(r['H'])@h
        x0=540.
        def directions(k):
            f,cy=k;K=np.array([[f,0,x0],[0,f,cy],[0,0,1]])
            return K,np.linalg.solve(K,h[:,0]),np.linalg.solve(K,h[:,1])
        def cost(k):
            K,a,b=directions(k);return [a@b/(np.linalg.norm(a)*np.linalg.norm(b)),np.log(np.linalg.norm(a)/np.linalg.norm(b))]
        fit=least_squares(cost,[1100,1250],bounds=([350,550],[3800,1700]))
        K,xaxis,zaxis=directions(fit.x);normal=np.cross(zaxis,xaxis);normal/=np.linalg.norm(normal)
        yaxis=K@normal*(np.linalg.norm(xaxis)+np.linalg.norm(zaxis))*.5
        mat=np.column_stack([h[:,0],yaxis,h[:,1],h[:,2]])
        if (-np.linalg.solve(mat[:,:3],mat[:,3]))[1]>0:mat[:,1]*=-1
    else:
        eye=[0.,-33.,1.65];yaxis=-(h[:,0]*eye[0]+h[:,1]*eye[2]+h[:,2])/eye[1]
        mat=np.column_stack([h[:,0],yaxis,h[:,1],h[:,2]])
    # The raster expects positive linear eye depth.
    mat/=np.linalg.norm(mat[2,:3])
    if mat[2,3]<0:mat=-mat
    return mat


def hall_camera():
    data=json.loads((HERE/'public-entrance-passage.json').read_bytes());c=data['relative_camera_30']
    vp=c['vanishing_point'];f=c['equivalent_focal_pixels'];r=c['roll_approx_rad']
    left,right=data['pier_centres_x_y_m'][1];eye=np.array([(left[0]+right[0])/2+c['eye_lateral_m'],(left[1]+right[1])/2-c['photographer_to_nearest_measured_column_m'],c['eye_height_m']])
    rotation=np.array([[f,vp[0],r*f],[r*f,vp[1],-f],[0,1,0]])
    return np.column_stack([rotation,-rotation@eye])


def east_camera():
    """Extend plate 19's measured planar projection into the outward half-space."""
    data=json.loads((HERE/'east-return-sign-registration.json').read_bytes())
    layout=json.loads((HERE/'riverfront-layout.json').read_bytes())
    h=np.array(data['front19_plane_to_image'])
    def axes(values):
        focal,cy=values
        k=np.array([[focal,0,355.5],[0,focal,cy],[0,0,1.]])
        return k,np.linalg.solve(k,h[:,0]),np.linalg.solve(k,h[:,1])
    def error(values):
        _,a,c=axes(values)
        return [a@c/(np.linalg.norm(a)*np.linalg.norm(c)),np.log(np.linalg.norm(a)/np.linalg.norm(c))]
    fit=least_squares(error,[600.,390.],bounds=([220.,210.],[1600.,500.]))
    k,a,c=axes(fit.x)
    d=np.cross(c,a)
    d=k@d*(np.linalg.norm(a)+np.linalg.norm(c))/(2*np.linalg.norm(d))
    local=np.column_stack((h[:,0],d,h[:,1],h[:,2]))
    if (-np.linalg.solve(local[:,:3],local[:,3]))[1]>0:local[:,1]*=-1
    start,end=np.array(layout['east_return'])
    t=(end-start)/np.linalg.norm(end-start);inward=np.array([-t[1],t[0]])
    to_local=np.array([[t[0],t[1],0.,-t@start],[inward[0],inward[1],0.,-inward@start],
                       [0.,0.,1.,0.],[0.,0.,0.,1.]])
    out=local@to_local
    return out/np.linalg.norm(out[2,:3])


def render(asset,output):
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    board=Image.new('RGB',(1130,1020),'#f6f4ee');pen=ImageDraw.Draw(board)
    def text(x,y,s,size,bold=False):
        face='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
        pen.text((x,y),s,fill='#24282a',font=ImageFont.truetype(face,size,index=2))
    text(26,12,'光复路195号 · 南门与中央通道',33,True)
    text(27,64,'原交通银行仓库　｜　按修缮完成后的石门框、题字与公共通道复原',18)
    sun=np.array([-.47,-.70,.54],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    shots=[
      ('front',front_camera([355,135,725,752]),[355,135,725,752],(27,122),375,'临河门楼 · 正面'),
      ('inscription',front_camera([442,568,644,664],True),[333,1050,683,1248],(425,122),665,'门楣与「光二倉庫」四字 · 斜视'),
      ('brand',front_camera([497,185,584,235]),[497,185,584,235],(425,536),225,'上部金属字'),
      ('east',east_camera(),[349,92,483,185],(27,799),278,'东墙字标 · 复原后的两行金字'),
      ('passage',hall_camera(),[190,150,953,571],(672,536),420,'入口段的双列折面灯带')]
    records=[]
    with tempfile.TemporaryDirectory() as dir_name:
        work=Path(dir_name);library=work/'raster.so';subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(library)],check=True)
        lib=ctypes.CDLL(str(library));lib.paint.restype=lib.shadow_depth.restype=None
        for tag,P,crop,xy,width,title in shots:
            cut=work/'clipped.glb';clip=clip_near_plane(asset,cut,P)
            img,record=raster(cut,lib,round(width*1.32),P,crop,sun,angles)
            height=round(width*img.height/img.width);board.paste(img.resize((width,height),Image.Resampling.LANCZOS),xy)
            text(xy[0],xy[1]-28,title,17,True)
            records.append(dict(tag=tag,camera=P.tolist(),clipped=clip,render=record))
    text(332,793,'战时旧照门额为「交通銀行倉庫」。竣工照中门楣改为「光二倉庫」。',17)
    text(332,832,'东侧「BAIspace 百空间」及「光二仓库 EST 1933」由地面照量取，另据斜航照校位。',16)
    text(332,872,'中央通道复原至距门槛约14.9米处。图中展示前三对结构柱、横梁、店面退口及灯带。',17)
    text(332,952,'原创模型渲染。测量依据为华建集团历史建筑保护设计院的首层平面及竣工实拍。',15)
    output.parent.mkdir(parents=True,exist_ok=True);board.save(output,quality=88,optimize=True)
    result=dict(model_sha256=digest(asset),board_sha256=digest(output),image_origin='Original rendering of the supplied mesh; source photographs informed the geometry and camera angles.',source_article='https://www.sohu.com/a/971431850_121124642',records=records)
    output.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('asset',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args();render(args.asset,args.output)
