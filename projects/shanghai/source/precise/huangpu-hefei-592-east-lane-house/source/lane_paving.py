"""Street pavers, photographed access cover, and the graded cement lane entrance."""
from functools import lru_cache

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box

from west_gable_shutters import finish

JOINT = "Hefei paving | sand-filled recessed joints"
PAVERS = tuple("Hefei paving | grey setts "+str(i+1) for i in range(5))
CEMENT = "Hefei paving | inside cement surface"
CURB = "Hefei paving | blue grey stone kerb"
LID = "Hefei paving | flush access cover"
DARK = "Hefei paving | cover rebates and keyhole"
PALETTE = {
    JOINT:finish((101,99,94),.99),CEMENT:finish((172,167,149),.97),
    CURB:finish((139,139,131),.95),LID:finish((141,140,130),.95),
    DARK:finish((77,78,73),.91),
    **{m:finish(rgb,.97) for m,rgb in zip(PAVERS,[(151,149,139),(148,147,138),
          (156,152,142),(143,144,136),(151,152,141)])},
}


def street_level(x,y):
    return .526-.0125*x+.003*(y+1.60)


def height_at(x,y,d):
    return x,y,street_level(x,y)+d


def curb_line(x):
    return -6.444-.223*x


@lru_cache(maxsize=1)
def pavement_plan():
    # The front edge of each side wall bounds the paving. The plastered
    # garden areas on the far sides of the two iron screens are not paved.
    left=np.array([[-6.48,-2.29],[-5.94,-2.35],[-5.58,-2.32],[-5.18,-2.27],
                   [-4.77,-2.12],[-4.45,-1.87],[-4.22,-1.49],[-4.12,-1.26]])
    right=np.array([[.06,-1.48],[.40,-1.70],[.52,-2.15],[.70,-2.60],
                    [.94,-2.96],[1.29,-3.23],[1.69,-3.42],[2.13,-3.56],[2.57,-3.61]])
    throat=[[-3.38,-1.23],[-.47,-1.17]]
    limits=[[-6.48,curb_line(-6.48)],[2.57,curb_line(2.57)]]
    return Polygon([*limits,*right[::-1],*throat[::-1],*left[::-1]])


def rolled_stones(b,lod):
    surface=pavement_plan()
    # The two photographs agree on the position of this small rectangular cover.
    lid=Polygon([[-2.09,-1.55],[-1.63,-1.59],[-1.83,-2.13],[-2.30,-2.12]])
    b.prism(surface,-.065,-.005,height_at,JOINT,"Continuous base beneath the street pavers")
    field=surface.difference(lid.buffer(.008,join_style=2))
    # Running courses turn with the street. Periods on orthorectified frames
    # place the short repeat at about 0.09–0.12 m. Exact bond varies locally.
    angle=-13.;radians=np.deg2rad(angle);cs,sn=np.cos(radians),np.sin(radians)
    local=affinity.rotate(field,-angle,origin=(0.,0.))
    minx,miny,maxx,maxy=local.bounds;width=.105;length=.205
    def mapped(x,y,d):
        return height_at(cs*x-sn*y,sn*x+cs*y,d)
    for i in range(int(np.floor(minx/width)),int(np.ceil(maxx/width))):
        offset=(i%2)*length*.5
        for j in range(int(np.floor((miny-offset)/length)),int(np.ceil((maxy-offset)/length))):
            x=i*width;y=j*length+offset
            boundary=box(x+.003,y+.003,x+width-.003,y+length-.003)
            # Preserve the narrow real joint even in the light-weight file.
            # The small clipped corners are retained in the near version.
            if not lod:
                a,c,h,k=boundary.bounds;d=.007
                boundary=Polygon([(a+d,c),(h-d,c),(h,c+d),(h,k-d),
                                  (h-d,k),(a+d,k),(a,k-d),(a,c+d)])
            clipped=boundary.intersection(local)
            if clipped.area>.00008:
                mat=PAVERS[(7*i+11*j+i*j)%len(PAVERS)]
                b.prism(clipped,-.009,0.,mapped,mat,f"Sidewalk paver, course {i} unit {j}")
    b.prism(lid,-.008,.002,height_at,DARK,"Dark access cover rebate")
    key=box(-2.059,-1.996,-2.027,-1.959)
    b.prism(lid.buffer(-.014,join_style=2).difference(key),-.001,.004,height_at,LID,
            "Flush access cover with an actual key slot")
    # A narrow recessed lead-in remains visible in the slot itself.


def kerb(b):
    # The stepped top gives way to a dropped edge in front of the two gates.
    xs=[-6.48,-5.87,-5.23,-4.54,-3.80,-3.16,-2.46,-1.75,-1.01,-.26,.47,1.17,1.89,2.57]
    for i,(l,r) in enumerate(zip(xs,xs[1:])):
        l+=.002;r-=.002
        def drop(x):
            return .015+.091*min(1.,max(0.,abs(x+2.0)-1.25)/1.58)
        zb=lambda x: street_level(x,curb_line(x))
        v=[]
        for x in (l,r):
            y=curb_line(x);z=zb(x)
            v.extend([(x,y+.001,z-.073-drop(x)),(x,y-.168,z-.073-drop(x)),
                      (x,y-.168,z-drop(x)),(x,y-.132,z-.003),(x,y+.002,z+.002)])
        faces=[tuple(range(5)),tuple(range(9,4,-1)),*((i,5+i,5+(i+1)%5,(i+1)%5)for i in range(5))]
        b.add(v,faces,CURB,"Street kerb segment "+str(i+1))


def inside_lane(b):
    # Distinct paving-to-cement seam at Y~-1.2 in 2017. The wall foot is
    # 0.67 m above the shared photographic datum in the 2015 primary view.
    sections=[([-3.47,-1.23],[-.02,-1.16]),([-3.47,.12],[-.013,.12]),
              ([-3.47,4.30],[-.013,4.30])]
    for i,((a,c),(h,k)) in enumerate(zip(sections,sections[1:])):
        polygon=Polygon([a,c,k,h])
        def level(x,y,d):
            t=np.clip((y+1.19)/1.31,0.,1.)
            return x,y,float((1-t)*street_level(x,y)+t*.666)+d
        b.prism(polygon,-.086,.0008,level,CEMENT,"Exposed cement surface at the lane mouth "+str(i+1))


def add_paving(b,lod=False):
    rolled_stones(b,lod)
    kerb(b)
    inside_lane(b)
