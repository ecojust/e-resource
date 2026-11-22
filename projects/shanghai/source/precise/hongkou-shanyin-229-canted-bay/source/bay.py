"""The two photographed upper bay-window faces at No. 1, Lane 229, Shanyin Road."""
from math import cos, pi, radians, sin, tan

from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def finish(rgb, roughness=.86, metallic=0):
    rgb = [v / 255 for v in rgb]
    return dict(color=[v / 12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb],
                roughness=roughness, metallic=metallic)


MORTAR = 'Bay | buff grey pointing'
BLUES = ['Bay | smoke brick', 'Bay | slate brick', 'Bay | brown grey brick']
REDS = ['Bay | red facing', 'Bay | muted red facing', 'Bay | warm rubbed red brick']
PAINT = 'Bay | vermilion casements'
DARK_RED = 'Bay | inner red glazing bead'
STONE = 'Bay | pale stone sill'
IRON = 'Bay | warm black iron'
GLASS = 'Bay | smoke blue glazing'
INNER = 'Bay | shaded room'
PALETTE = {MORTAR: finish((134,129,117)), PAINT: finish((157,43,24),.54),
           DARK_RED: finish((115,36,25),.56), STONE: finish((190,178,155)),
           IRON: finish((53,47,39),.58,.38), GLASS: finish((72,81,80),.26,.18),
           INNER: finish((45,43,35))}
PALETTE.update({k:finish(c) for k,c in zip(BLUES,[(98,99,93),(89,91,87),(108,105,93)])})
PALETTE.update({k:finish(c) for k,c in zip(REDS,[(163,83,47),(151,70,43),(177,93,54)])})


def survey_layout():
    return dict(height=3.2, left_width_ratio=.4675, center_width_ratio=.4690, turn_degrees=45.83)


