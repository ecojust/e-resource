"""No.19 side elevation and the glazed end underneath the garden terrace."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from courtyard_side_windows import openings, pigment
from material_names import MATERIAL, TEXTURE
from ochre_brick import make_texture, apply_uv

ROUGH='No19 | warm grey roughcast'
POWDER='No19 | white moulded stone'
REVEAL='No19 | shaded window reveal'
RED='No19 | dark oxblood timber'
GREEN='No19 | garden green head boards'
GLASS='No19 | shadowed window glass'
BLUE='No19 | blue-grey reflection'
DRAIN='No19 | weathered metal drainpipe'
FASCIA='No19 | russet timber fascia'
TILES='No19 | dark terracotta roof tiles'
TILERIM='No19 | curved tile lip'
SOFFIT='No19 | warm soffit boards'
METAL='No19 | old painted metal cage'
GROOVE='No19 | mortar and panel recess'
PALETTE={name:pigment(rgb,r,m) for name,rgb,r,m in [
    (ROUGH,(171,171,160),.96,0),(POWDER,(212,209,194),.88,0),
    (REVEAL,(117,111,97),.93,0),(RED,(107,46,33),.68,0),
    (GREEN,(53,93,73),.71,0),(GLASS,(55,52,47),.30,.14),
    (BLUE,(95,125,138),.28,.17),(DRAIN,(84,81,66),.78,.12),
    (FASCIA,(129,59,40),.82,0),(TILES,(106,76,64),.91,0),
    (TILERIM,(124,90,72),.90,0),(SOFFIT,(177,158,128),.88,0),
    (METAL,(141,138,119),.75,.12),(GROOVE,(146,139,120),.96,0)]}
PALETTE[MATERIAL]={'color':[1.,1.,1.],'texture':str(TEXTURE),'roughness':.92}

def block(b,x0,x1,y0,y1,z0,z1,material,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=name)

def yz(b,polygon,x0,x1,material,name):
    b.prism(polygon,x0,x1,lambda y,z,x:(x,y,z),material,name)

def xz(b,polygon,y0,y1,material,name):
    b.prism(polygon,-y1,-y0,lambda x,z,d:(x,-d,z),material,name)

def cut(shape,apertures):
    return shape.difference(unary_union([box(*rect) for rect in apertures]))

# Extra visible apertures measured on the rectified long wall. The three
# recessed red/blue window assemblies are supplied separately.
SIDE_OTHER=[
    ('caged central',-5.83,4.77,-4.59,6.74,2,3),
    ('lower central red',-7.69,2.96,-6.64,4.21,2,2),
    ('rear lower near',-9.51,4.83,-8.86,6.41,1,2),
    ('rear lower far',-11.15,4.75,-10.42,6.34,1,2),
    ('ground enclosed',-3.08,1.32,-1.12,3.12,3,2),
    ('rear upper slim',-9.60,6.58,-9.12,8.18,1,2)]
# Span coordinate for the end façade is +Y. The three unequal upper lights
# occupy the photographed opening, between a brick pier and an exposed jamb.
END_OPENINGS=[
    ('high garden end',.71,4.58,3.39,6.37),
    ('return blue window',4.10,4.03,5.68,6.22),
    ('ground garden end',.60,.08,3.21,3.03)]
UPPER_OPENINGS=[('terrace door',.15,7.49,1.43,9.78),
                ('upper glazed return',2.96,7.87,5.79,10.56)]

def _glazing(b,axis,face,opening,columns,rows,frame,glass,key,lod):
    _,l,bottom,r,top=opening
    deep=.12
    def part(a,c,h,j,d0,d1,mat,label):
        shape=box(a,h,c,j)
        if axis=='end':
            yz(b,shape,face-d1,face-d0,mat,key+' | '+label)
        else:
            xz(b,shape,face+d0,face+d1,mat,key+' | '+label)
    # Each reveal ends at a glass back. The dark jambs remain visible in a
    # grazing view from the courtyard.
    jamb=.047
    for a,c in ((l,l+jamb),(r-jamb,r)):
        part(a,c,bottom,top,0,deep+.055,REVEAL,'masonry reveal')
    for h,j in ((bottom,bottom+jamb),(top-jamb,top)):
        part(l+jamb,r-jamb,h,j,0,deep+.055,REVEAL,'head and sill returns')
    part(l+jamb,r-jamb,bottom+jamb,top-jamb,deep+.056,deep+.095,glass,'recessed panes')
    for a,c in ((l+jamb,l+jamb+.045),(r-jamb-.045,r-jamb)):
        part(a,c,bottom+jamb,top-jamb,deep,deep+.058,frame,'outer jamb')
    for h,j in ((bottom+jamb,bottom+jamb+.045),(top-jamb-.045,top-jamb)):
        part(l+jamb,r-jamb,h,j,deep-.003,deep+.060,frame,'timber rails')
    for fraction in columns:
        u=l+(r-l)*fraction
        part(u-.026,u+.026,bottom+jamb,top-jamb,deep-.010,deep+.060,frame,'vertical sash')
    for fraction in rows:
        z=bottom+(top-bottom)*fraction
        part(l+jamb,r-jamb,z-.018,z+.018,deep-.009,deep+.059,frame,'cross sash')
    if not lod:
        part(l+jamb,r-jamb,top-jamb-.064,top-jamb-.05,deep-.011,deep+.005,frame,'head glazing bead')

def side_fabric(b,lod):
    all_holes=[(x['left'],x['bottom'],x['right'],x['top']) for x in openings()]
    all_holes.extend([tuple(row[1:5]) for row in SIDE_OTHER])
    outline=Polygon([(-11.85,0),(0,0),(0,10.46),(-8.92,10.48),(-11.85,9.53)])
    xz(b,cut(outline,all_holes),0,.33,ROUGH,'Main long wall | south courtyard')
    for key,l,bot,r,top,cols,rows in SIDE_OTHER:
        _glazing(b,'side',0,(key,l,bot,r,top),[i/cols for i in range(1,cols)],
                 [i/rows for i in range(1,rows)],RED,GLASS,key,lod)
    for key,l,r,z0,z1 in [('upper square relief',-6.19,-4.70,6.83,8.17),
                           ('stepped square relief',-8.05,-6.40,5.08,6.38)]:
        block(b,l,r,-.037,.015,z0,z1,POWDER,key+' | stone plate')
        for x in (l+.08,r-.13):
            block(b,x,x+.047,-.063,-.036,z0+.082,z1-.080,POWDER,key+' | raised edge')
        for z in (z0+.08,z1-.13):
            block(b,l+.08,r-.08,-.062,-.037,z,z+.047,POWDER,key+' | horizontal edge')
        for sign in (-1,1):
            x=(l+r)/2;z=(z0+z1)/2;h=(z1-z0)*.17;w=(r-l)*.20
            # Two shallow tapering diagonals can be distinguished in the panel.
            b.tube([(x-w,-.049,z-sign*h),(x,-.065,z),(x+w,-.049,z+sign*h)],
                   .014,POWDER,6,key+' | diagonal relief')
    for count,(l,r,bot,top,depth) in enumerate([(-5.96,-4.47,4.75,6.84,.35),(-3.39,-.85,1.25,3.23,.57)]):
        name='Window guard '+str(count+1)
        for x in (l,r):
            block(b,x-.024,x+.024,-depth,-.025,bot,bot+.045,METAL,name+' | bottom bracket')
            block(b,x-.024,x+.024,-depth,-.025,top-.042,top,METAL,name+' | top bracket')
        for z in (bot,bot+.12,top-.11,top):
            block(b,l,r,-depth-.02,-depth+.020,z,z+.025,METAL,name+' | rails')
        n=9 if count==0 else 16
        for x in np.linspace(l,r,n):
            block(b,x-.014,x+.014,-depth-.010,-depth+.014,bot,top,METAL,name+' | vertical bar')
    for x,top,depth in [(-4.63,10.45,.10),(-9.50,9.98,.07),(-.33,7.15,.055)]:
        b.tube([(x,-depth,.18),(x,-depth,top-.25),(x-.07,-depth,top)],depth*.77,DRAIN,8 if lod else 14,'Long wall | round drainpipe')
        for z in np.arange(1.35,top-.4,2.05):
            block(b,x-depth*.95,x+depth*.95,-depth*1.87,-.003,z,z+.045,DRAIN,'Long wall | pipe saddle')

def end_fabric(b,lod):
    # The original pier supports the short face below the balustrade. A separate
    # reveal and pane are provided for the blue side window behind the near tree.
    xz(b,box(0,0,1.913,6.88),0,.24,ROUGH,'Glazed bay | projecting side return')
    yz(b,cut(box(0,0,5.93,6.89),[v[1:] for v in END_OPENINGS]),1.62,1.913,ROUGH,'Glazed bay | rendered end wall')
    yz(b,cut(box(.02,7.29,6.18,10.56),[v[1:] for v in UPPER_OPENINGS]),-.27,0,ROUGH,'Roof terrace | set back end wall')
    for key,l,bot,r,top in END_OPENINGS+UPPER_OPENINGS:
        upper=(key in {o[0] for o in UPPER_OPENINGS})
        face=0 if upper else 1.913
        columns={'high garden end':[.215,.62],'return blue window':[.52],'ground garden end':[.49],
                 'terrace door':[.52],'upper glazed return':[.31,.64]}[key]
        bars={'high garden end':[.69],'return blue window':[.51,.76],
              'ground garden end':[.72,.88],'terrace door':[.59],
              'upper glazed return':[.52,.90]}[key]
        _glazing(b,'end',face,(key,l,bot,r,top),columns,bars,RED if key!='upper glazed return' else DRAIN,BLUE if 'blue' in key or 'upper' in key else GLASS,key,lod)
        if key=='high garden end':
            for frac in columns:
                y=l+(r-l)*frac
                block(b,face-.16,face+.011,y-.073,y+.073,bot,top,POWDER,'End bay | two pale mullions')
            block(b,face-.035,face+.112,l-.08,r+.07,top-.012,top+.118,GREEN,'End bay | green painted lintel')
    # Staggered half-/one-brick exposed vertical corner. The
    # courses remain visible between the moulding and white terrace slab.
    low=3.785;high=6.665;count=round((high-low)/.0687)
    for i in range(count):
        z0=low+(high-low)*i/count;z1=low+(high-low)*(i+1)/count
        length=.25 if i%3==0 else .34 if i%3==1 else .44
        block(b,1.913-length,1.924,-.021,.035,z0,z1,MATERIAL,'Bay corner | staggered ochre brick');apply_uv(b.parts[-1])
    for y0,y1,z0,z1 in [(0,.7,4.0,6.68),(3.395,4.075,4.0,6.61)]:
        block(b,1.913,1.929,y0,y1,z0,z1,MATERIAL,'Garden end | ochre brick pier');apply_uv(b.parts[-1])
    for z0,height,projection in [(3.04,.090,.055),(3.17,.105,.115),(3.32,.053,.14),
                                 (3.40,.082,.091),(3.61,.081,.116),(3.75,.066,.15)]:
        block(b,1.91,1.91+projection,-projection,5.91,z0,z0+height,POWDER,'Garden end | belt moulding')
        block(b,-.16,1.92+projection,-projection,.012,z0,z0+height,POWDER,'Side return | belt moulding')
    for y in (.28,3.98):
        block(b,1.82,1.995,y-.16,y+.16,.13,3.03,POWDER,'Ground floor | white pier')
        for z,w,h in [(2.87,.23,.09),(2.96,.26,.08),(.10,.21,.10)]:
            block(b,1.81,2.027,y-w,y+w,z,z+h,POWDER,'Ground floor | pier capital and base')
    for x0,x1,y0,y1 in [(1.59,1.92,5.90,5.95),(-11.85,.01,6.14,6.20)]:
        block(b,x0,x1,y0,y1,.0,6.74 if x0>0 else 10.37,ROUGH,'Side closure | depth estimate')
    block(b,-11.85,-11.56,.01,6.19,.0,9.48,ROUGH,'Far wall | closed return')
    for i,z in enumerate(np.arange(7.41,10.44,.074)):
        width=.13 if i%2 else .22
        block(b,-width,.011,-.016,.19,z,min(10.46,z+.074),MATERIAL,'Upper corner | exposed ochre brick');apply_uv(b.parts[-1])

def _roof_strip(b,x0,x1,cross,material,label):
    yz(b,Polygon(cross),x0,x1,material,label)

def roof_fabric(b,lod):
    # The near long eave stays level to its hip. The far tip drops to the
    # return at X≈−12. The hidden ridge and rear slope close the visible roof.
    a,bx,c=-12.13,-8.94,.32
    y0,y1,ridge=-.33,6.40,3.01
    edge=10.62;tip=9.72;high=10.99
    _roof_strip(b,bx,c,[(y0,edge),(ridge,high),(y1,edge),(y1,edge-.095),
                         (ridge,high-.095),(y0,edge-.095)],TILES,'Main roof | two slopes')
    for i in range(9):
        u0=i/9;u1=(i+1)/9;x0=a+(bx-a)*u0;x1=a+(bx-a)*u1
        # Continuous hip with a lower eave at its far end.
        ymid=(y0+y1)/2
        pts=[(x0,y0,tip+(edge-tip)*u0),(x0,ymid,tip+(high-tip)*u0),
             (x0,y1,tip+(edge-tip)*u0),(x1,y0,tip+(edge-tip)*u1),
             (x1,ymid,tip+(high-tip)*u1),(x1,y1,tip+(edge-tip)*u1)]
        # Two independent sloped closed panels avoid a non-planar roof face.
        for inds in ((0,3,4,1),(1,4,5,2)):
            top=[pts[k] for k in inds];bottom=[(x,y,z-.092) for x,y,z in top]
            b.add(bottom+top,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],TILES,'Main hip | clay slope')
    for y in (y0,y1):
        block(b,bx,c,y-.032,y+.032,edge-.138,edge-.012,FASCIA,'Main roof | red-brown fascia')
        b.tube([(a,y,tip-.062),(bx,y,edge-.062),(c,y,edge-.062)],.034,DRAIN,8 if lod else 12,'Main roof | eaves gutter')
    block(b,bx+.01,c,y0+.04,-.001,edge-.148,edge-.101,SOFFIT,'Main roof | pale soffit')
    _roof_strip(b,c-.013,c+.046,[(y0,edge),(ridge,high),(y1,edge),(y1,edge-.16),(ridge,high-.16),(y0,edge-.16)],FASCIA,'End eaves | red verge')
    # A low shallow pitch covers the end terrace behind its white rail.
    _roof_strip(b,.01,.49,[(.06,10.56),(3.22,10.69),(5.87,10.52),(5.87,10.43),(.06,10.44)],
                SOFFIT,'Upper hall | narrow soffit return')
    for x in np.arange(bx+.065,c-.03,.215 if not lod else .43):
        b.tube([(x,y0+.015,edge+.016),(x,ridge,high+.016),(x,y1-.015,edge+.016)],
               .019 if not lod else .023,TILERIM,8 if not lod else 6,'Main roof | raised clay overlaps')
    block(b,-11.50,.01,.02,6.15,0,.12,ROUGH,'Foundation | floor edge')

def add_fabric(builder,lod=False):
    make_texture()
    builder.palette.update(PALETTE)
    side_fabric(builder,lod)
    end_fabric(builder,lod)
    roof_fabric(builder,lod)
    upper_glazed_room(builder,lod)
    condensers(builder,lod)

def upper_glazed_room(b,lod):
    # The black frame of the blue porch is in front of the recessed upper
    # doorway. Both faces and the projecting flat green glass roof are visible.
    x0,x1=.08,1.50
    y0,y1=2.12,5.60
    z0,z1=7.49,9.47
    _glazing(b,'end',x1,('front',y0,z0,y1,z1),[.34,.67],[.90],DRAIN,BLUE,'Sunroom | blue glazed face',lod)
    _glazing(b,'side',y0,('side',x0,z0,x1,z1),[.54],[.82],DRAIN,BLUE,'Sunroom | short green return',lod)
    for x in (x0,x1):
        for y in (y0,y1):
            block(b,x-.035,x+.035,y-.035,y+.035,z0,z1+.08,DRAIN,'Sunroom | dark corner posts')
    block(b,x0-.085,x1+.095,y0-.09,y1+.09,z1,z1+.07,GREEN,'Sunroom | shallow projecting roof')
    # A separate short white roof light rises behind, visible above the long
    # red verge in the original. Its concealed back is closed at shallow depth.
    x=-.26;y=2.58;w=1.50;bot=10.79;ridge=11.75
    poly=Polygon([(y,bot),(y,11.40),(y+w*.48,ridge),(y+w,11.44),(y+w,bot)])
    yz(b,poly,x-.78,x,POWDER,'Roof light | white end')
    for a,c,d in [(y,y+w*.48,1),(y+w*.48,y+w,-1)]:
        low,high=(11.42,ridge+.04) if d==1 else (ridge+.04,11.46)
        yz(b,Polygon([(a,low),(c,high),(c,high+.06),(a,low+.06)]),x-.86,x+.05,FASCIA,'Roof light | shallow pitched cover')

def condensers(b,lod):
    # Permanent outdoor units visible on the photographed 2015 side. The
    # support arms project from the exterior masonry beneath the soffit.
    for key,x,z,w,h in [('upper side',-.65,7.88,.69,.46),('lower centre',-4.08,3.36,.86,.43),('lower rear',-5.61,3.31,.71,.42)]:
        y=-.16
        block(b,x-w/2,x+w/2,-.27,-.046,z-h/2,z+h/2,POWDER,'Outdoor unit | '+key)
        r=min(h*.37,w*.27)
        angle=np.linspace(0,2*math.pi,17 if lod else 33)
        for rr in (r,r*.75,r*.53):
            b.tube([(x-w*.19+rr*math.cos(a),-.280,z+rr*math.sin(a)) for a in angle[:-1]]+[(x-w*.19+rr,-.280,z)],.0085,DRAIN,5,'Outdoor unit | fan guard')
        for xx in np.linspace(x+w*.12,x+w*.39,5):
            block(b,xx,xx+.013,-.283,-.269,z-h*.35,z+h*.34,REVEAL,'Outdoor unit | grille')
        for xx in (x-w*.32,x+w*.32):
            block(b,xx,xx+.055,-.292,.107,z-h*.50-.035,z-h*.50,METAL,'Outdoor unit | supports')
    # One unit is perpendicular to the long-wall units, below the end windows.
    block(b,1.95,2.25,.0,.84,4.20,4.61,ROUGH,'End bay | condenser housing')
    for yy in np.arange(.07,.79,.056):
        block(b,2.25,2.263,yy,yy+.018,4.245,4.567,METAL,'End bay | condenser grille')
