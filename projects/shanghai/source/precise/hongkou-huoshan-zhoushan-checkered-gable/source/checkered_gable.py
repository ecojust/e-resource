"""Street-side paired arched windows and checked gable at Huoshan and Zhoushan roads."""
from math import cos, pi, sin
from pathlib import Path
from random import Random
from PIL import Image, ImageDraw
from shapely.affinity import affine_transform
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

WALL='Weathered grey brick in running bond'
RED='Russet brick'
DARK='Blue grey brick'
EDGE='Pale cement coping'
GLASS='Recessed dim glazing'
JOINERY='Oxide red painted frames'
JOINT='Recessed mortar joints'
PALETTE={name:dict(color=rgb,roughness=rough) for name,rgb,rough in [
    (WALL,[.97,.97,.97],.97),(RED,[.44,.185,.114],.96),(DARK,[.165,.163,.144],.94),
    (EDGE,[.69,.64,.54],.87),(GLASS,[.214,.266,.266],.3),
    (JOINERY,[.30,.107,.071],.70),(JOINT,[.50,.46,.37],.96)]}
SCALE=.020
CENTRES=(158,249)
TOP=[(92,148),(110,127),(110,110),(128,110),(188,20),
     (195,11),(202,7),(208,6),(215,7),(221,11),(228,19),
     (283,101),(300,102),(300,127),(313,145)]
def xyz(u,v,depth):return ((u-203)*SCALE,-depth,(298-v)*SCALE)
def extrude(b,shape,back,front,mat,name):
    if shape.is_empty:return
    plane=affine_transform(shape,[SCALE,0,0,-SCALE,-203*SCALE,298*SCALE])
    b.prism(plane,back,front,lambda x,z,d:(x,-d,z),mat,name)
def arch(cx,rad,steps):
    return [(cx+rad*cos(t*pi/steps),184-rad*sin(t*pi/steps)) for t in range(steps+1)]
def void(cx,rad,steps):
    return Polygon(arch(cx,rad,steps)+[(cx-rad,274),(cx+rad,274)])
def ring(cx,ri,ro,start,end,n):
    def path(r,ids):
        return [(cx+r*cos(a),184-r*sin(a)) for i in ids for a in [(start+(end-start)*i/n)*pi/180]]
    return Polygon(path(ro,range(n+1))+path(ri,range(n,-1,-1)))
def texture(destination):
    rng=Random(423)
    img=Image.new('RGB',(670,860),(136,127,111));d=ImageDraw.Draw(img)
    for row,v in enumerate(range(-6,860,9)):
        for u in range(-25 if row%2 else -11,670,27):
            tone=rng.randint(-17,17);colour=(99+tone,99+tone,90+tone)
            d.rectangle((u+1,v+1,u+26,v+8),fill=colour)
            for _ in range(18):
                noise=rng.randint(-10,10)
                d.point((u+rng.randint(1,26),v+rng.randint(1,8)),fill=tuple(c+noise for c in colour))
    img.save(destination,optimize=True)
def add_building(b,lod):
    n=20 if lod else 52
    outer=Polygon(TOP+[(313,298),(92,298)])
    holes=unary_union([void(cx,27,n)for cx in CENTRES])
    extrude(b,outer.difference(holes),-.32,0,WALL,'Grey brick face with two full-depth arched window openings')
    # The checker field is clipped to the sloping pediment and narrows to a round crown.
    checked=outer.intersection(box(105,6,307,109))
    for row,top in enumerate(range(7,109,16)):
        for col,left in enumerate(range(102,305,16)):
            tile=checked.intersection(box(left+.65,top+.65,left+15.65,top+15.7))
            if tile.is_empty or tile.area<4:continue
            mat=RED if (col+row)%2 else DARK
            extrude(b,tile,.001,.014,mat,'Red and grey checker masonry units')
            # Alternating beds and upright fine joints are visible within the colour blocks.
            if mat==DARK:
                splits=[box(left+q,top+.8,left+q+.42,top+15.6)for q in (4.2,8.2,12.2)]
            else:
                splits=[box(left+.8,top+q,left+15.6,top+q+.38)for q in (5.2,10.5)]
            for seam in splits:
                g=tile.intersection(seam)
                if g.area>.12:extrude(b,g,.014,.016,JOINT,'Fine mortar lines within checker panels')
    # Five short courses of red and grey headers mediate between checks and the ordinary grey wall.
    for row in range(5):
        top=109+5*row
        for col,left in enumerate(range(91-5*(row%2),314,11)):
            cell=outer.intersection(box(left+.40,top+.42,left+10.6,top+4.72))
            if cell.area>1:
                tone=RED if ((col//2+row//2)%3 and row<4) or (col+2*row)%7==1 else DARK
                extrude(b,cell,.001,.009,tone,'Short mixed brick courses at the foot of the checking')
    extrude(b,box(200,51,214,93),.017,.042,EDGE,'Pale central upright inset')
    extrude(b,box(206.2,64,207.1,82),.042,.0435,DARK,'Visible vertical mark on central inset')
    coping=LineString(TOP[1:-1]).buffer(1.8,cap_style='square',join_style='round',quad_segs=3)
    extrude(b,coping,-.335,.067,EDGE,'Cement coping over curved peak and shoulder steps')
    for idx,cx in enumerate(CENTRES,1):
        opening=void(cx,27,n)
        extrude(b,opening,-.21,-.19,GLASS,f'Recessed glazing in window {idx}')
        extrude(b,opening.difference(void(cx,24.9,n).intersection(box(cx-28,0,cx+28,271.6))),-.191,-.085,JOINERY,f'Arched frame and bottom rail {idx}')
        for y in (184,214,243):
            extrude(b,box(cx-25,y-1.0,cx+25,y+1.0),-.183,-.106,JOINERY,f'Painted window rail {idx}')
        extrude(b,opening.intersection(box(cx-.94,157,cx+.94,273)),-.182,-.105,JOINERY,f'Central painted mullion {idx}')
        extrude(b,ring(cx,27,35,0,180,n),.0004,.010,JOINT,f'Mortar backing to radial voussoirs {idx}')
        for j in range(25):
            arc=ring(cx,27.15,34.6,j*7.2+.34,(j+1)*7.2-.34,2 if lod else 5)
            extrude(b,arc,.010,.057,DARK,f'Radial brick of window {idx}')
        for j in range(29):
            edge=ring(cx,27.02,28.55,j*180/29+.22,(j+1)*180/29-.22,2 if lod else 4)
            extrude(b,edge,.057,.073,RED,'Narrow rust-red inner archivolt')
        extrude(b,ring(cx,34.8,37.05,0,180,n),.001,.036,DARK,f'Outer brick hood {idx}')
        for side in (-1,1):
            lo,hi=sorted((cx+side*27,cx+side*31.5))
            extrude(b,box(lo,184,hi,274),.001,.034,RED,f'Brick reveal of window {idx}')
        extrude(b,box(cx-35,274,cx+35,279),-.24,.168,EDGE,f'Projecting sill of window {idx}')
        extrude(b,box(cx-32,279,cx+32,282),-.23,.126,EDGE,f'Lower sill return of window {idx}')
    b.palette[WALL]['texture']=str(Path(__file__).with_name('grey-facing-bricks.png'))
    for part in b.parts:
        if part['material']==WALL:
            part['texcoords']=[[.03+.94*(x/SCALE+203-92)/221,1.-(.03+.94*(298-z/SCALE-6)/292)]for x,y,z in part['vertices']]
