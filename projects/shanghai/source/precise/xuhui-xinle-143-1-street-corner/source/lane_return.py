"""Photographed short lane return of the 143-1 corner, ending at the pink neighbour."""
from pathlib import Path
import json
import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

DATA = json.loads((Path(__file__).parent.parent/'measurements/lane-return-metric.json').read_bytes())
BRICK = 'Xinlefang | red facing units with pale mortar'
CREAM = 'Xinlefang | coarse cream finish above brick'
PLINTH = 'Xinlefang | blue grey rendered plinth'
PANEL = 'Xinlefang | pale buff lane window panel'
RIM = 'Xinlefang | pale sill and wall cap'
STEEL = 'Xinlefang | weathered lane steelwork'
GLASS = 'Xinlefang | smoke green side window glass'
DARK = 'Xinlefang | shadow behind open lane casement'
HOOD = 'Xinlefang | green sheet on upper lane awning'
UNIT = 'Xinlefang | old ivory condenser housing'
INTAKE = 'Xinlefang | dark condenser intake'
PALETTE = {PANEL:{'color':[.75,.643,.475],'roughness':.93},
           RIM:{'color':[.65,.58,.43],'roughness':.90},
           STEEL:{'color':[.092,.099,.085],'roughness':.65,'metallic':.23},
           GLASS:{'color':[.255,.305,.277],'roughness':.44,'metallic':.12},
           DARK:{'color':[.031,.039,.034],'roughness':.88},
           HOOD:{'color':[.106,.212,.152],'roughness':.73},
           UNIT:{'color':[.54,.51,.41],'roughness':.73},
           INTAKE:{'color':[.098,.106,.095],'roughness':.84}}
X=DATA['wall_x_at_y0_m']
SLOPE=DATA['wall_dx_per_y']
LENGTH=DATA['measured_end_y_m']
def pt(y,z,out):
    return (X+SLOPE*y+out,y,z)
def add(b,shape,back,front,mat,label,mapper=pt):
    b.prism(shape,back,front,mapper,mat,'lane return / '+label)
def rail(b,y1,y2,z1,z2,back,front,mat,label):
    add(b,box(y1,z1,y2,z2),back,front,mat,label)
def band(left,right,bottom,top):
    return Polygon([(0,left),(LENGTH,right),(LENGTH,top),(0,bottom)])
def point(name):
    return DATA['source_points'][name]['registered_xyz_m'][1:]
def aperture(name):
    left,hi=point(name+'-head-near');right,hi2=point(name+'-head-far')
    l2,lo=point(name+'-sill-near');r2,lo2=point(name+'-sill-far')
    return ((left+l2)/2,(lo+lo2)/2,(right+r2)/2,(hi+hi2)/2)
def openings():
    return {
      'ground sash':(4.04,1.37,4.76,3.16),
      'gated doorway':(.96,.04,1.91,3.22),
      'near middle casement':aperture('middle-near'),
      'far middle sash':aperture('middle-far'),
      'attic front light':aperture('attic-near'),
      'attic awning light':aperture('attic-back')}
def fixed(b,label,bounds,columns,rows,open_leaf=False):
    l,lo,r,hi=bounds
    width,height=r-l,hi-lo
    frame=.043; inside=box(l+frame,lo+frame,r-frame,hi-frame)
    outer=box(l+.004,lo+.004,r-.004,hi-.004)
    bars=[outer.difference(inside)]
    for i in range(1,columns):
        mid=l+i*width/columns
        bars.append(box(mid-.014,lo+frame,mid+.014,hi-frame))
    for i in range(1,rows):
        mid=lo+i*height/rows
        bars.append(box(l+frame,mid-.014,r-frame,mid+.014))
    geometry=unary_union(bars)
    if open_leaf:
        add(b,outer.difference(inside),-.119,-.075,STEEL,label+' fixed jamb')
        add(b,inside,-.246,-.230,DARK,label+' exposed shaded opening')
        # The narrow side-hung steel light opens into the lane. Its vertical hinge remains in the rebate.
        angle=math.radians(42)
        def hinged(y,z,out):
            t=y-l;return pt(l+t*math.cos(angle),z,-.08+t*math.sin(angle)+out)
        add(b,geometry,-.017,.017,STEEL,label+' outward leaf, stiles and rails',hinged)
        add(b,inside.difference(geometry),-.010,-.005,GLASS,label+' outward glazing',hinged)
        for z in [lo+.26*height,lo+.77*height]:
            b.tube([pt(l,z-.032,-.074),pt(l,z+.032,-.074)],.018,STEEL,8,label+' vertical hinge')
    else:
        add(b,geometry,-.059,-.028,STEEL,label+' steel stiles and rails')
        add(b,inside.difference(geometry),-.078,-.062,GLASS,label+' individual glazed lights')
    rail(b,l-.031,r+.031,lo-.047,lo,-.027,.050,RIM,label+' sill')

