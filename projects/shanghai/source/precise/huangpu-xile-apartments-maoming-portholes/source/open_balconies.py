"""The open, southern half of three paired balconies above the entrance to number 116."""
from shapely.geometry import box
from shapely.ops import unary_union
from porthole_wall import facade, block


def back_wall(builder, floor, z, ceiling, d, lod):
    left,right,back=d['bay_edge'],d['north_cut'],d['balcony_back']
    base=z+d['floor_thickness']
    door_left=left+0.28
    window_left=door_left+0.92
    head=base+2.03
    door=box(door_left,base,door_left+0.75,head)
    window=box(window_left,base+0.83,window_left+0.67,head)
    cut=unary_union([door,window])
    wall=box(left,base,right,ceiling).difference(cut)
    name=f'{floor}F rear wall'
    facade(builder,wall,back,back+0.20,'Recessed ochre facing',name+' with door and window')
    for opening,midrail in [(door,base+0.86),(window,base+1.63)]:
        x0,z0,x1,z1=opening.bounds
        face=back+0.062
        facade(builder,opening,face+0.058,face+0.077,'Recess glazing',name+' glazing')
        border=opening.difference(box(x0+0.045,z0+0.042,x1-0.045,z1-0.042))
        facade(builder,border,face,face+0.058,'Warm dark joinery',name+' opening frame')
        block(builder,x0+0.045,x1-0.045,face+0.008,face+0.048,midrail-0.018,midrail+0.018,
              'Warm dark joinery',name+' cross rail')
        if opening is door:
            block(builder,x0+0.045,x1-0.045,face+0.015,face+0.053,z0+0.045,midrail-0.018,
                  'Door lower panel',name+' solid door bottom')
    if not lod:
        for j in range(1, int((ceiling-base)/0.15)):
            h=base+j*0.15
            facade(builder,wall.intersection(box(left,h,right,h+0.008)),back-0.006,back,
                   'Recessed pointing',name+' horizontal courses')
    # The house-side jamb returns to meet the circular-window pier.
    block(builder,left,left+0.095,0.03,back,base,ceiling,'Recessed ochre facing',name+' south return')


def side_glazing(builder,z,ceiling,lod,d,floor):
    """The thin perpendicular glazing visible beside the neighbouring enclosed half."""
    x=d['north_cut']
    low=z+d['floor_thickness']+0.06
    front,back=-0.56,d['balcony_back']
    name=f'{floor}F north glass return'
    for y0,y1 in [(front,(front+back)/2),((front+back)/2,back)]:
        block(builder,x-0.035,x-0.017,y0+0.029,y1-0.029,low+0.055,ceiling-0.058,
              'Side light',name+' glass')
    for y in [front,(front+back)/2,back]:
        block(builder,x-0.062,x,y-0.026,y+0.026,low,ceiling,'Deep bronze sash',name+' mullion')
    for h in [low+0.02,ceiling-0.038]:
        block(builder,x-0.064,x,front,back,h-0.020,h+0.020,'Deep bronze sash',name+' frame')
    if not lod:
        block(builder,x-0.055,x,front,back,low+1.65,low+1.679,'Deep bronze sash',name+' narrow rail')


def balcony(builder, floor, z, top, ceiling, d, lod):
    left,right=d['bay_edge'],d['north_cut']
    front,back=d['front_edge'],d['balcony_back']
    base=z+d['floor_thickness']
    name=f'{floor}F cantilever'
    block(builder,left,right,front+0.012,back+0.20,z,base,'Warm grey soffit',name+' floor slab')
    block(builder,left+0.032,right,front+0.032,back,base,base+0.027,'Stone balcony floor',name+' walking surface')
    # The two return faces of the southern end are visible from the direction of Nanchang Road.
    block(builder,left,right,front,front+0.147,z+0.040,top,'Sandy balcony render',name+' solid front parapet')
    block(builder,left,left+0.135,front+0.145,-0.018,base,top,'Sandy balcony render',name+' south parapet return')
    block(builder,left-0.008,right,front-0.013,front+0.154,top-0.031,top+0.012,'Buff coping',name+' coping')
    block(builder,left-0.008,left+0.145,front+0.155,0.005,top-0.031,top+0.012,'Buff coping',name+' return coping')
    rail_y=front+0.075
    cap=top+(0.302 if floor==2 else 0.218)
    # The rail runs above the solid panel. Air remains visible between the iron rails.
    for h in [cap,cap-0.111]:
        builder.tube([(left+0.075,-0.010,h),(left+0.075,rail_y+0.080,h),
                      (left+0.137,rail_y,h),(right-0.010,rail_y,h)],
                     0.014 if h==cap else 0.009,'Dark balcony iron',6 if lod else 10,name+' rail')
    for x in [left+0.075,left+1.25,right-0.067]:
        block(builder,x-0.014,x+0.014,rail_y-0.014,rail_y+0.014,top+0.011,cap,'Dark balcony iron',name+' rail posts')
    back_wall(builder,floor,z,ceiling,d,lod)
    side_glazing(builder,z,ceiling,lod,d,floor)
    if not lod:
        block(builder,left+0.148,right,front+0.13,front+0.153,z-0.012,z,
              'Soffit drip',name+' drip line')


def build_balconies(builder,lod,d):
    levels=d['slab_soffits']
    for i,(z,top) in enumerate(zip(levels,d['parapet_tops'])):
        ceiling=levels[i+1] if i+1<len(levels) else d['cap_soffit']
        balcony(builder,i+2,z,top,ceiling,d,lod)
