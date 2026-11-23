"""Roof and enclosure behind the two photographed gables, in the gate's local frame."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
import lane310 as gate
from roof_rows import PEAK, TILE, tile_quad, wall_segment
from street314 import BASE, BROWN, CAP, GREY, RED, STONE, TIMBER

SURVEY=json.loads((Path(__file__).with_name('roof-survey.json')).read_bytes())['row_310']

def roof_wings(b,lod):
    # Follow both observed gable axes out of the street photograph. The 2025 light
    # line constrains a break on the west half, but does not establish a roof height.
    y_front=gate.REAR+.14
    far_left,far_right=map(np.asarray,[SURVEY['rear_west_local'],SURVEY['rear_east_local']])
    front_width=[-6.45,-3.94,-1.29,1.38,4.03,6.32]
    far_fraction=[0,.186,.39,.62,.81,1.]
    finish=[far_left+(far_right-far_left)*f for f in far_fraction]
    breaks=[(y_front,[7.87,9.18,7.79,7.77,9.14,7.81]),
            (SURVEY['intermediate_transverse_break_y'],[7.70,8.94,7.58,7.68,9.04,7.77]),
            (19.5,[7.48,8.82,7.52,7.55,8.92,7.57]),
            (float(far_left[1]),[7.39,8.72,7.40,7.45,8.70,7.43])]
    rows=[]
    for y,heights in breaks:
        t=(y-y_front)/(far_left[1]-y_front)
        rows.append([list((1-t)*np.array([x,y_front])+t*f)+[h]
                     for x,f,h in zip(front_width,finish,heights)])
    # Leave the central front open for its separate, shorter roof over the mullioned band.
    for j,(front,back) in enumerate(zip(rows,rows[1:])):
        for i in [0,1,3,4]:
            tile_quad(b,[front[i],front[i+1],back[i+1],back[i]],TILE,f'310 rear roof wing {i+1} course {j+1}')
        for side,p,q in [('west',back[0],front[0]),('east',front[-1],back[-1])]:
            wall_segment(b,p[:2],q[:2],0,[p[2]-.092,q[2]-.092],RED,'310 '+side+' flank')
    for i,label in [(1,'west'),(4,'east')]:
        b.tube([row[i] for row in rows],.063,PEAK,8 if lod else 12,'310 '+label+' longitudinal ridge')
    # Match the actual back end of the photographed short roof. The saddle falls
    # to the inside eaves, then meets the two wings at their real common edges.
    base=gate.roof_corners()
    h=(base[2][2]+base[3][2])/2
    back_y=base[2][1]
    t=(back_y-y_front)/(rows[1][2][1]-y_front)
    start=[]
    for idx in [2,3]:
        a,c=map(np.asarray,[rows[0][idx],rows[1][idx]])
        p=list(a*(1-t)+c*t)
        start.append(p)
    shoulder=[list(base[3].copy()),list(base[2].copy())]
    for p in shoulder:p[2]=h
    # On the photograph the upper end flares beyond the clear opening. Offset
    # its transition inside the two tile-covered wings to preserve that outline.
    transition=[start[0],start[1]]
    for p in transition:p[1]+=.58
    tile_quad(b,[shoulder[0],shoulder[1],transition[1],transition[0]],TILE,'310 central saddle behind short roof')
    cross_sections=[transition]+[[r[2],r[3]] for r in rows[1:]]
    for j,(a,c) in enumerate(zip(cross_sections,cross_sections[1:])):
        tile_quad(b,[a[0],a[1],c[1],c[0]],TILE,f'310 central tile field {j+1}')
    rear=rows[-1]
    for idx in reversed(range(5)):
        a,c=rear[idx+1],rear[idx]
        wall_segment(b,a[:2],c[:2],0,[a[2]-.092,c[2]-.092],RED,'310 rear wall below roof')
    # Inner cheeks fill only the area visible above the short central eave.
    # Their forward part is hidden by the photographed thick gable wall.
    for wing,idx,end in [('west',2,0),('east',3,1)]:
        edge=rows[0][idx]
        a=gate.roof_corners()[0 if idx==2 else 1]
        p=gate.roof_corners()[3 if idx==2 else 2]
        top=start[end][2]-.092
        # The sloping front cover rises past the level of the wing eave.
        t_edge=(top-a[2])/(p[2]-a[2])
        end_y=a[1]+t_edge*(p[1]-a[1])
        shape=Polygon([(y_front,a[2]-.065),(end_y,top),(y_front,edge[2]-.092)])
        x=edge[0]
        interior=-1 if idx==2 else 1
        lo,hi=sorted([x,x+interior*.12])
        b.prism(shape,lo,hi,lambda y,z,x:(x,y,z),RED,'310 '+wing+' internal roof cheek')
    base_outline=Polygon([rows[0][0][:2],rows[0][-1][:2],rear[-1][:2],rear[0][:2]]).buffer(-.12,join_style=2)
    b.plan_prism(base_outline,-.11,.012,CAP,'310 rear house floor')

def lower_walls(b,lod):
    front=gate.Front(b,lod)
    # The two photograph panels already contain their upper gable walls, and
    # the central entrance already contains its own solid low wall and doors.
    for tag,a,c in [('west',143,355),('east',529,727)]:
        x,z=gate.cut(a,240,gate.REAR)[[0,2]]
        x1,z1=gate.cut(c,240,gate.REAR)[[0,2]]
        f=Polygon([(x,0),(x1,0),(x1,z1),(x,z)])
        front.panel(f,gate.REAR+.012,.32,RED,tag+' lower housing behind street wall')

def entrance_sides(b,lod):
    # The lane narrows behind the red posts. The camera sees a small plastered
    # front and green vent at left, and a blank grey cheek to the right.
    w=gate.Front(b,lod)
    face_y=.73
    ochre='314 | terracotta patch'
    w.face([(298,342),(362,351),(366,552),(302,560)],face_y,.24,BASE,'little west lane wall')
    w.face([(300,343),(361,350),(362,380),(302,380)],face_y-.013,.028,ochre,'ochre wall above square vent')
    w.rect(318,384,351,408,face_y-.021,.023,gate.EAVE,'green glazed vent')
    w.rect(315,380,354,386,face_y-.053,.074,BROWN,'west small timber window head')
    for u in [321,327,333,339,345,350]:
        w.rim([(u,386),(u,407)],face_y-.038,.009,gate.CAST,'small vent upright')
    for v in [390,396,402]:
        w.rim([(318,v),(351,v)],face_y-.039,.008,gate.CAST,'small vent crossbar')
    w.rim([(298,337),(363,345)],face_y-.07,.079,BROWN,'small projecting dark drip')
    for name,u,v,far_u,far_v,top in [('west',365,550,399,478,2.10),('east',489,547,470,478,2.57)]:
        start=gate.cut(u,v,face_y)[:2]
        end=gate.cut(far_u,far_v,gate.REAR-.25)[:2]
        # Wall thickness always away from the passage's visible face.
        if name=='west':p,q=start,end
        else:p,q=end,start
        wall_segment(b,p,q,.025,[top,top],BASE,'310 '+name+' passage side')
    # Right-hand roof edge stood immediately behind the grey noticeboard wall.
    # It is recorded as a shallow weather roof with its ribbed edge and a drip.
    low=[gate.cut(587,266,.18),gate.cut(839,260,.18)]
    high=[gate.cut(587,246,1.82),gate.cut(839,237,1.82)]
    tile_quad(b,[low[0],low[1],high[1],high[0]],GREY,'310 corrugated roof behind east wall')
    n=16 if lod else 37
    for i in range(n+1):
        t=i/n
        p=(1-t)*low[0]+t*low[1];q=(1-t)*high[0]+t*high[1]
        b.tube([p.tolist(),q.tolist()],.027,GREY,5 if lod else 7,'310 foreground corrugation')
    b.tube([p.tolist() for p in low],.041,CAP,7 if lod else 10,'310 foreground rain edge')
    wall_segment(b,high[0][:2],low[0][:2],.0,[high[0][2]-.092,low[0][2]-.092],BASE,'310 east lean-to passage flank')
    wall_segment(b,low[1][:2],high[1][:2],.0,[low[1][2]-.092,high[1][2]-.092],BASE,'310 east lean-to far flank')
    wall_segment(b,high[1][:2],high[0][:2],.0,[high[1][2]-.092,high[0][2]-.092],BASE,'310 east lean-to back')
    # Across the lane the small tiled gable is set back just behind the post.
    # Its rectangular plan is only represented for the depth visible behind the roof edge.
    x=-1.42
    profile=[]
    for u,v in [(278,184),(340,139),(369,218)]:
        ray=gate.M@np.array([u,v,1.])
        profile.append(gate.EYE+ray*((x-gate.EYE[0])/ray[0]))
    far=[p+[-3.05,.08,-.05] for p in profile]
    for k in range(2):
        tile_quad(b,[profile[k],profile[k+1],far[k+1],far[k]],TILE,'310 small west tiled gable plane')
    shell=Polygon([(p[1],p[2]-.09) for p in profile]+[(profile[-1][1],2.2),(profile[0][1],2.2)])
    b.prism(shell,x-.15,x-.008,lambda y,z,x:(x,y,z),ochre,'310 small west gable wall')
    wall_segment(b,far[0][:2],profile[0][:2],0,[far[0][2]-.092,profile[0][2]-.092],ochre,'310 west annex street wall')
    wall_segment(b,profile[-1][:2],far[-1][:2],0,[profile[-1][2]-.092,far[-1][2]-.092],BASE,'310 west annex rear')
    for i in [0,1]:
        a,c=far[i+1],far[i]
        wall_segment(b,a[:2],c[:2],0,[a[2]-.092,c[2]-.092],BASE,'310 west annex outside flank')
    wall_segment(b,profile[0][:2],profile[-1][:2],0,[2.20,2.20],BASE,'310 small west gable lower wall')
    b.tube([p.tolist()for p in profile],.047,STONE,7 if lod else 12,'310 small west gable coping')
    b.tube([profile[1].tolist(),far[1].tolist()],.052,PEAK,7 if lod else 10,'310 small west gable ridge')
    # Thin paving follows the photographed ground between the inner door and
    # both piers. Its side boundaries sit below their plastered passage walls.
    landing=Polygon([(-1.39,-.25),(1.39,-.25),(1.22,face_y+.2),(.85,gate.REAR+.17),
                     (-.91,gate.REAR+.17),(-1.23,face_y+.2)])
    b.plan_prism(landing,-.085,-.002,CAP,'310 gateway paving')
    w.face([(489,311),(533,314),(533,555),(490,548)],face_y+.02,.17,BASE,'east wall behind the gatepost')
    w.face([(489,517),(533,520),(533,555),(490,548)],face_y+.004,.18,BROWN,'east passage wall foot')

def add_housing(b,lod):
    roof_wings(b,lod)
    lower_walls(b,lod)
    entrance_sides(b,lod)
