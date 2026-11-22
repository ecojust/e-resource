"""Open wooden casements in the upper wall over the numbered 212 Nanchang entrance."""
from pathlib import Path
import json
import math
import numpy as np
from scipy.optimize import minimize_scalar
from huanlong_photo_plane import CALIBRATION,pixel

ROOT=Path(__file__).resolve().parents[1]
OBS=json.loads((ROOT/'measurements'/'212-casement-evidence.json').read_text())
WOOD="Huanlong | dark brown painted sash timber"
FRAME="Huanlong | fixed outer window casing"
PUTTY="Huanlong | weathered glazing bead"
GLASS="Huanlong | reflected casement glass"
STONE="Huanlong | grey sill nose"
SHADOW="Huanlong | shadow in window recess"
def colour(rgb,roughness,metallic=0.):
    c=np.array(rgb)/255
    return dict(color=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)
PALETTE={WOOD:colour((69,52,53),.68),FRAME:colour((56,48,48),.78),PUTTY:colour((99,87,83),.78),GLASS:colour((119,134,141),.22,.26),STONE:colour((114,117,117),.85),SHADOW:colour((42,40,39),.98)}

def openings():
    return tuple(dict(key=name,left=row['x'][0],right=row['x'][1],bottom=row['z'][0],top=row['z'][1])
                 for name,row in zip(('west','east'),CALIBRATION['local_openings']))

def leaf_geometry(row,index):
    a,b,base,head=[row[k] for k in ('left','right','bottom','top')]
    inset=.024
    hinge_x=(a+inset,(a+b)/2,b-inset)[index]
    sign=(1,-1,-1)[index]
    width=(b-a)/4-.018
    target=np.asarray(OBS['upper_free_corner_upright_px'][0 if row['key']=='west' else 1][index])
    # The east bay's west sash folds across the reveal. Set its hinge on the
    # outer arris so its open stile clears the photographed roughcast return.
    hinge_y = -.012 if row['key']=='east' and index==0 else .028
    hinge=np.array([hinge_x,hinge_y,0.])
    def direction(angle):
        t=math.radians(angle)
        return np.array([sign*math.cos(t),-math.sin(t),0.])
    def residual(angle):
        q=hinge+width*direction(angle);q[2]=head-.022
        return np.linalg.norm(np.array(pixel(q))-target)
    # The two angle branches have different depth: the photographed leaves swing out toward the pavement.
    result=minimize_scalar(residual,bounds=(32,149),method='bounded')
    d=direction(result.x)
    n=np.array([-d[1],d[0],0.])
    return hinge,d,n,width,float(result.x),float(result.fun)

def casing(builder,row):
    l,r,b,t=[row[k] for k in ('left','right','bottom','top')]
    key=row['key']
    def box(x0,x1,y0,y1,z0,z1,material,label):
        builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=key+' bay | '+label)
    for x in (l,r-.024):
        box(x,x+.024,.047,.135,b,t,FRAME,'fixed jamb')
    box(l+.024,r-.024,.047,.135,t-.030,t,FRAME,'fixed head')
    box((l+r)/2-.018,(l+r)/2+.018,.057,.130,b,t-.031,FRAME,'fixed centre post')
    box(l-.032,r+.032,-.064,.165,b-.044,b+.001,STONE,'projecting sill')
    box(l+.010,r-.010,1.14,1.16,b+.008,t-.013,SHADOW,'shadow behind the photographed open casements')

def add_windows(builder,lod=False):
    low=lod in (True,'lod')
    up=np.array([0.,0.,1.])
    for row in openings():
        casing(builder,row)
        for i in range(3):
            hinge,d,n,width,_,_=leaf_geometry(row,i)
            base=row['bottom']+.024;head=row['top']-.022
            side=.030;bottom=.052;top=.043
            a,b=base+bottom,head-top
            tag=f"{row['key']} bay, visible sash {i+1} | "
            def box(x0,x1,y0,y1,z0,z1,material,label):
                p=hinge+d*((x0+x1)/2)+n*((y0+y1)/2)+up*((z0+z1)/2)
                builder.box(p,(x1-x0,y1-y0,z1-z0),material,basis=[d,n,up],label=tag+label)
            for x in (0,width-side):
                box(x,x+side,-.015,.017,base,head,WOOD,'outer stile')
            box(side,width-side,-.015,.017,base,a,WOOD,'bottom rail')
            box(side,width-side,-.015,.017,b,head,WOOD,'top rail')
            box(width/2-.007,width/2+.007,-.009,.014,a,b,WOOD,'centre glazing bar')
            for k in (1,2,3):
                z=a+(b-a)*k/4
                for j,(x0,x1) in enumerate(((side,width/2-.007),(width/2+.007,width-side))):
                    box(x0,x1,-.009,.014,z-.008,z+.008,WOOD,f'intermediate bar {k}.{j+1}')
            for j,(x0,x1) in enumerate(((side,width/2-.007),(width/2+.007,width-side))):
                for k in range(4):
                    z0=a+(b-a)*k/4+(.008 if k else 0)
                    z1=a+(b-a)*(k+1)/4-(.008 if k<3 else 0)
                    box(x0,x1,-.002,.002,z0,z1,GLASS,f'glazed pane {j+1}.{k+1}')
                    if not low:
                        for x in (x0,x1-.004):
                            box(x,x+.004,-.006,-.002,z0,z1,PUTTY,f'glazing rebate {j+1}.{k+1}')
