"""Glazed bays, stone figures and black granite shopfront observed from Fuzhou Road."""
from pathlib import Path
from math import cos, sin, pi
import json
import numpy as np
from shapely.geometry import box, LineString
from shapely.ops import unary_union
from fuzhou_photo_plane import on_wall
from material_names import MATERIAL
from upper_bookshop_windows import finish, openings

SOURCE=Path(__file__).resolve().parents[1]/'measurements'
DATA=json.loads((SOURCE/'bookshop-street-level.json').read_bytes())
GRANITE='Polished black granite on the Fuzhou storefront'
RAIL='Black lacquered street window sections'
GLASS='Cool grey street glazing'
SHOP='Warm light within the ground floor displays'
CANOPY='Grey weathered laminated pavement canopy'
STEEL='Dark metal frame of the inclined canopies'
SHADE='Dark interior behind the shop entrance'
STONE='Weathered grey stone shopfront figures'
BRASS='Faded metal lettering on the central fascia'
RECESS='Unlit recess beyond photographed open casements'
CARVED='Recesses of the draped stone figures'
PALETTE={RECESS:finish((32,30,32),.97,.0),BRASS:finish((164,148,119),.72,.17),GRANITE:finish((50,51,56),.46,.17),RAIL:finish((40,37,37),.50,.19),
         GLASS:finish((83,105,105),.26,.24),SHOP:finish((162,143,100),.35,.17),
         CANOPY:finish((126,137,142),.37,.30),STEEL:finish((69,65,65),.58,.22),
         SHADE:finish((46,40,36),.82,.00),STONE:finish((159,146,131),.88,.02),
         CARVED:finish((144,132,118),.94,.00)}

def rect(quad, y=0.):
    p=np.asarray([on_wall(*uv,y=y) for uv in quad])
    return box((p[0,0]+p[3,0])/2,(p[2,2]+p[3,2])/2,
               (p[1,0]+p[2,0])/2,(p[0,2]+p[1,2])/2)

def plate(b,shape,y0,y1,mat,label):
    if not shape.is_empty:b.prism(shape,-y1,-y0,lambda x,z,y:(x,-y,z),mat,label)

def block(b,l,z,r,top,y0,y1,mat,label):
    if r<=l or top<=z or y1<=y0:raise ValueError(label)
    b.box([(l+r)*.5,(y0+y1)*.5,(z+top)*.5],[r-l,y1-y0,top-z],mat,label=label)

def shop_glazing(b,l,z,r,top,y,count,material,name,depth=.15):
    outline=box(l,z,r,top)
    plate(b,outline.difference(outline.buffer(-.070,join_style=2)),y,y+depth,RAIL,name+' perimeter')
    pitch=(r-l)/count
    for k in range(count):
        lo=l+k*pitch+.033;hi=l+(k+1)*pitch-.033
        block(b,lo,z+.041,hi,top-.042,y+.084,y+.100,material,name+f' glazed light {k+1}')
    for k in range(1,count):
        x=l+pitch*k;block(b,x-.029,z+.060,x+.029,top-.060,y+.005,y+.128,RAIL,name+f' mullion {k}')

def shop_openings():
    rows=[]
    for bay in DATA['bays']:
        l,z,r,top=rect(bay['upper_shop_window']).bounds
        rows.append((bay['bay'],'upper',l,z,r,top,bay['vertical_lights']))
    for door in DATA['street_openings']:
        a,c=[on_wall(*p) for p in door['visible_head_px']]
        l,r=a[0],c[0];top=(a[2]+c[2])*.5;n=door['glazed_pier_openings'];bay=door['bay']
        if n==2:
            gap=.34;mid=(l+r)*.5
            for ll,rr in [(l,mid-gap/2),(mid+gap/2,r)]:
                rows.append((bay,'display',ll,.33,rr,top,1))
        else:rows.append((bay,'entrance' if bay==3 else 'display',l,.01 if bay==3 else .33,r,top,2 if bay==3 else 1))
    return rows

