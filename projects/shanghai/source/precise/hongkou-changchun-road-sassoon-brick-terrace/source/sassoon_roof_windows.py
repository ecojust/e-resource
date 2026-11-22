"""Four gabled roof windows and three intervening low dormers on Changchun Road."""
from pathlib import Path
from math import atan2, ceil, cos, degrees, hypot, radians, sin
import json
from shapely.geometry import Polygon, box
from frontage_coordinates import WINDOW_PLANES, facade_point

MEASUREMENTS = Path(__file__).resolve().parent.parent / 'measurements'
OBS = json.loads((MEASUREMENTS / 'roof-window-observations.json').read_text())
CREAM = 'Attic | warm ivory render'
WOOD = 'Attic | aged red brown timber'
SOFFIT = 'Attic | shaded bargeboard'
FELT = 'Attic | dark eaves flashing'
TILE = 'Attic | dark weathered clay'
TILE_RIM = 'Attic | exposed tile edges'
GLASS = 'Attic | cool grey glazing'
LIGHT = 'Attic | light replacement frames'
TINT = 'Attic | light replacement glass'
RECESS = 'Attic | window reveal shadow'

def finish(rgb, rough=.82, metal=0):
    # The author's GLB receives linear PBR coefficients. Colors are sRGB readings.
    return dict(color=[((c/255+.055)/1.055)**2.4 for c in rgb],
                roughness=rough, metallic=metal)

PALETTE = {CREAM:finish((207,200,183)),WOOD:finish((96,67,61)),
           SOFFIT:finish((62,51,52)),FELT:finish((77,72,72),.81,.08),
           TILE:finish((104,87,83)),TILE_RIM:finish((126,112,103)),
           GLASS:finish((99,126,139),.35,.17),LIGHT:finish((182,182,173)),
           TINT:finish((145,162,174),.33,.15),RECESS:finish((54,58,58))}


def point(pair, y):
    x, _, z = facade_point(*pair, y)
    return float(x),float(z)


def return_depth(front_uv, back_uv, front):
    """Recover the depth of a constant-X, constant-height eave from its two image ends."""
    x,z = point(front_uv,front)
    x0,z0 = point(back_uv,front)
    x1,z1 = point(back_uv,front+1)
    ux,uz = x1-x0,z1-z0
    return ((x-x0)*ux+(z-z0)*uz)/(ux*ux+uz*uz)


def metric_rows():
    result=[]
    for i,row in enumerate(OBS['gables']):
        plane=WINDOW_PLANES[row['bay']]
        y=float(plane)-.88
        soffit=[point(p,y) for p in row['white_soffit_outline']]
        sky=[point(p,y-.46) for p in row['roof_outline']]
        head=[point(p,y) for p in row['window_head']]
        sill=[point(p,y) for p in row['window_sill']]
        foot=[point(p,y) for p in row['post_feet']]
        xl=(foot[0][0]+head[0][0]+soffit[0][0])/3
        xr=(foot[1][0]+head[1][0]+soffit[2][0])/3
        key='West pair inner east' if i<2 else 'East pair inner west'
        start,end=OBS['rear_eave_on_visible_returns'][key]
        depth=return_depth(start,end,y-.46)
        result.append(dict(name=row['name'],key=f'G{i+1}',kind='gable',face=y,
            xl=xl,xr=xr,base=sum(p[1]for p in foot)/2,
            sill=sum(p[1]for p in sill)/2,head=sum(p[1]for p in head)/2,
            wall_bottom=sum(point((p[0],p[1]+8),y)[1]for p in row['post_feet'])/2,
            soffit=soffit,sky=sky,depth=depth,rows=row['rows'],
            columns=row['leaves'],open_leaves=dict(row['open_leaves'])))
    for i,row in enumerate(OBS['flat_dormers']):
        # The street photograph puts the front sills just inside the central cornice.
        y=float(WINDOW_PLANES[3])+(1.06,2.01,1.96)[i]
        cap=[point(p,y-.16) for p in row['cap_ends']]
        foot=[point(p,y) for p in row['foot']]
        head=[point(p,y) for p in row['head']]
        sill=[point(p,y) for p in row['sill']]
        xl,xr=foot[0][0],foot[1][0]
        xp,zp=point(row['cap_high'],y-.16)
        result.append(dict(name=row['name'],key=f'D{i+1}',kind='flat',face=y,
            xl=xl,xr=xr,base=sum(p[1]for p in foot)/2-.17,
            sill=sum(p[1]for p in sill)/2,head=sum(p[1]for p in head)/2,
            jamb=[head[0][0],head[1][0]],sky=[cap[0],(xp,zp),cap[1]],
            depth=(xr-xl)*(.96 if i==0 else .86),rows=row['rows'],
            columns=row['cols'],open_leaves={}))
    return result


