"""Eight-sided corner drum, alternating openings, and the measured profile of the gold roof."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade,opening
from grey_brick import BRICK
from frontage import BRIGHT,GILT,GLASS,METAL,RED,SASH,SEAM,SHADOW,STONE,brick_arch,sash,storefront

# (elevation above skirt / total height, radius / skirt radius). Shoulder, neck
# and flared foot follow the silhouette in Fayhoo's 2060 × 1372 original.
PROFILE=[(0.,1.),(.037,.955),(.11,.902),(.22,.875),(.34,.854),(.45,.806),
         (.54,.706),(.602,.575),(.65,.419),(.685,.302),(.716,.229),
         (.758,.179),(.81,.145),(.873,.133),(.895,.151),(.914,.165),
         (.938,.125),(.963,.067),(.980,.038),(1.,.013)]


def octagon(radius):
    return [(radius*math.cos((i+.5)*math.pi/4),radius*math.sin((i+.5)*math.pi/4)) for i in range(8)]


def ledge(b,r,z,upper,outer,material,label):
    # Hollow rings preserve the space behind each window in section.
    outside=Polygon(octagon(r+outer))
    inside=Polygon(octagon(r-.18))
    b.plan_prism(outside.difference(inside),z,upper,material,label)


def cupola(b,p,lod):
    z=p['dome_skirt'];height=p['dome_cap']-z;r=p['gold_radius']
    rr=PROFILE if not lod else [pt for j,pt in enumerate(PROFILE) if j in (0,2,4,5,6,8,10,12,14,16,18,19)]
    for k in range(8):
        a=np.array(octagon(1.)[k]);c=np.array(octagon(1.)[(k+1)%8]);m=(a+c)/2
        outward=m/np.linalg.norm(m)
        count=2 if lod else 6
        pts=[];faces=[]
        for lev,rad in rr:
            for j in range(count+1):
                t=j/count
                # The roof is slightly bellied between its folded raised ribs.
                xy=((1-t)*a+t*c+outward*.033*math.sin(math.pi*t))*r*rad
                pts.append([*xy,z+height*lev])
        for i in range(len(rr)-1):
            for j in range(count):
                n=i*(count+1)+j;faces.append([n,n+1,n+count+2,n+count+1])
        b.add(pts,faces,GILT,'Cupola / eight curved metal gores')
        path=[[*((r*rad+.008)*a),z+height*lev]for lev,rad in rr]
        b.tube(path,.019 if lod else .024,SEAM,5 if lod else 8,'Cupola / eight folded standing seams')
    b.lathe([0.,0.],[(z+height*.952,.058),(z+height*.974,.077),(z+height*.992,.049),(z+height,.038),
                       (z+height+.105,.019),(z+height+.23,.008)],SEAM,12 if lod else 24,'Cupola / crown and short finial')
    ledge(b,r,z-.10,z+.014,.08,METAL,'Cupola / skirt flashing')


def tower(b,p,lod,body):
    r=p['tower_radius'];pts=octagon(r);zb=p['drum_base'];cap=p['drum_cap'];eave=p['eave']
    for i,a in enumerate(pts):
        c=pts[(i+1)%8];f=Facade(b,a,c,'Tower')
        # normals N, NW, W face the street; the flanking north-east and
        # south-west panels return behind the wing walls.
        angle=(i+1)*45%360;street=angle in (90,135,180)
        if street:
            if angle==135:
                holes=[sash(f,0,z,.79,h,.14,lod)for z,h in ((3.72,2.05),(7.48,2.12))]
                # The front spandrel is flush-faced red brick between slim grey piers.
                f.box(0,6.63,.69,1.13,.050,.025,RED,'Front brick spandrel')
                if not lod:
                    for row in range(12):
                        zz=6.102+row*.093
                        f.box(0,zz,.688,.008,.012,.054,STONE,'Spandrel bed joints')
                        for off in (-.23,0,.23):
                            xx=off+(row%2)*.106
                            if abs(xx)<.319:f.box(xx,zz+.043,.008,.084,.012,.054,STONE,'Spandrel head joints')
            else:
                holes=[]
                # Shallow blind bays beside the tower's central red casements.
                for z in (3.91,7.48):
                    top=z+2.1
                    f.box(0,z+1.06,.99,2.12,.065,.02,RED,'Infilled side panels')
                    f.box(0,z+1.03,.84,1.87,.073,.055,BRIGHT,'Recessed brick infill')
                    brick_arch(f,0,top-.12,.98,.13,lod)
            f.wall(3.49,zb,holes,.29,BRICK)
            for side in (-1,1):
                f.box(side*(f.length/2-.059),(zb+3.49)/2,.105,zb-3.49,.10,.034,RED,'Upright brick arrises')
        elif not body.covers(Polygon([a,c,(0,0)])):
            f.wall(.13,zb,(),.29,BRICK)
        else:
            f.wall(eave-.16,zb,(),.29,BRICK)
        # Upper gallery: the NW face is a square, deeply shadowed opening
        # under a pale lintel. On the adjoining two faces the arches are blind.
        lower=p['opening_sill'];hh=p['opening_height']
        if angle==135:
            w=p['opening_width']
            hole=box(-w/2,lower,w/2,lower+hh)
            f.wall(zb,cap,[hole],.31,BRICK)
            f.prism(hole.buffer(.013,join_style=2),-.71,-.68,SHADOW,'Gallery inner shade')
            for side in (-1,1):f.box(side*(w/2+.07),lower+hh/2,.15,hh+.15,.16,.065,RED,'Gallery jamb bricks')
            f.box(0,lower+hh+.085,w+.28,.16,.29,.066,STONE,'Gallery beam')
            arch=opening(0,lower+.03,w*.85,hh*.70,w*.345,12 if lod else 25)
            f.prism(arch.buffer(.037).difference(arch),-.49,-.44,SASH,'Arched frame behind gallery')
        else:
            arch=opening(0,lower,f.length*.65,hh,f.length*.30,12 if lod else 25)
            f.wall(zb,cap,([arch] if angle in (90,180) else []),.30,BRICK)
            if angle in (90,180):
                f.prism(arch.buffer(.012,join_style=2),-.20,-.176,BRICK,'Blind arches in gallery')
                brick_arch(f,0,lower+hh-f.length*.30,f.length*.65,f.length*.30,lod)
        for side in (-1,1):
            f.box(side*(f.length/2-.095),(zb+cap)/2,.17,cap-zb,.14,.052,RED,'Gallery corner pilasters')
        for u in np.linspace(-f.length*.38,f.length*.38,5):
            f.box(u,cap-.21,.14,.19,.21,.082,BRIGHT,'Crown dentils')
            if not lod:f.box(u,zb-.11,.131,.143,.16,.07,RED,'Gallery floor dentils')
    for h,th,out,m in [(zb-.29,.09,.08,RED),(zb-.18,.09,.13,BRIGHT),(zb-.065,.16,.20,RED),
                         (zb+.18,.085,.09,BRIGHT),(zb+.38,.079,.066,RED),(cap-.45,.084,.07,RED),
                         (cap-.087,.13,.15,RED),(cap+.046,.112,.205,BRIGHT),(cap+.158,.072,.165,RED)]:
        ledge(b,r,h,h+th,out,m,'Tower / stepped brick string courses')
    cupola(b,p,lod)
