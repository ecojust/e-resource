"""Street-facing walls, lower sash, corbel ends and measured front roof slope."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box

from material_names import MATERIAL
from south_loggia import porch_openings,plate,solid_box
from west_upper_windows import openings,paint,FRAME,BAR,LIGHT,STONE
from west_photo_plane import on_wall

M=Path(__file__).resolve().parents[1]/'measurements'
SURVEY=json.loads((M/'house-fabric-and-roof.json').read_bytes())
GROUT='Shaanxi street wall pale pointing'
BRICKS=['Shaanxi surround russet brick','Shaanxi surround muted brick','Shaanxi surround burnt brick']
FASCIA='Shaanxi eaves dark painted timber'
LEAD='Shaanxi rainwater pipe'
FELT='Shaanxi tile bedding'
TILES=['Shaanxi curved clay tile warm','Shaanxi curved clay tile faded','Shaanxi curved clay tile plum']
PALETTE={GROUT:paint((167,150,131),.93),FASCIA:paint((69,62,55),.86),LEAD:paint((94,96,87),.72,.14),
         FELT:paint((97,78,71),.96),**{k:paint(v,.95) for k,v in zip(BRICKS,[(145,98,78),(132,89,74),(150,107,87)])},
         **{k:paint(v,.85) for k,v in zip(TILES,[(143,108,94),(156,125,115),(124,97,95)])}}

def ranges(row):
    return tuple(row[k] for k in ('left','right','bottom','top'))

def add_lower_light(b,row,label):
    left,right,bottom,top=ranges(row)
    ys=.115
    width=right-left
    exterior=.050
    solid_box(b,left,right,ys+.042,ys+.066,bottom,top,LIGHT,label+' shaded glass foot')
    for i in range(7):
        cx=left+width*i/6.
        thick=exterior if i%2==0 else .017
        a=max(left,cx-thick/2);c=min(right,cx+thick/2)
        solid_box(b,a,c,ys,ys+.049,bottom,top,FRAME if i%2==0 else BAR,label+f' stile {i+1}')
    for i,f in enumerate([0,.22,.54,.80,1.]):
        cz=bottom+(top-bottom)*f
        thick=.043 if i in (0,4) else .020
        solid_box(b,left,right,ys+.004,ys+.031,max(bottom,cz-thick/2),min(top,cz+thick/2),FRAME if i in (0,4) else BAR,label+f' rail {i+1}')
    solid_box(b,left-.045,right+.045,-.052,.14,bottom-.044,bottom+.002,STONE,label+' sill at visible lower edge')

def brick_surround(b,row,label):
    left,right,bottom,top=ranges(row)
    # Red soldier headers are individually visible over both floors. The jambs
    # alternate long and short ends against the pale sand finish.
    length=.139
    module=.065
    count=round((right-left+2*length)/module)
    solid_box(b,left-length,right+length,-.009,.010,top,top+.112,GROUT,label+' head mortar')
    for i in range(count):
        lo=left-length+(right-left+2*length)*i/count+.0025
        hi=left-length+(right-left+2*length)*(i+1)/count-.0025
        solid_box(b,lo,hi,-.022,-.006,top+.004,top+.110,BRICKS[(i*7+int(top*10))%3],label+f' soldier {i+1:02}')
    levels=round((top-bottom)/.064)
    for side,edge,sign in [('left',left,-1),('right',right,1)]:
        for i in range(levels):
            low=bottom+(top-bottom)*i/levels
            high=bottom+(top-bottom)*(i+1)/levels
            extension=.25 if i%3==1 else .105 if i%3==2 else .14
            a,c=sorted((edge,edge+sign*extension))
            solid_box(b,a,c,-.012,-.002,low,high,GROUT,label+f' {side} bed {i:02}')
            solid_box(b,a+.001,c-.001,-.023,-.009,low+.0028,high-.0028,BRICKS[(i+int(edge*8))%3],label+f' {side} brick {i:02}')

def roof(b,lod,x0,x1):
    values=SURVEY['envelope'];front=values['eaves_front_y_m'];back=values['represented_rear_y_m']
    low=float(np.mean(values['eaves_front_z_m']));high=float(np.mean(values['upper_z_m']))
    xmin=x0-.82;xmax=x1+.51
    def elevation(y):
        return low+(high-low)*(y-front)/(back-front)
    # End the section at the last measured strip of the slope. Both the
    # front and back faces below the curved tiles are closed editable solids.
    b.prism(Polygon([[front,low-.064],[back,high-.064],[back,high],[front,low]]),xmin,xmax,
            lambda y,z,x:(x,y,z),FELT,'Visible sloped roof bedding')
    solid_box(b,xmin,xmax,front,front+.112,low-.185,low-.008,FASCIA,'Street eaves fascia')
    solid_box(b,xmin,xmax,front+.097,.13,low-.179,low-.140,FASCIA,'Soffit behind the projecting eaves')
    for i,u in enumerate([857,1102,1365,1608,1878,2139,2396,2665,2924]):
        x=on_wall(u,900)[0]
        b.prism(Polygon([[-.475,low-.148],[.05,low-.148],[.05,low-.328],[-.36,low-.328]]),x-.053,x+.053,
                lambda y,z,x:(x,y,z),FASCIA,f'Exposed sawn rafter end {i+1:02}')
    count=round((xmax-xmin)/.188)
    rows=8
    step=(back-front)/rows
    finish=np.random.default_rng(19506).choice(len(TILES),size=(rows,count),p=[.45,.36,.19])
    for j in range(rows):
        y=front+j*step
        y1=min(back,y+step+.058)
        for i in range(count):
            left=xmin+i*(xmax-xmin)/count
            right=xmin+(i+1)*(xmax-xmin)/count
            samples=5 if lod else 9
            across=np.linspace(-1,1,samples)
            # A low, rounded barrel crest and the lower weathering lip of
            # each course catch different light in WQL's oblique photograph.
            curve=.056*np.maximum(0.,1.-across*across)**.85
            verts=[]
            for yy,lip in ((y,.018),(y1,0.)):
                for f,z in zip(across,curve):
                    xx=(left+right)*.5+f*(right-left)*.496
                    verts.extend([(xx,yy,elevation(yy)+lip+.005),(xx,yy,elevation(yy)+lip+.015+z)])
            n=2*samples;faces=[]
            for k in range(samples-1):
                a=2*k
                faces.extend([(a,a+2,a+2+n,a+n),(a+1,a+1+n,a+3+n,a+3),
                              (a,a+1,a+3,a+2),(a+n,a+2+n,a+3+n,a+1+n)])
            faces.extend([(0,n,n+1,1),(n-2,n-1,2*n-1,2*n-2)])
            # Each strip is oriented as a closed volume (upper face toward +Z).
            b.add(verts,[tuple(reversed(f)) for f in faces],TILES[finish[j,i]],f'Curved clay tile {j+1:02}-{i+1:02}')

def add_house(b,lod=False):
    obs=SURVEY['envelope'];left,right=obs['wall_ends_x_m'];top=np.mean(obs['eaves_front_z_m'])-.150
    all_windows=list(openings())+SURVEY['lower_windows']
    area=box(left,0,right,top)
    for row in all_windows:
        l,r,z,t=ranges(row);area=area.difference(box(l,z,r,t))
    for opening in porch_openings():area=area.difference(opening)
    plate(b,area,0.,.195,MATERIAL,'Sand rendered street wall with six openings')
    z=np.mean(obs['string_course_z_m'])
    solid_box(b,left,right,-.046,.025,z-.064,z-.018,STONE,'Street stringcourse narrow underside')
    solid_box(b,left,right,-.078,.025,z-.022,z+.021,STONE,'Street stringcourse weathered cap')
    for row,label in zip(SURVEY['lower_windows'],['North lower','South lower']):
        add_lower_light(b,row,label);brick_surround(b,row,label)
    for row,label in zip(openings(),['North upper','South upper']):brick_surround(b,row,label)
    # A limited solid return terminates at the street-side portion of the
    # north wall. The south return and both porch side openings have their
    # own surveyed cross-sections in south_loggia.
    solid_box(b,left,left+.186,.195,2.83,0,top,MATERIAL,'North wall at the eaves return')
    x=on_wall(965,1253)[0]
    b.tube([(x,-.12,.22),(x,-.12,z-.24),(x-.044,-.11,z-.16),(x-.044,-.11,top-.07)],.043,LEAD,sides=10 if lod else 16,label='North rainwater downpipe')
    for i,level in enumerate([1.24,3.86,5.30,6.82]):
        b.tube([(x,-.120,level-.024),(x,-.120,level+.024)],.051,LEAD,sides=8 if lod else 14,label=f'Downpipe collar {i+1}')
    roof(b,lod,left,right)
