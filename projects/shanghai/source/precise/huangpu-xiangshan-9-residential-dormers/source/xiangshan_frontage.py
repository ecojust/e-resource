"""The street-facing plaster wall, five casements, timber shutters and tiled main eaves."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import Polygon, box as rectangle
from shapely.ops import unary_union
from material_names import MATERIAL
from xiangshan_dormers import roof_seats, colour

WINDOWS=json.loads((Path(__file__).resolve().parents[1]/'measurements/five-main-wall-windows.json').read_text())['windows']
STONE='Street wall | worn grey concrete'
SASH='Street wall | green black window frames'
GLASS='Street wall | muted reflective glazing'
DEEP='Street wall | shaded window reveal'
IRON='Street wall | weathered iron'
SHUTTER='Street wall | painted brown timber shutters'
SOFFIT='Main roof | timber soffit'
FASCIA='Main roof | dark red verge'
GUTTER='Main roof | grey green rainwater goods'
CASE='Later fittings | cream painted casing'
VENT='Later fittings | dark grille'
TILES=['Main roof | earthenware tile '+str(i) for i in range(1,5)]
PALETTE={
    STONE:colour([145,143,132],.88), SASH:colour([59,65,60],.78),
    GLASS:colour([102,119,117],.25,.23),DEEP:colour([57,61,55],.95),
    IRON:colour([77,77,70],.75,.19),SHUTTER:colour([99,71,59],.84),
    SOFFIT:colour([90,77,66],.92),FASCIA:colour([110,77,67],.89),
    GUTTER:colour([92,102,93],.76,.15),CASE:colour([183,181,161],.75),
    VENT:colour([87,93,87],.71),
}
PALETTE.update({k:colour(rgb,.90) for k,rgb in zip(TILES,([143,88,76],[139,83,69],[154,99,81],[130,80,69]))})

def wall_box(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2], [x1-x0,y1-y0,z1-z0],material,label=label)

def front_slab(b,outline,y0,y1,material,label):
    b.prism(outline,-y1,-y0,lambda x,z,d:(x,-d,z),material,label)

def window(b,row,low):
    left,right,bottom,top=[row[k] for k in ('left','right','bottom','top')]
    k=row['label']+' casement'
    y=.14
    wall_box(b,left-.014,right+.014,.19,.225,bottom-.014,top+.014,DEEP,k+' shaded backing')
    wall_box(b,left-.075,right+.075,-.105,.16,bottom-.07,bottom,STONE,k+' short sill')
    wall_box(b,left-.105,right+.105,-.11,.07,top,top+.075,STONE,k+' overhanging lintel')
    for x in (left,right-.045):
        wall_box(b,x,x+.045,y-.045,y+.035,bottom,top,SASH,k+' fixed jamb')
    for z in (bottom,top-.05):
        wall_box(b,left+.045,right-.045,y-.045,y+.035,z,z+.05,SASH,k+' casing rail')
    xs=np.linspace(left+.045,right-.045,row['columns']+1)
    zs=np.linspace(bottom+.05,top-.05,row['rows']+1)
    for x in xs[1:-1]:
        wall_box(b,x-.021,x+.021,y-.047,y+.017,bottom+.05,top-.05,SASH,k+' leaf stile')
    for z in zs[1:-1]:
        wall_box(b,left+.045,right-.045,y-.032,y+.014,z-.013,z+.013,SASH,k+' glazing bar')
    for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
        for j,(z0,z1) in enumerate(zip(zs,zs[1:])):
            wall_box(b,x0,x1,y+.017,y+.022,z0,z1,GLASS,k+f' pane {i+1}.{j+1}')
            if not low:
                for x in (x0,x1-.008):
                    wall_box(b,x,x+.008,y+.003,y+.017,z0,z1,SASH,k+' putty fillet')
    if row['label'] in ('east','east centre','middle'):
        for x in np.linspace(left+.16,right-.16,3):
            b.tube([[x,-.057,bottom+.06],[x,-.057,top-.07]],.009,IRON,sides=6 if low else 9,label=k+' exterior upright')
        for z in np.linspace(bottom+.22,top-.19,3):
            b.tube([[left+.036,-.064,z],[right-.036,-.064,z]],.009,IRON,sides=6 if low else 9,label=k+' exterior crosspiece')

def timber_shutters(b):
    left,right,bottom,top=2.28,3.78,1.37,3.57
    k='Western ground floor'
    wall_box(b,left-.065,right+.065,-.085,.08,top,top+.09,STONE,k+' lintel')
    wall_box(b,left,right,.18,.22,bottom,top,DEEP,k+' shadow')
    for i,(a,c) in enumerate(((left,(left+right)/2),((left+right)/2,right))):
        p=k+f' timber leaf {i+1}'
        for x in (a,c-.048):
            wall_box(b,x,x+.048,.052,.109,bottom,top,SHUTTER,p+' stile')
        for z in (bottom,top-.055):
            wall_box(b,a+.048,c-.048,.052,.109,z,z+.055,SHUTTER,p+' rail')
        n=27
        zvals=np.linspace(bottom+.055,top-.055,n+1)
        for za,zb in zip(zvals,zvals[1:]):
            section=Polygon([(.047,za),(.071,za),(.126,zb),(.102,zb)])
            b.prism(section,a+.048,c-.048,lambda y,z,x:(x,y,z),SHUTTER,p+' sloping louvre')

def main_roof_section(b,low,name,x0,x1,edge_z,pitch,seats,region):
    front=-.56
    rear=3.65
    break_y=.64
    def height(y):
        return edge_z+pitch*min(y-front,break_y-front)+.52*max(0.,y-break_y)
    ystations=np.r_[np.linspace(front,break_y,5),np.linspace(break_y,rear,10)[1:]]
    nx=round((x1-x0)/.224)
    for j,(ya,yb) in enumerate(zip(ystations,ystations[1:])):
        outline=rectangle(x0,ya,x1,yb).intersection(region).difference(seats)
        if outline.area:
            b.prism(outline,-.095,0,lambda x,y,d:(x,y,height(y)+d),SOFFIT,name+' roof board')
        for i in range(nx):
            xa=x0+(x1-x0)*i/nx;xb=x0+(x1-x0)*(i+1)/nx
            if not outline.intersects(rectangle(xa,ya,xb,yb)):continue
            coords=np.linspace(xa,xb,4 if low else 7)
            for a,c in zip(coords,coords[1:]):
                tile_section=outline.intersection(rectangle(a,ya,c,yb))
                if tile_section.area<1.e-6:continue
                def roll(x):return .007+.023*(.5+.5*math.cos((x-xa)*2*math.pi/(xb-xa)))**2
                g=roll(a);slope=(roll(c)-g)/(c-a)
                def tile(x,y,d):
                    return (x,y,height(y)+g+slope*(x-a)+.021*(yb-y)/(yb-ya)+d)
                b.prism(tile_section,-.009,.004,tile,TILES[(i+2*j)%4],f'{name} roof | row {j+1} tile {i+1}')
    front_start=(-4.32 if name=='Western' else x0)
    wall_box(b,front_start,x1,front-.055,front+.02,edge_z-.14,edge_z-.012,FASCIA,name+' eaves | fascia')
    b.tube([[front_start,front-.065,edge_z-.063],[x1,front-.065,edge_z-.063]],.047,GUTTER,
           sides=8 if low else 14,label=name+' eaves | rounded gutter')

def roof(b,low):
    seats=unary_union([rectangle(row['x_limits'][0],row['front_y']-.025,row['x_limits'][1],row['cut_y'])
                       for row in roof_seats()])
    # In the 2018 oblique view the lower western slope laps the higher eastern
    # eave. The return tapers to the eastern dormer and stops short of the link.
    east_outline=Polygon([(-11.49,-.56),(-4.32,-.56),(-5.36,.02),(-5.36,3.65),(-11.49,3.65)])
    west_outline=rectangle(-5.36,-.56,4.99,3.65).difference(east_outline)
    main_roof_section(b,low,'Eastern',-11.49,-4.32,8.58,1.065,seats,east_outline)
    main_roof_section(b,low,'Western',-5.36,4.99,8.015,1.04,seats,west_outline)
    # Plastered aprons close the visible joint down to the red tile at each gable.
    wall_box(b,-7.9,-5.35,.008,.23,9.10,9.25,MATERIAL,'Eastern dormer | lower plaster apron')
    wall_box(b,-1.63,2.48,.008,.23,8.52,8.80,MATERIAL,'Western dormer | lower plaster apron')
    wall_box(b,-4.32,-1.63,.586,.72,9.11,9.25,MATERIAL,'Link windows | lower apron')
    # The shallow west roof meets the solid end of the higher eastern slope.
    flank=Polygon([(-.56,8.49),(-.56,8.58),(.02,9.198),(.02,9.108)])
    b.prism(flank,-.040,0.,lambda y,z,d:(-4.32-(y+.56)*1.04/.58+d,y,z),FASCIA,
            'Roof level change | narrow return fascia')

def lower_canopies(b,low):
    # The east canopy is a shallow tiled hood, with a wall plate at the top and
    # a projecting front edge. Both ends of the west slope appear in winter.
    front_y=-1.32
    top_z=4.88
    for i,(a,c) in enumerate([(-8.22,-3.21)]):
        depth=-front_y
        def elevation(y): return top_z+.83*(y/depth)
        lid=rectangle(a,front_y,c,.08)
        b.prism(lid,-.07,.0,lambda x,y,d:(x,y,elevation(y)+d),SOFFIT,'Lower canopy | exposed board')
        nx=round((c-a)/.23);ny=5
        for j in range(ny):
            start=front_y+depth*j/ny;end=front_y+depth*(j+1)/ny
            for z in range(nx):
                x0=a+(c-a)*z/nx;x1=a+(c-a)*(z+1)/nx
                height=.012+(j%2)*.003
                b.prism(rectangle(x0+.001,start,x1-.001,end),-.005,height,
                        lambda x,y,d:(x,y,elevation(y)+.015*(end-y)/(end-start)+d),
                        TILES[(z+2*j)%4],f'Lower canopy | clay tile {j+1}.{z+1}')
        for x in (a+.16,c-.16):
            b.tube([[x,-.06,3.47],[x,front_y+.13,elevation(front_y)+.015]],.034,SOFFIT,
                   sides=6 if low else 10,label='Lower canopy | visible bracket')
        wall_box(b,a,c,front_y-.035,front_y+.04,elevation(front_y)-.11,elevation(front_y),
                 FASCIA,'Lower canopy | red fascia')
    # A short, flatter reddish cap can also be seen near the east wall return.
    wall_box(b,-10.56,-8.74,-.74,.03,3.74,3.81,FASCIA,'Eastern lower wall | shallow cap')

def period_fittings(b,low):
    for idx,(xc,zc) in enumerate(((1.82,6.95),(1.83,5.86),(-4.45,5.86))):
        k=f'Photographed exterior casing {idx+1}'
        wall_box(b,xc-.32,xc+.32,-.35,-.014,zc-.235,zc+.235,CASE,k)
        wall_box(b,xc-.247,xc+.08,-.359,-.349,zc-.18,zc+.18,VENT,k+' grille backing')
        for x in np.linspace(xc-.23,xc+.061,7 if low else 14):
            wall_box(b,x,x+.008,-.365,-.357,zc-.16,zc+.16,CASE,k+' grille upright')
        for x in (xc-.222,xc+.219):
            wall_box(b,x-.016,x+.016,-.36,.017,zc-.268,zc-.24,IRON,k+' support')
    for x,edge in ((-10.6,8.58),(-2.27,8.015)):
        b.tube([[x,-.54,edge-.07],[x,-.12,edge-.18],[x,-.105,2.38]],.046,GUTTER,sides=8 if low else 14,label='Street wall | exposed rainwater pipe')

def add_frontage(b,lod=False):
    low=lod in (True,'lod')
    openings=[rectangle(row['left'],row['bottom'],row['right'],row['top']) for row in WINDOWS]
    openings.append(rectangle(2.28,1.37,3.78,3.57))
    outline=Polygon([(-11.12,0),(4.72,0),(4.72,8.56),(-4.32,8.56),(-4.32,9.105),(-11.12,9.105)])
    wall=outline.difference(unary_union(openings))
    front_slab(b,wall,0,.36,MATERIAL,'Residence | plaster street wall with five upper openings')
    # Only the ends visible from the pavement are carried behind the street face.
    for x,wall_top in ((-11.12,9.10),(4.6,8.54)):
        wall_box(b,x,x+.12,.36,2.0,.02,wall_top,MATERIAL,'Residence | return of visible wall')
    for row in WINDOWS:window(b,row,low)
    timber_shutters(b)
    lower_canopies(b,low)
    roof(b,low)
    period_fittings(b,low)
