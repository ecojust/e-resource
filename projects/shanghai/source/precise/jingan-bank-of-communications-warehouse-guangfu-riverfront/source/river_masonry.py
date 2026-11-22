"""Continuous carved side bays, raised gabled pilasters and return walls on the southern bend."""
from pathlib import Path
from math import hypot
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from south_entrance import finish

STONE='Guangfu | grey washed aggregate'
LIP='Guangfu | honed stone edges'
PLINTH='Guangfu | weathered base'
RETURN='Guangfu | gable render'
DARK='Guangfu | deep vent cavity'
IRON='Guangfu | rainwater cast iron'
JOINT='Guangfu | recessed joint'
PALETTE={
    STONE:dict(color=[1,1,1],texture=str(Path(__file__).with_name('guangfu-washed-aggregate.jpg')),roughness=.93,metallic=0),
    LIP:finish([181,178,169],.86),PLINTH:finish([151,148,140],.92),
    RETURN:finish([170,167,159],.93),DARK:finish([66,64,59],.9),
    IRON:finish([61,63,60],.57,.47),JOINT:finish([137,133,125],.90)
}

def face_at(bay):
    slope=(bay['y1']-bay['y0'])/(bay['x1']-bay['x0'])
    def wall(x,z,d):
        return x,bay['y0']+(x-bay['x0'])*slope-d,z
    return wall

def slab(b,area,out,inside,face,material,name):
    b.prism(area,-inside,out,face,material,name)

def widthwise(b,left,right,bottom,top,out,inside,face,material,name):
    if right-left>.004 and top-bottom>.004:
        slab(b,box(left,bottom,right,top),out,inside,face,material,name)

def opening_box(o,ex=0,ez=0):
    return box(o['x0']-ex,o['z0']-ez,o['x1']+ex,o['z1']+ez)

def outline_cap(left,right,top):
    return [(left,top-.120),(left+.19*(right-left),top-.11),
            ((left+right)/2,top),(right-.19*(right-left),top-.11),(right,top-.12)]

def side_bay(b,lod,g,opens,layout):
    name=g['bay'];face=face_at(g);left,right=g['x0'],g['x1'];top=layout['bay_wall_top']
    rows={o['level']:o for o in opens if o['level']>1}
    upper=rows[4];u0,u1=upper['x0'],upper['x1'];half=(u0+u1)/2
    # Each visible spandrel has two shallow fields. The small upper vents really pierce the front skin.
    # Midlevel passages are recessed slots; restored glazing sits behind the original stone.
    pits=[]
    for frac in (.25,.75):
        u=u0+(u1-u0)*frac
        pits.append(box(u-.075,upper['z1']+.33,u+.075,upper['z1']+.402))
    for floor in (3,2):
        u=half;zmid=(rows[floor]['z1']+rows[floor+1]['z0'])/2
        pits.append(box(u-.084,zmid-.061,u+.084,zmid+.061))
    holes=[opening_box(o,.016,.016)for o in opens]+pits
    body=box(left,0,right,top).difference(unary_union(holes))
    slab(b,body,0,.44,face,STONE,name+' bowed street wall and actual openings')
    split=(u1-u0)*.030
    for floor in (4,3,2):
        o=rows[floor];zlo=o['z1']+.104
        zhi=(top if floor==4 else rows[floor+1]['z0']-.105)
        if zhi<=zlo:continue
        for side,(a,c) in enumerate([(u0,half-split/2),(half+split/2,u1)]):
            surface=box(a,zlo,c,zhi).difference(unary_union(pits))
            slab(b,surface,.057,-.001,face,STONE,f'{name} F{floor} spandrel leaf {side+1}')
        widthwise(b,u0-.006,u1+.006,o['z1']+.008,zlo,.072,.007,face,LIP,f'{name} F{floor} stone window head')
        widthwise(b,u0-.017,u1+.017,o['z0']-.089,o['z0']-.016,.079,.010,face,LIP,f'{name} F{floor} external drip sill')
    for i,vent in enumerate(pits):
        a,lo,c,hi=vent.bounds
        slab(b,vent.buffer(.012,join_style='mitre'),-.272,.302,face,DARK,f'{name} recessed vent {i+1}')
        if not lod:
            widthwise(b,a+.008,c-.008,lo+.032,lo+.043,-.110,.138,face,IRON,f'{name} vent grille {i+1}')
    # Stone cheeks slope into the recess beside the three modern ground-level lights.
    for o in opens:
        if o['level']!=1:continue
        for side,u in [('west',o['x0']),('east',o['x1'])]:
            q=box(u-.022,o['z0'],u+.022,o['z1'])
            slab(b,q,.045,.133,face,LIP,o['key']+' '+side+' arris')
        widthwise(b,o['x0'],o['x1'],o['z0']-.093,o['z0']-.017,.063,.15,face,PLINTH,o['key']+' sill')
    widthwise(b,left,right,top-.067,top+.008,.022,.46,face,LIP,name+' broad parapet coping')

