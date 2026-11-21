"""Street shops, concrete piers, coupled roof lights and the river-facing gable."""
from math import cos, sin, pi
import random
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union
from warehouse_brick import MATERIAL as BRICK


def finish(rgb, roughness=.8, metal=0.):
    def channel(n):
        v=n/255.
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[channel(v) for v in rgb],roughness=roughness,metallic=metal)


CEMENT='Weathered cement bands'
SAND='Pale mineral edging'
RED='Red brick over the river bays'
SLATE='Dark coping and joint'
STONE='Taupe cement pilasters'
SHOP_GLASS='Inset blue-green shop glazing'
SHOP_FRAME='Shopfront dark metal reveal'
WARM='Warm shop display back'
WOOD='Oxide red timber shutters'
PAPER='Two off-white attic signboards'
LEAF='Ivy across the first storey belt'
STEM='Shadowed ivy stems'
PALETTE={CEMENT:finish((164,159,145)),SAND:finish((197,188,166)),RED:finish((144,92,76)),
         SLATE:finish((90,91,82)),STONE:finish((158,138,116)),SHOP_GLASS:finish((76,85,77),.32,.18),
         SHOP_FRAME:finish((76,73,64),.48,.28),WARM:finish((153,119,71),.65),
         WOOD:finish((123,79,73),.7),PAPER:finish((207,203,188),.79),
         LEAF:finish((82,107,64)),STEM:finish((61,78,57)),BRICK:finish((149,144,132)),
         'Warm shop shelf edge':finish((197,166,111),.57),'Pane reflection':finish((145,146,123),.4,.24)}


def poly_from_profile(dimensions):
    top=dimensions['main_profile']
    half=dimensions['wall_width']/2
    return Polygon([(-half,0),(half,0),(half,top[-1][1]),*reversed(top),(-half,top[0][1])]).buffer(0)


def upper_vents(d):
    width_scale=d['pillar_distance']/8.512467609215205
    return [rect(x*width_scale-.36*width_scale,12.75,x*width_scale+.36*width_scale,13.60)
            for x in (-5.43,5.62)]


def shop_openings(d):
    return {
        key:rect(item['center']-item['width']/2,item['sill'],item['center']+item['width']/2,item['head'])
        for key,item in d['street'].items()
    }


def edge_band(facade, points, thickness, back, front, material, label):
    from shapely.geometry import LineString
    line=LineString(points)
    facade.prism(line.buffer(thickness/2,cap_style=2,join_style=2),back,front,material,label)


def upper_front(f,d,lod):
    half=d['wall_width']/2
    scale=d['pillar_distance']/8.512467609215205
    profile=d['main_profile']
    for idx,(depth,thick,dz,mat) in enumerate(((.104,.13,-.05,SLATE),(.145,.09,-.17,CEMENT))):
        edge_band(f,[(x,z+dz)for x,z in profile],thick,-.51,depth,mat,'Gable continuous coping '+str(idx+1))
    for side in (-1,1):
        x=side*d['pillar_distance']/2
        f.prism(Polygon([(x-.70,0),(x+.70,0),(x+.61,4.47),(x+.58,8.03),(x+.58,11.91),(x-.56,11.91),(x-.55,8.03),(x-.63,4.47)]),
                -.015,.155,STONE,'Full-height cement pier')
        for z,width in [(4.46,1.38),(8.01,1.28),(11.92,1.37)]:
            f.box(x,z,width,.15,.32,.072,CEMENT,'Pier capital and belt junction')
        if not lod:
            f.box(x,3.34,.17,.65,.065,.162,CEMENT,'Vertical dash on portal piers')
            f.box(x,3.47,.083,.32,.055,.209,STONE,'Pier raised rib')
        vent=upper_vents(d)[0 if side<0 else 1]
        surround=vent.buffer(.27,join_style=2)
        f.prism(surround.difference(vent),-.012,.105,RED,'Square attic vent in red brick')
        f.prism(vent.buffer(.08,join_style=2).difference(vent),.103,.151,CEMENT,'Deep square attic vent lip')
        f.prism(vent.buffer(.006,join_style=2),-.82,-.79,SHOP_FRAME,'Dark vent recess')
        u=(vent.bounds[0]+vent.bounds[2])/2
        if not lod:
            for j in (-1,1): f.box(u+j*.125,13.16,.028,.68,.05,-.47,SLATE,'Attic vent iron bar')
        shoulder=[(side*6.90*scale,12.23),(side*12.76*scale,12.23),
                  (side*12.54*scale,13.27),(side*7.04*scale,14.24)]
        panel=Polygon(shoulder).buffer(0)
        f.prism(panel,-.012,.052,RED,'Inclined red brick attic panel')
        f.prism(panel.buffer(-.16,join_style=2),.050,.079,CEMENT,'Recessed lime panel in brick parapet')
        centre=side*12.62*scale
        from shapely.geometry import Point
        ring=Point(centre,13.02).buffer(.30*scale,quad_segs=6 if lod else 11)
        inset=Point(centre,13.02).buffer(.205*scale,quad_segs=6 if lod else 11)
        f.prism(ring.difference(inset),.075,.19,RED,'Attic circular inset rim')
        f.prism(inset,.077,.101,SAND,'Inset roundel')
    # Offset twin commercial boards, photographed in 2019 and 2020. The lower
    # panel is largely blank in the later November image.
    panel_w=6.50*scale
    for z,h in [(14.66,.65),(13.64,.83)]:
        f.box(-.075,z,panel_w+.09,h+.09,.13,.163,SLATE,'Attic fascia shadow')
        f.box(-.075,z,panel_w,h,.11,.24,PAPER,'Stacked pale attic signboards')
    return -.075,14.66,panel_w*.85,.38,.30


