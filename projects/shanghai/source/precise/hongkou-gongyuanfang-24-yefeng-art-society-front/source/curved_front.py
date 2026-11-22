"""The two-storey brick bow below the elevated veranda, cut around the six recorded sashes."""
import numpy as np
from shapely.geometry import Polygon

from bay_windows import opening_profiles
from frontage_coordinates import CUT_BOTTOM, CX, CY, SILL_RADIUS, WALL_RADIUS, STUDY, bay_y, facade_point
from gable_face import CAST, STONE, IVORY, GREY
from material_names import DARK, RED

LEFT=.041
RIGHT=3.48
TOP=1.43


def slab(b,x0,x1,z0,z1,r0,r1,mat,label):
    if z1-z0<1e-5 or x1-x0<1e-5:return
    shape=Polygon([(x0,bay_y(x0,r0)),(x1,bay_y(x1,r0)),(x1,bay_y(x1,r1)),(x0,bay_y(x0,r1))])
    b.plan_prism(shape,z0,z1,mat,label)


def ring(b,left,right,step,low,high,outer,inner,material,name):
    axis=np.linspace(left,right,max(2,int(np.ceil((right-left)/step))+1))
    for l,r in zip(axis,axis[1:]):
        slab(b,l,r,low,high,outer,inner,material,name)


def add_wall(b,lod=False):
    holes=list(opening_profiles().values())
    low_sill=float(np.median([p['bottom_z']for p in holes if p['storey']=='lower']))
    # At the two right-hand windows the oblique reveals need a 10 mm allowance beyond the outer frame.
    cuts=[{**h,'left_x':h['left_x']-(.010 if h['id'] in ('upper-right','lower-right') else 0.)}for h in holes]
    step=.26 if lod else .145
    axis=sorted({LEFT,RIGHT,*[p[z]for p in cuts for z in ('left_x','right_x')],*np.linspace(LEFT,RIGHT,1+int((RIGHT-LEFT)/step))})
    for left,right in zip(axis,axis[1:]):
        mid=(left+right)/2
        clipped=sorted((p['bottom_z'],p['top_z'])for p in cuts if p['left_x']<mid<p['right_x'])
        foot=CUT_BOTTOM
        for low,high in [*clipped,(TOP,TOP)]:
            if low>foot:
                # The weathering is especially visible between the two levels.
                breaks=[foot]+[z for z in [low_sill,-1.73,-.56] if foot+.025<z<low-.025]+[low]
                for lo,hi in zip(breaks,breaks[1:]):
                    material=GREY if (lo+hi)/2 < low_sill else DARK if -1.73<(lo+hi)/2<-.56 else RED
                    slab(b,left,right,lo,hi,WALL_RADIUS,WALL_RADIUS-.28,material,'Curved bay | brick wall and reveals')
            foot=max(foot,high)
    # Raking horizontal stone joints are continuous over the three planar window openings.
    z=STUDY['curved_sill']['height']
    ring(b,LEFT,RIGHT,step,z-.137,z-.099,SILL_RADIUS-.024,WALL_RADIUS-.085,CAST,'Curved bay | underside of sill')
    ring(b,LEFT,RIGHT,step,z-.099,z+.025,SILL_RADIUS,WALL_RADIUS-.08,STONE,'Curved bay | pale sill ribbon')
    for p in holes:
        l,r=p['left_x'],p['right_x']
        lo=p['top_z']+.002
        wedge=.145 if p['storey']=='lower' else .12
        # Individual light cement blocks over the heads are visible even in the dark upper windows.
        ring(b,l-.035,r+.035,step,lo,lo+wedge,WALL_RADIUS+.020,WALL_RADIUS-.07,CAST,'Curved bay | lintel bedding')
        for j in range(5 if p['storey']=='upper' else 3):
            n=5 if p['storey']=='upper' else 3
            a=l-.03+(r-l+.06)*j/n+.003;c=l-.03+(r-l+.06)*(j+1)/n-.003
            slab(b,a,c,lo+.008,lo+wedge-.008,WALL_RADIUS+.036,WALL_RADIUS-.008,STONE,'Curved bay | jointed pale window lintels')
    # The 2022 photograph shows a continuous pale stone sill immediately below all three lower windows.
    ring(b,LEFT,RIGHT,step,low_sill-.176,low_sill-.135,SILL_RADIUS-.025,WALL_RADIUS-.085,CAST,'Curved bay | underside of lower window sill')
    ring(b,LEFT,RIGHT,step,low_sill-.135,low_sill+.004,SILL_RADIUS,WALL_RADIUS-.085,STONE,'Curved bay | curved lower sill')
    # Short return under the right end wall. It is distinct from the next residential bay.
    y=bay_y(RIGHT)
    poly=Polygon([(RIGHT,y),(3.88,y+.14),(3.88,1.19),(RIGHT,1.19)])
    b.plan_prism(poly,low_sill,TOP,RED,'Curved bay | right cut return')
    b.plan_prism(poly,CUT_BOTTOM,low_sill,GREY,'Curved bay | rendered lower right return')

    # A portion of an ivory-painted rainwater pipe survives at the right border of photograph 6.
    path=[]
    for u,v in [(545,706),(541,708),(540,713),(541.2,722),(547,746),(554.5,778),(558,794),(563,820),(564.5,824)]:
        q=facade_point(u,v,.137)
        if q[2]<CUT_BOTTOM:
            last=path[-1];t=(CUT_BOTTOM-last[2])/(q[2]-last[2]);q=last+(q-last)*t
        path.append(q)
    b.tube(path,.047,IVORY,10 if lod else 16,'Curved bay | adjoining pale drainpipe')
    middle=path[3]
    b.tube([middle+[0,0,-.026],middle+[0,0,.026]],.053,IVORY,10 if lod else 16,'Curved bay | pipe collar')
