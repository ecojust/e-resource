"""Bonded blue-grey wall, red pilaster, recessed panels and the stepped floor band."""
import json,math
from pathlib import Path
import numpy as np
from shapely.geometry import box,Polygon,LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from photo_plane import original,position,front_shape
from material_names import MATERIAL
MORTAR='Pale mineral pointing'
RED='Muted red face brick'
BURNT='Burnt red headers'
BLUE='Dark blue-grey headers'
STONE='Warm pale string-course stone'
MOLD='Red cut brick cornice'
REVEAL='Pilaster recess return'
DARK='Recessed vent darkness'
MEASURE=Path(__file__).resolve().parents[1]/'measurements'

def shape(points,y=0):
    return front_shape([original(u,v) for u,v in points],y).buffer(0)

def tier_holes():
    outlines=json.loads((MEASURE/'arch-outlines.json').read_bytes())
    holes=[]
    for name,feet in [('upper',[(470,253),(134,319)]),('lower',[(530,774),(84,818)])]:
        row=outlines['tiers'][name]
        outer=row['outer'];inner=row['front_intrados']
        top=front_shape([*outer,inner[-1],*[original(*q)for q in feet],inner[0]])
        holes.append(top.buffer(0))
    return unary_union(holes)

def panel_holes():
    # Independent outlines of the long blind fields in the red pilaster. The
    # blue rear plane is solid except for the small vent visible in the lower bay.
    lower=[(606,425),(607,413),(613,404),(616,400),(620,393),(629,390),(636,388),(646,389),(654,398),(661,402),(666,415),(736,767),(739,780),(736,788),(728,795),(720,803),(704,806),(686,804),(676,799),(668,792),(663,781)]
    upper=[(533,32),(534,25),(540,20),(543,15),(550,12),(558,13),(569,18),(573,26),(611,200),(614,209),(611,215),(603,220),(584,225),(570,224),(566,219),(562,210)]
    return [shape(x,-.058) for x in (lower,upper)]