def add_wall(b):
    # The large marker piers are set at Y=0. The brick between windows is a
    # second, recessed face. All 90 upper apertures continue behind the sash.
    holes=[box(r['left'],r['bottom'],r['right'],r['top']) for r in openings()]
    holes.extend(box(l,z,r,top) for _,_,l,z,r,top,_ in shop_openings())
    wall=box(-13.246,0,13.246,27.54).difference(unary_union(holes))
    plate(b,wall,0.,1.08,MATERIAL,'Red brick frontage with upper windows and street openings')

def add_shopfront(b,lod=False):
    for aperture,(bay,kind,l,z,r,top,n) in enumerate(shop_openings(),1):
        label=f'Bookshop bay {bay} {kind} {aperture}'
        if kind!='entrance':
            y=.34 if kind=='upper' else .46
            shop_glazing(b,l,z,r,top,y,n,GLASS if kind=='upper' else SHOP,label)
            block(b,l-.061,z-.118,r+.061,z+.013,-.196,.48,GRANITE,label+' polished sill')
            if kind=='display':
                block(b,l-.10,top,r+.10,top+.29,-.23,.21,GRANITE,label+' sign bed')
        else:
            # The illuminated central entrance is recessed behind two large
            # jambs. The source does not resolve the room beyond the doors.
            depth=1.30
            for sign,x in [(-1,l),(1,r)]:
                block(b,x-.055,z,x+.055,top,.18,depth+.27,GRANITE,label+' dark return '+str(sign))
            block(b,l,z-.09,r,z+.025,-.36,depth+.60,GRANITE,label+' sill floor')
            block(b,l,top-.06,r,top+.07,.185,depth+.2,GRANITE,label+' soffit')
            block(b,l,z,r,top,depth+.38,depth+.45,SHADE,label+' shaded interior')
            shop_glazing(b,l+.06,z+.04,r-.06,top-.35,depth,3,SHOP,label+' door')
            for k in [1,2]:
                x=l+(r-l)*k/3
                b.tube([[x-.053,depth-.075,1.04],[x-.053,depth-.12,1.12],[x-.053,depth-.12,1.53],
                        [x-.053,depth-.075,1.61]],.016,STEEL,6 if lod else 12,label+f' handle {k}')
            block(b,l,top-.33,r,top,-.13,.23,GRANITE,label+' black transom sign')
    for bay in DATA['bays']:
        l,z,r,top=rect(bay['black_fascia'],-.32).bounds
        block(b,l,z,r,top,-.38,.25,GRANITE,f'Bay {bay["bay"]} dark granite sign fascia')
        block(b,l-.023,z-.027,r+.023,z+.018,-.414,.21,RAIL,f'Bay {bay["bay"]} narrow slate drip')
    for a in DATA['canopies']:
        n=a['visible_glass_lights'];bay=a['bay']
        # Use the two individually observed edges. Their depths are a
        # photograph-based estimate. Each pane is separately bedded in metal.
        rear=np.array([on_wall(*p,-.095) for p in a['rear_edge']])
        street=np.array([on_wall(*p,-.91) for p in a['street_edge']])
        # A sheet of glazing is planar. Fit the four photographed edge
        # samples together before subdividing the metal rafters and sheets.
        ends=np.vstack([rear,street])
        design=np.column_stack([ends[:,:2],np.ones(4)])
        plane=np.linalg.lstsq(design,ends[:,2],rcond=None)[0]
        rear[:,2]=np.column_stack([rear[:,:2],np.ones(2)])@plane
        street[:,2]=np.column_stack([street[:,:2],np.ones(2)])@plane
        def corner(u,v):return (1-v)*((1-u)*rear[0]+u*rear[1])+v*((1-u)*street[0]+u*street[1])
        for k in range(n):
            q=[corner(k/n+.006,0),corner((k+1)/n-.006,0),corner((k+1)/n-.006,1),corner(k/n+.006,1)]
            b.add([v.tolist()for v in q]+[(v+[0,0,-.031]).tolist()for v in q],
                  [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],CANOPY,f'Bay {bay} inclined glass canopy {k+1}')
        for k in range(n+1):
            pos=k/n;b.tube([corner(pos,0),corner(pos,1)],.027,STEEL,6 if lod else 10,f'Bay {bay} canopy rafter {k+1}')
        for end in [0,1]:
            b.tube([corner(0,end),corner(1,end)],.032,STEEL,6 if lod else 10,f'Bay {bay} canopy rail {end+1}')
        for s in [.14,.86]:
            f=corner(s,.72);h=corner(s,0)+[0,0,.34]
            b.tube([h,f],.016,STEEL,6 if lod else 9,f'Bay {bay} canopy stay {s:.2f}')

