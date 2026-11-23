"""Four wings and their open lightwell, traced from the November 2021 orthophoto."""
import json
from math import ceil, cos, pi, sin
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from shapely import set_precision
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from fabric import GRAY, LAYOUT, PROJECT, RED, RED_STONE, SOURCE, STONE, face, metric, paint, polygons

sys.path.insert(0,str(PROJECT/'source/precise/changning-hongji-yuyuan-garden-houses-8-and-9/source'))
from hongji_roof_geometry import roof_envelope, surface

TILE='Nanlin | weathered courtyard roof tiles'
CLAY='Nanlin | half-round ridge tile'
ZINC='Nanlin | folded valley flashing'
SOFFIT='Nanlin | sheltered timber soffit'
COURT='Nanlin | courtyard paving'
CAP='Nanlin | warm grey stone coping'
PALETTE={TILE:{'color':[1,1,1],'roughness':.91,'texture':str(SOURCE/'nanlin-clay-tile.png')},
         CLAY:paint((139,79,54)), ZINC:paint((94,90,83),.57,.20), SOFFIT:paint((90,77,62)),
         COURT:paint((156,147,132)), CAP:paint((166,154,137))}
SOUTH=metric(119,452)[0]
NORTH=SOUTH+LAYOUT['window_wall_length_m']
WIDTH=LAYOUT['arcade_outer_width_m']


