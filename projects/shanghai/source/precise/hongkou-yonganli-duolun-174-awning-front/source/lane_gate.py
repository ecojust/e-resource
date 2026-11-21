"""Model the named Duolun Road lane entrance and its shopfront neighbours."""
import json, math
from pathlib import Path
import numpy as np
from shapely.geometry import box,Polygon,LineString
from pebbled_stucco import CAST
from fabric_canopies import CANVAS,PIPE,IRON
from lane_windows import DARK,GLASS,STONE,RECESS,PANEL,SASH

BLUE='Blue-black lamp stripe'
MILK='Pale lamp glass'
LETTER='Dark name lettering'
GREEN='Enamel address plate'
SHOP='Muted shopfront timber'


def cylinder(f,u,z,d,r,h,turns,lod):
    sides=24 if lod else 40;layers=30 if lod else 56
    # Rotate each glass ring as it rises. The contrasting helical band is
    # part of the same cylindrical shade, beneath its conical caps.
    vertices=[]
    for j in range(layers+1):
        for k in range(sides):
            a=2*math.pi*(k/sides+turns*j/layers)
            vertices.append(f.point(u+r*math.cos(a),z+h*j/layers,d+r*math.sin(a)))
    def arc(k,j):return j*sides+k%sides
    for mat,start,stop in ((BLUE,0,max(3,round(sides*.25))),(MILK,max(3,round(sides*.25)),sides)):
        faces=[[arc(k,j),arc(k,j+1),arc(k+1,j+1),arc(k+1,j)]for j in range(layers)for k in range(start,stop)]
        f.builder.add(vertices,faces,mat,'Street fixtures/Spiral lantern glazing')
    for upper in (False,True):
        zz=z+h if upper else z
        section=[(zz,.118),(zz+.052,.114),(zz+.145,.026),(zz+.171,.012)] if upper else [(zz-.079,.023),(zz-.042,.110),(zz,.118)]
        coords=[];faces=[]
        for zp,rr in section:
            for k in range(sides):
                a=2*math.pi*k/sides;coords.append(f.point(u+rr*math.cos(a),zp,d+rr*math.sin(a)))
        for j in range(len(section)-1):
            for k in range(sides):faces.append([arc(k,j),arc(k,j+1),arc(k+1,j+1),arc(k+1,j)])
        faces.extend([tuple(range(sides)),tuple(reversed(range((len(section)-1)*sides,len(section)*sides)))])
        f.builder.add(coords,faces,IRON,'Street fixtures/Shaped lantern caps')
    f.box(u,z+h/2,.07,.15,d,d/2,IRON,'Lantern mounting brackets')


def glyphs(f,key,x,z,back,front,mat):
    raw=json.loads(Path(__file__).with_name('sign-outlines.json').read_bytes())
    for shell,*holes in raw[key]:
        def place(ring):return [(u+x,v+z)for u,v in ring]
        f.prism(Polygon(place(shell),[place(h)for h in holes]),back,front,mat,'Street inscriptions')


