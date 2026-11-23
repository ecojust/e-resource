"""143-1 shop entrance, stepped threshold and the separate 143 lane-number pier as photographed in 2018."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from register_street import Camera

DATA=json.loads((Path(__file__).parent.parent/'measurements/number-plates.json').read_bytes())
BRICK='Xinlefang | red facing units with pale mortar'
PLINTH='Xinlefang | blue grey rendered plinth'
JAMB='Xinlefang | slate grey doorway surround'
HOOD='Xinlefang | charcoal fabric fascia'
PILLAR='Xinlefang | ochre lane gatepost'
EDGE='Xinlefang | pale grey gatepost coping'
FRAME='Xinlefang | dark entrance metalwork'
GLASS='Xinlefang | warm reflective door glass'
SHADOW='Xinlefang | dark interior at entrance'
BLACK='Xinlefang | black enamel number plate'
GREEN='Xinlefang | green enamel lane plate'
LETTERS='Xinlefang | pale enamel lettering'
METAL='Xinlefang | brushed threshold hardware'
STEP='Xinlefang | dark entrance stone'
PALETTE={
 BRICK:{'color':[.41,.173,.142],'roughness':.86},
 PLINTH:{'color':[.292,.323,.355],'roughness':.86},
 JAMB:{'color':[.224,.253,.282],'roughness':.71},
 HOOD:{'color':[.053,.050,.052],'roughness':.87},
 PILLAR:{'color':[.748,.624,.352],'roughness':.85},
 EDGE:{'color':[.45,.484,.499],'roughness':.84},
 FRAME:{'color':[.045,.046,.047],'roughness':.55,'metallic':.40},
 GLASS:{'color':[.242,.208,.15],'roughness':.20,'alpha':.67,'metallic':.18},
 SHADOW:{'color':[.069,.054,.042],'roughness':.86},
 BLACK:{'color':[.013,.016,.019],'roughness':.43,'metallic':.18},
 GREEN:{'color':[.019,.144,.079],'roughness':.46,'metallic':.16},
 LETTERS:{'color':[.72,.736,.663],'roughness':.65},
 METAL:{'color':[.49,.47,.424],'roughness':.39,'metallic':.62},
 STEP:{'color':[.063,.065,.065],'roughness':.70},
}

def plate(face,cam,name,depth,mat):
    rec=DATA['plates'][name]
    a,b,c,d=[cam.wall(uv,-depth)for uv in rec['corners_full_source_px']]
    # Keep the perspective-derived centre and independent measured dimensions.
    left=(a[0]+d[0])/2;right=(b[0]+c[0])/2;top=(a[2]+b[2])/2;low=(d[2]+c[2])/2
    plate=box(left,low,right,top)
    face.prism(plate,depth-.017,depth,mat,name+'/enamel plate')
    for n,rings in enumerate(rec['rectified_ink_regions_uv']):
        def coords(ring):return [(left+u*(right-left),top-v*(top-low))for u,v in ring]
        glyph=Polygon(coords(rings[0]),[coords(r)for r in rings[1:]])
        if not glyph.is_valid:glyph=glyph.buffer(0)
        if not glyph.is_empty:face.prism(glyph,depth+.0004,depth+.0024,LETTERS,name+f'/enamel inscription {n+1}')

def bounds(cam,tl,tr,br,bl,y=0):
    points=[cam.wall((u*5312/1120,v*2988/630),y)for u,v in [tl,tr,br,bl]]
    a,b,c,d=points
    return ((a[0]+d[0])/2,(c[2]+d[2])/2,(b[0]+c[0])/2,(a[2]+b[2])/2)

def door_opening(cam=None):
    cam=cam or Camera('2018')
    return box(*bounds(cam,(475,444),(573,440),(576,600),(475,603)))

def add_portal(builder,lod=False):
    cam=Camera('2018');face=Facade(builder,(-1,0),(1,0),'143-1 entrance')
    outer=door_opening(cam);l,lo,r,hi=outer.bounds
    il,below,ir,head=bounds(cam,(490,448),(558,444),(561,597),(491,600),.056)
    clear=box(il,below,ir,head)
    face.prism(outer.difference(clear),-.157,.037,JAMB,'slate door jambs and lintel')
    face.prism(clear,-.49,-.47,SHADOW,'recess behind glazed entrance')
    centre=(il+ir)/2
    for no,(a,b) in enumerate([(il+.008,centre-.004),(centre+.004,ir-.008)],1):
        pane=box(a,below+.026,b,head-.016)
        inside=box(a+.017,below+.052,b-.017,head-.042)
        face.prism(pane.difference(inside),-.104,-.073,FRAME,f'leaf {no}/perimeter')
        face.prism(inside,-.10,-.092,GLASS,f'leaf {no}/glass')
        handle=(b-.047) if no==1 else (a+.047)
        face.box(handle,below+1.12,.024,.36,.035,.002,FRAME,f'leaf {no}/pull')
        for z in [below+.970,below+1.265]:
            face.box(handle,z,.026,.026,.094,-.041,METAL,f'leaf {no}/handle fixing')
        for x in (a+.033,b-.033):
            face.box(x,below+.047,.060,.061,.037,-.061,METAL,f'leaf {no}/bottom pivot')
    face.box((l+r)/2,lo-.058,r-l+.12,.116,.307,.100,STEP,'upper stone threshold')
    face.box((l+r)/2,lo-.174,r-l+.17,.116,.495,.194,STEP,'projecting lower step')
    face.box((l+r)/2,lo-.11,r-l+.13,.023,.038,.268,EDGE,'pale tread arris')
    # The broad fabric canopy is held below a shallow, separately visible metal cap.
    ca,cz,cb,ct=bounds(cam,(430,420),(601,405),(599,431),(430,451),-.318)
    face.box((ca+cb)/2,(cz+ct)/2,cb-ca,max(.08,ct-cz),.32,.155,HOOD,'box awning with dark lettering fascia')
    face.box((ca+cb)/2,ct+.043,cb-ca+.07,.044,.361,.148,FRAME,'upper projecting canopy edge')
    plate(face,cam,'black-door',.045,BLACK)
    # The gatepost stands on the doorway side of the lane. It carries the
    # green communal lane plate. The adjoining red wall carries the black 143-1.
    p0,pl,p1,pt=bounds(cam,(644,435),(689,433),(695,604),(654,604),-.17)
    face.box((p0+p1)/2,(0+pt)/2,p1-p0,pt,.46,-.046,PILLAR,'yellow lane gatepost')
    for row in (2285,2333):
        _,_,z=cam.wall((3108,row),-.196)
        face.box((p0+p1)/2,z,p1-p0+.014,.016,.022,.185,JAMB,'two fine ruled bands below lane number')
    face.box((p0+p1)/2,.153,p1-p0+.018,.306,.468,-.045,PLINTH,'grey base on lane gatepost')
    face.box((p0+p1)/2,pt+.038,p1-p0+.068,.076,.50,-.038,EDGE,'grey coping of entrance pier')
    plate(face,cam,'green-lane',.205,GREEN)
    # Two dark conduits are visible between the black number and the
    # gatepost. Their rear ends disappear behind the awning and its cables.
    for n,(u,v) in enumerate([(2934,2251),(2960,2251)],1):
        x=cam.wall((u,v),-.080)[0]
        low=cam.wall((u+7,2800),-.080)[2]
        top=cam.wall((u-5,2018),-.080)[2]
        builder.tube([(x,-.077,low),(x,-.077,top-.14),(x-.022,-.073,top)],
                     .036,FRAME,9 if lod else 14,f'street conduit {n}')
        for vv in [2244,2617]:
            _,_,z=cam.wall((u,vv),-.111)
            face.box(x,z,.086,.044,.092,.073,FRAME,f'street conduit {n} / clamp')