def belts(f,d,lod):
    half=d['wall_width']/2
    for z,height,project,material in [(4.39,.20,.13,CEMENT),(7.96,.27,.135,SLATE),(8.11,.105,.17,CEMENT),
                                       (11.92,.24,.17,SLATE),(12.08,.08,.16,SAND)]:
        f.box(0,z,half*2,height,.30+project,project/2-.13,material,'Belt course')
    # A long line of real greenery follows the first sill belt. Reproduce its
    # rhythm separately from the deep red window boxes directly above it.
    rng=random.Random(1295)
    step=.45 if lod else .26
    pts=[]
    for i in range(int(2*half/step)+1):
        x=-half+(2*half)*i/int(2*half/step)
        pts.append((x,4.45+.055*sin(x*1.66)+.035*sin(x*3.21),.201))
    f.line(pts[0],pts[1],.028,STEM,6,'Garland stem')
    for i,(x,z,depth) in enumerate(pts[1:],1):
        if i>1:f.line(pts[i-1],pts[i],.031,STEM,5,'Garland stem')
        count=2 if lod else 3
        for j in range(count):
            shift=(rng.random()-.5)*step
            cx=x+shift;cz=z+(rng.random()-.5)*.12;r=rng.uniform(.052,.103)
            shape=Polygon([(cx-r,cz),(cx-.28*r,cz+.80*r),(cx+.47*r,cz+r),(cx+r,cz-.08*r),
                           (cx+.20*r,cz-.71*r),(cx-.32*r,cz-.60*r)])
            f.prism(shape,depth,depth+.018,LEAF,'Leaf clusters along first storey')


def shops(f,d,lod):
    openings=shop_openings(d)
    for k in ('east_shutter','east_retail','west_retail','display'):
        aperture=openings[k];l,b,r,t=aperture.bounds;cx=(l+r)/2;cz=(b+t)/2
        surround=aperture.buffer(.107 if k=='east_shutter' else .095,join_style=2)
        f.prism(surround.difference(aperture),-.071,.077,CEMENT,'Street opening squared masonry edge')
        if k=='east_shutter':
            f.prism(aperture.buffer(.005,join_style=2),-.23,-.18,WOOD,'Low red shutter back')
            for j in range(9 if not lod else 5):
                x=l+(r-l)*(j+.5)/(9 if not lod else 5)
                f.box(x,cz,.054,(t-b)*.80,.06,-.12,SHOP_FRAME,'Dark louvre slots')
            f.box(cx,cz,.072,t-b,.11,-.075,WOOD,'Louvre centre stile')
            continue
        inset=aperture.buffer(-.067,join_style=2)
        f.prism(aperture.difference(inset),-.20,-.095,SHOP_FRAME,'Retail window or door reveal')
        f.prism(aperture.buffer(.009,join_style=2),-.72,-.70,WARM if k=='display' or k=='west_retail' else SHOP_GLASS,'Shop interior visible through glazing')
        if k=='display':
            f.box(cx-.42,b+.70,(r-l)*.68,.065,.45,-.43,'Warm shop shelf edge','Display shelf and plinth')
            f.box(cx+.26,b+.32,(r-l)*.61,.07,.42,-.42,WOOD,'Display shelf and plinth')
            for i in range(3 if lod else 8):
                x=l+(r-l)*(.17+.71*i/(2 if lod else 7))
                h=.18+.13*(.5+.5*sin(i*2.5))
                f.box(x,b+.73+h/2,.08+.02*(i%3),h,.08,-.41,SHOP_FRAME if i%3 else WOOD,'Objects on window shelf')
            f.box(cx,t-.48,r-l,.055,.075,-.18,SHOP_FRAME,'Display transom')
            f.box(cx+.58,cz,.050,t-b,.07,-.16,SHOP_FRAME,'Display vertical mullion')
        else:
            f.box(cx+.12,cz,.043,t-b,.085,-.14,SHOP_FRAME,'Retail door jamb')
            f.box(cx,t-.59,r-l,.045,.09,-.14,SHOP_FRAME,'Retail door transom')
            f.box(cx-.18,b+.97,.027,.29,.104,-.085,SLATE,'Retail door handle')
            if not lod:
                f.box(cx-.23,cz,.018,(t-b)*.72,.026,-.20,'Pane reflection','Narrow reflected glazing edge')
        f.box(cx,b-.035,r-l+.13,.075,.39,-.05,SAND,'Inset street threshold')


