"""Measure elliptical sign rims and their painted strokes in dated street views of Wusheng Road."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.optimize import least_squares

RECORDS={
 '2017': {'station':'09000300121710141031291991A','date':'2017-10-14','pano_origin':[-512,1154],
          'seeds':[(415,715,52,53),(547,690,55,54),(683,686,55,54),(807,710,53,54)]},
 '2020': {'station':'09000300122002221044155365O','date':'2020-02-22','pano_origin':[7351,1154],
          'seeds':[(222,748,51,53),(330,722,51,53),(445,713,52,54),(572,725,52,54)]}}
LETTERS = ['重','新','小','区']

def value(src,xy):
    return map_coordinates(src,[xy[...,1],xy[...,0]],order=1,mode='nearest')
def coordinates(params,theta,radius):
    x,y,rx,ry,slant=params
    cs=np.cos(theta);sn=np.sin(theta)
    return np.stack((x+radius*(rx*cs+slant*ry*sn),y+radius*ry*sn),axis=-1)
def residual(params,points):
    cx,cy,rx,ry,slant=params
    py=(points[:,1]-cy)/ry
    px=(points[:,0]-cx-slant*(points[:,1]-cy))/rx
    return (np.hypot(px,py)-1)*np.sqrt(rx*ry)
def fit(rgb,seed):
    params=np.array([*seed,0.],float)
    # Rims are dark against the sky, masonry or foliage. Cables and glints
    # intersect only short angular runs and are downweighted in the fit.
    lum=gaussian_filter(.3*rgb[:,:,0]+.57*rgb[:,:,1]+.13*rgb[:,:,2],.85)
    theta=np.linspace(0,2*np.pi,180,endpoint=False)[:,None]
    radii=np.linspace(.80,1.18,77)[None,:]
    for iteration in range(4):
        uv=coordinates(params,theta,radii)
        pixels=value(lum,uv);gradient=np.gradient(pixels,axis=1)
        inside=np.mean(pixels[:,:12],axis=1)
        scoring=gradient-.30*abs(radii-1.)
        ind=np.argmax(scoring,axis=1)
        chosen=uv[np.arange(len(ind)),ind]
        strength=gradient[np.arange(len(ind)),ind]
        usable=(strength>.9)&(inside<100)&(ind>=2)&(ind<75)
        if usable.sum()<14:raise ValueError('Too few light-dark rim transitions')
        points=chosen[usable]
        lo=[seed[0]-15,seed[1]-15,seed[2]*.77,seed[3]*.77,-.25]
        hi=[seed[0]+15,seed[1]+15,seed[2]*1.22,seed[3]*1.22,.25]
        sol=least_squares(residual,params,args=(points,),bounds=(lo,hi),loss='soft_l1',f_scale=1.8)
        params=sol.x
    use=abs(residual(params,chosen))<2.2
    return params,chosen[use&usable],int(len(points))
def normalized_patch(rgb,fit,size=180):
    y,x=np.indices((size,size),dtype=float);u,v=(x+.5-size/2)/(size/2),(y+.5-size/2)/(size/2)
    cx,cy,rx,ry,slant=fit
    xx=cx+rx*u+slant*ry*v; yy=cy+ry*v
    return np.stack([map_coordinates(rgb[:,:,i],[yy,xx],order=1,mode='nearest') for i in range(3)],axis=-1)
def measure(input_path,key):
    data=RECORDS[key]
    # Limit memory to the narrow region holding the signs rather than decoding
    # separate full-scene floating-point arrays for every date.
    src=Image.open(input_path)
    xmin,ymin,xmax,ymax=70,515,945,845
    rgb=np.asarray(src.crop((xmin,ymin,xmax,ymax)).convert('RGB'),dtype=float)
    records=[];patches=[]
    for ch,(x,y,rx,ry) in zip(LETTERS,data['seeds']):
        par,points,considered=fit(rgb,(x-xmin,y-ymin,rx,ry))
        patch=normalized_patch(rgb,par);patches.append(patch)
        par[:2]+=[xmin,ymin]
        records.append(dict(character=ch,ellipse=np.round(par,4).tolist(),inlier_count=len(points),considered=considered,
                            edge_points=np.round(points+[xmin,ymin],2).tolist()))
    return records,patches
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('source_dir',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    report={};canvas=Image.new('RGB',(4*170,2*190),'#f4f5ed');draw=ImageDraw.Draw(canvas)
    for r,(key,datum)in enumerate(RECORDS.items()):
        src=args.source_dir/(datum['station']+'.jpg');cells,patches=measure(src,key)
        report[key]={**{k:v for k,v in datum.items()if k!='seeds'},'research_crop_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'plates':cells}
        for i,pic in enumerate(patches):
            im=Image.fromarray(pic.clip(0,255).astype('uint8')).resize((158,158))
            canvas.paste(im,(i*170+4,r*190));draw.text((i*170+4,r*190+160),key+' '+str(cells[i]['inlier_count']),fill='#263e32')
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    canvas.save(args.output.with_suffix('.jpg'),quality=90)