def roof_openings():
    """Plan cutouts for the main roof, measured at the outside face of each dormer."""
    out={}
    for row in metric_rows():
        x0,x1=row['xl'],row['xr']
        y0,y1=row['face'],row['face']+row['depth']
        edge=row['sky']
        out[row['key']]=dict(kind=row['kind'],plan_xy=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],
            front_xz=[(x0,row.get('wall_bottom',row['base'])),*edge,(x1,row.get('wall_bottom',row['base']))],front_y=y0,
            bottom_z=row.get('wall_bottom',row['base']),eaves_z=min(edge[0][1],edge[2][1]),ridge_z=edge[1][1])
    return out


def front_prism(b,outline,y0,y1,mat,name):
    b.prism(outline,-y1,-y0,lambda x,z,d:(x,-d,z),mat,name)


def cubic(b,x0,x1,y0,y1,z0,z1,mat,name):
    if min(x1-x0,y1-y0,z1-z0)>1e-6:
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)


def glazing(b,frame,x0,x1,z0,z1,n,rows,angles,tag,metal=False):
    """Open each individual light about its own upright. The central meeting rails stay distinct."""
    outer=LIGHT if metal else WOOD
    light=TINT if metal else GLASS
    def member(bounds,material,label,angle=0,hinge=0):
        a,c,d,e,p,q=bounds
        if min(c-a,e-d,q-p)<1e-6:return
        rad=radians(angle);cs,sn=cos(rad),sin(rad)
        def mapv(x,y,z):
            xx=x-hinge
            return frame(hinge+xx*cs-y*sn,xx*sn+y*cs,z)
        verts=[mapv(x,y,z) for x,y,z in [(a,d,p),(c,d,p),(c,e,p),(a,e,p),
                                           (a,d,q),(c,d,q),(c,e,q),(a,e,q)]]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        b.add(verts,faces,material,tag+' '+label)
    surround=.038 if metal else .050
    for a,c in [(x0,x0+surround),(x1-surround,x1)]:
        member((a,c,.002,.099,z0,z1),outer,'outer jamb')
    for p,q in [(z0,z0+surround),(z1-surround,z1)]:
        member((x0+surround,x1-surround,.002,.099,p,q),outer,'head and sill')
    clear_l,clear_r=x0+surround,x1-surround
    low,high=z0+surround,z1-surround
    size=(clear_r-clear_l)/n
    for i in range(n):
        a=clear_l+i*size+.004
        c=clear_l+(i+1)*size-.004
        angle=angles.get(i,0)
        hinge=a if angle<=0 else c
        rail=min(.031 if metal else .039,(c-a)*.16)
        margin=.004
        p,q=low+margin,high-margin
        name=f'leaf {i+1}'
        for al,ar in [(a,a+rail),(c-rail,c)]:
            member((al,ar,.014,.062,p,q),outer,name+' upright',angle,hinge)
        for pl,pr in [(p,p+rail),(q-rail,q)]:
            member((a+rail,c-rail,.014,.062,pl,pr),outer,name+' rails',angle,hinge)
        pl,pr=p+rail,q-rail
        for j in range(1,rows):
            z=pl+(pr-pl)*j/rows
            member((a+rail,c-rail,.032,.063,z-.012,z+.012),outer,name+' bars',angle,hinge)
        member((a+rail,c-rail,.067,.077,pl,pr),light,name+' glass',angle,hinge)


