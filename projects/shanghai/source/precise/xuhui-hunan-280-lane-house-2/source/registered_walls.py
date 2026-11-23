"""Two street-facing wall levels, a short return and the oblique lane wall of No. 2."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from register_house import Camera
from curved_corner import corner_limits
from flat_windows import add_window
import exterior_fittings as fittings
import east_face
from house_finishes import WALL,GROUND,SILL,STEEL

HERE=Path(__file__).resolve().parent
MEAS=HERE.parent/'measurements'
OBS=json.loads((MEAS/'flat-window-observations.json').read_text())['stations']
OUTLINE=json.loads((MEAS/'face-outlines.json').read_text())
PAINT='280-2 | dark rainwater iron'
PLINTH='280-2 | faded rose plinth'
RAIL='280-2 | fine roof guard'
PALETTE={PAINT:{'color':[.128,.125,.107],'roughness':.77,'metallic':.23},
         PLINTH:{'color':[.465,.379,.359],'roughness':.92},
         RAIL:{'color':[.256,.284,.27],'roughness':.67,'metallic':.47}}

def facade_coords(face,cam,picks):
    values=np.array([cam.plane(uv,face.center,face.n) for uv in picks])
    u=(values-face.center)@face.t
    return box(np.median(u[[0,3]]),np.median(values[[2,3],2]),
               np.median(u[[1,2]]),np.median(values[[0,1],2]))

def plaster(face,outlines,windows,label,lod):
    holes=unary_union(list(windows.values()))
    for z0,z1,material in outlines:
        wall=box(-face.length/2,z0,face.length/2,z1).difference(holes)
        face.prism(wall,-.22,0,material,label)
    for name,aperture in windows.items():
        add_window(face,aperture,label,name,lod)

def tiled_edge(face,z0,z1):
    face.prism(box(-face.length/2-.018,z0,face.length/2+.018,z1),-.20,.028,SILL,'weathered coping')

def pos_face(builder,lo,hi,depth,label):
    return Facade(builder,(lo,depth),(hi,depth),label)

def strip_roof_rail(b,face,z,length,height=.49):
    span=min(face.length,length)
    start=-face.length/2;end=start+span
    for rise in (.47*height,height):
        b.tube([face.point(start,z+rise,-.13),face.point(end,z+rise,-.13)],.014,RAIL,7,'280-2 roof / long horizontal guard')
    count=math.ceil(span/1.0)
    for u in np.linspace(start,end,count+1):
        b.tube([face.point(u,z+.01,-.13),face.point(u,z+height+.01,-.13)],.014,RAIL,7,'280-2 roof / guard upright')

def window_from_points(face,results,code,cam):
    pts=results['points']
    if code+'TL' in pts:
        left=pts[code+'BL'][0];right=pts[code+'BR'][0]
        return box(left-face.center[0],pts[code+'BL'][2],right-face.center[0],pts[code+'TL'][2])
    for key in ('43052486','no2-6-1512'):
        poly=OBS[key]['windows'].get(code)
        if poly:
            return facade_coords(face,cam if key=='43052486' else Camera('6-1512'),poly)
    return None

def add_street_wall(b,results,lod):
    parameters=results['parameters'];span=parameters['span'];depth=parameters['depth'];cam=Camera('86')
    west,_,zwest=cam.wall(OUTLINE['south_front']['upper_west_corner'])
    eastern=east_face.data()
    turn,far,rail_top,_=east_face.side_measurements()
    surveyed=eastern['geometry_on_retained_eight_station_system']
    cwest=span[3]-.53;ceast=span[4]+.44
    ewest=span[5]-.48
    zbreak=cam.wall((395,568))[2]
    ztop=cam.wall(OUTLINE['south_front']['upper_step_right'])[2]
    previous={}
    for low,high in [(1,1),(2,5)]:
        group='1' if low==1 else '2'
        def edge(bank,x):
            p=np.array(surveyed[bank+group+'BL'][:2]);q=np.array(surveyed[bank+group+'BR'][:2])
            return east_face.point_at_x(p,q,x)
        c0,c1=edge('C',cwest),edge('C',ceast)
        ep=np.array(surveyed['E'+group+'BL'][:2]);eq=np.array(surveyed['E'+group+'BR'][:2])
        e0=edge('E',ewest)
        e1=east_face.turn_curve(ep,eq,turn,far,2)[0]
        panels=[('AB',[west,0.],[cwest,0.],ztop),('C',c0,c1,turn[2]),
                ('',[ceast,0.],[ewest,0.],turn[2]),('E',e0,e1,turn[2])]
        z0=0 if low==1 else zbreak
        for banks,p,q,roof_z in panels:
            z1=zbreak if low==1 else roof_z
            surf=Facade(b,p,q,'280-2 street')
            holes={}
            for bank in banks:
                for storey in range(low,high+1):
                    code=bank+str(storey)
                    if code+'BL' in surveyed:
                        corners=[np.array(surveyed[code+corner]) for corner in ('BL','TR')]
                        u=[(vertex-surf.center)@surf.t for vertex in corners]
                        opening=box(u[0],corners[0][2],u[1],corners[1][2])
                    else:
                        opening=window_from_points(surf,results,code,cam)
                    if opening is not None:holes[code]=opening
            outlines=[(z0,z1,WALL)] if low>1 else [(z0,.34,PLINTH),(.34,z1,GROUND)]
            plaster(surf,outlines,holes,'south',lod)
            if low==1:
                previous[banks]=(p,q)
                if 'A' in banks:fittings.ground_vent(surf,cam,[(338,733),(358,746)])
            else:
                if banks in ('C','E'):
                    oldp,oldq=previous[banks]
                    ledge=Polygon([p,q,oldq,oldp])
                    if ledge.is_valid and ledge.area>.002:
                        b.plan_prism(ledge,z0-.055,z0,SILL,'280-2 street / soffit connecting the two storeys')
                if 'B' in banks:
                    fittings.condenser(surf,Camera('6-1512'),OUTLINE['visible_fixtures']['6-1512_front_air_unit'][0],'street lower condenser',lod)
                    fittings.bracket_pair(surf,holes['A3'],lod)
                tiled_edge(surf,z1,z1+.06)
                if banks=='E':strip_roof_rail(b,surf,z1+.06,surf.length,rail_top[2]-turn[2]-.06)
        for earlier,later in zip(panels,panels[1:]):
            p=earlier[2];q=later[1]
            if np.linalg.norm(np.array(q)-p)<.002:continue
            side=Facade(b,p,q,'280-2 stepped facade')
            z1=zbreak if low==1 else min(earlier[3],later[3])
            side.prism(box(-side.length/2,z0,side.length/2,z1),-.12,0,GROUND if low==1 else WALL,'exposed side of window bank')
    rail=pos_face(b,west,cwest,0.,'280-2 south roof')
    strip_roof_rail(b,rail,ztop+.07,rail.length)
    return np.array([west,0.]),ztop

def lane_direction(cam):
    directions=[]
    for code,quad in OBS['43052484']['windows'].items():
        if code[0]!='E':continue
        for i,j in [(0,1),(3,2)]:
            normal=np.cross(cam.ray(quad[i]),cam.ray(quad[j]))
            v=np.array([-normal[1],normal[0]])
            v/=np.linalg.norm(v)
            if v@cam.R[0,:2]<0:v=-v
            directions.append(v)
    v=np.median(directions,axis=0)
    return v/np.linalg.norm(v)

def add_lane_wall(b,limits,lod):
    cam=Camera('84')
    tangent=lane_direction(cam);normal=np.array([tangent[1],-tangent[0],0.])
    near=np.array(limits['jambs_xy'][0])
    # Fit to the visible face at the outer west jamb, not to an orthogonal block.
    def point(uv):return cam.plane(uv,[*near,0],normal)
    far=point(OUTLINE['inner_oblique_wall']['outer_visible_left'])[:2]
    face=Facade(b,far,near,'280-2 oblique lane wall')
    ztop=float(np.median([point(p)[2] for p in [(151,118),(79,205)]]))
    openings={k:facade_coords(face,cam,v) for k,v in OBS['43052484']['windows'].items()}
    door=json.loads((MEAS/'entrance-placement.json').read_text())
    left=np.array(door['left_sill_enu_m'][:2])
    door_axis=np.array(door['across_unit_enu'])
    along,_=np.linalg.solve(np.column_stack([tangent,-door_axis]),left-near)
    miter=near+tangent*along
    # The lane-side ground facade meets the door face behind the upper corner.
    # Extending the upper window line to grade hides the green plate in camera 84.
    lo=-face.length/2
    hi=lo+np.linalg.norm(miter-far)
    foot=max(0.,limits['bracket_bottom'])
    all_holes=unary_union(list(openings.values()))
    for z0,z1,mat in [(0,.32,PLINTH),(.32,foot,GROUND)]:
        face.prism(box(lo,z0,hi,z1).difference(all_holes),-.22,0,mat,'set-back foot of oblique wall')
    face.prism(box(lo,foot,face.length/2,ztop).difference(all_holes),-.22,0,WALL,'upper oblique plaster')
    for code,opening in openings.items():add_window(face,opening,'lane',code,lod)
    fittings.condenser(face,cam,OUTLINE['visible_fixtures']['84_long_air_units'][0],'lane lower condenser',lod)
    tiled_edge(face,ztop,ztop+.066)
    pipe=point((375,414))[:2]+face.n[:2]*.079
    b.tube([(*pipe,.05),(*pipe,ztop+.012)],.052,PAINT,10 if lod else 16,'280-2 west / tall downpipe')
    for z in np.arange(.83,ztop,2.65):
        b.tube([(*pipe,z),(*pipe,z+.028)],.064,PAINT,8 if lod else 12,'280-2 west / pipe socket')

def add_short_return(b,limits,west,ztop,lod):
    e=np.array(limits['jambs_xy'][-1])
    face=Facade(b,e,west,'280-2 short return')
    cam=Camera('86')
    holes={k:facade_coords(face,cam,v) for k,v in OUTLINE['short_return']['windows'].items()}
    # The west roof edge drops towards the turning bay in the 2016 near view.
    low,high=-face.length/2,face.length/2
    head=limits['parapet_top']
    roof_edge=Polygon([(low,3.65),(high,3.65),(high,ztop),(low,head)])
    cut=unary_union(list(holes.values()))
    for z0,z1,material in [(0,.32,PLINTH),(.32,3.65,GROUND)]:
        face.prism(box(low,z0,high,z1).difference(cut),-.22,0,material,'short return footing')
    face.prism(roof_edge.difference(cut),-.22,0,WALL,'return and sloping parapet')
    for code,opening in holes.items():add_window(face,opening,'short side',code,lod)
    for i,observed in enumerate(OUTLINE['visible_fixtures']['86_short_air_units']):
        fittings.condenser(face,cam,observed,'short return condenser '+str(i+1),lod,fan=i!=0)
    coping=Polygon([(low,head),(high,ztop),(high,ztop+.062),(low,head+.062)])
    face.prism(coping,-.22,.028,SILL,'parapet coping following photographed edge')
    for rise in (.27,.50):
        b.tube([face.point(low,head+rise,-.13),face.point(high,ztop+rise,-.13)],.013,RAIL,7,'280-2 west roof / sloped edge guard')
    for f in np.linspace(0,1,math.ceil(face.length)+1):
        u=low+face.length*f;z=head+(ztop-head)*f
        b.tube([face.point(u,z+.062,-.13),face.point(u,z+.51,-.13)],.013,RAIL,7,'280-2 west roof / upright')

def add_door_wall(b,limits):
    rec=json.loads((MEAS/'entrance-placement.json').read_text())
    left,right=(np.array(rec[k]) for k in ['left_sill_enu_m','right_sill_enu_m'])
    direction=np.array(rec['across_unit_enu'])
    far=np.array(limits['jambs_xy'][0])
    tangent=lane_direction(Camera('84'))
    _,left_extent=np.linalg.solve(np.column_stack([tangent,-direction]),left[:2]-far)
    a=left[:2]+direction*left_extent;d=right[:2]+direction*.38
    face=Facade(b,a,d,'280-2 recessed ground entrance')
    half=face.length/2
    hole=box(-half-left_extent,left[2],half-.38,rec['head_elevation_m'])
    face.prism(box(-half,0,half,limits['bracket_bottom']).difference(hole),-.20,0,GROUND,'wall with recessed gate opening')
    face.prism(box(-half,0,half,.28).difference(hole),.001,.014,PLINTH,'weathered footing')
    ledge=Polygon([*limits['jambs_xy'],d,a])
    if ledge.is_valid:
        b.plan_prism(ledge,limits['bracket_bottom']-.042,limits['bracket_bottom']+.012,SILL,'280-2 entrance / underside of projecting corner')
    for p,q in [(d,np.array(limits['jambs_xy'][-1]))]:
        return_wall=Facade(b,p,q,'280-2 threshold return')
        return_wall.prism(box(-return_wall.length/2,0,return_wall.length/2,limits['bracket_bottom']),-.18,0,GROUND,'under the projecting corner')

def add_registered_walls(b,lod=False):
    data=json.loads((MEAS/'house-cameras.json').read_text())
    limits=corner_limits()
    west,ztop=add_street_wall(b,data,lod)
    add_short_return(b,limits,west,ztop,lod)
    add_lane_wall(b,limits,lod)
    east_face.add_east_face(b,lod)
    add_door_wall(b,limits)