def add_carvings(b,lod=False):
    for i,statue in enumerate(DATA['stone_figures'],1):
        # The single street photograph gives a silhouette, not a surveyed
        # depth. The front and rear halves of each stone are interpolated
        # separately; the second figure's head and shoulders are obscured.
        sections=[]
        for v,left,right in statue['body_sections_px'][::-1]:
            a=on_wall(left,v,-.32);c=on_wall(right,v,-.32)
            sections.append(((a[0]+c[0])*.5,(a[2]+c[2])*.5,max(.027,(c[0]-a[0])*.5)))
        n=10 if lod else 22
        verts=[]
        for rank,(x,z,r) in enumerate(sections):
            for k in range(n):
                angle=2*pi*k/n; flutes=.028*cos(7*angle+rank*.11) if rank<len(sections)*.55 else .005*cos(4*angle)
                verts.append([x+r*(1+flutes)*cos(angle),-.34+r*.73*(1+flutes)*sin(angle),z])
        faces=[list(range(n-1,-1,-1))]
        for rank in range(len(sections)-1):
            for k in range(n):
                a=rank*n+k;c=rank*n+(k+1)%n;faces.append([a,c,c+n,a+n])
        faces.append(list(range((len(sections)-1)*n,len(sections)*n)))
        b.add(verts,faces,STONE,f'Stone figure {i} outlined from street photograph')
        arm=[on_wall(u,v,-.34-.64*sections[len(sections)//2][2])for u,v in statue['visible_arm_centreline_px']]
        b.tube(arm,.061 if i==2 else .075,STONE,7 if lod else 12,f'Stone figure {i} visible bent arm')
        x,z,r=sections[0]
        block(b,x-.38,z-.11,x+.38,z,-.67,.20,STONE,f'Stone figure {i} plinth')
        block(b,x-.42,z-.20,x+.42,z-.105,-.69,.21,GRANITE,f'Figure {i} black support cap')
        block(b,x-.31,z-.60,x+.31,z-.188,-.53,.22,GRANITE,f'Figure {i} projecting support')

def add_shop_mark(b,lod=False):
    sign=json.loads((SOURCE/'visible-brass-shop-mark.json').read_bytes())
    y=-.400
    for line in sign['strokes']:
        path=[on_wall(u,v,y) for u,v in line['centreline_px']]
        x,z=np.asarray(path)[:,[0,2]].T
        u,v=line['centreline_px'][0]
        width=np.linalg.norm(on_wall(u+line['half_thickness_px'],v,y)-on_wall(u,v,y))
        shape=LineString(zip(x,z)).buffer(width,cap_style=1,join_style=1,quad_segs=2 if lod else 4)
        plate(b,shape,y,-.379,BRASS,'Central fascia script '+line['label'])

def add_recess_backings(b,lod=False):
    # The 2016 close photographs show a nearly unlit space beyond these
    # five swung leaves. Its depth is estimated; the recess closes behind
    # the open sash, while the foreground remains unobstructed.
    names={'B1-R4-W1','B1-R4-W3','B5-R4-W3','B5-R5-W1'}
    for r in openings():
        if r['label'] not in names:continue
        l,z,rgt,top=r['left'],r['bottom'],r['right'],r['top']
        block(b,l-.38,z-.32,rgt+.38,top+.34,1.86,1.93,RECESS,r['label']+' unlit recess backing')
        block(b,l-.39,z-.32,l-.34,top+.34,1.07,1.90,RECESS,r['label']+' shadowed left return')
        block(b,rgt+.34,z-.32,rgt+.39,top+.34,1.07,1.90,RECESS,r['label']+' shadowed right return')
