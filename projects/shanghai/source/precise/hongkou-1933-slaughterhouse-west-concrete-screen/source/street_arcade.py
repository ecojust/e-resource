"""Continuous shaped arcade edge, square piers, ornamented caps, and the projecting entrance."""
import math,json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point,LineString,box
from aggregate_finish import CAST
from pierced_screens import EDGE,SHADE,METAL,PALE,MID,DARK

DRESS='Warm limestone-grey coping'
SOFFIT='Dark soffit concrete'
FLOOR='Worn concrete paving'
INSET='Subdued facade medallions'
LETTER='Pale cast letters'


def shaped_opening(width,top,centre):
    if centre:
        pts=[(-width/2,.035),(width/2,.035),(width/2,top-.065),(width/2-.095,top),(-width/2+.095,top),(-width/2,top-.065)]
    else:
        # Photographs show two raised shoulders in each opening and a shallow central drop.
        pts=[(-width/2,.035),(width/2,.035)]
        for t in np.linspace(1,0,27):
            z=top+.35*math.sin(2*math.pi*t)**2+.055*math.sin(math.pi*t)
            pts.append(((t-.5)*width,z))
    return Polygon(pts)


def pier(b,u,p,wide,lod):
    # On either side of the entry the square shaft broadens at the head. Its
    # chamfered lower edges turn into the shallow triangular grooves below the capital.
    depth=.84 if wide else .73
    for j,(zz0,zz1,r0,r1) in enumerate(((.045,.24,.387,.383),(.24,2.64,.383,.371),(2.64,3.52,.371,.505),(3.52,3.72,.505,.54))):
        def corners(r,z):
            xy=[(-r+.087,-r), (r-.087,-r),(r,-r+.087),(r,r-.087),(r-.087,r),(-r+.087,r),(-r,r-.087),(-r,-r+.087)]
            return [(x+depth*.23,-u+y,z)for x,y in xy]
        vv=corners(r0,zz0)+corners(r1,zz1);fs=[[7-i for i in range(8)],[8+i for i in range(8)]]
        fs.extend([[i,(i+1)%8,8+(i+1)%8,8+i]for i in range(8)])
        b.add(vv,fs,CAST,'Arcade / tapered octagonal-edged piers')
    if not lod:
        from photo_architecture import Facade
        f=Facade(b,[-.23,-u+.36],[-.23,-u-.36],'Street piers')
        for k in (-.214,0,.214):
            f.prism(Polygon([(k-.078,3.47),(k+.078,3.47),(k,3.04)]),.023,.047,DRESS,'Tapered capital flutes')


def plaque(f,base,cap_width,lod):
    ww=cap_width*.86
    # The shallow rounded tympanum meets short horizontal shoulders, above the straight portal lintel.
    y=base+.91;theta=np.linspace(math.pi,0.,14 if lod else 36);cx=ww*.35
    top=[(-ww/2,y),(-cx,y)]+[(float(cx*math.cos(t)),float(y+.69*math.sin(t))) for t in theta[1:-1]]+[(cx,y),(ww/2,y)]
    face=Polygon([(-ww/2,base), (ww/2,base),*reversed(top)])
    f.prism(face,.31,.351,INSET,'Shallow entrance tablet')
    f.prism(LineString(top).buffer(.025,join_style=2),.351,.376,SHADE,'Recessed tablet border')

    # Windmemories' 2026 west elevation resolves all three lines on the
    # present-day entrance sign. The contours use open-licensed fonts.
    glyphs=json.loads(Path(__file__).with_name('entrance-letters.json').read_bytes())
    for row in glyphs[:3] if lod else glyphs:
        for shell,*holes in row['polygons']:
            def place(loop):return [(x,base+.15+z) for x,z in loop]
            shape=Polygon(place(shell),[place(h) for h in holes])
            if shape.area>1.e-5:
                f.prism(shape,.385,.419,LETTER,'Entrance lettering')


def entrance_returns(f,p,lod):
    width=p['entrance_clear_width'];h=p['arcade_impost'];depth=p['cut_depth']
    for side in (-1,1):
        f.box(side*(width/2+.11),h/2,.22,h,depth-1.14,-(depth+1.14)/2,SOFFIT,'Entrance passage jambs')
    for distance in (1.39,2.87):
        f.box(0,h-.082,width,.165,.16,-distance,DRESS,'Passage ceiling ribs')


def arcade(f,p,centre,lod):
    top=p['arcade_impost'];sill=p['central_sill'] if centre else p['ordinary_sill']
    clear=p['entrance_clear_width'] if centre else f.length-.62
    hole=shaped_opening(clear,top,centre)
    f.prism(box(-f.length/2,.06,f.length/2,sill+.068).difference(hole),-1.25,.315 if centre else .033,CAST,'Arcade and deep shaped lintel')
    # A shallow continuous floor and ceiling give the lower passage its real depth.
    f.box(0,.07,f.length,.14,p['cut_depth']+.11,-p['cut_depth']/2+.03,FLOOR,'Street arcade paving')
    f.box(0,top+.13,f.length,.17,p['cut_depth']-1.15,-(p['cut_depth']+1.15)/2,SOFFIT,'Arcade soffit')
    if centre:
        plaque(f,top+.24,p['entrance_cap_width'],lod)
        entrance_returns(f,p,lod)
    else:
        disc=Point(0,sill-.99).buffer(.47,quad_segs=10 if lod else 24)
        f.prism(disc,.034,.053,INSET,'Circular fascia medallion')
        # The exterior panels retain a shallow stylized inset relief. The fine
        # figure varies among bays; only its circular setting is repeated here.
        for end in (-1,1):
            f.box(end*(f.length/2-.42),sill-1.20,.16,1.66,.052,.064,DRESS,'Incised upright fascia ends')
    if not centre:
        # Existing dark inner storefront line is set back behind the old portico.
        for x in (-f.length*.27,f.length*.27):
            aperture=box(x-f.length*.202,.26,x+f.length*.202,top-.11)
            f.prism(aperture,-p['cut_depth']+.015,-p['cut_depth']+.045,DARK,'Recessed shop glazing')
            frame=aperture.difference(aperture.buffer(-.069,join_style=2))
            f.prism(frame,-p['cut_depth']+.061,-p['cut_depth']+.105,METAL,'Shopfront frame')
