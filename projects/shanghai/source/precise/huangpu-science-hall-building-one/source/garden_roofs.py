"""Hipped pavilions, four dormers, bracketed eaves and garden clock pediment."""
import math
import numpy as np
from shapely.geometry import box, Polygon, Point, LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from garden import EAVE,BACK,FIELDS,TILE,CAP,CREAM,WOOD,CUT,DIAL,METAL,GLASS,PEBBLE,slab


def plate(b,points,mat,label,thick=.10):
    n=len(points);vertices=list(points)+[(x,y,z-thick)for x,y,z in points]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    b.add(vertices,faces,mat,label)


def surface(b,lower,upper,lod,label):
    """Each contour spans the same three visible roof faces up to the transverse cut."""
    for i in range(3):
        a,v=np.array(lower[i],float),np.array(lower[i+1],float)
        p,q=np.array(upper[i],float),np.array(upper[i+1],float)
        pts=[tuple(t)for j,t in enumerate([a,v,q,p])if j==0 or np.linalg.norm(t-[a,v,q,p][j-1])>.001]
        if len(pts)>2:plate(b,pts,TILE,label+' tile slope')
        levels=max(2,round(np.linalg.norm(a-p)/(.78 if lod else .42)))
        for k in range(1,levels):
            t=k/levels;c=a*(1-t)+p*t;d=v*(1-t)+q*t
            if np.linalg.norm(c-d)>.06:
                c[2]+=.021;d[2]+=.021
                b.tube([c,d],.031 if lod else .040,CAP,4 if lod else 6,label+' clay tile courses')
    for i in (1,2):
        b.tube([lower[i],upper[i]],.067,CAP,6 if lod else 9,label+' diagonal hip cap')


def contour(mid,half,front,z):
    return [(mid-half,BACK,z),(mid-half,front,z),(mid+half,front,z),(mid+half,BACK,z)]


def pediment(b,lod,mid,front,is_clock):
    # The cream attic stands in front of the tiles, following the curved shoulders.
    f=Facade(b,(mid-3.55,front),(mid+3.55,front),'clock pediment'if is_clock else'end attic oculus')
    if is_clock:
        base=12.22
        outline=Polygon([(-2.78,base),(2.78,base),(2.78,12.73),(2.44,12.81),(2.20,13.00),
            (2.07,13.34),(2.16,13.52),(2.27,13.57),(2.27,13.94),(2.17,14.03),(2.14,14.48),
            (2.33,14.63),(2.30,14.82),(2.12,14.94),(0,15.95),(-2.12,14.94),(-2.30,14.82),
            (-2.33,14.63),(-2.14,14.48),(-2.17,14.03),(-2.27,13.94),(-2.27,13.57),
            (-2.16,13.52),(-2.07,13.34),(-2.20,13.00),(-2.44,12.81),(-2.78,12.73)])
        f.prism(outline,-.225,.08,CREAM,'scroll shoulders and attic')
        for z,width,height in [(12.24,5.70,.13),(14.57,4.78,.12),(14.84,4.65,.095)]:
            f.prism(box(-width/2,z,width/2,z+height),.08,.25,CREAM,'horizontal pediment courses')
        roof=LineString([(-2.34,14.86),(0,16.00),(2.34,14.86)]).buffer(.105,cap_style=2,join_style=2)
        f.prism(roof,.074,.27,CREAM,'raking pediment cornice')
        for sign in (-1,1):
            triangle=Polygon([(sign*.40,15.01),(sign*1.68,15.01),(sign*.40,15.56)])
            f.prism(triangle,.082,.103,WOOD,'recessed triangle panel')
        cx,cz=0,13.65;radius=.75
        disk=Point(cx,cz).buffer(radius,quad_segs=12 if lod else 22)
        ring=disk.buffer(.12).difference(disk.buffer(-.025))
        f.prism(disk,.083,.15,DIAL,'clock dial')
        f.prism(ring,.143,.229,CREAM,'clock rim')
        for k in range(12):
            th=k*math.tau/12;v=np.array([math.sin(th),math.cos(th)]);t=np.array([cx,cz])
            tick=LineString([t+v*radius*.74,t+v*radius*.91]).buffer(.026,cap_style=2)
            f.prism(tick,.152,.175,METAL,'clock hour index')
        for dx,dz in [(-.38,.19),(-.034,.59)]:
            hand=LineString([(cx,cz),(cx+dx,cz+dz)]).buffer(.026,cap_style=2)
            f.prism(hand,.181,.206,METAL,'clock hand')
    else:
        base=11.68
        outline=Polygon([(-1.89,base),(1.89,base),(1.77,12.21),(1.44,12.36),(1.55,13.04),
                         (0,13.76),(-1.55,13.04),(-1.44,12.36),(-1.77,12.21)])
        hole=Point(0,12.71).buffer(.38,quad_segs=12)
        f.prism(outline.difference(hole),-.22,.045,CREAM,'end attic shaped surround')
        f.prism(hole,-.25,-.228,GLASS,'end attic circular vent')
        f.prism(hole.buffer(.08).difference(hole),.0,.118,CREAM,'oculus rim')
        f.prism(LineString([(-1.66,13.06),(0,13.84),(1.66,13.06)]).buffer(.08,cap_style=2),.034,.14,WOOD,'attic hood')