def brick_grid(f,region,face,back,material,prefix,pitch,origin_z,lod,red=False):
    # Course heights come from independent narrow strips of the photograph.
    # Courses alternate long stretchers and headers. The narrow revealed
    # mortar at the joints is modelled at both display resolutions.
    xmin,zmin,xmax,zmax=region.bounds
    left=math.floor(xmin/.21)*.21
    row0=math.floor((zmin-origin_z)/pitch);row1=math.ceil((zmax-origin_z)/pitch)
    for j in range(row0,row1):
        z=origin_z+j*pitch
        span=.195 if j%2==0 else .104
        x=left-span+(0.5*span if j%4 in (1,2) else 0)
        idx=0
        while x<xmax:
            tile=box(x+.0023,z+.0026,x+span-.0023,z+pitch-.0026)
            if region.intersects(tile):
                part=tile.intersection(region)
                if part.area>.000012:
                    shade=material
                    if (j*19+idx*7)%13 in (1,7):
                        shade=BURNT if red else BLUE
                    label=prefix+' rows '+str((j//4)*4)+' to '+str((j//4)*4+3)
                    if not lod and part.geom_type=='Polygon' and len(part.exterior.coords)==5 and part.equals(tile):
                        # A brick is one closed editable component. Twelve vertices
                        # describe its bed, exposed arris and recessed front corners.
                        x0,z0,x1,z1=part.bounds
                        def ring(inset,y):
                            return [[x0+inset,y,z0+inset],[x1-inset,y,z0+inset],
                                    [x1-inset,y,z1-inset],[x0+inset,y,z1-inset]]
                        vertices=ring(0,back)+ring(0,face)+ring(.0017,face-.0011)
                        faces=[(3,2,1,0),(8,9,10,11)]
                        for k in (0,4):
                            for i in range(4):
                                n=(i+1)%4
                                faces.append((k+i,k+n,k+4+n,k+4+i))
                        f.builder.add(vertices,faces,shade,label)
                    else:
                        f.prism(part,-back,-face,shade,label)
            idx+=1;x+=span

def add_wall(b,lod):
    f=Facade(b,(-7,0),(7,0),'East bay')
    shell=shape([(27,956),(14,941),(68,185),(79,151),(125,0),(643,0),(688,244),(713,259),(731,347),(845,833),(859,861),(869,920),(865,938),(572,955)])
    openings=tier_holes()
    # One edge remains at the real photographic frame, where the upper eave
    # at the right end of the building leaves the view.
    pier=shape([(480,0),(639,0),(683,242),(713,256),(731,344),(843,833),(857,848),(866,924),(567,941),(601,833),(562,563),(544,429),(529,355),(492,300),(514,279),(494,137)],-.058)
    voids=unary_union(panel_holes())
    opaque=shell.difference(openings)
    main=opaque.difference(pier)
    # The outer brick rim projects forward. Underneath it a continuous mortar
    # bed spans from the projected outer arris to the wall-face survey curve.
    outlines=json.loads((MEASURE/'arch-outlines.json').read_text())['tiers']
    for tier, outline in outlines.items():
        points=outline['outer']
        front=[position(u,v,-.036)[[0,2]] for u,v in points]
        wall=[position(u,v,0.)[[0,2]] for u,v in points]
        seam=LineString(front).buffer(.035,cap_style=2).union(LineString(wall).buffer(.035,cap_style=2))
        f.prism(seam,-.093,-.032,MORTAR,tier+' outer arch bedding')
    # Wall backs provide real reveals around both rows of windows.
    f.prism(main,-.275,-.009,MORTAR,'solid wall with measured window reveals')
    f.prism(pier.difference(voids),-.26,.046,MORTAR,'pilaster cut for two recessed fields')
    intervals=json.loads((MEASURE/'wall-courses.json').read_bytes())['groups']
    blue_pitch=intervals['grey_under_window']['median_observed_spacing_m']
    red_pitch=intervals['lower_pier_red']['median_observed_spacing_m']
    brick_grid(f,main,0.,.010,MATERIAL,'grey wall',blue_pitch,-.535,lod)
    brick_grid(f,pier.difference(voids),-.058,-.045,RED,'red pier',red_pitch,-.344,lod,True)
    # The registered blind recesses have a separate blue-brick floor set 75mm
    # back from the pilaster face, and their reveals retain a visible shadow.
    vent=shape([(631,434),(633,432),(638,431),(642,432),(644,435),(642,439),(638,441),(632,440)],.014)
    for j,field in enumerate(panel_holes(),1):
        ring=field.boundary.buffer(.0045)
        f.prism(ring,-.018,.056,REVEAL,'recess '+str(j)+' jamb rim')
        region=field.difference(vent) if j==1 else field
        f.prism(region,-.24,-.026,MORTAR,'recess '+str(j)+' rear bed')
        brick_grid(f,region,.016,.029,MATERIAL,'recess '+str(j),blue_pitch,-.535,lod)
    # Exposed brick returns darken the small opening from the oblique street view.
    # The rear plate bounds the recess at its inferred depth.
    f.prism(vent.boundary.buffer(.00055),-.106,-.018,DARK,'dark vent returns')
    f.prism(vent,-.111,-.105,DARK,'inside photographed vent')
    # The pale cap and moulded red courses follow a jog across the projecting
    # pier. Strip widths reflect the photographed lower edges of the cornice.
    for i,(points,delta,depth,mat) in enumerate([
        ([(34,397),(491,300),(491,295),(709,250)],14,.105,STONE),
        ([(34,414),(492,317),(494,311),(714,266)],13,.088,MOLD),
        ([(32,429),(497,332),(498,326),(717,280)],7,.080,BURNT),
        ([(30,438),(498,345),(506,337),(719,294)],8,.066,MOLD),
        ([(28,449),(506,360),(508,350),(722,311)],8,.053,RED),
        ([(27,459),(512,376),(516,359),(721,323)],5,.041,MOLD),
        ([(23,948),(566,928),(571,920),(869,916)],13,.082,STONE)]):
        line=np.asarray(points,float);base=line+np.array([0.,delta])
        poly=shape([*line,*base[::-1]],-depth)
        f.prism(poly,-.08,depth,mat,'stepped string course '+str(i+1))
