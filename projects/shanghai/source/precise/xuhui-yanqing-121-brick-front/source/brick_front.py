"""Five-window grey brick front with soldier courses, herringbone panels and a stepped parapet."""
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from brick_finishes import GREY_BRICK,HERRINGBONE,RED_BAND
from masonry_details import grille,herringbone_panel,window_jambs
from front_layout import LEFT,RIGHT,OPENINGS,PARAPET
from materials import BROWN,CREAM,DARK,GLASS,GREEN,PALE,STONE,WHITE

def frame(f,hole,name,mat,cols,rails):
    x0,z0,x1,z1=hole.bounds
    inner=hole.buffer(-.040,join_style=2)
    f.solid(hole,-.127,-.105,DARK,name+' | deep perimeter')
    f.solid(inner,-.100,-.090,GLASS,name+' | glass')
    f.solid(hole.difference(inner),-.099,-.031,mat,name+' | outer casement')
    for i in range(1,cols):
        x=x0+i*(x1-x0)/cols;rad=.020 if i*2==cols else .010
        f.rect(x-rad,x+rad,z0+.024,z1-.023,-.09,-.038,mat,name+' | central meeting rail')
    for k in rails:
        z=z0+(z1-z0)*k
        f.rect(x0+.025,x1-.025,z-.016,z+.016,-.09,-.046,mat,name+' | horizontal glazing bar')

def add_front(f,lod):
    voids=unary_union(list(OPENINGS.values()))
    face=box(LEFT,0,RIGHT,6.3).difference(voids)
    f.solid(face,-.24,0,GREY_BRICK,'long street wall | grey Flemish masonry')
    for z,h in [(.89,.115),(2.73,.115),(4.25,.105),(6.11,.12)]:
        f.solid(box(LEFT,z,RIGHT,z+h).difference(voids),-.006,.008,RED_BAND,'street wall | horizontal soldier course')
    f.solid(box(LEFT,.015,RIGHT,.215).difference(voids),-.009,.047,STONE,'street wall | grey plinth')
    for key,hole in OPENINGS.items():
        x0,z0,x1,z1=hole.bounds;mid=(x0+x1)/2;name='street facade | '+key
        if key not in ('paired_green_light','green_entry_door','lower_dark_east'):
            surround=box(x0-.095,z0-.012,x1+.095,z1+.135).difference(hole)
            f.solid(surround,-.002,.020,RED_BAND,name+' | red jambs and head')
            if not lod:window_jambs(f,hole,name)
        if key=='green_entry_door':
            f.solid(hole,-.12,-.074,GREEN,name+' | recessed door leaf')
            f.rect(x1-.087,x1-.062,z0+.70,z0+.82,-.075,-.043,STONE,name+' | small metal handle');continue
        if key=='lower_louver':
            f.solid(hole,-.15,-.13,DARK,name+' | shadow inside louvres')
            for i in range(12):
                z=z0+.055+i*(z1-z0-.11)/12
                f.rect(x0+.027,x1-.027,z,z+.055,-.115,-.035,BROWN,name+' | horizontal slat')
        else:
            white=('white' in key or key in ['lower_glass_west','lower_glass_mid']);mat=WHITE if white else GREEN if key=='paired_green_light' else BROWN
            rails=() if 'white' in key or key=='paired_green_light' else (.67,.86) if 'lower' in key else (.30,.67)
            frame(f,hole,name,mat,2 if white or 'green' in key or 'lower' in key else 4,rails)
        f.rect(x0-.055,x1+.055,z0-.078,z0-.009,-.009,.078,STONE,name+' | projecting sill')
        if key.startswith('upper'):
            panel=box(x0,3.15,x1,4.19);rim=panel.buffer(.032,join_style=2).difference(panel)
            f.solid(panel,.005,.014,HERRINGBONE,name+' | herringbone spandrel')
            if not lod:herringbone_panel(f,panel,name)
            f.solid(rim,.004,.019,BROWN,name+' | spandrel edging')
            for x in (x0-.125,x1+.125):f.rect(x-.044,x+.044,2.86,4.26,.002,.012,RED_BAND,name+' | red brick strip')
    for z0,z1,back,front,mat,name in [(6.23,6.30,-.18,.076,STONE,'thin lower moulding'),(6.30,7.02,-.21,.024,CREAM,'rendered fascia'),(7.02,7.11,-.21,.143,DARK,'dark soffit'),(7.11,7.21,-.24,.19,STONE,'projecting cornice'),(7.21,PARAPET,-.23,-.015,PALE,'grey rendered parapet'),(PARAPET-.016,PARAPET+.046,-.25,.025,STONE,'stepped coping')]:
        f.rect(LEFT,RIGHT,z0,z1,back,front,mat,'long street wall | '+name)
    for x in [-12.2,-7.1,-1.92]:
        f.rect(x-.085,x+.085,7.21,PARAPET+.09,-.25,.017,PALE,'parapet | projecting pier')
    for x,z0,z1 in [(-9.36,.15,6.78),(-1.54,.12,6.73)]:
        f.rail([(x,-.075,z0),(x,-.075,z1-.31),(x+.087,-.086,z1-.20),(x+.087,-.086,z1)],.045,WHITE,'front | downpipe',6 if lod else 12)
    # The right edge of the flat frontage returns towards the recessed arched opening.
    f.face(RIGHT,0,0,1).rect(0,1.24,0,6.26,-.14,0,GREY_BRICK,'west end of brick front | stepped return')
    f.face(RIGHT,0,0,1).rect(0,1.24,6.26,PARAPET,-.14,0,CREAM,'west end of brick front | upper return')
    for a,b in [(-4.03,-3.57),(-2.69,-2.30)]:grille(f,a,b,.93,2.43,lod,'lower west window')
    # Two attached canopies are visible in the dated street photograph below the brick panels.
    for x0,x1,top,depth,mat,name in [(-7.57,-4.67,2.92,.37,BROWN,'brown shop canopy'),(-3.62,-2.08,2.90,.25,STONE,'metal window hood')]:
        fall=.105
        f.b.prism(box(x0,-depth,x1,.005),-.045,0,lambda x,d,t:f.point(x,d,top+d*fall/depth+t),mat,'street facade | '+name)
        f.face(0,-depth,1,0).rect(x0,x1,top-fall-.15,top-fall+.012,-.045,0,mat,'street facade | '+name+' valance')
        for x in (x0+.09,x1-.09):f.rail([(x,.0,top-.28),(x,-depth+.022,top-fall-.06)],.012,DARK,name+' | bracket',5 if lod else 8)