def add_roofs(b,lod):
    for left,right,kind in FIELDS:
        x=(left+right)/2;ext=(1.18 if kind=='inner'else .95)if kind!='range'else .03
        if kind=='range':
            front=6.84
            a=(left,front,EAVE-.14);v=(right,front,EAVE-.14)
            c=(right,BACK,13.69);d=(left,BACK,13.69)
            plate(b,[a,v,c,d],TILE,'straight tiled roof')
            slab(b,x,BACK-.03,EAVE-.02,right-left,.08,13.69-EAVE+.02,CUT,'rear cut above the continuous roof eaves')
            for z in np.arange(.05,1.,.13 if lod else .069):
                p=np.array(a)*(1-z)+np.array(d)*z;q=np.array(v)*(1-z)+np.array(c)*z
                p[2]+=.021;q[2]+=.021;b.tube([p,q],.036,CAP,4 if lod else 6,'straight roof tile courses')
            f=Facade(b,(x-1.1,8.35),(x+1.1,8.35),'shallow dormer')
            arch=Point(0,12.40).buffer(.59,quad_segs=10).intersection(box(-1,12,1,13.0))
            f.prism(arch,-.21,.06,WOOD,'curved dormer face')
            f.prism(box(-.59,11.79,.59,12.07),-.22,.04,WOOD,'dormer sill set into roof tiles')
            for sign in (-1,1):
                at=x+sign*.56
                cheek=[(at,8.35,11.82),(at,9.75,12.27),(at,9.70,12.77),(at,8.35,12.44)]
                b.add(cheek,[(0,1,2,3)],WOOD,'sloping dormer cheek')
            f.prism(arch.buffer(-.115),.060,.081,GLASS,'dormer light')
            pts=[(x-.75,8.17,12.45),(x,8.30,13.13),(x+.75,8.17,12.45),(x,9.72,12.87)]
            plate(b,[pts[0],pts[1],pts[3]],TILE,'dormer tiled hood')
            plate(b,[pts[1],pts[2],pts[3]],TILE,'dormer tiled hood')
        else:
            front=5.48;half=(right-left)/2+ext
            # The lower long ridge runs behind the raised pavilions. Its short
            # infill planes continue the adjacent range up to each dormer's hips.
            # Without them the valley below the higher hip would open to sky.
            under_left=max(left,-46.975);under_right=min(right,46.975)
            a=(under_left,6.84,11.36);v=(under_right,6.84,11.36)
            c=(under_right,BACK,13.69);d=(under_left,BACK,13.69)
            plate(b,[a,v,c,d],TILE,'continuous roof behind pavilion valleys')
            for fraction in np.arange(.05,1.,.13 if lod else .069):
                start=np.array(a)*(1-fraction)+np.array(d)*fraction
                end=np.array(v)*(1-fraction)+np.array(c)*fraction
                start[2]+=.021;end[2]+=.021
                b.tube([start,end],.036,CAP,4 if lod else 6,'tile rows at roof valley')
            slab(b,(under_left+under_right)/2,BACK-.032,EAVE-.02,under_right-under_left,.077,13.69-EAVE+.02,CUT,'rear section of lower long ridge')
            base=contour(x,half,front,EAVE)
            # The building behind the south ridge is left with its original city
            # geometry. At the cut, a plain face closes the roof profile.
            contours=[base]
            if kind in ('clock','end'):
                eaves=contour(x,half-.49,front+.62,EAVE+.28)
                knuckle=contour(x,half-1.02,front+1.30,EAVE+.92)
                high=contour(x,half-2.35,front+4.08,16.89 if kind=='clock'else 15.35)
                top=contour(x,max(.26,half-3.68),front+5.62,17.78 if kind=='clock'else 16.02)
                for low,up in [(base,eaves),(eaves,knuckle),(knuckle,high),(high,top)]:surface(b,low,up,lod,kind+' mansard')
                plate(b,top,TILE,kind+' crest')
                contours.extend([eaves,knuckle,high,top])
                pediment(b,lod,x,6.63 if kind=='clock'else 6.51,kind=='clock')
                for u in [x-(half-3.68),x+(half-3.68)]:
                    b.lathe((u,front+5.65),[(top[1][2],.098),(top[1][2]+.13,.095),(top[1][2]+.45,.02)],METAL,6 if lod else 10,'roof finial')
            else:
                top=contour(x,.02,12.06,15.18)
                contours.append(top)
                surface(b,base,top,lod,'intermediate hipped pavilion')
                b.tube([(x,12.06,15.20),(x,BACK,15.20)],.085,CAP,6 if lod else 10,'pavilion summit')
                b.lathe((x,12.06),[(15.2,.08),(15.31,.08),(15.61,.018)],METAL,8,'short hip finial')
            roof_profile=[(c[0][0],c[0][2])for c in contours]+[(c[3][0],c[3][2])for c in reversed(contours)]
            rear=Facade(b,(left,BACK),(right,BACK),'cut at north side of garden roof')
            rear.prism(Polygon([(u-x,z)for u,z in roof_profile]),-.015,.017,CUT,'neutral exposed roof section')
        slab(b,x,front+.28,EAVE-.27,(right-left)+2*ext,.58,.19,WOOD,'dark timber eave')
        groups=np.linspace(left+.71,right-.71,4 if kind!='range'else 3)
        bracket_positions=[center+offset for i,center in enumerate(groups)
                           for offset in ((-.23,0,.23)if i in (0,len(groups)-1) else (-.12,.12))]
        for u in bracket_positions:
            ys=[front+.17,front+.58,front+1.00];zs=[EAVE-.27,EAVE-.49,EAVE-1.04]
            b.tube([(u,y,z)for y,z in zip(ys,zs)],.077,WOOD,5 if lod else 8,'curved rafter bracket')
            slab(b,u,front+1.00,EAVE-.98,.17,.15,.79,CREAM,'bracket wall block')
    # Street evidence shows a single slender chimney west of the central clock mass.
    slab(b,-12.54,13.84,13.20,.78,.79,3.84,PEBBLE,'garden roof chimney')
    slab(b,-12.54,13.84,17.04,.94,.94,.18,CREAM,'chimney cap')
