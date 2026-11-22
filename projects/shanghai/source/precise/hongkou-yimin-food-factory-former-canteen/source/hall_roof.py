"""The tiled hip and small exposed gable at either end of the long roof."""
from math import ceil,pi
import numpy as np
from shapely.geometry import Polygon,box
from hall_coordinates import WIDTH,LENGTH
from hall_masonry import GABLE,TRIM,SOFFIT,section,finish
from material_names import TILE

RIDGE='Yimin canteen | rounded dark ridge caps'
FLASH='Yimin canteen | grey gable flashing'
PALETTE={RIDGE:finish([98,82,77]),FLASH:finish([115,114,116],.68,.14)}
EAVE=7.85
PEAK=12.0
FOOT=10.12
SETBACK={'northwest':5.20,'southeast':5.36}
EXT=.46
LEFT=4.97
RIGHT=WIDTH-LEFT

def roof_panel(b,outline,name):
    if not Polygon([(a,c)for a,c,z in outline]).exterior.is_ccw:outline=outline[::-1]
    n=len(outline);verts=[(a,c,z-.105)for a,c,z in outline]+list(outline)
    faces=[list(range(n-1,-1,-1)),list(range(n,2*n))]
    faces.extend([i,(i+1)%n,(i+1)%n+n,i+n]for i in range(n))
    b.add(verts,faces,TILE,name)

def roof_roll(b,a,c,r,mat,label,sides=8):
    p=np.asarray(a);q=np.asarray(c);axis=q-p;axis/=np.linalg.norm(axis)
    right=np.cross(axis,[0.,0.,1.]);right/=np.linalg.norm(right)
    up=np.cross(axis,right)
    ring=np.array([np.cos(t)*right*r+np.sin(t)*up*r for t in np.arange(sides)*2*pi/sides])
    v=np.r_[p+ring,q+ring];n=len(ring)
    f=[list(range(n-1,-1,-1)),list(range(n,n*2))]+[[i,(i+1)%n,(i+1)%n+n,i+n]for i in range(n)]
    b.add(v,f,mat,label)

def caps(b,start,end,r,tag,lod):
    a=np.asarray(start,dtype=float);c=np.asarray(end,dtype=float)
    # The continuous dark bead is visible from the two photographed approaches.
    roof_roll(b,a,c,r,RIDGE,tag,8 if lod else 12)
    if lod:return
    n=ceil(np.linalg.norm(c-a)/.36)
    for i in range(1,n):
        t=i/n;lo=max(0,t-.021/n);hi=min(1,t+.068/n)
        roof_roll(b,a+lo*(c-a),a+hi*(c-a),r+.012,RIDGE,tag+' joints')

def add_roof(b,lod=False):
    a=SETBACK['northwest'];c=LENGTH-SETBACK['southeast'];h=WIDTH/2
    for edge,foot in [(-EXT,LEFT),(WIDTH+EXT,RIGHT)]:
        p=[(edge,-EXT,EAVE),(foot,a,FOOT),(foot,c,FOOT),(edge,LENGTH+EXT,EAVE)]
        roof_panel(b,p,'Lower long tiled slope')
        p=[(foot,a,FOOT),(h,a,PEAK),(h,c,PEAK),(foot,c,FOOT)]
        roof_panel(b,p,'Upper long tiled slope')
    for face,y,stop,ori in [('northwest',-EXT,a,1),('southeast',LENGTH+EXT,c,-1)]:
        corners=[(-EXT,y,EAVE),(WIDTH+EXT,y,EAVE),(RIGHT,stop,FOOT),(LEFT,stop,FOOT)]
        roof_panel(b,corners,face.title()+' low tiled hip')
        distance=SETBACK[face]
        # The pale rendered triangle starts at the high edge of the end hip.
        shape=Polygon([(LEFT,FOOT-.05),(RIGHT,FOOT-.05),(h,PEAK-.055)])
        section(b,face,shape,distance+.037,distance+.24,GABLE,face.title()+' pale gable')
        for side,foot in [(-EXT,LEFT),(WIDTH+EXT,RIGHT)]:
            caps(b,[side,y,EAVE+.025],[foot,stop,FOOT+.024],.066,'Hip rolls',lod)
            p0=np.array([foot,stop-.008*ori,FOOT+.024]);p1=np.array([h,stop-.008*ori,PEAK+.024])
            roof_roll(b,p0,p1,.086,FLASH,face.title()+' gable verge')
            # Folded grey bargeboards below the inclined metal edge are visible on the white triangle.
            xclose=h if face=='northwest' else WIDTH-h
            f_local=foot if face=='northwest' else WIDTH-foot
            strip=Polygon([(f_local,FOOT+.013),(xclose,PEAK+.013),(xclose,PEAK-.207),(f_local,FOOT-.185)])
            section(b,face,strip,distance-.045,distance+.04,TRIM,face.title()+' fascia on gable')
    caps(b,[h,a,PEAK+.028],[h,c,PEAK+.028],.083,'Long ridge cap',lod)
    for face,span in [('northwest',WIDTH),('southeast',WIDTH),('street',LENGTH),('canal',LENGTH)]:
        section(b,face,box(-EXT,7.521,span+EXT,7.612),-.32,.04,SOFFIT,face.title()+' projecting soffit')
        section(b,face,box(-EXT,7.604,span+EXT,7.778),-.411,-.18,TRIM,face.title()+' fascia board')
        section(b,face,box(-EXT,7.765,span+EXT,7.845),-.461,-.24,FLASH,face.title()+' eave rim')
