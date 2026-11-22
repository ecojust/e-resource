"""Two second-storey windows and the striped street corner of the Metropole East Wing."""
from pathlib import Path
from math import sqrt
import numpy as np
from shapely.geometry import Polygon, box
from profile_tools import BRICK, cb, slab, bricks_uv

STONE='Pale quoin stone'
CAP='Light window hood'
EDGE='Dark drip moulding'
FRAME='Recessed dark window frame'
GLASS='Street-facing window glass'
METAL='Slender projecting iron rails'
SILL='Horizontal sill and cornice'
PALETTE={}
for title,rgb in [(BRICK,(255,255,255)),(STONE,(209,199,187)),(CAP,(195,186,174)),(EDGE,(101,89,84)),(FRAME,(80,69,65)),(GLASS,(65,66,65)),(METAL,(78,66,61)),(SILL,(179,167,155))]:
    PALETTE[title]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.83)
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))

LEFT=-2.42
RIGHT=2.24
CENTERS=(-.88,1.14)
SILL_Z=.47
SPRING=2.70
HALF=.56
RISE=.135
COURSE=.293
WIDTHS=(.66,.46)
def arch(x):
    radius=(HALF**2+RISE**2)/(2*RISE)
    return SPRING+sqrt(max(0,radius**2-x**2))-(radius-RISE)
def outline(xc,offset,bottom,steps):
    width=HALF+offset
    pts=[(xc-width,bottom),(xc+width,bottom)]
    for x in np.linspace(width,-width,steps+1):
        pts.append((xc+x,arch(x*HALF/width)+offset))
    return Polygon(pts)
def model(b,lod=False):
    steps=9 if lod else 30
    wall=box(LEFT,0,RIGHT,3.63)
    for xc in CENTERS:
        wall=wall.difference(outline(xc,.075,SILL_Z-.07,steps))
    slab(b,wall,0,.36,BRICK,'Red street wall with two window openings')
    cb(b,LEFT,LEFT+.17,.36,.76,0,3.63,BRICK,'Brick return at the end of the window pair')
    for i in range(11):
        z=.24+i*COURSE;le=WIDTHS[i%2]
        cb(b,LEFT-.045,LEFT+le,-.053,.045,z,z+COURSE-.026,STONE,'Alternating long and short face quoins')
        cb(b,LEFT-.046,LEFT+.08,.03,.57 if i%2 else .72,z,z+COURSE-.026,STONE,'Pale side return of the corner block')
    for xc in CENTERS:
        outer=outline(xc,.075,SILL_Z-.07,steps)
        aperture=outline(xc,0,SILL_Z,steps)
        top=box(xc-.8,SPRING-.005,xc+.8,3.12)
        slab(b,outer.difference(aperture),-.057,.135,CAP,'Pale arch and jambs')
        mould=outline(xc,.132,SILL_Z-.09,steps).difference(outline(xc,.084,SILL_Z-.083,steps))
        slab(b,mould.intersection(top),-.106,-.014,CAP,'Projecting arched hood with narrow drip')
        dark=outline(xc,.078,SILL_Z-.069,steps).difference(outline(xc,.050,SILL_Z-.044,steps))
        slab(b,dark.intersection(top),-.075,-.022,EDGE,'Dark roll under the raised hood')
        pane=outline(xc,-.037,SILL_Z+.049,steps)
        slab(b,aperture.difference(pane),.093,.172,FRAME,'Rebated dark sash frame')
        slab(b,pane,.175,.203,GLASS,'Recessed glazing')
        for x in (xc-.161,xc+.161):
            cb(b,x-.013,x+.013,.110,.157,SILL_Z+.049,arch(x-xc)-.03,FRAME,'Slender internal sash stile')
        for z in (1.45,2.26):
            cb(b,xc-HALF+.022,xc+HALF-.022,.106,.152,z-.015,z+.015,FRAME,'Window sash cross rail')
        for x in (xc-HALF-.014,xc+HALF+.014):
            cb(b,x-.012,x+.012,-.156,-.124,SILL_Z+.07,SPRING-.07,METAL,'Outer upright in front of jamb')
        for z in np.linspace(.73,2.51,10):
            cb(b,xc-HALF-.065,xc+HALF+.065,-.149,-.132,z-.008,z+.008,METAL,'Fine projecting horizontal metal rail')
        cb(b,xc-.68,xc+.68,-.125,.119,SILL_Z-.079,SILL_Z-.029,SILL,'Stone sill toe beneath each arch')
    # The sill and cornice both turn the projecting corner onto its short west face.
    for lo,hi,projection in [(0,.155,.132),(.155,.202,.087),(3.39,3.46,.071),(3.46,3.54,.110),(3.54,3.62,.145)]:
        cb(b,LEFT-projection,RIGHT,-projection,.37,lo,hi,SILL,'Continuous horizontal floor moulding')
        cb(b,LEFT-projection,LEFT+.02,.37,.76,lo,hi,SILL,'Moulding returning around the west corner')
    bricks_uv(b)
