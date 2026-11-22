"""The two segmental arches between the hexagonal turret and the old east entrance."""
from shapely.geometry import box,LineString
from photo_architecture import Facade, opening
from brickwork import END,TRIM,CLAY,PALE,FRAME,IRON,YARD,window,grating,fan_case

END_X=9.98
FRONT_Y=-1.82
BACK_Y=1.46


def east_wing(builder,outline,fit,lod):
    join=outline.intersection(LineString([(-8,FRONT_Y),(8,FRONT_Y)]));begin=join.bounds[2]-.035
    f=Facade(builder,(begin,FRONT_Y),(END_X,FRONT_Y),'East end');offset=f.center[0]
    roof=fit['levels']['sill']['height_m'];first=fit['levels']['belt']['height_m']
    centres=(4.94,8.37);holes=[]
    for j,cx in enumerate(centres):
        u=cx-offset;width=2.50 if j==0 else 2.34
        glazed=opening(u,5.92,width,2.92,.68,12 if lod else 32)
        lower=opening(u,.43 if j==0 else .83,width*.76,3.22 if j==0 else 2.84,.095,12 if lod else 24)
        holes.extend([glazed,lower]);window(f,glazed,.68,(.27,.54,.78),(.19,.70,),lod,'paired arch '+str(j+1))
        window(f,lower,.095,(.36,.68),(.69,),lod,'courtyard lower joinery '+str(j+1));grating(f,u,2.06,width*.78,2.83,lod,'end face barred openings')
        fan_case(f,u+.17,5.22,lod)
        # A second, shallow band of molded brick follows each arch.
        brow=glazed.buffer(.26,join_style=2).difference(glazed.buffer(.18,join_style=2))
        brow=brow.intersection(box(u-width,8.12,u+width,9.23));f.prism(brow,.012,.085,TRIM,'hood over paired arches')
    f.wall(.13,roof,holes,.36,END)
    for i,cx in enumerate([begin+.20,6.67,END_X-.18]):
        u=cx-offset;f.box(u,7.13,.23,5.64,.16,.055,TRIM,'east facade brick pilasters')
        f.box(u,9.78,.38,.2,.24,.098,CLAY,'east facade pilaster capitals')
    for z,h,d,mat,name in [(first-.20,.15,.11,TRIM,'base belt'),(first-.065,.10,.145,PALE,'lower course cap'),(roof-.31,.18,.17,TRIM,'cornice bed'),(roof-.12,.12,.23,CLAY,'parapet ledge'),(roof+.01,.084,.245,PALE,'drip ledge')]:
        f.beam(z,h,d,mat,width=f.length+.028,label=name)
    for j in range(7 if lod else 15):
        u=f.length*((j+.5)/(7 if lod else 15)-.5)
        f.box(u,roof-.28,.152,.125,.235,.116,TRIM,'short wing dentils')
    floor=box(0,FRONT_Y,END_X,BACK_Y).difference(outline)
    builder.plan_prism(floor,.035,.135,YARD,'East end plinth')
    builder.plan_prism(floor,roof-.14,roof+.04,YARD,'East end flat roof behind parapet')
    # Capped parapet with the low recessed panels visible behind the twin arches.
    f.box(0,roof+.43,f.length,.78,.25,-.01,END,'terrace parapet')
    f.box(0,roof+.85,f.length+.05,.12,.34,.015,PALE,'parapet stone cap')
    for cx in (begin+.17,5.66,7.82,9.76):
        u=cx-offset;f.box(u,roof+.61,.26,1.15,.35,.022,TRIM,'parapet uprights')
        f.box(u,roof+1.20,.325,.11,.40,.035,PALE,'parapet upright caps')
    north=Facade(builder,(END_X,FRONT_Y),(END_X,BACK_Y),'End wall cut return');north.wall(.13,roof,[],.27,END)
    start=(outline.intersection(LineString([(-8,BACK_Y),(8,BACK_Y)]))).bounds[2]
    if END_X>start:
        rear=Facade(builder,(END_X,BACK_Y),(start-.02,BACK_Y),'Short wing rear joint');rear.wall(.13,roof,[],.27,END)
    for x in (begin+.16,END_X-.25):
        f.line((x-offset,.22,.215),(x-offset,roof+.81,.215),.055,IRON,sides=8 if lod else 14,label='rainwater downpipe')
        for z in (1.0,3.2,5.5,7.7,9.4):f.box(x-offset,z,.15,.08,.23,.10,TRIM,'drain strap')