def gate(b,bounds,lod):
    l,lo,r,hi=bounds
    rail(b,l+.007,r-.007,lo+.006,hi-.008,-.247,-.235,DARK,'lower doorway deep shadow')
    rim=box(l+.005,lo+.005,r-.005,hi-.005).difference(box(l+.046,lo+.048,r-.046,hi-.046))
    bars=[rim];open_width=r-l-.11
    for i in range(1,8 if lod else 11):
        mid=l+.055+i*open_width/(8 if lod else 11)
        bars.append(box(mid-.009,lo+.05,mid+.009,hi-.055))
    for f in [.09,.32,.68,.73,.80,.91]:
        h=lo+(hi-lo)*f
        bars.append(box(l+.035,h-.015,r-.035,h+.015))
    add(b,unary_union(bars),-.139,-.093,STEEL,'dark gate grille and its deeper upper light')
def awning(b,bounds,lod):
    l,lo,r,hi=bounds
    left,right=l-.13,r+.16
    back,tip=-.004,.52
    zh,zl=hi+.20,hi+.065
    def lid(y,out,z):return pt(y,z,out)
    lower=[lid(left,back,zh),lid(left,tip,zl),lid(right,tip,zl),lid(right,back,zh)]
    upper=[(x,y,z+.034) for x,y,z in lower]
    b.add(lower+upper,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],HOOD,'lane return / single sloping green sheet')
    for y in [left+.025,right-.025]:
        for a,c in [(pt(y,zh,back),pt(y,zl,tip)),(pt(y,zh-.41,.008),pt(y,zl,tip))]:
            b.tube([a,c],.017,STEEL,6 if lod else 9,'lane return / awning strut')
    b.tube([pt(left,zl,tip),pt(right,zl,tip)],.018,STEEL,6 if lod else 9,'lane return / outer awning lip')
def condenser(b,lod):
    # Different stations see the sides differently. Fit the projected unit to the clear panel width.
    l,r=2.57,3.45; lo,hi=2.05,2.86
    rail(b,l,r,lo,hi,.050,.334,UNIT,'street-facing condenser box')
    opening=box(l+.056,lo+.09,l+.56,hi-.09)
    add(b,opening,.334,.340,INTAKE,'condenser dark air inlet')
    for i in range(1,8 if lod else 13):
        h=lo+.09+(hi-lo-.18)*i/(8 if lod else 13)
        rail(b,l+.057,l+.56,h-.008,h+.008,.341,.348,UNIT,'fine horizontal grille')
    for y in [l+.09,r-.08]:
        b.tube([pt(y,lo-.035,.020),pt(y,lo-.035,.36)],.023,STEEL,6,'lane return / appliance shelf')
        b.tube([pt(y,lo-.215,.018),pt(y,lo-.035,.31)],.019,STEEL,6,'lane return / angled shelf support')
def add_lane_return(b,lod=False):
    for name,props in PALETTE.items():b.palette.setdefault(name,props)
    holes=openings()
    ground_panel=Polygon([(.94,.035),(1.92,.035),(1.92,1.16),(5.44,1.16),(5.44,3.27),(.94,3.39)])
    mid_panel=Polygon([(.66,4.86),(5.36,4.71),(5.36,6.60),(.66,6.86)])
    inside=unary_union([box(*v) for v in holes.values()])
    panels=unary_union([ground_panel,mid_panel])
    # Trim bands follow the measured roofward fall. The side wall terminates at the different neighbouring render.
    for geom,material,name in [(band(0,0,1.106,1.106),PLINTH,'plinth'),(band(1.106,1.106,8.602,7.85),BRICK,'red unit facing'),
       (band(8.602,7.85,10.52,9.72),CREAM,'upper roughcast')]:
        add(b,geom.difference(inside.union(panels)),-.207,0,material,name)
    for p in [ground_panel,mid_panel]:add(b,p.difference(inside),-.207,-.012,PANEL,'light rendered opening panel')
    for label,bounds in holes.items():
        if label=='gated doorway':gate(b,bounds,lod)
        else:fixed(b,label,bounds,2 if label in ('ground sash','far middle sash','attic awning light')else 1,
                   5 if label=='ground sash' else 4,label=='near middle casement')
    awning(b,holes['attic awning light'],lod)
    condenser(b,lod)
    for low,high,y in [(1.16,1.24,5.43),(3.33,3.41,5.43),(4.82,4.88,5.36)]:
        start=1.92 if low<2 else .64
        rail(b,start,y,low,high,-.006,.04,RIM,'projecting lane string and sill')
