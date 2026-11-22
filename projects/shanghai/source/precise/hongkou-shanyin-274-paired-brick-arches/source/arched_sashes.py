"""Two photographed upper arched sashes and their red brick jambs in Lane 274, Shanyin Road."""
from math import pi, sin, cos, sqrt


def finish(rgb, metallic=0, rough=.85):
    return {'color':[((c/255+.055)/1.055)**2.4 for c in rgb], 'metallic': metallic, 'roughness':rough}


PALETTE={'grey joint':finish((147,139,125)), 'old grey brick':finish((151,143,122)),
         'brick shade':finish((134,128,112)), 'red brick':finish((159,92,66)),
         'light facing brick':finish((179,106,76)), 'dark facing brick':finish((147,77,56)),
         'red timber':finish((132,59,43)), 'frame highlight':finish((150,70,52)),
         'glass':finish((91,112,120),.15,.40),'pale stone sill':finish((181,175,155))}
SPRING=1.507
CENTRES=(-.698,.698)
RADIUS=.503


def box(b,l,r,front,back,low,high,mat,label):
    b.box(((l+r)/2,(front+back)/2,(low+high)/2),(r-l,back-front,high-low),mat,label=label)


def plate(b,vertices,front,back,mat,label):
    n=len(vertices);pts=[(x,y,z)for y in(front,back)for x,z in vertices]
    faces=[(0,i,i+1)for i in range(1,n-1)]+[(n,n+i+1,n+i)for i in range(1,n-1)]
    faces.extend((i,i+n,(i+1)%n+n,(i+1)%n)for i in range(n))
    b.add(pts,faces,mat,label)


def arc(b,x,r1,r2,front,back,a0,a1,div,mat,label):
    pts=[]
    for i in range(div+1):
        a=a0+(a1-a0)*i/div
        for rr,y in [(r1,front),(r2,front),(r2,back),(r1,back)]:
            pts.append((x+rr*cos(a),y,SPRING+rr*sin(a)))
    faces=[(0,3,2,1),(4*div,4*div+1,4*div+2,4*div+3)]
    for k in range(div):
        for j in range(4):faces.append((4*k+j,4*k+(j+1)%4,4*k+(j+1)%4+4,4*k+j+4))
    b.add(pts,faces,mat,label)


def spandrel_bricks(b, cx, side, lod):
    # Clip each end of a flat-laid grey brick at the red arch extrados.
    # The narrow grey wall above and to either side remains in running bond.
    height=.061
    length=.205
    for course in range(14):
        bottom=SPRING+height*course+.002
        if bottom>=2.294:break
        top=min(2.294,bottom+height-.004)
        shift=length/2 if course%2 else 0
        for brick in range(-5,5):
            low=max(-.698,brick*length+shift+.0015)
            high=min(.698,(brick+1)*length+shift-.0015)
            if low>=high:continue
            for wing in (-1,1):
                def limits(z):
                    rel=z-SPRING
                    offset=sqrt(max(0,.661**2-rel**2)) if rel<.661 else 0
                    return (max(low,offset),high)if wing==1 else (low,min(high,-offset))
                lower_left,lower_right=limits(bottom)
                upper_left,upper_right=limits(top)
                if lower_left>=lower_right or upper_left>=upper_right:continue
                outline=[(cx+lower_left,bottom),(cx+lower_right,bottom),
                         (cx+upper_right,top),(cx+upper_left,top)]
                color='brick shade' if (brick*3+course)%5==0 else 'old grey brick'
                plate(b,outline,.005,.017,color,side+' grey course '+str(course+1))


def add_building(b,lod=False):
    detail=18 if lod else 52
    bounds=[(-1.41,-1.201),(-.195,.195),(1.201,1.41)]
    for i,(l,r) in enumerate(bounds):
        box(b,l,r,.012,.292,0,SPRING,'grey joint',f'masonry pier {i+1}')
    for which,x in enumerate(CENTRES):
        side='left' if which==0 else 'right'
        # Wall above the curved aperture, following its inner radius all around.
        for k in range(detail):
            t0=pi*k/detail;t1=pi*(k+1)/detail
            l=x+RADIUS*cos(t1);r=x+RADIUS*cos(t0)
            p=[(l,SPRING+RADIUS*sin(t1)),(r,SPRING+RADIUS*sin(t0)),(r,2.294),(l,2.294)]
            plate(b,p,.011,.292,'grey joint',side+' upper arch wall')
        for x0,x1 in [(x-.698,x-RADIUS),(x+RADIUS,x+.698)]:
            box(b,x0,x1,.012,.292,SPRING,2.294,'grey joint',side+' outer spandrel')
        spandrel_bricks(b,x,side,lod)
        # Radial mortar is a solid backing, front red voussoirs separated by genuine joints.
        arc(b,x,.501,.662,-.018,.225,0,pi,detail,'grey joint',side+' mortar bed behind arch')
        for j in range(23):
            a0=pi*j/23+.0038;a1=pi*(j+1)/23-.0038
            mat=('red brick','light facing brick','red brick','dark facing brick')[j%4]
            arc(b,x,.501,.662,-.032,.212,a0,a1,2 if lod else 4,mat,side+f' arch brick {j+1:02d}')
        for sign in (-1,1):
            l=x+sign*.501;r=x+sign*.662;l,r=min(l,r),max(l,r)
            for j in range(19):
                mat=('red brick','red brick','light facing brick','dark facing brick')[(j+which)%4]
                depth=-.034 if j not in (0,17)else -.047
                box(b,l,r,depth,.214,.108+j*.0739,.108+(j+1)*.0739-.005,mat,side+f' jamb {sign} course {j+1:02d}')
            box(b,l-.013,r+.013,-.065,.22,SPRING-.038,SPRING+.018,'light facing brick',side+f' impost at {sign}')
        # Continuous glass sits behind the wood, including the half-round upper light.
        box(b,x-.502,x+.502,.120,.133,.14,SPRING,'glass',side+' lower glass')
        pts=[(x+RADIUS*cos(pi*i/detail),SPRING+RADIUS*sin(pi*i/detail))for i in range(detail+1)]
        plate(b,pts,.12,.133,'glass',side+' semicircular upper glass')
        arc(b,x,.466,.501,.069,.126,0,pi,detail,'red timber',side+' curved wood frame')
        box(b,x-.5,x+.5,.065,.133,SPRING-.029,SPRING+.026,'red timber',side+' upper sash transom')
        for u in (-.477,-.248,0,.248,.477):
            half=.024 if abs(u)>.46 or u==0 else .014
            box(b,x+u-half,x+u+half,.068,.125,.154,SPRING,'red timber',side+f' upright {u}')
        for z in (.151,.276,.86):
            thick=.042 if z<.3 else .016
            box(b,x-.5,x+.5,.066,.125,z,z+thick,'frame highlight',side+f' horizontal rail {z}')
        for u in (-.246,.246):
            box(b,x+u-.211,x+u+.211,.080,.122,.191,.273,'red timber',side+' lower panel between rails')
        for u in (-.245,0,.245):
            h=(.469**2-u**2)**.5
            box(b,x+u-.012,x+u+.012,.09,.122,SPRING+.02,SPRING+h,'red timber',side+f' upper-light glazing bar {u}')
        box(b,x-.535,x+.535,-.082,.195,.074,.122,'pale stone sill',side+' sill lip')
        box(b,x-.502,x+.502,.087,.208,0,.074,'old grey brick',side+' sill support')
