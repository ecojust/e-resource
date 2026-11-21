"""Raised central pair of brick bays, wavy parapet, string courses and flat window heads."""
import math
import numpy as np
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from scipy.interpolate import PchipInterpolator
from brick_facing import CAST
from arcade import RED,SECOND,JOINT,GREY,WOOD,DARK,grid_sash


def top_path(d,lod):
    # Left shoulder, scalloped summit and the descending shoulder are visible in both dated views.
    left=d['middle_left'];width=d['middle_right']-left;crest=d['crest_z'];shoulder=d['shoulder_z']
    samples=[(0.,shoulder),(.042,shoulder+.29),(.077,shoulder+.32),(.114,shoulder+.20),
             (.178,shoulder+.184),(.252,shoulder+.31),(.327,shoulder+.65),(.356,shoulder+.70),
             (.398,shoulder+.59),(.458,shoulder+.69),(.505,shoulder+1.10),(.542,crest-.09),
             (.569,crest),(.596,crest-.16),(.624,crest-.49),(.703,crest-.74),(.768,crest-.99),
             (.824,shoulder+.18),(.896,shoulder-.065),(.954,shoulder-.15),(1.,shoulder-.25)]
    u,z=zip(*samples);curve=PchipInterpolator(u,z)
    us=np.unique(np.r_[u,np.linspace(0,1,30 if lod else 88)])
    return [(left+width*t,float(curve(t)))for t in us]


def plate(f,d,lod):
    left,right=d['middle_left'],d['middle_right'];base=2.71;ridge=top_path(d,lod)
    face=Polygon([(left,base),(right,base),*reversed(ridge)])
    apertures=[];labels=['middle','upper','attic']
    widths=[1.13,1.22,1.16]
    for k,level in enumerate(labels):
        sill,head=d['square_levels'][level]
        for i,cx in enumerate(d['square_axes']):
            w=widths[k];a=box(cx-w/2,sill,cx+w/2,head);apertures.append(a)
            title=level+' central sash '+str(i+1)
            f.prism(a,-.246,-.231,DARK,title+'/shadow behind glazing')
            grid_sash(f,cx,sill,w,head,2,[sill+(head-sill)*(.59 if level=='attic' else .76)],lod,title,-.125,
                      WOOD if level!='attic' else 'Grey painted joinery')
            f.box(cx,sill-.062,w+.224,.116,.184,.028,GREY,title+'/stone sill')
            for side in(-1,1):
                f.box(cx+side*(w/2+.052),(sill+head)/2,.109,head-sill+.018,.130,.012,RED,title+'/brick jamb')
            # Narrow splayed head of vertically laid red bricks leaves actual mortar joints.
            course=Polygon([(cx-w/2-.12,head),(cx+w/2+.12,head),(cx+w/2+.18,head+.238),(cx-w/2-.18,head+.238)])
            f.prism(course,.010,.086,JOINT,title+'/flat arch joint')
            n=9 if lod else 15
            for j in range(n):
                l=(j+.04)/n;r=(j+.96)/n
                bottom=lambda t:cx+(2*t-1)*(w/2+.12)
                top=lambda t:cx+(2*t-1)*(w/2+.18)
                part=Polygon([(bottom(l),head+.007),(bottom(r),head+.007),(top(r),head+.232),(top(l),head+.232)])
                f.prism(part,.076,.107,SECOND if j%5==2 else RED,title+'/flat arch bricks')
    f.prism(face.difference(unary_union(apertures)),-.36,0,CAST,'Central brick front/opened wall')
    cap=LineString(ridge).buffer(.050,cap_style=2,join_style=2,mitre_limit=2)
    f.prism(cap,-.386,.104,RED,'Parapet/projecting curved cap')
    for i,x in enumerate([left+.098,(left+right)/2,right-.098]):
        top=float(np.interp(x,*map(np.array,zip(*ridge))))-.095
        f.box(x,(base+top)/2,.218,top-base,.119,.081,SECOND,'Parapet/three raised strips')
    for i,(z,x0,x1)in enumerate([(2.82,left,right),(6.794,left,right),(10.96,left,right),(11.44,left+.02,right-.02),(14.125,left+.03,right-.03)]):
        width=x1-x0
        for k,(dz,h,pr) in enumerate([(0,.073,.22),(.075,.067,.30),(.144,.048,.34)]):
            f.box((x0+x1)/2,z+dz,width+.022*k,h,pr,.053,GREY if k==1 else RED,'Central front/brick and stone strings')
        if i in(1,2) and not lod:
            count=max(4,round(width/.152))
            for m in range(count):
                f.box(x0+(m+.5)*width/count,z-.089,.072,.105,.133,.100,SECOND,'Central front/rectangular dentils')