def tile_image():
    size=256
    y,x=np.mgrid[:size,:size];row=y//64
    t=(x/64+.07*(row%2))%1;v=y%64/64
    waves=8*np.cos(2*pi*t)-10*np.exp(-((t-.80)/.085)**2)
    lips=np.where(v>.95,-23,np.where(v<.055,6,0))
    rng=np.random.default_rng(51201)
    fired=rng.normal(0,4.0,(4,4))[row,(x//64)%4]
    grain=rng.normal(0,2.9,(size,size))
    tone=waves+lips+fired+grain
    result=np.array([159,99,73])+tone[:,:,None]*np.array([1.,.83,.67])
    Image.fromarray(np.clip(result,0,255).astype('uint8')).save(SOURCE/'nanlin-clay-tile.png',optimize=True)


def roof_survey():
    source=json.loads((SOURCE.parent/'measurements/placement-identity.json').read_text())
    epoch=next(e for e in source['per_epoch'] if e['wayback_id']==39767)
    nw,ne,se,sw=np.array(epoch['rim_NW_NE_SE_SW_pixels'])
    axes=np.column_stack([(ne-se)/(NORTH-SOUTH),(sw-se)/WIDTH])
    def local(p):
        xy=np.linalg.solve(axes,np.asarray(p)-se)
        return float(xy[0]+SOUTH),float(xy[1])
    inner=np.array([local(p) for p in source['2021_open_court']['NW_NE_SE_SW_image_xy']])
    sides={'south':float(inner[2:4,0].mean()),'north':float(inner[:2,0].mean()),
           'east':float(inner[1:3,1].mean()),'west':float(inner[[0,3],1].mean())}
    ridges={}
    for side in ['south','north']:
        pts=source['2021_ridges'][side+'_range_ridge_endpoints_pixels']
        ridges[side]=float(np.mean([local(p)[0] for p in pts]))
    return sides,ridges


def make_facets(c,ridges):
    # The two ridges coincide with the photographed gables at the river wall.
    # The east and west link roofs are simple pitches. Their upper edges are
    # partly hidden by trees in the four independent aerial captures.
    peaks={'south':9.82,'north':9.95}
    outer=8.06; inner=7.77
    x0,x1=SOUTH+.17,NORTH-.14
    y0,y1=.32,WIDTH-.13
    rows=[]
    def longitudinal(name,a,b,h0,h1):
        rise=(h1-h0)/(b-a);rows.append((name,box(a,y0,b,y1),(rise,0.,h0-rise*a)))
    longitudinal('south roof facing square',x0,ridges['south'],outer,peaks['south'])
    longitudinal('south roof facing court',ridges['south'],c['south'],peaks['south'],inner)
    longitudinal('north roof facing court',c['north'],ridges['north'],inner,peaks['north'])
    longitudinal('north roof facing garden',ridges['north'],x1,peaks['north'],outer)
    for name,a,b,za,zb in [('east link',y0,c['east'],8.19,inner),
                           ('west link',c['west'],y1,inner,8.27)]:
        rise=(zb-za)/(b-a)
        rows.append((name,box(ridges['south'],a,ridges['north'],b),(0.,rise,za-rise*a)))
    facets=roof_envelope(rows)
    outline=unary_union([shape for _,shape,_ in facets])
    expected=box(x0,y0,x1,y1).difference(box(c['south'],c['east'],c['north'],c['west']))
    if outline.symmetric_difference(expected).area>1e-4:
        raise ValueError('The four roof wings do not meet around their survey lightwell.')
    return facets,peaks


def wall_along(b,a,end,depth,base,top,material,label):
    p=Polygon([a,end,(end[0]+depth[0],end[1]+depth[1]),(a[0]+depth[0],a[1]+depth[1])])
    b.plan_prism(p,base,top,material,label)


def roof_edges(b,facets,lod):
    outline=unary_union([f for _,f,_ in facets])
    for name,part,(a,c,k) in facets:
        boundary=part.boundary.intersection(outline.boundary)
        for line in getattr(boundary,'geoms',[boundary]):
            if line.geom_type!='LineString' or line.length<.13: continue
            for p,q in zip(line.coords,line.coords[1:]):
                if np.linalg.norm(np.subtract(p,q))<.15:continue
                z=lambda xy:a*xy[0]+c*xy[1]+k
                # Drip rails follow the real outline, particularly the four
                # sides dropping toward the open sky of the court.
                b.tube([(p[0],p[1],z(p)-.071),(q[0],q[1],z(q)-.071)],
                       .046,ZINC,6 if lod else 8,name+' eave channel')


def covered_ridge(b,x,top,y0,y1,lod,label):
    length=.78 if lod else .39
    count=ceil((y1-y0)/length);pitch=(y1-y0)/count
    for i in range(count):
        # The thin lower hollow of the barrel cap is closed by the return skin.
        rr=.135+(.006 if i%3==0 else 0.)
        t=np.linspace(0.,pi,7 if lod else 12)
        p=[(x+rr*cos(a),top-.035+rr*sin(a)) for a in t]
        p.extend((x+(rr-.034)*cos(a),top-.035+(rr-.034)*sin(a))for a in reversed(t))
        y=y0+i*pitch
        face(b,Polygon(p),y,y+pitch-.004,CLAY,label+' overlapping ridge barrels')


def add_four_wings(b,lod=False):
    c,ridges=roof_survey();facets,peaks=make_facets(c,ridges)
    for name,shape,plane in facets:
        a,z,k=plane
        for q in polygons(shape):
            b.prism(q,-.154,-.083,lambda x,y,d:(x,y,a*x+z*y+k+d),SOFFIT,name+' roof boarding')
            surface(b,q,plane,TILE,name+' lapped clay courses',lod)
    roof_edges(b,facets,lod)
    for side,peak in peaks.items():
        covered_ridge(b,ridges[side],peak,.40,WIDTH-.20,lod,side)
    # Set the four courtyard walls just behind the visible drip edges; the
    # independently traced opening is measured at the roof, not at ground.
    court=box(c['south']-.18,c['east']-.18,c['north']+.18,c['west']+.18)
    full=box(SOUTH,0,NORTH,WIDTH)
    ring=full.difference(court)
    b.plan_prism(ring,-.12,.0,COURT,'four-wing plinth opening on courtyard')
    b.plan_prism(court,-.083,-.016,COURT,'open courtyard ground')
    # The arcade already has its own slabs and a recessed outer stair landing.
    floor=ring.intersection(box(SOUTH+LAYOUT['arcade_recess_m']+.15,.04,NORTH-.05,WIDTH-.05))
    b.plan_prism(floor,4.23,4.47,SOFFIT,'first floor ring around courtyard')
    si,ei,ni,wi=court.bounds
    for name,a,end,v in [('south',(si,ei),(si,wi),(-.23,0)),
                          ('east',(si,ei),(ni,ei),(0,-.23)),
                          ('north',(ni,wi),(ni,ei),(.23,0)),
                          ('west',(ni,wi),(si,wi),(0,.23))]:
        wall_along(b,a,end,v,0,7.72,GRAY,name+' courtyard wall')
    # Ends hidden by the modern estate and mature trees have continuous wall
    # surfaces. The photo record gives no reliable count for their apertures.
    wall_along(b,(NORTH,0),(NORTH,WIDTH),(-.29,0),0,8.17,GRAY,'north garden enclosure')
    wall_along(b,(SOUTH,WIDTH),(NORTH,WIDTH),(0,-.28),0,8.23,GRAY,'west enclosure towards estate')
    # Fill the gables behind their roof slopes at the west end. At the
    # east window wall the decorative crowns already cover these profiles.
    for side,left,right in [('south',SOUTH,c['south']),('north',c['north'],NORTH)]:
        hc=peaks[side]
        left_z=8.06 if side=='south' else 7.77
        right_z=7.77 if side=='south' else 8.06
        profile=Polygon([(left,7.72),(right,7.72),(right,right_z),
                          (ridges[side],hc-.075),(left,left_z)])
        face(b,profile,WIDTH-.30,WIDTH-.01,GRAY,side+' plain west gable closure')
        face(b,profile,.24,.42,GRAY,side+' east gable backing')
    # Only the paved south landing documented in the restored arcade photos.
    b.plan_prism(box(SOUTH-2.08,.08,SOUTH-.02,WIDTH-.08),-.15,-.018,COURT,'paved approach to public forecourt')
    b.plan_prism(box(SOUTH-.57,.07,SOUTH+.02,WIDTH-.07),-.039,.027,CAP,'arcade stone threshold landing')


if __name__=='__main__':tile_image()
