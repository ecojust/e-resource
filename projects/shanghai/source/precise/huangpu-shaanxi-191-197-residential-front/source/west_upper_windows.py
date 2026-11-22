"""Editable upper lights and stone sills at the 2018 front of 195 Shaanxi Road South."""
from functools import lru_cache
import json
from pathlib import Path
from west_photo_plane import FRAME_SETBACK, on_wall

M=Path(__file__).resolve().parents[1]/'measurements'
FRAME="Shaanxi house dark upright frames"
BAR="Shaanxi house narrow painted glazing bars"
LIGHT="Shaanxi house shaded reflective glazing"
SKY="Shaanxi house cooler sky-reflecting glazing"
SEAL="Shaanxi house inset glazing beads"
STONE="Shaanxi house grey window ledge"

def paint(rgb,roughness,metallic=0.):
    c=[v/255. for v in rgb]
    return {'color':[k/12.92 if k<=.04045 else ((k+.055)/1.055)**2.4 for k in c],
            'roughness':roughness,'metallic':metallic}

PALETTE={FRAME:paint((44,44,41),.52,.13),BAR:paint((45,48,45),.45,.16),
         LIGHT:paint((64,76,68),.27,.32),SKY:paint((64,75,79),.24,.32),
         SEAL:paint((34,35,34),.55),STONE:paint((143,137,126),.84)}

@lru_cache(maxsize=1)
def openings():
    obs=json.loads((M/'west-upper-window-observations.json').read_bytes())['corners']['2018_commons']
    dims=json.loads((M/'upper-lights-2018.json').read_bytes())
    rows=[]
    for win in dims['windows']:
        k=win['key']
        p={s:on_wall(*obs[k+s],FRAME_SETBACK) for s in ('TL','TR','BL','BR')}
        l=(p['TL'][0]+p['BL'][0])/2;r=(p['TR'][0]+p['BR'][0])/2
        z0=(p['BL'][2]+p['BR'][2])/2;z1=(p['TL'][2]+p['TR'][2])/2
        uc=sum(obs[k+s][0] for s in p)/4;vc=sum(obs[k+s][1] for s in p)/4
        x=lambda u:on_wall(u,vc,FRAME_SETBACK)[0]
        z=lambda v:on_wall(uc,v,FRAME_SETBACK)[2]
        rows.append({'label':win['label'],'left':l,'right':r,'bottom':z0,'top':z1,
                     'primary':[x(u) for u in win['heavy_stile_u']],
                     'fine':[x(u) for u in win['slender_stile_u']],
                     'rails':sorted(z(v) for v in win['rail_v']),
                     'sill_x':[x(u) for u in win['sill_left_right_u']],
                     'sill_height':abs(z(win['sill_top_bottom_v'][0])-z(win['sill_top_bottom_v'][1]))})
    return tuple(rows)

def sections(row):
    l,r,z0,z1=(row[k] for k in ('left','right','bottom','top'))
    # Joining members share an edge. The glass stops at each rebate.
    return ([(l,l+.045,FRAME)]+sorted([(x-.023,x+.023,FRAME) for x in row['primary']]+
            [(x-.009,x+.009,BAR) for x in row['fine']])+[(r-.045,r,FRAME)],
            [(z0,z0+.033,FRAME)]+[(z-.009,z+.009,BAR) for z in row['rails']]+[(z1-.048,z1,FRAME)])

def ledge(builder,row):
    l,r=row['sill_x'];z=row['bottom'];h=row['sill_height']
    # Outside face, tiny lower arris, flat underside and canted weathering surface.
    yz=[(-.125,z-.006),(-.125,z-h+.009),(-.115,z-h),(.18,z-h),(.18,z+.005)]
    vs=[(x,y,high) for x in (l,r) for y,high in yz]
    count=len(yz)
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces += [(a,(a+1)%count,(a+1)%count+count,a+count) for a in range(count)]
    builder.add(vs,faces,STONE,row['label']+' | splayed sill with arris')

def add_windows(builder,lod):
    for row in openings():
        label=row['label'];l,r,z0,z1=(row[k] for k in ('left','right','bottom','top'))
        xsect,zsect=sections(row)
        def box(a,b,c,d,y,depth,mat,role):
            builder.box(((a+b)/2,y+depth/2,(c+d)/2),(b-a,depth,d-c),mat,label=label+' | '+role)
        for n,(a,b,material) in enumerate(xsect):
            fine=material==BAR
            box(a,b,z0,z1,FRAME_SETBACK+(.016 if fine else 0),.048 if fine else .069,material,f'vertical {n+1}')
        for col in range(len(xsect)-1):
            a,b=xsect[col][1],xsect[col+1][0]
            for n,(c,d,mat) in enumerate(zsect):
                box(a,b,c,d,FRAME_SETBACK+(.017 if mat==BAR else .001),.049 if mat==BAR else .067,mat,f'column {col+1} horizontal {n+1}')
            for n in range(len(zsect)-1):
                c,d=zsect[n][1],zsect[n+1][0]
                mat=SKY if n>=2 else LIGHT
                if lod=='full':
                    bead=.006;face=FRAME_SETBACK+.034
                    box(a,a+bead,c,d,face,.014,SEAL,f'light {col+1}/{n+1} left rebate')
                    box(b-bead,b,c,d,face,.014,SEAL,f'light {col+1}/{n+1} right rebate')
                    box(a+bead,b-bead,c,c+bead,face,.014,SEAL,f'light {col+1}/{n+1} lower rebate')
                    box(a+bead,b-bead,d-bead,d,face,.014,SEAL,f'light {col+1}/{n+1} upper rebate')
                    a1,b1,c1,d1=a+bead,b-bead,c+bead,d-bead
                else:a1,b1,c1,d1=a,b,c,d
                box(a1,b1,c1,d1,FRAME_SETBACK+.043,.010,mat,f'glazing {col+1}/{n+1}')
        ledge(builder,row)
