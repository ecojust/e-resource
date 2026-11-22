"""Two terrace rockers traced independently in the historic sun-deck photograph."""
import json
import numpy as np
from scipy.interpolate import PchipInterpolator
from terraced_section import HERE, UPPER

TRACE=json.loads((HERE.parent/'measurements/chair-profiles.json').read_bytes())['chairs']
TUBE='Aged bright steel tube'
FABRIC='Pale woven chair sling'
SEAM='Bound canvas seam'

def curves(points,segments,keep_controls=False):
    pts=np.asarray(points,dtype=float)
    keep=np.r_[True,np.linalg.norm(np.diff(pts,axis=0),axis=1)>.00005]
    pts=pts[keep];t=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    if len(pts)==2:return pts
    parameters=np.linspace(0,t[-1],segments)
    if keep_controls:parameters=np.unique(np.r_[parameters,t])
    return PchipInterpolator(t,pts)(parameters)

def shaft(b,points,radius,lod,label):
    spline=curves(points,max(6,len(points)*(2 if lod else 4)),keep_controls=True)
    b.tube(spline+[0,0,UPPER+.020],radius,TUBE,6 if lod else 12,label)

def cloth(b,a,c,lod,label):
    # The canvas meets the two rails; the unsupported middle has a shallow transverse sag.
    along=12 if lod else 32;across=4 if lod else 10
    a=curves(a,along);c=curves(c,along)
    if len(a)==2:a=np.linspace(a[0],a[1],along)
    if len(c)==2:c=np.linspace(c[0],c[1],along)
    vertices=[];faces=[]
    for i,(p,q)in enumerate(zip(a,c)):
        for j,t in enumerate(np.linspace(0,1,across+1)):
            vertices.append((1-t)*p+t*q+[0,0,UPPER+.02-.026*4*t*(1-t)])
            if i and j:
                k=i*(across+1)+j;faces.append((k-across-2,k-1,k,k-across-1))
    b.add(vertices,faces,FABRIC,label+'/woven canvas')
    for i,edge in enumerate([a,c]):
        b.tube(edge+[0,0,UPPER+.020],.0065,SEAM,5 if lod else 8,label+'/canvas binding '+str(i+1))

def chairs(b,lod):
    for role,spec in TRACE.items():
        front=role=='near_chair';label='Near chair' if front else 'Far chair';disp=np.r_[spec['second_side_displacement_xy'],0.]
        path={k:np.asarray(v) for k,v in spec['lifted_traces'].items()}
        primary=path['outer_rocker'];opposite=path['inner_rocker']
        if front:
            shaft(b,primary,.011,lod,label+'/visible outward rocker')
            shaft(b,primary+disp,.011,lod,label+'/opposite rocker')
            for i in range(2):shaft(b,path['visible_tail']+i*disp,.011,lod,label+'/folded rear foot '+str(i+1))
            # The short independent inside arc records the return tube below the seat, where the two frames overlap.
            shaft(b,opposite,.009,lod,label+'/inner bent support')
            back=path['back_tube'];cloth(b,back[4:],back[4:]+disp,lod,label+'/back')
            shaft(b,[back[0],back[0]+disp],.011,lod,label+'/upper cross tube')
            # The folded fabric at the back/seat hinge is hidden in the photograph.
            # Join both traced panels at the supporting tube with a narrow canvas strip.
            near=np.vstack([back[-1],path['seat_near']]);far=np.vstack([back[-1]+disp,path['seat_far']]);cloth(b,near,far,lod,label+'/seat')
            for i in range(2):
                shaft(b,back+i*disp,.010,lod,label+'/inclined seat back '+str(i+1))
            for i in [0,1]:
                shaft(b,[primary[i*8],primary[i*8]+disp],.0085,lod,label+'/transverse tube '+str(i+1))
        else:
            # Two low pivots are seen almost superposed. Separate them using the width of the photographed head loop.
            for i in range(2):
                shaft(b,primary+i*disp,.0105,lod,label+'/front bow '+str(i+1))
                shaft(b,opposite-i*disp,.0105,lod,label+'/long lower return '+str(i+1))
            a=path['back_tube'];c=path['back_opposite'];cloth(b,a,c,lod,label+'/back')
            shaft(b,path['back_hoop'],.009,lod,label+'/open rectangular head loop')
            for i,edge in enumerate([a,c]):shaft(b,edge,.010,lod,label+'/back upright '+str(i+1))
            a1=np.array([a[-1],primary[0],primary[-1]]);c1=np.array([c[-1],primary[0]+disp,primary[-1]+disp]);cloth(b,a1,c1,lod,label+'/seat')
            shaft(b,[primary[-1],primary[-1]+disp],.010,lod,label+'/seat foot crossbar')
        for i in range(2):shaft(b,path['arm']+i*disp,.009,lod,label+'/rounded arm '+str(i+1))
