"""The part of the 2018 boundary wall in front of the two sash and south porch."""
import json
from pathlib import Path
import numpy as np
from west_photo_plane import on_wall
from west_upper_windows import paint
from south_loggia import solid_box

DATA=json.loads((Path(__file__).resolve().parents[1]/'measurements/court-wall-2018.json').read_bytes())
PANEL='Shaanxi darker mineral boundary panel'
PIER='Shaanxi grey coursed gate piers'
BELT='Shaanxi pale grey boundary bands'
GROUT='Shaanxi recessed pier joints'
IRON='Shaanxi blackened boundary iron'
DIFFUSER='Shaanxi misted glass pier lanterns'
PALETTE={PANEL:paint((103,101,97),.93),PIER:paint((129,127,121),.89),BELT:paint((157,152,140),.91),GROUT:paint((105,102,96),.96),
         IRON:paint((56,54,49),.62,.17),DIFFUSER:paint((167,169,160),.46,.07)}

def add_boundary(b,lod):
    y=DATA['front_y_m']
    def x(u,v=1760.):return on_wall(u,v,y)[0]
    def z(v,u=1800.):return on_wall(u,v,y)[2]
    l,r=[x(u) for u in DATA['run_px']]
    top=np.mean([on_wall(u,v,y)[2] for u,v in DATA['wall_top_sample']])
    band=np.mean([on_wall(u,v,y)[2] for u,v in DATA['wall_belt_sample']])
    spaces=[];start=l
    for i,p in enumerate(DATA['piers'],1):
        u=p['centre'];left,right=[x(k,p['shoulder'])for k in p['body']]
        spaces.append((start,left+.012));start=right-.012
        shoulder=z(p['shoulder'],u)
        solid_box(b,left+.006,right-.006,y+.005,y+.36,0,shoulder,GROUT,f'Courtyard pier {i} joint core')
        courses=max(1,round(shoulder/.202))
        for j in range(courses):
            solid_box(b,left,right,y,y+.37,shoulder*j/courses+.003,shoulder*(j+1)/courses-.003,PIER,f'Courtyard pier {i} course {j+1:02}')
        cap_left,cap_right=[x(k,p['lamp_bottom'])for k in p['cap']];stem=z(p['lamp_bottom'],u)
        solid_box(b,cap_left,cap_right,y+.026,y+.344,shoulder-.005,stem,PIER,f'Courtyard pier {i} raised shoulder')
        lamp_x=x(u,p['lamp_bottom']);lamp_y=y+.155;radius=(x(p['lamp'][1])-x(p['lamp'][0]))/2
        roof=z(p['lamp_top'],u)
        b.tube([(lamp_x,lamp_y,stem),(lamp_x,lamp_y,stem+.049)],radius*1.05,IRON,sides=12,label=f'Boundary lamp {i} foot')
        b.tube([(lamp_x,lamp_y,stem+.041),(lamp_x,lamp_y,roof-.023)],radius*.90,DIFFUSER,sides=8,label=f'Boundary lamp {i} frosted lights')
        for k in range(8):
            angle=np.pi*k/4
            cx=lamp_x+np.sin(angle)*radius*.91;cy=lamp_y-np.cos(angle)*radius*.91
            b.tube([(cx,cy,stem+.043),(cx,cy,roof-.014)],radius*.095,IRON,sides=5 if lod else 8,label=f'Boundary lamp {i} upright {k+1}')
        b.tube([(lamp_x,lamp_y,roof-.028),(lamp_x,lamp_y,roof)],radius*1.02,IRON,sides=12,label=f'Boundary lamp {i} top lip')
    spaces.append((start,r))
    for k,(a,c) in enumerate(spaces,1):
        solid_box(b,a,c,y+.062,y+.292,0,top-.042,PANEL,f'Court wall {k} mineral panel')
        solid_box(b,a,c,y+.032,y+.312,top-.047,top,BELT,f'Court wall {k} coping')
        solid_box(b,a,c,y+.035,y+.30,band-.036,band+.037,BELT,f'Court wall {k} narrow band')
        count=max(1,round((c-a)/.138));pitch=(c-a)/count
        pos=[a+(i+.5)*pitch for i in range(count)]
        yy=y+.153;spike=z(np.mean(DATA['spike_tips_v']));rail=z(DATA['top_rail_v'])
        b.tube([(a,yy,rail),(c,yy,rail)],.010,IRON,sides=6,label=f'Courtyard screen {k} upper rail')
        for j,cx in enumerate(pos,1):
            # In the 2018 close view each fork divides above the rail.
            b.tube([(cx,yy,top),(cx,yy,rail),(cx+.033,yy,spike)],.009,IRON,sides=5 if lod else 7,label=f'Fence {k} fork {j:02} upright')
            b.tube([(cx,yy,rail),(cx-.035,yy,spike-.018)],.008,IRON,sides=5 if lod else 7,label=f'Fence {k} fork {j:02} tine')
        for j,(x0,x1) in enumerate(zip(pos,pos[1:]),1):
            ts=np.linspace(0,1,5 if lod else 9)
            upper=z(DATA['lower_scroll_v'][0]);dip=upper-z(DATA['lower_scroll_v'][1])
            path=[(x0+(x1-x0)*t,yy,upper-dip*np.sin(np.pi*t)) for t in ts]
            b.tube(path,.006,IRON,sides=5 if lod else 7,label=f'Fence {k} curved tie {j:02}')