def major_pier(b,lod,name,half_width,peak,shoulder,face,center):
    # Figure 36 shows a slightly pitched crown with two recessed shoulders at either side.
    outer=half_width;inner=outer*.79
    crown=outline_cap(center-inner,center+inner,peak)
    side_top=shoulder-.18
    outline=[(center-outer,0),(center+outer,0),(center+outer,side_top),
             (center+inner,side_top),(center+inner,peak-.12),*reversed(crown[:-1]),
             (center-inner,side_top),(center-outer,side_top)]
    p=Polygon(outline)
    slab(b,p,.134,.42,face,STONE,name+' uninterrupted shoulder pilaster')
    spine=Polygon([(center-inner,0),(center+inner,0),*reversed(crown)])
    slab(b,spine,.192,-.130,face,STONE,name+' raised gable blade')
    top=[(x,z+.015)for x,z in crown]
    crown_cap=Polygon(top+[(x,z-.050)for x,z in reversed(crown)])
    slab(b,crown_cap,.206,.295,face,LIP,name+' sloping crown coping')
    for side,(a,c) in enumerate([(center-outer,center-inner),(center+inner,center+outer)]):
        widthwise(b,a,c,side_top-.045,side_top+.012,.147,.29,face,LIP,name+f' return cap {side+1}')
    if not lod:
        for n,xx in enumerate([center-inner-.018,center+inner+.016]):
            widthwise(b,xx-.008,xx+.008,.23,side_top-.09,.144,-.131,face,JOINT,name+f' vertical recess {n+1}')

def rain_pipe(b,lod,name,u,face,top):
    # The reproduced hoppers stand inside the flanking jamb, below the short upper vents.
    sides=6 if lod else 10
    def pt(z,d):return face(u,z,d)
    pipe_z=top-1.63
    b.tube([pt(.14,.181),pt(.32,.153),pt(pipe_z-.27,.153)],.073,IRON,sides,name+' cast iron downpipe')
    for i,z in enumerate(np.arange(1.09,pipe_z-.46,3.56)):
        b.tube([pt(z-.040,.153),pt(z+.040,.153)],.089,IRON,sides,name+f' socket {i+1}')
    # Closed funnel flares into a lipped square mouth, according to the reinstated original.
    verts=[];faces=[]
    for z,width,depth in [(pipe_z-.30,.15,.15),(pipe_z-.22,.17,.16),(pipe_z-.04,.39,.27),(pipe_z+.008,.42,.30)]:
        for dx,dd in [(-width/2,-depth/2),(width/2,-depth/2),(width/2,depth/2),(-width/2,depth/2)]:
            verts.append(face(u+dx,z,.16+dd))
    faces.append((0,1,2,3))
    for i in range(3):
        for k in range(4):
            j=(k+1)%4
            faces.append((4*i+k,4*(i+1)+k,4*(i+1)+j,4*i+j))
    faces.append((15,14,13,12))
    # Face() makes increasing outward depth point towards the river; local x cross depth is downward.
    b.add(verts,faces,IRON,name+' flared rain hopper')
    lx=u-.224;rx=u+.224
    widthwise(b,lx,rx,pipe_z+.008,pipe_z+.060,.322,.015,face,IRON,name+' hopper rim')
    if not lod:
        for n,z in enumerate((2.91,6.52,10.16,13.84)):
            if z>pipe_z-.20:continue
            widthwise(b,u-.093,u+.093,z-.019,z+.019,.235,-.055,face,IRON,name+f' wall collar {n+1}')

def return_wall(b,layout,side):
    points=np.asarray(layout[side+'_return'],float);a,c=points;vec=c-a;distance=np.linalg.norm(vec);vec/=distance
    if side=='west':a,c=c.copy(),a.copy();vec=-vec
    normal=np.array([vec[1],-vec[0]])
    def face(s,z,d):
        q=a+s*vec+d*normal;return q[0],q[1],z
    top=layout['bay_wall_top']
    panel=box(0,0,distance,top)
    if side=='west':
        # The third original horizontal light goes beyond the southern paving cut.
        # The return continues to the complete jamb observed independently from the bridge.
        openings=layout['west_return_windows']
        holes=[box(distance-o['d1'],o['z0'],distance-o['d0'],o['z1']) for o in openings]
        panel=panel.difference(unary_union(holes))
        for o in openings:
            widthwise(b,distance-o['d1']-.018,distance-o['d0']+.018,o['z0']-.064,o['z0']-.002,
                      .044,.19,face,LIP,'West return '+o['key']+' sill')
    slab(b,panel,.0,.36,face,RETURN,side+' exposed return to terrace limit')
    widthwise(b,0,distance,top-.077,top+.010,.019,.388,face,LIP,side+' return coping')
    # Broad construction joints are readable in the blank eastern wall in the oblique finished photograph.
    if side=='east':
        for i,h in enumerate((4.07,8.27,12.43)):
            widthwise(b,.04,distance-.04,h,h+.019,.008,-.001,face,JOINT,side+f' gable horizontal joint {i+1}')

def add_wings(b,lod,layout):
    bays=layout['bays'];all_openings=layout['openings']
    for g in bays:
        side_bay(b,lod,g,[o for o in all_openings if o['bay']==g['bay']],layout)
    for unit in (bays[:5],bays[5:]):
        for left,right in zip(unit,unit[1:]):
            x=right['x0'];la=next(o for o in all_openings if o['bay']==left['bay'] and o['level']==4)
            ra=next(o for o in all_openings if o['bay']==right['bay'] and o['level']==4)
            usable=min(x-la['x1'],ra['x0']-x)
            face=face_at(right);name=left['bay']+' '+right['bay']
            major_pier(b,lod,name,usable*.84,layout['pier_peak_top'],layout['pier_shoulder_top'],face,x)
            rain_pipe(b,lod,name,x+usable*.77,face,layout['bay_wall_top'])
    # Both terminal piers are visible above the roof line, with a plainer cap at each outer return.
    for g,sign in ((bays[0],1),(bays[-1],-1)):
        end=g['x0'] if sign==1 else g['x1'];face=face_at(g)
        major_pier(b,lod,g['bay']+' end',.42,layout['pier_peak_top']-.09,layout['pier_shoulder_top'],face,end+sign*.43)
    for side in ('west','east'):
        return_wall(b,layout,side)
