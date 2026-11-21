"""Construct the two kinds of concrete lattice seen on the old abattoir's western facade."""
import math
import numpy as np
from shapely.geometry import Point,box
from shapely.ops import unary_union
from aggregate_finish import CAST

EDGE='Pale concrete screen arris'
SHADE='Deep grey concrete reveal'
METAL='Blackened window metal'
PALE='Upper blue-grey glazing'
MID='Grey-green glazing'
DARK='Shadowed shop glazing'
LOW='Lower circular glazing'
GLASS_ALPHA={LOW:.28,MID:.23,PALE:.19}


def annular_lip(f,u,z,pitch,radius,segments,front):
    # A narrowing rounded arris is visible from the exterior; the back face is
    # squared off. Use closed, finite strips around the actual centre aperture.
    section=[(radius+.021*pitch,front-.011),(radius+.043*pitch,front+.008),
             (radius+.047*pitch,front+.025),(radius+.027*pitch,front+.038),
             (radius+.003*pitch,front+.023),(radius-.003*pitch,front+.006)]
    vs=[]
    for r,d in section:
        for k in range(segments):
            a=2*math.pi*k/segments;vs.append(f.point(u+r*math.cos(a),z+r*math.sin(a),d))
    faces=[]
    for j in range(len(section)):
        nj=(j+1)%len(section)
        for k in range(segments):
            nk=(k+1)%segments;faces.append([j*segments+k,j*segments+nk,nj*segments+nk,nj*segments+k])
    f.builder.add(vs,faces,EDGE,f.label+'/Rolled circle arrises')


def screen(f,u,bottom,pitch,rows,regular,lod):
    """Cast a whole leaf in one slab. All holes penetrate its true thickness."""
    seg=5 if lod else 12;ns=seg*4
    hw=(1.230 if regular else .505)*pitch
    top=bottom+rows*pitch
    slab=box(u-hw,bottom,u+hw,top)
    holes=[];ri=.349*pitch;ro=.452*pitch
    for i in range(rows):
        z=bottom+(i+.5)*pitch
        cen=Point(u,z);outer=cen.buffer(ro,quad_segs=seg)
        clear=cen.buffer(ri,quad_segs=seg)
        holes.append(clear)
        centre_cell=box(u-.411*pitch,z-.441*pitch,u+.411*pitch,z+.441*pitch)
        # Small corner openings between the circular band and the square frame survive.
        holes.append(centre_cell.difference(outer))
        if regular:
            for sign in (-1,1):
                for j in (.676,1.035):
                    mid=u+sign*j*pitch
                    for level in (-.25,.25):
                        zz=z+level*pitch
                        holes.append(box(mid-.122*pitch,zz-.185*pitch,mid+.122*pitch,zz+.185*pitch))
        # The circular panes seen from Sha Jing Road sit behind the cast screen.
        # A single surface prevents double attenuation through a thin pane. Its
        # planar outline stops at the reveal, leaving the corner vents open.
        ring=list(clear.exterior.coords)[:-1]
        vertices=[f.point(u,z,-.377)]+[f.point(x,y,-.377) for x,y in ring]
        faces=[(0,(k+1)%len(ring)+1,k+1) for k in range(len(ring))]
        mat=LOW if i<4 else MID if i<8 else PALE
        f.builder.add(vertices,faces,mat,f.label+'/Inset circular panes')
        if not lod:
            annular_lip(f,u,z,pitch,ri,ns,-.145)
    f.prism(slab.difference(unary_union(holes)),-.357,-.145,CAST,'Perforated concrete')
    for i in range(4,rows,4):
        f.box(u,bottom+i*pitch,2*hw,.052,.062,-.45,METAL,'Floor-level metal transoms')
    for sign in (-1,1):
        f.box(u+sign*(hw-.032),(bottom+top)/2,.065,rows*pitch,.063,-.44,METAL,'Glazing edge stiles')
