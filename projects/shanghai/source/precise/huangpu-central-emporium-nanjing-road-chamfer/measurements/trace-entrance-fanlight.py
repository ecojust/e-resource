"""Trace both semicircular steel frames and all three spokes in the 2022 corner fanlight."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageOps
from scipy.ndimage import gaussian_filter,gaussian_filter1d,map_coordinates

CROP=(192,113,366,199)
REVIEW=np.array([809,400])
SOURCE='https://commons.wikimedia.org/wiki/File:355_Middle_Sichuan_Road_Shanghai-20220828.jpg'


def sample_plane(image,path,axes,offsets):
    coordinates=path[:,None,:]+axes[:,None,:]*offsets[None,:,None]
    return map_coordinates(image,[coordinates[:,:,1],coordinates[:,:,0]],order=1,mode='nearest')


def follow(image,path,axes,span,width,search=12):
    offsets=np.arange(-span,span+.26,.5)
    field=sample_plane(image,path,axes,offsets)
    smoothed=gaussian_filter(field,(1.2,1.6))
    wide=gaussian_filter1d(smoothed,width*2.2,axis=1,mode='nearest')
    local=(smoothed-wide)*.75+.18*smoothed
    allowed=abs(offsets)<=search
    means=local[:,allowed];ts=offsets[allowed]
    # A dark line on a pane can run into a dark reflection. The continuity
    # cost keeps the trace on the same steel member across that interruption.
    cost=means[0]+.08*ts**2
    jumps=.68*(ts[:,None]-ts[None,:])**2
    history=np.empty(means.shape,dtype=int)
    for i in range(1,len(means)):
        options=cost[:,None]+jumps
        history[i]=np.argmin(options,axis=0)
        cost=options[history[i],np.arange(len(ts))]+means[i]+.035*ts**2
    row=np.argmin(cost);levels=[row]
    for i in range(len(means)-1,0,-1):
        row=history[i,row];levels.append(row)
    shift=gaussian_filter1d(ts[levels[::-1]],2.8,mode='nearest')
    centre=path+axes*shift[:,None]
    # Find the outer edge of each flank of the dark steel within a narrow
    # interval around its observed width. The nominal-width penalty is low
    # enough to retain the changes in apparent thickness across the arch.
    refined=sample_plane(image,centre,axes,offsets)
    slope=np.gradient(gaussian_filter(refined,(2.0,1.8)),.5,axis=1)
    sides=[]
    for direction in [-1,1]:
        widths=direction*offsets
        keep=(widths>=width*.48)&(widths<=width*1.65)
        score=direction*slope[:,keep]-.12*(widths[keep]-width)**2
        chosen=offsets[keep][np.argmax(score,axis=1)]
        sides.append(centre+axes*gaussian_filter1d(chosen,3.,mode='nearest')[:,None])
    return sides[0],sides[1],centre



def straight_steel_edges(gray,path,normal,width):
    # A straight rolled spoke projects to two straight lines. Fit both long
    # outer boundaries against the original light-to-dark steps so a dark
    # reflection within the glass cannot pull the measured strip off its seat.
    lateral=np.arange(-29.,29.25,.25)
    strip=sample_plane(gray,path,normal,lateral)
    strip=gaussian_filter(strip,(1.2,3.1))
    t=np.linspace(0.,1.,len(path));use=(t>.12)&(t<.93)&((t<.60)|(t>.75))
    keep=np.flatnonzero(use);rows=np.arange(len(keep))
    cross=np.gradient(strip,.25,axis=1)
    result=[]
    for side in [-1,1]:
        candidates=np.arange(-17.,17.5,1.)
        best=(-np.inf,None)
        for oa in candidates:
            for ob in candidates:
                if not (2.5<side*((oa+ob)/2)<17):continue
                offsets=oa+(ob-oa)*t[keep]
                ids=np.rint((offsets-lateral[0])/.25).astype(int)
                gradient=side*cross[keep,ids]
                inside=strip[keep,ids-int(side)*12]
                outside=strip[keep,ids+int(side)*12]
                score=np.median(gradient)+.045*np.median(outside-inside)-.003*(abs(oa-ob))
                if score>best[0]:best=(score,(oa,ob))
        oa,ob=best[1];offset=oa+(ob-oa)*t
        result.append(path+normal*offset[:,None])
    return result[0],result[1],(result[0]+result[1])/2

def arc(rx,rz,xc,zc,xshift,tilt):
    # The camera sees the left spring slightly lower than the right one.
    a=np.linspace(0,np.pi,213);sa=np.sin(a);ca=np.cos(a)
    p=np.column_stack((xc-rx*ca+xshift*sa,zc+tilt*ca-rz*sa))
    tangent=np.column_stack((rx*sa+xshift*ca,-tilt*sa-rz*ca))
    normal=np.column_stack((tangent[:,1],-tangent[:,0]))
    normal/=np.linalg.norm(normal,axis=1)[:,None]
    return p,normal


def line(first,last,n=130):
    a=np.array(first,dtype=float);b=np.array(last,dtype=float)
    t=np.linspace(0,1,n);p=a+t[:,None]*(b-a)
    axis=np.array([b[1]-a[1],a[0]-b[0]],dtype=float)
    axis/=np.linalg.norm(axis)
    return p,np.tile(axis,(n,1))


def native_right_haunch(tile, rect, edge, opposite, centre):
    """Follow the inner lip of the right haunch against dark reflected glass."""
    first, stop = 128, 158
    c = np.asarray(centre)[first:stop]
    prior = np.asarray(edge)[first:stop]
    axis = prior - np.asarray(opposite)[first:stop]
    axis /= np.linalg.norm(axis, axis=1)[:, None]
    distances = np.arange(7., 40.25, .25)
    values = sample_plane(np.asarray(tile.convert('L'), float), c - rect[:2], axis, distances)
    gradient = np.gradient(gaussian_filter(values, (.85, 6.4)), .25, axis=1)
    current = np.einsum('ij,ij->i', prior - c, axis)
    # Fit the continuous dark-to-light boundary next to the reflection, with
    # a weak preference for the nearby edge when several reflections overlap.
    scores = gradient - .009 * (distances[None, :] - current[:, None])**2
    offsets = gaussian_filter1d(distances[np.argmax(scores, axis=1)], 1., mode='nearest')
    index = np.arange(len(c))
    fade = np.minimum(np.minimum(index, len(c) - 1 - index) / 4., 1.)
    refined = prior + (fade * (offsets - current))[:, None] * axis
    result = np.asarray(edge).copy()
    result[first:stop] = refined
    return np.round(result, 2).tolist()


def trace(photo):
    factor=photo.width/690
    rect=(np.array(CROP)*factor).astype(int)
    tile=photo.crop(tuple(rect)).convert('RGB')
    reduced=tile.resize(tuple(REVIEW),Image.Resampling.LANCZOS)
    rgb=np.asarray(reduced,float);gray=rgb@np.array([.299,.587,.114])
    paths=[
      ('outer arch',*arc(355.,339.,400.,366.,10.,8.5),6.0,7.5),
      ('inner arch',*arc(246.,226.,399.,365.,7.,6.1),7.0,7.5),
      ('left spoke',*line((394.,365.),(163.,130.)),6.0,6.0),
      ('vertical spoke',*line((394.,365.),(411.,31.)),6.8,6.0),
      ('right spoke',*line((394.,365.),(651.,120.)),6.0,6.0),
      ('spring rail',*line((42.,375.),(758.,357.),215),2.8,4.0)]
    scale=np.array(tile.size)/REVIEW
    def original(a):return np.round((a+.5)*scale-.5+rect[:2],2).tolist()
    out=[];pen=ImageDraw.Draw(reduced)
    for name,points,axis,width,search in paths:
        if 'spoke'in name:l,r,c=straight_steel_edges(gray,points,axis,width)
        else:l,r,c=follow(gray,points,axis,18.,width,search)
        left,right,centre=original(l),original(r),original(c)
        if name=='inner arch':
            left=native_right_haunch(tile,rect,left,right,centre)
            l=(np.asarray(left)+.5-rect[:2])/scale-.5
        out.append(dict(member=name,edge_a=left,edge_b=right,centreline=centre))
        for side in [l,r]:
            pen.line([tuple(v)for v in side],fill='#63f3bd',width=1)
    return out,reduced


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('original',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--sheet',type=Path)
    a=ap.parse_args()
    with Image.open(a.original)as image:records,sheet=trace(ImageOps.exif_transpose(image))
    if a.sheet:sheet.save(a.sheet,quality=92)
    data={'source':SOURCE,'credit':'Shwangtianyuan, 28 August 2022. CC BY-SA 4.0.','photo_sha256':hashlib.sha256(a.original.read_bytes()).hexdigest(),'coordinates':'Upright pixels of the full photograph. Each member has an edge on each side of its traced dark centre. An interior arc, three radial spokes and the sill divide the outer semicircle into eight lights.','members':records}
    a.output.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print([(v['member'],len(v['centreline']))for v in records])
