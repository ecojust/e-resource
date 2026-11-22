"""Garden-facing central loggia and dormer, after the published 2022 frontal photograph."""
from math import cos, pi, sin, tau
from pathlib import Path

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from roof_tiles import roof_uv
from repeat import repeat_only_texture

STONE = 'Ivory carved stone'
RENDER = 'Warm white render'
SHADE = 'Shaded soffit'
SASH = 'Oxide red timber'
GLASS = 'Dark grey glazing'
TILE = 'Terracotta roof tiles'
PALETTE = {
    STONE: {'color': [.85,.82,.73], 'roughness': .77},
    RENDER: {'color': [.87,.846,.772], 'roughness': .91},
    SHADE: {'color': [.66,.63,.554], 'roughness': .86},
    SASH: {'color': [.33,.173,.126], 'roughness': .71},
    GLASS: {'color': [.147,.192,.183], 'roughness': .34, 'metallic': .21},
    TILE: {'color': [1.,1.,1.], 'roughness': .84,'texture':str(Path(__file__).with_name('tiles.png'))},
}
AXES = (-7.95,-2.68,2.68,7.95)
CENTERS = tuple((a+c)/2 for a,c in zip(AXES,AXES[1:]))


def point(x,z,depth):
    return x,-depth,z


def face(b,outline,y,zdepth,material,label):
    b.prism(outline,-(y+zdepth),-y,point,material,label)


