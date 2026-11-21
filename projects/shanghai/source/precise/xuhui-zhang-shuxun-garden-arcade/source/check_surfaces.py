"""Read the actual triangles and test the materials across all three openings."""
from math import pi,sin,cos
from pathlib import Path
import os,runpy
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
from garden_arcade import BAY,SPRING,STONE,EDGE,SHADOW,WALL,GLASS,METAL
def check(reader):
    rows=[]
    def probe(name,x,z,materials,near,far):
        origin=[x,-.6,z];hit=reader.ray(origin,[0,1,0],1.4)
        rows.append(dict(part=name,origin=origin,hit=hit,passed=bool(hit and hit['material'] in materials and near<=hit['distance_m']-.6<=far)))
    for x in (-BAY,0,BAY):
        for column in range(4):
            for row in range(5):
                probe('Daylight pane',x+(column-1.5)*.370,.218+(row+.5)*(SPRING-.048-.218)/5,GLASS,.163,.175)
        for dx in [-.37,0,.37]:
            for z in (.46,1.41,2.31):
                probe('Vertical glazing bar',x+dx,z,[METAL],.087,.130)
        for n in (1,2,3,4):
            probe('Transverse glazing bar',x+.185,.218+n*(SPRING-.048-.218)/5,[METAL],.085,.127)
        probe('Kick panel',x+.34,.137,['oxidized metal kick panel'],.080,.125)
        for radius in (.139,.358):
            for theta in (.32*pi,.64*pi):
                probe('Concentric semicircle',x+radius*cos(theta),SPRING+radius*sin(theta),[METAL],.085,.127)
        for t in (.25*pi,.50*pi,.75*pi):
            probe('Fanlight spoke',x+.578*cos(t),SPRING+.578*sin(t),[METAL],.085,.127)
        for t in (.21*pi,.41*pi,.61*pi,.81*pi):
            probe('Carved pale arch band',x+.805*cos(t),SPRING+.805*sin(t),[STONE],-.068,-.038)
        for t in (.165*pi,.415*pi,.67*pi,.89*pi):
            probe('Semi-circular projecting bead',x+.851*cos(t),SPRING+.851*sin(t),[EDGE],-.10,-.06)
    for x in (-BAY/2,BAY/2):
        for z in (.08,.15,.73,1.26,1.94):
            probe('Stone column base and shaft',x,z,[STONE,SHADOW],-.215,-.115)
        for z in (2.06,2.23,2.32,2.37,2.417):
            probe('Royal capital and abacus',x,z,[STONE,EDGE],-.279,-.105)
    for x in (-2.97,-1.04,.8,2.95):
        probe('Garden stucco spandrel',x,3.52,[WALL],.009,.015)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)