def roof_half(b,p0,p1,y0,y1,lod,tag):
    """A closed clay plane, timber rake, stepped tile courses and rounded ridge end."""
    x0,z0=p0; x1,z1=p1
    shell=Polygon([(x0,z0),(x1,z1),(x1,z1-.098),(x0,z0-.098)])
    front_prism(b,shell,y0,y1,TILE,tag+' clay slope')
    fascia=Polygon([(x0,z0-.060),(x1,z1-.060),(x1,z1-.190),(x0,z0-.190)])
    front_prism(b,fascia,y0-.012,y0+.145,SOFFIT,tag+' rake fascia')
    span=hypot(x1-x0,z1-z0)
    streams=max(3,round(span/(.415 if lod else .238)))
    for i in range(1,streams):
        t=i/streams
        w=.035/span if lod else .041/span
        xa=x0+(x1-x0)*(t-w);xb=x0+(x1-x0)*(t+w)
        za=z0+(z1-z0)*(t-w);zb=z0+(z1-z0)*(t+w)
        tile_edge=Polygon([(xa,za+.002),(xb,zb+.013),(xb,zb-.012),(xa,za-.012)])
        front_prism(b,tile_edge,y0-.006,y1-.012,TILE_RIM,tag+' tile courses')
        if not lod:
            step=.247
            joints=max(1,round((y1-y0)/step))
            for j in range(joints):
                y=y0+(j+(.23 if i%2 else .63))*(y1-y0)/joints
                if y>y1-.018:continue
                t1,t2=(i-.88)/streams,(i-.14)/streams
                xa=x0+(x1-x0)*t1;xb=x0+(x1-x0)*t2
                za=z0+(z1-z0)*t1;zb=z0+(z1-z0)*t2
                strip=Polygon([(xa,za+.006),(xb,zb+.006),(xb,zb-.003),(xa,za-.003)])
                front_prism(b,strip,y,y+.014,TILE_RIM,tag+' tile ribs')


