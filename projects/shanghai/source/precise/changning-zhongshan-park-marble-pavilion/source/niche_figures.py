"""Sculpt the two observed draped silhouettes from separate measured sections."""
import json,math
from pathlib import Path
import numpy as np

DATA=Path(__file__).resolve().parent.parent/'measurements/statue-sections.json'

def add_figures(b,params,lod,stone):
    book=json.loads(DATA.read_bytes())
    for side,x in [('left',-params['niche_x']),('right',params['niche_x'])]:
        d=book[side];table=d['body']
        foot,top=d['foot_px'],d['head_px'];sc=(params['arch_z']-params['sill_z'])*.791/(foot-top)
        # The two concave niches have separate sculpture planes and arm poses.
        ns=12 if lod else 24;base=params['sill_z']+.104;y=params['screen_y']+.24
        center=d['center_px']
        def pos(u,row,depth):return [x+(u-center)*sc,y+depth,base+(foot-row)*sc]
        def loft(rows,name,gather=False):
            verts=[]
            for row,left,right,depth,offset in rows:
                mid=(left+right)/2;radius=(right-left)*.5*sc
                for k in range(ns):
                    t=k*2*math.pi/ns
                    ripple=1.
                    if gather and row>195:
                        ripple+=.064*math.cos(7*t+.91*(row-foot)/140)
                    v=pos(mid,row,offset)
                    verts.append([v[0]+radius*math.cos(t)*ripple,v[1]+depth*sc*math.sin(t)*ripple,v[2]])
            faces=[tuple(reversed(range(ns))),tuple(range((len(rows)-1)*ns,len(rows)*ns))]
            for i in range(len(rows)-1):
                for j in range(ns):
                    a=i*ns+j;q=i*ns+(j+1)%ns;faces.append((a,q,q+ns,a+ns))
            b.add(verts,faces,stone,side+' sculpture / '+name)
        b.box([x,y,params['sill_z']+.052],[.56,.40,.104],stone,label=side+' sculpture / rectangular foot plinth')
        loft(table if not lod else [v for i,v in enumerate(table)if i%2==0 or i==len(table)-1], 'head shoulders and draped body',True)
        for key in ['lowered_arm','crossed_arm']:
            pts=[pos(u,row,dep*sc)for u,row,dep in d[key]]
            b.tube(pts,sc*d['arm_radius_px'],stone,8 if lod else 14,side+' sculpture / '+key.replace('_',' '))
        # Two raised ridges follow opposite diagonals of each observed skirt.
        if not lod:
            for j,line in enumerate(d['drape_folds']):
                b.tube([pos(u,row,dep*sc)for u,row,dep in line],sc*2.5,stone,8,
                       side+f' sculpture / forward drapery fold {j+1}')
