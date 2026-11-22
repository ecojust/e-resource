"""Check the iron strips, separate panes, brick joints and open tile profiles in the two meshes."""
import numpy as np
from iron_window import BASE,R,SPRING,APEX,top,inner,TILES,CLAY,WALL,SILL,IRON,GLASS,GLOW,SPANDREL,MORTAR
def test(tri,names,hit):
    rows=[]
    def shot(label,x,y,z,direction,material):
        q=hit(tri,names,np.array([x,y,z]),np.array(direction,float));assert q and q[0]==material,(label,x,y,z,material,q)
        rows.append(dict(label=label,material=q[0],point=q[1]))
    def front(x,z,material,label):shot(label,x,-1.42,z,(0,1,0),material)
    for x in (-.62,-.38,-.17,.17,.38,.62):
        for z in (1.71,2.015,2.36):front(x,z,GLOW,'Separated lower casement lights')
        for z in (2.68,2.81):front(x,z,GLASS,'Dark glass above horizontal iron rail')
        for z in (2.52,2.93):front(x,z,IRON,'Horizontal ironwork')
    for z in (1.62,1.90,2.31,2.76,3.08,3.40,3.72,3.98):front(0,z,IRON,'Central mullion')
    for s in (-1,1):
        for t in (.12,.27,.46,.63,.81,.95):
            x,z=inner(t,s);front(x,z,IRON,'Inclined curving iron glazing strip')
        for x in (.14,.25,.37,.49,.59,.68):
            front(s*x,top(x),IRON,'Curved metal border of pointed light')
        for z in (1.66,2.19,2.70,3.00,3.32,3.72,4.12):
            front(s*1.18,z,WALL,'Roughcast flank')
        for x,z in ((.755,3.92),(.546,4.204),(.280,4.23)):
            front(s*x,z,SPANDREL,'Recessed field surrounding the curls')
    for i in range(17):
        x=-.925+(i+.5)*(1.85/17);front(x,1.402,SILL,'Individual edge-set clay sill brick')
    for i in (3,6,9,12,15):
        x=-.925+i*1.85/17;front(x,1.397,MORTAR,'Recessed mortar joint between sill bricks')
    for x in TILES:
        for y in (-.98,-.63,-.31):shot('Crown of a barrel tile course',x,y,1.5,(0,0,-1),CLAY)
    for x in (TILES[:-1]+TILES[1:])/2:shot('Trough between adjacent tile caps',x,-.57,1.5,(0,0,-1),CLAY)
    return rows