def window_group(b,row,lod):
    tag='Attic '+row['key']
    xl,xr=row['xl'],row['xr']; y=row['face']; rear=y+row['depth']
    base,sill,head=row['base'],row['sill'],row['head']
    p0,peak,p1=row['sky'];width=xr-xl
    is_gable=row['kind']=='gable'
    wall_bottom=row.get('wall_bottom',base)
    if is_gable:
        left,right=xl+.066,xr-.066
        e0,ap,e1=row['soffit']
        face=Polygon([(xl,wall_bottom),(xr,wall_bottom),(xr,e1[1]),ap,(xl,e0[1])])
    else:
        left,right=row['jamb']
        roof_z=min(p0[1],p1[1])-.086
        face=box(xl,base,xr,roof_z)
    def under_tile(x):
        (ax,az),(bx,bz)=(p0,peak) if x<=peak[0] else (peak,p1)
        return az+(bz-az)*(x-ax)/(bx-ax)-.065
    enclosure=Polygon([(xl,wall_bottom),(xr,wall_bottom),(xr,under_tile(xr)),
                       (peak[0],under_tile(peak[0])),(xl,under_tile(xl))])
    # The street photograph shows a broad dark sloping soffit above the plaster.
    # The front, side boards and the backing all rise to the actual underside.
    trim=enclosure.difference(face)
    if not trim.is_empty:
        front_prism(b,trim,y-.010,y+.110,SOFFIT,tag+' rafter lining')
    front_prism(b,enclosure,rear-.083,rear,CREAM,tag+' roof junction backing')
    aperture=box(left,sill,right,head)
    front_prism(b,face.difference(aperture),y,y+.10,CREAM,tag+' window wall')
    front=lambda u,depth,z:(u,y+depth,z)
    glazing(b,front,left,right,sill,head,row['columns'],row['rows'],row['open_leaves'],tag,
            metal=row['key'] in ('G4','D1','D2'))
    # A dark painted inner lining, visible through the opened leaves.
    cubic(b,left,right,y+.27,y+.30,sill,head,RECESS,tag+' dark reveal')
    clipped_side=row['key'] in ('G2','G3')
    for side in (-1,1):
        x=xl if side==-1 else xr
        ztop=(row['soffit'][0 if side==-1 else 2][1] if is_gable else roof_z)
        if side==-1:
            frame=lambda u,d,z:(x+d,rear-u,z)
        else:
            frame=lambda u,d,z:(x-d,y+u,z)
        depth=row['depth']
        profile=box(0,wall_bottom,depth,ztop)
        if under_tile(x)>ztop+.001:
            b.prism(box(0,ztop,depth,under_tile(x)),-.095,0,
                    lambda u,z,d:frame(u,-d,z),SOFFIT,tag+' under eaves')
        facing_center=clipped_side and ((row['key']=='G2' and side==1) or (row['key']=='G3' and side==-1))
        if facing_center:
            # In Gao's 2015 quarter view the side window begins at the corner post.
            start,end=.066,min(depth-.16,.69*width)
            if side==-1:start,end=depth-end,depth-start
            profile=profile.difference(box(start,sill,end,head))
            glazing(b,frame,start,end,sill,head,4,4,{},tag+' cheek')
        mapper=lambda u,z,d:frame(u,-d,z)
        b.prism(profile,-.095,0,mapper,CREAM,tag+' return wall')
    if is_gable:
        for x in (xl,xr):
            cubic(b,x-.066,x+.066,y-.068,y+.008,base+.07,head+.18,WOOD,tag+' corner timber')
            for i in range(3):
                span=.18+i*.025
                cubic(b,x-span/2,x+span/2,y-.072-i*.015,y+.045,head+.10+i*.048,head+.15+i*.048,
                      WOOD if i!=1 else SOFFIT,tag+' stepped cap')
        for z,size in [(head,.070),(sill,.075)]:
            cubic(b,xl-.055,xr+.055,y-.065,y+.012,z-size/2,z+size/2,WOOD,tag+' long rails')
        roof_half(b,p0,peak,y-.46,rear,lod,tag+' left')
        roof_half(b,peak,p1,y-.46,rear,lod,tag+' right')
        b.tube([(peak[0],y-.48,peak[1]),(peak[0],rear,peak[1])],.052,TILE_RIM,7 if lod else 10,tag+' ridge tiles')
    else:
        roof_half(b,p0,peak,y-.17,rear,lod,tag+' left')
        roof_half(b,peak,p1,y-.17,rear,lod,tag+' right')
        cubic(b,xl-.045,xr+.045,y-.13,y+.017,roof_z-.073,roof_z+.013,SOFFIT,tag+' eaves fascia')


def add_roof_windows(b,lod=False):
    rows=metric_rows()
    for r in rows:window_group(b,r,lod)
    # The top corners of each gable pair flank a short recessed horizontal connection.
    for first,second in [(rows[0],rows[1]),(rows[2],rows[3])]:
        a,c=first['xr'],second['xl']; yl=first['face']
        if c<=a:continue
        y=max(yl,second['face'])+.012
        base=min(first['wall_bottom'],second['wall_bottom']);top=min(first['soffit'][2][1],second['soffit'][0][1])+.025
        tag='Attic '+first['key']+'-'+second['key']
        cubic(b,a,c,y,y+.12,base,top,CREAM,tag+' valley wall')
        for z in [first['sill'],first['head'],top-.12]:
            cubic(b,a,c,y-.041,y+.001,z-.037,z+.037,WOOD,tag+' cross rails')
        cubic(b,a-.063,c+.063,y-.24,min(yl+first['depth'],second['face']+second['depth']),top,top+.105,
               FELT,tag+' valley gutter')
