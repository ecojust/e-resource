"""Editable forged-iron strips from two photo-rectified panels on the Liang residence window."""
from collections import defaultdict
import json
import numpy as np
from window_photo import EYE,WIDTH,HEIGHT,MEASURE

FERRO='Oxide on the window grille';EDGE='Warm worn iron highlight'
PLANE=.020
PATTERN=json.loads((MEASURE/'iron-grille-traces.json').read_bytes())
R,H=PATTERN['rectified_pixels']
def to_plane(points,y):
    px=np.array(points,float);xz=np.column_stack([(px[:,0]/R-.5)*WIDTH,(1-px[:,1]/H)*HEIGHT])
    ratio=(y-EYE[1])/-EYE[1]
    return EYE[[0,2]]+(xz-EYE[[0,2]])*ratio

def add_strand(storage,points,width,label,lod=False):
    points=np.asarray(points,float)
    d=np.diff(points,axis=0);keep=np.r_[True,np.linalg.norm(d,axis=1)>1.e-5];points=points[keep]
    if len(points)<2:return
    difference=np.diff(points,axis=0);length=np.linalg.norm(difference,axis=1)
    directions=difference/length[:,None];tn=np.vstack([directions[0],directions[:-1]+directions[1:],directions[-1]])
    bad=np.linalg.norm(tn,axis=1)<1.e-4
    if bad.any():tn[bad]=np.vstack([directions,directions[-1]])[bad]
    tn/=np.linalg.norm(tn,axis=1)[:,None];normal=np.column_stack([-tn[:,1],tn[:,0]])
    # A flat iron strip has dark sides and small rubbed bevels. Keep an actual
    # rectangular section even in the distance view, so the holes continue through.
    if lod:
        profile=[(-.50,.008),(-.50,0),(.50,0),(.50,.008)]
    else:
        profile=[(-.50,.0065),(-.50,.0018),(-.36,0),(.36,0),(.50,.0018),(.50,.0065),(.36,.008),(-.36,.008)]
    count=len(profile);verts,faces=storage[label];offset=len(verts)
    for p,n in zip(points,normal):
        for width_factor,depth in profile:
            x,z=p+n*width*width_factor;verts.append((x,PLANE+depth,z))
    for step in range(len(points)-1):
        ia=offset+step*count;ib=ia+count
        for e in range(count):
            f=(e+1)%count;faces.append((ia+e,ib+e,ib+f,ia+f))
    faces.extend((tuple(offset+j for j in range(count)),tuple(offset+(len(points)-1)*count+j for j in reversed(range(count)))))

def grille(builder,lod):
    groups=defaultdict(lambda:([],[]))
    for curve in PATTERN['paths']:
        # In a tight coil even a subpixel chord change cuts across the strip.
        # Both distances retain the measured centreline. The cross section above
        # changes from eight edges to four in the distance mesh.
        pixels=np.asarray(curve['xy'])
        points=to_plane(pixels,PLANE)
        width=np.clip(curve['measured_width_px']*.91,1.65,3.55)*WIDTH/R
        label=curve['panel'].title()+' iron/'+curve['group']+' scrolls '+str(curve['section'])
        add_strand(groups,points,width,label,lod)
    # The projecting outer frames and two long stiles remain continuous where
    # glints, bolt heads and timber beads interrupt the photographed edge.
    outlines={'tall border':[[38,37],[440,35],[441,621],[37,624],[38,37]],
            'lower border':[[38,661],[441,660],[442,843],[38,846],[38,661]],
            'left tall division':[[105,38],[104,241],[104,416],[104,622]],
            'right tall division':[[375,35],[375,243],[375,415],[375,621]]}
    for name,pixels in outlines.items():
        add_strand(groups,to_plane(pixels,PLANE-.002),.0093,'Iron edging/'+name,lod)
    for label,(verts,faces)in groups.items():
        builder.add(verts,faces,FERRO,label)