def add_bay(b,lod=False,layout=None):
    """Append the pair of masonry faces around their shared corner at (0,0,0).

    Z=0 is the lower band datum. +X follows the central face to image right.
    Height is in display units and can be changed without changing the proportions.
    """
    dimensions = {**survey_layout(), **(layout or {})}
    h = dimensions['height']
    turn = radians(dimensions['turn_degrees'])
    far = lod is True or lod == 'lod'
    if h <= 0 or not 0 < turn < pi/2:
        raise ValueError('The display height and observed convex turn must be positive.')
    b.palette.update(PALETTE)

    def face(which, width_ratio, win_left, win_right, lower, transom, head, spring, crown, sill_span):
        left = which == 'oblique'
        w = width_ratio*h
        tx,ty = (cos(turn),-sin(turn)) if left else (1.,0.)
        ox,oy = (-w*tx,-w*ty) if left else (0.,0.)
        nx,ny = ty,-tx
        joint = tan(turn/2)
        def xyz(u,z,depth):
            return (ox+tx*u+nx*depth, oy+ty*u+ny*depth,z)

        def skin(shape,back,front,material,label):
            if shape.is_empty or shape.area <= 1.e-10:
                return
            b.prism(shape,back*h,front*h,xyz,material,which+' | '+label)

        def pane(u0,z0,u1,z1,back,front,material,label):
            skin(box(u0*w,z0*h,u1*w,z1*h),back,front,material,label)

        def path_xz(points,radius,material,label,sides=None):
            b.tube([xyz(u*w,z*h,d*h) for u,z,d in points],radius*h,material,
                   sides or (5 if far else 8),which+' | '+label)

        def ledge(z0,z1,back,front,material,label):
            # A true angle bisector at the common arris keeps both moulding runs mitred.
            p=[]
            for u,d in [(0,back),(w,back),(w,front),(0,front)]:
                if u==w and left:
                    u+=joint*d*h
                elif u==0 and not left:
                    u-=joint*d*h
                x,y,_=xyz(u,0,d*h)
                p.append((x,y))
            b.plan_prism(Polygon(p),h*z0,h*z1,material,which+' | '+label)

        aperture=box(win_left*w,lower*h,win_right*w,head*h)
        wall=box(0,0,w,h).difference(aperture)
        skin(wall,-.060,-.002,MORTAR,'reveal and backing masonry')
        # A shallow segmental brick arch sits above the rectangular transom.
        mid=(win_right+win_left)*.5
        def arch(t,outer):
            half=(win_right-win_left)*(.75 if outer else .5)
            return ((mid+half*t)*w,(spring+(crown-spring)*(1-t*t)+(.064 if outer else 0))*h)
        samples=14 if far else 32
        base=[arch(i*2/samples-1,False) for i in range(samples+1)]
        outside=[arch(i*2/samples-1,True) for i in range(samples+1)]
        arch_shape=Polygon(base+outside[::-1]).intersection(box(0,0,w,1.02*h))
        red_base=box(0,0,w,.104*h)
        full_field=wall.difference(arch_shape.union(red_base))
        if far:
            skin(full_field,-.002,.001,BLUES[0],'grey brick field')
        else:
            course=.0197*h
            length=.073*h
            row=0
            while row*course<h:
                z=row*course
                col=-1
                while col*length<w:
                    x=(col+(row%2)*.5)*length
                    brick=box(x+.003*h,z+.0017*h,x+length-.0015*h,min(z+course-.0011*h,h))
                    clipped=full_field.intersection(brick)
                    if clipped.area>1.e-7:
                        skin(clipped,-.0018,.0013,BLUES[(row*7+col*5+col//3)%3],
                             'stretcher %02d.%02d'%(row,col+2))
                    col+=1
                row+=1
        # The red band carries real stretcher joints across both faces.
        ledge(-.008,.104,-.064,-.001,REDS[1],'red base band')
        for row in range(5):
            for col in range(-1,9):
                x=(col+row%2*.5)*.075*h
                brick=box(x+.002*h,row*.0208*h+.0015*h,x+.074*h,(row+1)*.0208*h-.001*h)
                skin(red_base.intersection(brick),-.001,.002,REDS[(row+col)%3],'base stretcher')
        ledge(-.021,-.008,-.056,.016,REDS[0],'terracotta base arris')
        ledge(-.043,-.021,-.059,.026,REDS[2],'lower projecting fillet')
        for i in range(13):
            pane((i+.08)/13,-.063,(i+.67)/13,-.043,.002,.020,REDS[1],'cornice dentil')
        skin(arch_shape,-.001,.004,REDS[2],'arch bed')
        n=14 if far else 25
        for i in range(n):
            lo=-1+2*(i+.032)/n
            hi=-1+2*(i+.965)/n
            sector=Polygon([arch(lo,False),arch(hi,False),arch(hi,True),arch(lo,True)])
            skin(sector.intersection(box(0,0,w,1.02*h)),.0038,.007,REDS[(i*5)%3],'radial rubbed brick')
        for i in range(samples):
            a,bp=outside[i],outside[i+1]
            pts=Polygon([(a[0],a[1]),(bp[0],bp[1]),(bp[0],bp[1]+.012*h),(a[0],a[1]+.012*h)])
            skin(pts.intersection(box(0,0,w,1.025*h)),.005,.017,REDS[1],'raised arch label')
        # Multiple profiles are visible between the arch and the iron foot.
        for z0,z1,back,front,mat,name in [
            (1.,1.014,-.060,.015,REDS[1],'top fascia'),(1.014,1.032,-.060,.026,REDS[2],'lower roll'),
            (1.032,1.059,-.060,.020,REDS[0],'crowning red band'),(1.059,1.072,-.061,.032,REDS[2],'cornice tongue'),
            (1.072,1.112,-.061,.037,REDS[0],'projecting frieze'),(1.112,1.128,-.061,.046,REDS[1],'cornice drip'),
            (1.128,1.143,-.062,.047,IRON,'dark coping')]:
            ledge(z0,z1,back,front,mat,name)

        # Rectangular painted sash sits below the fan of brick, with a working open leaf on the left face.
        for u0,u1 in [(win_left,win_left+.023),(win_right-.023,win_right)]:
            pane(u0,lower,u1,head,-.031,.006,PAINT,'window jamb')
        for z in [lower,transom,head-.025]:
            pane(win_left,z,win_right,z+.025,-.031,.006,PAINT,'head sill or transom rail')
        pane(mid-.018,transom,mid+.018,head,-.02,.003,PAINT,'transom mullion')
        pane(win_left+.018,transom+.017,win_right-.018,head-.013,-.027,-.020,GLASS,'two transom lights')
        pane(win_left+.002,lower+.001,win_right-.002,transom-.003,-.061,-.059,INNER,'deep reveals')
        umin,umax=win_left+.022,win_right-.022
        for leaf,(hinge,end) in enumerate([(umin,mid),(umax,mid)]):
            opened=left and leaf==1
            # The free edge folds out past the right jamb in the 2015 photograph.
            angle=radians(119) if opened else 0
            def leafpoint(x,z,d):
                p=(end-hinge)*x
                return (hinge+p*cos(angle),z,d+abs(p)*w/h*sin(angle))
            def leafbar(xa,za,xb,zb,radius,name):
                points=[leafpoint(xa,za,-.009),leafpoint(xb,zb,-.009)]
                path_xz(points,radius,PAINT,name,4)
            bottom,top=lower+.016,transom-.004
            for xa,za,xb,zb in [(0,bottom,0,top),(1,bottom,1,top),(0,bottom,1,bottom),(0,top,1,top)]:
                leafbar(xa,za,xb,zb,.012,'opening sash stile or rail')
            for fraction in [1/3,2/3]:
                level=bottom+(top-bottom)*fraction
                leafbar(0,level,1,level,.006,'slender horizontal glazing bar')
            # Basis is along the opened leaf, the pane normal, and the true vertical.
            a=xyz(*[0,0,0]);pts=[]
            for x,z in [(0,bottom),(1,bottom),(1,top),(0,top)]:
                u,zz,dd=leafpoint(x,z,-.012)
                pts.append(xyz(u*w,zz*h,dd*h))
            import numpy as np
            ex=np.asarray(pts[1])-pts[0];width=np.linalg.norm(ex);ex/=width
            normal=np.cross([0.,0.,1.],ex)
            b.box(np.mean(pts,axis=0),(width,.003*h,(top-bottom)*h),GLASS,
                  (ex,normal,[0,0,1]),which+' | sash glass')

        l,r=sill_span
        pane(l,lower-.020,r,lower+.011,-.035,.037,STONE,'projecting pale sill')
        # Two short dropped ends flank three shallow curved lobes under the sill.
        al,ar=l+.070,r-.070
        end_z=lower-.133;seat_z=lower-.025
        curve=[(al*w,seat_z*h),(ar*w,seat_z*h),(ar*w,end_z*h),((ar-.07)*w,end_z*h)]
        for i in range(37):
            t=i/36
            x=ar-.07-(ar-al-.14)*t
            lift=.018*(1-cos(6*pi*t))*.5
            z=lower-.078+lift
            if t<.12:z-=.044*(1-t/.12)**2
            if t>.88:z-=.044*((t-.88)/.12)**2
            curve.append((x*w,z*h))
        curve.extend([((al+.07)*w,end_z*h),(al*w,end_z*h)])
        skin(Polygon(curve).buffer(0),.001,.022,REDS[2],'scalloped brick apron with end drops')

        start=.12 if left else 0
        stop=1. if left else .96
        step=(stop-start)/(9 if left else 10)
        zbase,ztop=1.148,1.42
        for u in [start,stop]:
            path_xz([(u,zbase,.003),(u,ztop,.003)],.0058,IRON,'iron post',6)
        for z in [zbase,ztop-.042,ztop]:
            path_xz([(start,z,.004),(stop,z,.004)],.0043 if z!=ztop else .0064,IRON,'iron horizontal rail',6)
        # Unequal flower heads, long sinuous stems and the opposed middle curls are visible at this scale.
        for j in range(9 if left else 10):
            u=start+(j+.55)*step
            def ironline(data,label,radius=.0026):
                path_xz([(u+x*step,zbase+(ztop-zbase)*y,.0065)for x,y in data],radius,IRON,label)
            def stem(t):
                return .20*sin(2*pi*t-.13*pi)-.035,t*.85
            ncurve=11 if far else 21
            ironline([stem(i/ncurve)for i in range(ncurve+1)],'undulating forged stem',.003)
            for side in [-1,1]:
                branch=[(.025,.39),(.14*side,.48),(.34*side,.51),(.43*side,.48),(.41*side,.445),(.34*side,.443)]
                ironline(branch,'opposed mid-height scroll',.0023)
                petal=[(0,.73),(.17*side,.77),(.20*side,.81),(.12*side,.844),(0,.856)]
                ironline(petal,'petal forging at the upper bar',.0022)
        return
    face('oblique',dimensions['left_width_ratio'],.165,.768,.322,.687,.846,.842,.91,(.066,.855))
    face('central',dimensions['center_width_ratio'],.201,.745,.309,.674,.842,.836,.906,(.116,.834))
