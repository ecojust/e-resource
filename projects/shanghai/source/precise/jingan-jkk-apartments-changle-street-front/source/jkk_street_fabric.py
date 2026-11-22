"""The four pierced street-wall sections, two recessed stairs and photographed roofline."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from jkk_central_steel import central_openings, finish
from material_names import MATERIAL

LAYOUT = json.loads((Path(__file__).resolve().parents[1] / 'measurements/street-facade-layout.json').read_text())
PEACH = 'Recessed wall | salmon mineral render'
BAND = 'Stringcourses | pale grey concrete'
SHADOW = 'Room sash | shaded internal reveal'
STEEL = 'Room sash | dark painted metal'
BEAD = 'Room sash | glazing bead'
STONE = 'Room sash | cast sill'
GLASSES = ['Room sash | glass '+str(i+1) for i in range(4)]
ROOF = 'Upper ledge | asphalt roof surface'
AWNING = 'Canopies | ivory grey cloth'
BRACKET = 'Fittings | weathered iron'
CASE = 'Fittings | pale grey enamel'
FAN = 'Fittings | shaded ventilation grille'
PALETTE = {
    PEACH:finish([191,154,133],.90), BAND:finish([194,190,182],.88), 
    SHADOW:finish([49,46,43],.95), STEEL:finish([60,59,54],.67,.32),
    BEAD:finish([77,77,71],.69,.20), STONE:finish([153,148,139],.87),
    ROOF:finish([112,108,100],.96), AWNING:finish([142,145,138],.88),
    BRACKET:finish([87,80,72],.72,.25), CASE:finish([175,169,157],.74,.1), FAN:finish([76,78,74],.77,.15),
    **{name:finish(rgb,.29,.15)for name,rgb in zip(GLASSES,([87,94,89],[69,76,75],[99,105,102],[62,66,64]))},
}

def solid(b,xa,xb,ya,yb,za,zb,mat,label):
    b.box([(xa+xb)/2,(ya+yb)/2,(za+zb)/2],[xb-xa,yb-ya,zb-za],mat,label=label)

def face(b,region,ya,yb,mat,label):
    if not region.is_empty and region.area>1.e-7:
        b.prism(region,-yb,-ya,lambda x,z,d:(x,-d,z),mat,label)

def aperture(row):
    return box(row['left'],row['bottom'],row['right'],row['top'])

def frames(b,row,lod):
    x0,x1,z0,z1=[row[a]for a in ('left','right','bottom','top')]
    y=row['wall_y'];label=row['key']; cols=row['columns']; high=row['rows']
    y0=y+.105; surface=y+.165
    solid(b,x0-.012,x1+.012,y+.188,y+.219,z0-.015,z1+.015,SHADOW,label+' | recess shadow')
    solid(b,x0-.052,x1+.052,y-.075,y+.176,z0-.064,z0,STONE,label+' | sill')
    for x in (x0,x1-.044):
        solid(b,x,x+.044,y0,surface,z0,z1,STEEL,label+' | outer jamb')
    for z in (z0,z1-.045):
        solid(b,x0+.044,x1-.044,y0,surface,z,z+.045,STEEL,label+' | outer rail')
    xs=np.linspace(x0+.044,x1-.044,cols+1)
    # The transom above the main pair of lights is shallower.
    fractions={4:(0.,.30,.61,.82,1.),3:(0.,.40,.76,1.),1:(0.,1.)}[high]
    zs=z0+.045+np.asarray(fractions)*(z1-z0-.090)
    for part,x in enumerate(xs[1:-1]):
        solid(b,x-.018,x+.018,y0+.002,surface,zs[0],zs[-1],STEEL,label+' | vertical glazing bar')
    for z in zs[1:-1]:
        solid(b,xs[0],xs[-1],y0+.011,surface,z-.0135,z+.0135,STEEL,label+' | horizontal glazing bar')
    ix=sum(ord(c)for c in label)
    for i,(a,d) in enumerate(zip(xs,xs[1:])):
        for j,(f,h) in enumerate(zip(zs,zs[1:])):
            solid(b,a,d,surface,surface+.008,f,h,GLASSES[(i+ix+j//2)%4],label+f' | glass {i+1}.{j+1}')
            if not lod:
                solid(b,a+.017,d-.017,surface-.010,surface,f+.013,f+.022,BEAD,label+' | lower glazing bead')

def make_main_wall(b,row,openings):
    x0,x1,y=row;cut=unary_union([aperture(r) for r in openings])
    top=15.12 if x1<2 else 14.91 if x0>=15 else 15.
    face(b,box(x0,0,x1,top).difference(cut),y,y+.34,MATERIAL,'Street wall | '+str(x0))
    for z1,z2 in ((3.65,4.96),(7.02,8.44),(10.94,12.025)):
        span=box(x0,z1,x1,z2).difference(cut)
        for j,z in enumerate(np.linspace(z1,z2-.076,6)):
            face(b,span.intersection(box(x0,z,x1,z+.076)),y-.045,y+.015,BAND,'Stringcourse | horizontal raised band')
    solid(b,x0,x1,y-.105,y+.25,top-.17,top+.012,BAND,'Street wall | cornice lower return')
    solid(b,x0,x1,y-.19,y+.29,top+.012,top+.119,MATERIAL,'Street wall | upper plaster cornice')
    solid(b,x0,x1,y-.21,y+.35,top+.119,top+.179,BAND,'Street wall | coping edge')
    return top

def notch(b,bounds,rows,capped):
    x0,x1,y=bounds
    cut=unary_union([aperture(r)for r in rows])
    top=14.10 if capped=='west' else 13.98
    face(b,box(x0,0,x1,top).difference(cut),y,y+.33,PEACH,capped+' stairwell | recessed wall')
    for x,depth in ((x0,-.12 if capped=='west' else .055),(x1,0. if capped=='west' else .10)):
        # Join the discontinuity at the side of the hard stucco return.
        xa,xb=(x,x+.033) if x==x0 else (x-.033,x)
        solid(b,xa,xb,depth,y+.30,0,top,MATERIAL,capped+' stairwell | full-depth side return')
    solid(b,x0,x1,y-.08,y+.30,top-.09,top+.07,BAND,capped+' stairwell | roof weathering')
    solid(b,x0,x1,y+.28,2.64,top-.11,top+.025,ROOF,capped+' stairwell | shallow roof')

def roof(b,x0,x1,y,z,shaft_side):
    # Top slab in the street photographs projects across the outer balcony bays.
    outline=box(x0,y-.22,x1,2.64)
    wing=(x0+.09,x1-1.90) if shaft_side=='east' else (x0+1.9,x1-.09)
    projecting=box(wing[0],y-1.12,wing[1],y+.10)
    plan=outline.union(projecting)
    b.prism(plan,z-.17,z-.016,lambda x,y,h:(x,y,h),BAND,'Roof | projecting concrete soffit')
    b.prism(plan,z-.016,z+.028,lambda x,y,h:(x,y,h),ROOF,'Roof | weathering finish')
    solid(b,x0,x1,2.62,2.81,z-.34,z+.028,ROOF,'Roof | rear cut edge')

def furniture(b,lod):
    for index,(x,z,w,curve) in enumerate([(-2.66,6.87,1.42,True),(2.70,6.82,1.23,False),(16.81,6.77,1.19,False)]):
        y=(-.12 if index==0 else .10 if index==2 else 0.)
        if curve:
            for a,c in zip(np.linspace(-1.,1.,12)[:-1],np.linspace(-1.,1.,12)[1:]):
                ya=y-.72;yb=y+.006
                def canopy(u,v,off):
                    rel=(u-x)/(w/2)
                    t=(rel-a)/(c-a)
                    return (u,v,z+.14*(v-y)+.25*((1-t)*np.sqrt(max(0.,1-a*a))+t*np.sqrt(max(0.,1-c*c)))+off)
                b.prism(box(x+a*w/2,ya,x+c*w/2,yb),-.018,.012,canopy,AWNING,'Western window | curved fabric hood')
        else:
            b.prism(box(x-w/2,y-.59,x+w/2,y+.015),-.03,.015,lambda u,v,d:(u,v,z+.17*(v-y)+d),AWNING,'Room window | shallow awning')
        for dx in [-w*.40,w*.40]:
            b.tube([[x+dx,y-.02,z-.26],[x+dx,y-.51,z-.07]],.012,BRACKET,sides=6 if lod else 10,label='Awning | diagonal support')
    for x,y,z in [(-2.69,-.12,4.35),(7.70,.055,9.70),(11.95,.055,4.44),(17.25,.10,12.99)]:
        solid(b,x-.40,x+.40,y-.36,y-.015,z,z+.48,CASE,'Street fittings | air-conditioning casing')
        solid(b,x-.305,x+.055,y-.368,y-.359,z+.065,z+.416,FAN,'Street fittings | condenser grille')
        for t in np.linspace(z+.08,z+.4,8 if lod else 15):
            solid(b,x-.303,x+.055,y-.376,y-.365,t,t+.010,CASE,'Street fittings | grille slots')

def add_street_fabric(b,lod=False):
    rows=LAYOUT['openings']
    for i,bounds in enumerate(LAYOUT['faces_x_y']):
        x0,x1,y=bounds;here=[r for r in rows if x0<r['left'] and r['right']<x1]
        top=make_main_wall(b,bounds,here);roof(b,x0,x1,y,top+.17,'east' if i%2==0 else 'west')
        for row in here:frames(b,row,lod)
    native=[dict(left=v['rect_xz_m'][0],bottom=v['rect_xz_m'][1],right=v['rect_xz_m'][2],top=v['rect_xz_m'][3]) for v in central_openings()]
    notch(b,LAYOUT['stair_bounds_x_y'][0],native,'west')
    notch(b,LAYOUT['stair_bounds_x_y'][1],LAYOUT['east_stair'],'east')
    for row in LAYOUT['east_stair']:frames(b,row,lod)
    for x,y,z in [(-7.88,-.12,15.12),(21.53,.10,14.91)]:
        solid(b,x-.075,x+.075,y,2.64,0,z,MATERIAL,'Exposed street frontage | short end return')
    furniture(b,lod)