def passage(f,p,lod):
    h=p['portal_slab_soffit'];width=p['portal_inner_clear_width'];depth=p['section_depth']
    clear=box(-width/2,.08,width/2,h)
    f.prism(box(-f.length/2,.08,f.length/2,p['shop_cornice']).difference(clear),-.42,.092,CAST,'Passage and solid piers')
    for side in (-1,1):
        edge=side*width/2;col=side*(width/2+(f.length-width)/4)
        for x in (col-.19,col+.19):f.box(x,1.78,.061,3.15,.066,.099,STONE,'Recessed pier panel rims')
        f.box(col,.17,(f.length-width)/2+.035,.24,.48,-.055,STONE,'Street pier feet')
        f.box(edge+side*.076,h/2,.15,h,depth-.38,-(depth+.38)/2,CAST,'Deep passage jambs')
        pts=[(edge-side*.035,h-.02),(edge-.41*side,h-.02),(edge-.36*side,h-.116),(edge-.30*side,h-.133),(edge-.25*side,h-.083),(edge-.15*side,h-.10),(edge-side*.055,h-.24)]
        poly=Polygon(pts);f.prism(poly,-.083,.116,STONE,'Corner scrolls under lintel')
        cylinder(f,side*p['portal_lamp_axes_m']/2,2.00,.176,.097,.681,1.15,lod)
    # Photograph of February 2020 shows a closed iron grille and an upper
    # fanlight, through which the covered passage remains visible.
    gate=-.292
    for j in range(17):
        x=-width/2+.08+j*(width-.16)/16
        f.box(x,h-.40,.024,.68,.032,gate,IRON,'Transom vertical grille')
    for side in (-1,1):
        mid=side*width/4;gw=width/2-.046;gh=h-.84
        f.prism(box(mid-gw/2,.09,mid+gw/2,gh).boundary.buffer(.026,join_style=2),gate-.030,gate+.030,IRON,'Iron double gate frames')
        for k in range(6):
            x=mid+gw*(k-2.5)/6;f.box(x,(gh+.12)/2,.021,gh-.12,.024,gate,IRON,'Open gate bars')
        for z in (.43,1.93,gh-.21):
            f.box(mid,z,gw,.028,.034,gate,IRON,'Gate crosspieces')
    f.box(0,h-.781,width,.085,.09,gate,IRON,'Full width transom rail')
    for dist in (.62,2.62):f.box(0,h-.022,width,.075,.099,-dist,STONE,'Passage ceiling ribs')
    f.box(0,h+.05,width,.111,depth-.42,-(depth+.42)/2,CAST,'Passage ceiling')
    f.box(0,.071,width,.102,depth+.18,-depth/2+.09,STONE,'Passage floor')
    bottom,top=p['letter_panel']
    f.prism(box(-.95,bottom,.95,top),.035,.074,PANEL,'Name tablet')
    glyphs(f,'lane',0,bottom+.126,.077,.098,LETTER)
    for side in (-1,1):
        v=[(.93,bottom+.11),(.97,bottom+.11),(.97,bottom+.37),(1.13,bottom+.37),(1.13,top+.004),(.945,top+.004)]
        f.prism(Polygon([(side*u,z)for u,z in v]),.052,.086,STONE,'Tablet flanking steps')
    # The rectangular panel below the number has clipped shoulders and a brass bead.
    plate=Polygon([(-1.96,1.58),(-1.91,1.61),(-1.82,1.61),(-1.76,1.65),(-1.67,1.61),(-1.51,1.61),(-1.47,1.56),(-1.49,1.32),(-1.56,1.30),(-1.88,1.30),(-1.96,1.34)])
    f.prism(plate,.151,.18,IRON,'Historic marker on gate pier')
    f.prism(plate.difference(plate.buffer(-.014,join_style=2)),.18,.19,STONE,'Marker edge bead')
    # Smooth plaster volutes flank the name tablet in the photographed lintel.
    if not lod:
        for side in (-1,1):
            points=[]
            for t in np.linspace(0,math.pi*2.08,28):
                r=.078*(1-t/(2.42*math.pi))
                points.append((side*(1.13+r*math.cos(t)),bottom+.16+r*math.sin(t)))
            f.prism(LineString(points).buffer(.012,join_style=1),.077,.091,PANEL,'Name-tablet volutes')
    # Two flat notices were clipped to the bars in the 2020 survey. Only their
    # boards, attachment points and paper colours are identified in the photo.
    for x,z,w,h in ((-.35,1.28,.42,.28),(.60,1.39,.37,.64)):
        f.box(x,z,w,h,.016,gate+.047,'Paper on street gate','2020 notice boards')
        if not lod:
            for dx in (-w*.4,w*.4):f.box(x+dx,z+h*.422,.015,.015,.013,gate+.063,IRON,'Notice clips')
    addr=-1.74;f.box(addr,1.96,.224,.166,.037,.163,GREEN,'Enamel number 174')
    if not lod:glyphs(f,'address',addr,1.93,.185,.192,MILK)


def shop(f,p,north,lod):
    top=3.32;width=f.length-.47;h=3.00;lower=.13
    outer=box(-width/2,lower,width/2,top)
    f.prism(box(-f.length/2,.08,f.length/2,p['shop_cornice']).difference(outer),-.31,.022,CAST,'Shopfront and street piers')
    f.prism(outer,-.273,-.239,GLASS if north else DARK,'Recessed shopfront')
    edge=outer.difference(outer.buffer(-.075,join_style=2))
    f.prism(edge,-.172,-.097,PIPE if north else SHOP,'Shopfront casings')
    if north:
        # Light metal frame and the shallow straight scalloped blind at 176.
        door=-width*.07
        f.box(door,1.59,width*.59,.068,.089,-.112,PIPE,'Shopfront meeting rail')
        for x in (door-width*.28,door+width*.28):
            f.box(x,1.56,.069,2.85,.06,-.091,PIPE,'Shop door stiles')
        f.box(0,2.75,width,.075,.072,-.10,PIPE,'Shop transom')
        ledge=Polygon([(-width/2,.0),(width/2,0),(width/2,-.147)]+[(x,-.145-.035*(1+math.cos((x/width+.5)*math.pi*28))/2)for x in np.linspace(width/2-.001,-width/2,114)])
        from shapely import affinity
        f.prism(affinity.translate(ledge,yoff=3.53),.57,.589,PIPE,'Street shop valance')
        f.builder.add([f.point(-width/2,3.81,.021),f.point(width/2,3.81,.021),f.point(width/2,3.53,.589),f.point(-width/2,3.53,.589)],[(3,2,1,0),(0,1,2,3)],CANVAS,f.label+'/Sloping shop blind')
    else:
        for x in (-width*.32,width*.022,width*.31):
            f.box(x,1.66,.050,3.04,.066,-.108,SASH,'Shop sash stiles')
        f.box(0,2.63,width,.087,.08,-.093,SASH,'Deep red shop transom')
        for x in np.linspace(-width*.37,width*.37,7):
            f.box(x,2.96,.032,.56,.071,-.112,SASH,'Transom lights')
