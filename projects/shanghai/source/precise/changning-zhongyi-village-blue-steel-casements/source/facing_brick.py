"""Alternate header and stretcher faces, cut real jambs and place each measured soldier brick."""
import math
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from brick_texture import CAST

MORTAR='Light grey bedding mortar';DARK='Muted plum facing brick';LIGHT='Sunlit rose facing brick';REVEAL='Brick reveal in shade'
SILL='Grey projecting sill';BED='Stone sill shadow'

def brick_face(face,poly,depth,mat,label,lod):
    x0,z0,x1,z1=poly.bounds
    if lod or min(x1-x0,z1-z0)<.022 or abs(poly.area-(x1-x0)*(z1-z0))>1e-7:
        face.prism(poly,-.020,depth,mat,label)
        return
    coords=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    inset=.0028;inner=[(x0+inset,z0+inset),(x1-inset,z0+inset),(x1-inset,z1-inset),(x0+inset,z1-inset)]
    vertices=[face.point(x,z,d)for d,row in [(-.020,coords),(depth-.002,coords),(depth,inner)]for x,z in row]
    faces=[(3,2,1,0),(8,9,10,11)]
    for ring in [0,4]:
        for k in range(4):
            q=(k+1)%4;faces.append((ring+k,ring+q,ring+4+q,ring+4+k))
    face.builder.add(vertices,faces,mat,face.label+'/'+label)

def add_facing(builder,face,d,measured,lintels,lod):
    openings=[d['open_bay'],d['closed']];l=d['wall_left'];r=d['wall_right'];lo=d['section_bottom'];hi=d['section_top']
    apertures=unary_union([box(*b)for b in openings]);wall=box(l,lo,r,hi).difference(apertures)
    face.prism(wall,-.25,-.018,MORTAR,'continuous pointed wall and deep reveals')
    frieze_height=.21
    heads=[box(a-.008,e-.001,c+.008,e+frieze_height)for a,b,c,e in openings]
    clad=wall.difference(unary_union(heads))
    height=measured['course_height_m'];short=measured['header_module_m'];long=measured['stretcher_module_m'];cycle=short+long
    # Offset from the measured pier: at z=.19 m, adjacent vertical joints lie
    # at x=-1.7636 and -1.5924; the row above shifts its short headers.
    phase_z=measured['resolved_mortar_beds_m'][0];n0=math.floor((lo-phase_z)/height);n1=math.ceil((hi-phase_z)/height)
    for row in range(n0,n1):
        z0=phase_z+row*height+.0048;z1=z0+height-.0096
        if z1<=lo or hi<=z0:continue
        start=-1.76356 if row%2==0 else -1.51467
        first=math.floor((l-start)/cycle)-1;last=math.ceil((r-start)/cycle)
        for k in range(first,last):
            x=start+k*cycle
            for idx,(a,b)in enumerate([(x,x+short),(x+short,x+cycle)]):
                x0=max(l,a+.005);x1=min(r,b-.005);bottom=max(lo,z0);top=min(hi,z1)
                if x1<=x0 or top<=bottom:continue
                poly=box(x0,bottom,x1,top).intersection(clad)
                if poly.is_empty or poly.area<.000055:continue
                shade=(row*13+k*23+idx*7)%19
                mat=DARK if shade in [0,8]else LIGHT if shade==6 else CAST
                brick_face(face,poly,.001+.0007*(shade%3),mat,'brick course '+str(row-n0+1),lod)
    for idx,(bounds,record)in enumerate(zip(openings,lintels['bays'])):
        a,b,c,e=bounds;boundary=record['x_joints_m'];name='Head '+str(idx+1)
        for j,(aa,bb)in enumerate(zip(boundary,boundary[1:])):
            left=max(a-.014,aa+.004);right=min(c+.014,bb-.004)
            if right<=left:continue
            face.prism(box(left,e+.004,right,e+frieze_height-.004),-.026,.006,CAST if j%6 else DARK,name+' upright brick')
            # Narrow brick soffit slopes back to the window frame; it shows on a view from below.
            face.box((left+right)/2,e+.004,right-left,.014,.157,-.077,REVEAL,name+' visible soffit')
        for label,jamb,sign in [('left',a,1),('right',c,-1)]:
            for n in range(math.ceil((e-b)/height)):
                bot=b+n*height+.004;top=min(e-.004,bot+height-.008)
                if top>bot:
                    face.box(jamb+sign*.002,(bot+top)/2,.01,top-bot,.162,-.09,REVEAL,name+' '+label+' jamb returns')
        # Projecting stone sill with a sloping upper surface and a drip under its nose.
        x0=a-.085;x1=c+.085;yt=-.16;yb=.13;z0=b-.083;front=b-.021;back=b+.005
        vv=[(x0,yt,z0),(x1,yt,z0),(x1,yb,z0),(x0,yb,z0),(x0,yt,front),(x1,yt,front),(x1,yb,back),(x0,yb,back)]
        builder.add(vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],SILL,name+'/sloped window sill')
        face.box((a+c)/2,b-.087,c-a+.13,.018,.058,.081,BED,name+' sill drip groove')