def bay_masonry(f,d,lod):
    half=d['wall_width']/2
    rings=[]
    for side in (-1,1):
        for cx,width in [(side*(half-.65),1.04),(side*6.77,1.04)]:
            f.box(cx,8.16,width,7.27,.15,.061,BRICK,'Broad brick piers framing each side bay')
            for z in (4.47,8.00,11.88):
                f.box(cx,z,width+.16,.145,.235,.10,CEMENT,'Stepped brick pier cap')
        for cx,width in [(side*9.97,4.31),(0,5.22)]:
            if cx==0 and side>0: continue
            # The older oblique photograph shows the recessed under-sill
            # masonry as a red surround with pale weathered centre panels.
            outer=rect(cx-width/2,8.10,cx+width/2,9.39)
            f.prism(outer,.010,.047,RED,'Brick spandrel beneath upper windows')
            divisions=3 if cx==0 else 2
            pitch=width/divisions
            for j in range(divisions):
                x=cx+(j-(divisions-1)/2)*pitch
                inner=rect(x-pitch*.40,8.20,x+pitch*.40,9.30)
                f.prism(inner,.045,.065,BRICK,'Inset worn-lime spandrel field')
            f.box(cx,8.15,width+.14,.11,.165,.073,CEMENT,'Spandrel lower moulding')
    for j in (-1,1):
        cx=j*9.94
        f.box(cx,4.34,4.72,.20,.24,.102,SLATE,'Sill shadow over ground floor')
        f.box(cx,4.49,4.70,.091,.24,.124,CEMENT,'Sill edge over ground floor')
    if not lod:
        # Discontinuous reddish brick returns survive beside all four tall
        # pilasters below the uppermost string course.
        for side in (-1,1):
            for x in (side*6.75,side*(half-.64)):
                for z in (5.75,10.10):
                    f.box(x-.29*side,z,.12,.70,.15,.10,RED,'Exposed brick arris')


def front_display(f,d,lod):
    item=d['street']['display'];x=item['center'];w=item['width'];z=item['sill'];h=item['head']-z
    f.box(x,z+h-.15,w-.11,.22,.11,-.62,'Warm shop shelf edge','Lit timber shop soffit')
    for side in (-1,1):
        f.box(x+side*(w/2-.075),z+h/2,.096,h-.10,.56,-.42,WARM,'Timber lining to the display recess')
    f.box(x-.42,z+.51,w*.51,.30,.40,-.44,SAND,'Low pale display cabinet')
    f.box(x-.44,z+.69,w*.55,.063,.43,-.42,'Warm shop shelf edge','Top of display cabinet')
    f.box(x+.36,z+1.52,.70,.70,.10,-.59,SLATE,'Deep shadow on the shop back wall')
    plant_x=x+w*.31
    f.box(plant_x,z+.22,.30,.39,.22,-.48,WOOD,'Planter inside the street display')
    rng=random.Random(129510)
    for j in range(4 if lod else 13):
        px=plant_x+rng.uniform(-.22,.23);pz=z+rng.uniform(.58,1.31)
        f.line((plant_x,.39+z,-.46),(px,pz,-.46),.014,STEM,5,'Plant stems inside display')
        f.prism(Polygon([(px,pz),(px-.104,pz+.043),(px-.14,pz+.145),(px-.023,pz+.096)]),
                -.47,-.439,LEAF,'Plant leaves inside display')