def block(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box(((x1+x0)/2,(y1+y0)/2,(z1+z0)/2),(x1-x0,y1-y0,z1-z0),material,label=label)


def rails_and_glass(b,aperture,y,lod,n,diamond=False):
    x0,z0,x1,z1=aperture.bounds;zmid=z0+.73*(z1-z0)
    face(b,aperture,y+.085,.032,GLASS,'Dark recessed panes')
    bars=[aperture.difference(aperture.buffer(-.065,join_style='mitre')),box(x0,zmid-.035,x1,zmid+.035)]
    for i in range(1,n):
        x=x0+i*(x1-x0)/n;bars.append(box(x-.032,z0,x+.032,z1))
    if not lod:
        z=z0+.40*(z1-z0);bars.append(box(x0,z-.020,x1,z+.020))
        if diamond:
            for i in range(n):
                left=x0+(x1-x0)*i/n;right=x0+(x1-x0)*(i+1)/n
                pts=[(left+.055,zmid-.060),((left+right)/2,zmid-.38),(right-.055,zmid-.06)]
                bars.append(LineString(pts).buffer(.015,cap_style='flat'))
    face(b,unary_union(bars).intersection(aperture),y,.081,SASH,'Red glazing casements')


def fluted_shaft(b,x,lod):
    nr=48 if lod else 112;flutes=16
    # Each radial section recedes smoothly inside the shaft, leaving sixteen continuous arrises.
    levels=[(.22,.51,0),(.39,.49,.033),(7.93,.45,.031),(8.23,.449,0)]
    verts=[]
    for z,outer,recession in levels:
        for n in range(nr):
            a=tau*n/nr;r=outer-recession*(.5+.5*cos(flutes*a));verts.append((x+r*cos(a),.09+r*sin(a),z))
    faces=[tuple(reversed(range(nr))),tuple((len(levels)-1)*nr+n for n in range(nr))]
    for row in range(len(levels)-1):
        for n in range(nr):
            i=row*nr+n;j=row*nr+(n+1)%nr;faces.append((i,j,j+nr,i+nr))
    b.add(verts,faces,STONE,'Two fluted giant shafts')
    ns=20 if lod else 40
    b.lathe((x,.09),[(.05,.53),(.13,.53),(.16,.57),(.19,.57),(.22,.51)],STONE,ns,'Shaft foot mouldings')
    b.lathe((x,.09),[(8.22,.45),(8.27,.49),(8.32,.49),(8.36,.45),(8.42,.48),(8.52,.525),(8.58,.525)],STONE,ns,'Shaft capital rings')
    for i in range(10 if lod else 16):
        a=tau*i/(10 if lod else 16);nx,ny=cos(a),sin(a)
        vv=[(x+.465*nx-.053*ny,.09+.465*ny+.053*nx,8.32),(x+.465*nx+.053*ny,.09+.465*ny-.053*nx,8.32),(x+.535*nx,.09+.535*ny,8.52),(x+.56*nx,.09+.56*ny,8.40)]
        b.add(vv,[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],STONE,'Capital leaf collar')
    block(b,x-.53,x+.53,-.44,.62,8.57,8.71,STONE,'Square abaci')


def balcony(b,a,c,lod):
    left=a+.28;right=c-.28;half=(right-left)/2;middle=(left+right)/2
    def front(x): return .10-.31*(1-((x-middle)/half)**2)
    steps=9 if lod else 19;line=[(left+(right-left)*i/steps,front(left+(right-left)*i/steps))for i in range(steps+1)]
    slab=Polygon([*line,(right,2.63),(left,2.63)])
    b.plan_prism(slab,5.08,5.28,SHADE,'Three curved balcony floors')
    for z0,z1,t,label in [(5.22,5.33,.085,'Curved fascia edge'),(5.32,5.40,.085,'Balustrade lower rail'),(6.16,6.28,.115,'Balustrade curved coping')]:
        rail=LineString(line).buffer(t,cap_style='flat',join_style='round');b.plan_prism(rail,z0,z1,STONE,label)
    # The 2022 photo resolves an open row of turned, pinched stone balusters in each bay.
    for i in range(1,19):
        x=left+(right-left)*i/19;y=front(x)
        profile=[(5.39,.076),(5.47,.076),(5.51,.06),(5.58,.038),(5.84,.050),(5.99,.073),(6.075,.042),(6.13,.064),(6.17,.064)]
        b.lathe((x,y),profile,STONE,6 if lod else 10,'Three rows of open stone balusters')


def dormer(b,lod):
    # One dormer in the centre of the red-tiled slope. The recessed triple sash is cut through the cheek.
    profile=Polygon([(-3.28,12.94),(3.28,12.94),(3.23,13.51),(2.49,14.29),(0,16.53),(-2.49,14.29),(-3.23,13.51)])
    outline=[(-2.04,13.11),(2.04,13.11),(1.66,13.64),(1.45,14.32),(1.24,14.77),(.94,15.00),(.69,15.10),(-.69,15.10),(-.94,15.00),(-1.24,14.77),(-1.45,14.32),(-1.66,13.64)]
    hole=Polygon(outline);face(b,profile.difference(hole),1.41,.34,RENDER,'Central dormer cheek with cutout')
    rails_and_glass(b,hole,1.79,lod,6)
    for x in (-.78,.78):block(b,x-.065,x+.065,1.69,1.85,13.11,15.11,STONE,'Three dormer lights')
    rake=LineString([(-3.34,13.46),(0,16.60),(3.34,13.46)]).buffer(.09,cap_style='flat',join_style='mitre');face(b,rake,1.30,.21,STONE,'Dormer gable coping')
    seal=Polygon([(.26*cos(tau*i/24),15.91+.30*sin(tau*i/24))for i in range(24)]);face(b,seal,1.34,.08,SASH,'Dormer circular ornament');face(b,seal.buffer(.038).difference(seal),1.30,.09,STONE,'Dormer ornament surround')
    # Intersect the pitched dormer roof with the main slope, retaining clay on each side.
    roof_cut=Polygon([(-3.23,1.35),(3.23,1.35),(3.23,1.64),(0,5.38),(-3.23,1.64)])
    panel=box(-8.42,.66,8.42,5.48).difference(roof_cut)
    b.prism(panel,-.10,0,lambda x,y,t:(x,y,12.68+(y-.66)*.82+t),TILE,'Visible slope of clay roof')
    for sign in (-1,1):
        wedge=Polygon([(0,1.36),(sign*3.23,1.36),(sign*3.23,1.64),(0,5.38)])
        b.prism(wedge,-.07,0,lambda x,y,t:(x,y,16.55-abs(x)*.95+t),TILE,'Pitched dormer returns')



def add_building(b,lod):
    repeat_only_texture(b,'tiles.png');half=8.42
    for x in AXES[1:3]:fluted_shaft(b,x,lod)
    for x in (AXES[0],AXES[-1]):
        block(b,x-.47,x+.47,-.22,.53,0,8.68,STONE,'Two rectangular end pilasters')
        if not lod:
            for i in range(-3,4):block(b,x+i*.102-.022,x+i*.102+.022,-.247,-.21,.24,8.18,STONE,'End pilaster narrow fluting')
    openings=[]
    for x in CENTERS:
        for z0,z1,n in [(.27,4.26,6),(5.48,8.15,6),(10.62,12.05,5)]:
            hole=box(x-1.97,z0,x+1.97,z1);openings.append(hole);rails_and_glass(b,hole,2.73,lod,n,True)
    face(b,box(-half,0,half,12.68).difference(unary_union(openings)),2.56,.23,RENDER,'Recessed loggia wall and reveals')
    for x in (-half,half):block(b,x-.055,x+.055,.01,2.74,0,12.58,RENDER,'Portico end returns')
    block(b,-half,half,-.34,2.8,-.09,.11,STONE,'Threshold plinth')
    for a,c in zip(AXES,AXES[1:]):balcony(b,a,c,lod)
    for x in AXES[1:3]:block(b,x-.102,x+.102,.58,.83,10.57,12.14,STONE,'Upper gallery piers')
    block(b,-half,half,-.28,2.82,8.70,9.08,SHADE,'Entablature soffit')
    for z0,z1,forward in [(8.79,8.93,-.33),(9.05,9.19,-.31),(9.32,9.39,-.34),(10.45,10.55,-.34),(12.40,12.52,-.31),(12.58,12.76,-.49)]:block(b,-half,half,forward,1.14,z0,z1,STONE,'Horizontal cornice mouldings')
    block(b,-half,half,-.20,.19,9.13,10.49,RENDER,'Solid upper terrace parapet')
    for i in range(24):
        x=-8.03+i*.700
        pts=[(x+.24,9.91),(x-.23,9.91),(x-.23,9.55),(x+.16,9.55),(x+.16,9.75),(x-.03,9.75)]
        face(b,LineString(pts).buffer(.036,cap_style='flat',join_style='mitre'),-.239,.049,STONE,'Raised Greek key panels')
    for i in range(48 if not lod else 24):
        x=-8.14+i*16.28/(47 if not lod else 23);block(b,x-.057,x+.057,-.28,.06,12.29,12.43,STONE,'Dentils below garden roof')
    dormer(b,lod)
    for part in b.parts:
        if part['material']==TILE:part['texcoords']=[roof_uv(*vertex)for vertex in part['vertices']]
