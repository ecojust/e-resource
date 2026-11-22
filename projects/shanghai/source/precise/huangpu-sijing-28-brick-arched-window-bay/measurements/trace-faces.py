"""Trace the photographed mortar divisions, stepped keystones and arch front edges."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, gaussian_filter1d, median_filter
from scipy.signal import find_peaks
from scipy.interpolate import PchipInterpolator

reference=runpy.run_path(Path(__file__).with_name('measure-voussoirs.py'))
TIERS=reference['TIERS']
# These stems belong to the same radial mortar joint at the three sampled depths.
# The centre stone interrupts the sequences, and several service wires cover the upper tier.
STEMS={
 'lower':[0,18,40,62,82,103,121,140,158,178,195,215,232,252,273,294,314,334,354,374,394,417,439,461,480,560,582,601,622,648,669,694,718,741,763,785,808,831,855,879,902,925,947,972,996,1022,1048,1073,1098,1120],
 'upper':[0,18,36,54,72,92,111,132,152,171,192,212,232,253,272,291,312,332,352,374,394,420,440,462,480,560,581,603,624,649,673,699,723,747,771,796,820,847,873,900,922,948,974,998,1018,1045,1070,1093,1114,1120]}
# End sections intersect the photographed springing blocks. Far-right joints in
# the upper tier that disappear behind the cable are interpolated locally.
def geometry(row,colors,levels,t):
    A,B=[reference['controls'](row[k]) for k in ('outer','inner')]
    def edge(t,level):
        a,b=[reference['evaluate'](sp,t) for sp in (A,B)]
        return a+np.asarray(level)[...,None]*(b-a)
    samples=t*80
    chroma=gaussian_filter(colors[:,:,0]-colors[:,:,2],(1.7,7.))
    lum=gaussian_filter(colors[:,:,1]*.56+colors[:,:,2]*.44,(1.3,8.))
    def trace(score,low,high,baseline):
        allowed=np.where((levels>=low)&(levels<=high))[0]
        obs=levels[allowed[np.argmax(score[allowed],axis=0)]]
        valid=((samples<468)|(samples>570))&(samples>=7)&(samples<=1112)
        curve=np.interp(t,t[valid],median_filter(obs,size=19)[valid])
        return gaussian_filter1d(curve,12.)
    ridge=trace(np.gradient(chroma,axis=0),-.12,.13,0.)
    middle=trace(lum-gaussian_filter1d(lum,5.,axis=0),.075,.28,.16)
    inner=trace(-np.gradient(lum,axis=0),.80,1.22,1.)
    org,scale=reference['registration'](row)
    def image_coord(s,depth):
        return org+scale*edge(np.asarray(s)/80,depth)
    def boundary(s,num):
        return np.interp(s,samples,[ridge,middle,inner][num])
    return samples,image_coord,boundary
def scalar(v):
    return np.round(np.asarray(v),2).tolist()
def height(ridge,inner,w):
    return ridge+(inner-ridge)*w
def extract(name,row,colors,levels,t):
    samples,image_coord,boundary=geometry(row,colors,levels,t)
    palette=colors[:,:,1]*.55+colors[:,:,2]*.45
    brightness=gaussian_filter1d(palette-gaussian_filter1d(palette,10,axis=1),1.2,axis=1)
    def joint(stem):
        if stem in (0,1120,480,560):return [stem,stem]
        positions=[];depths=[]
        for lo,hi in [(.27,.45),(.47,.65),(.68,.86),(.83,.94)]:
            curve=np.median(brightness[(levels>=lo)&(levels<=hi)],axis=0)
            indices=np.flatnonzero(abs(samples-stem)<9)
            best=indices[np.argmax(curve[indices])]
            if curve[best]>7:
                positions.append(samples[best]);depths.append((lo+hi)/2)
        if len(positions)<2:return [stem,stem]
        slope,intercept=np.polyfit(depths,positions,1)
        return [float(np.clip(slope*v+intercept,stem-14,stem+14))for v in (.16,1.)]
    pair=np.array([joint(s)for s in STEMS[name]])
    # Explicit keystone corners are independent of the ordinary brick bands.
    org,scale=reference['registration'](row)
    stone=(org+np.array(row['key'])*scale)
    def bezier_piece(lo,hi,a,b,v):
        s0=lo[0]+v*(lo[1]-lo[0]);s1=hi[0]+v*(hi[1]-hi[0])
        s=np.linspace(s0,s1,5)
        return image_coord(s,height(boundary(s,a),boundary(s,b),v))
    fins=[]
    cells=[]
    for i,(lo,hi) in enumerate(zip(pair[:-1],pair[1:])):
        midpoint=np.mean([lo,hi])
        if 480<midpoint<560:continue
        center=(lo+hi)/2
        # Compare measured chroma in the interior with the grey brick's generally
        # neutral shade. Taking a median discards light mortar and crossing wires.
        mask=(samples>center.mean()-3)&(samples<center.mean()+3)
        rgb=np.median(colors[(levels>.35)&(levels<.87)][:,mask],axis=(0,1))
        color='red' if rgb[0]-rgb[2]>25 else 'blue'
        # A photographed transverse joint turns some full-depth headers into a pair.
        s=np.linspace(0,1,11)[2:-2]
        zy=[];strength=[]
        for v in np.linspace(.35,.78,44):
            m=(1-v)*lo[0]+v*lo[1];n=(1-v)*hi[0]+v*hi[1]
            station=m+(n-m)*s
            idx=np.searchsorted(samples,station).clip(0,len(samples)-1)
            lev=height(boundary(station,1),boundary(station,2),v)
            iy=np.searchsorted(levels,lev).clip(5,len(levels)-6)
            signal=palette[iy,idx]-.5*(palette[iy-5,idx]+palette[iy+5,idx])
            zy.append(v);strength.append(np.median(signal))
        cut=zy[int(np.argmax(strength))]if max(strength)>9 else None
        for j,(v0,v1) in enumerate([(0.,1.)]if cut is None else [(0.,cut),(cut,1.)]):
            # A tightly inset dark mortar bed stays visible between separate brick faces.
            gap=min(1.1,(hi.mean()-lo.mean())*.08)
            p=lo+gap;q=hi-gap
            top=bezier_piece(p,q,1,2,v0+.011)
            bottom=bezier_piece(p,q,1,2,v1-.011)
            cells.append(dict(id=f'{name}-face-{i+1}-{j+1}',color=color,polygon=scalar(np.vstack((top,bottom[::-1])))))
        fins.append(dict(id=f'{name}-intrados-{i+1}',color=color,
                         line=scalar(bezier_piece(lo+.9,hi-.9,1,2,1.))))
    # Long horizontal bricks follow the narrow red outer ring; their mortar
    # boundaries are light, nearly radial strokes visible in its middle.
    tmid=height(boundary(samples,0),boundary(samples,1),.53)
    indices=np.arange(len(samples))
    y=np.searchsorted(levels,tmid).clip(7,len(levels)-8)
    signal=brightness[y,indices]
    peaks,_=find_peaks(gaussian_filter1d(signal,2.),distance=61,height=7.,prominence=6.)
    rim_points=[0]+[round(samples[p],2) for p in peaks if 8<samples[p]<1112 and not 460<samples[p]<578]+[480,560,1120]
    rim=[]
    for i,(l,r)in enumerate(zip(sorted(rim_points)[:-1],sorted(rim_points)[1:])):
        if 480<.5*(l+r)<560:continue
        sx=np.linspace(l+.8,r-.8,6)
        top=image_coord(sx,boundary(sx,0)+.007)
        bottom=image_coord(sx,boundary(sx,1)-.008)
        rim.append(dict(id=f'{name}-outer-rim-{i+1}',polygon=scalar(np.vstack((top,bottom[::-1])))))
    steps=np.linspace(0,1120,129)
    outer=image_coord(steps,boundary(steps,0))
    inner=image_coord(steps,boundary(steps,2))
    return dict(outer=scalar(outer),front_intrados=scalar(inner),key=scalar(stone),key_back_corners=scalar(org+np.array(row['key_return'])*scale),
                face_cells=cells,visible_intrados=fins,rim_bricks=rim)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('photo',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]/'source')
    args=ap.parse_args();roles={}
    sys.path.insert(0,str(args.source))
    from photo_plane import position,pixel
    with Image.open(args.photo) as img:
        for name,data in TIERS.items():
            crop=img.crop(data['crop'])
            local={**data,'crop':[0,0,crop.width,crop.height]}
            t,levels,col=reference['strip'](np.asarray(crop,dtype=float),local)
            roles[name]=extract(name,data,col,levels,t)
            back=[]
            for u,v in roles[name]['front_intrados']:
                x,y,z=position(u,v,-.022)
                back.append(pixel([x,.16,z]).round(2).tolist())
            roles[name]['rear_intrados']=back
    record=dict(original_size=[5312,2988],photo_sha256=hashlib.sha256(args.photo.read_bytes()).hexdigest(),
                photographer='Antigng',date='2017-08-31',license='CC BY-SA 4.0',
                source='https://commons.wikimedia.org/wiki/File:%E6%B3%97%E6%B3%BE%E8%B7%AF28%E5%8F%B7.jpg',
                coordinates='Original upright photograph in pixels, increasing right and down. Both visible storeys at the east end of the street facade.',
                tiers=roles,depth_m={'main_front':-.022,'outer_trim':-.036,'keystone_front':-.06,'rear_intrados':.16})
    args.output.write_text(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
    for k,d in roles.items():print(k,len(d['face_cells']),len(d['visible_intrados']),len(d['rim_bricks']))
if __name__=='__main__':
    main()
