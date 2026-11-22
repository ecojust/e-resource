"""The two polychrome street names and their green address plates in February 2020."""
from functools import lru_cache
from pathlib import Path
import json
import sys
from shapely import affinity
from shapely.geometry import Polygon

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[1]/"hongkou-general-post-office/source/common"))
from sign_lettering import lettering_shapes
from gatehouse_fabric import finish

GREEN = "Yongjia signs | deep green enamel"
CREAM = "Yongjia signs | ivory white ground"
WHITE = "Yongjia signs | pale enamel lettering"
RED = "Yongjia signs | dark red brush lettering"
RIM = "Yongjia signs | folded dark edge"
PIPE = "Yongjia signs | faded light grey iron"
BAND = "Yongjia signs | dark pipe collars"
PALETTE = {GREEN:finish((35,83,65),.53,.08), CREAM:finish((212,206,195),.79),
           WHITE:finish((202,212,191),.54), RED:finish((114,38,43),.76),
           RIM:finish((89,83,75),.71,.20), PIPE:finish((173,171,159),.76,.23),
           BAND:finish((106,103,93),.73,.25)}

@lru_cache(maxsize=1)
def survey():
    path=SOURCE.parent/"measurements/gatehouse-sign-positions.json"
    return json.loads(path.read_text())

def face(b, shape, y0, y1, material, label):
    b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),material,label)

def sign_board(b, shape, y, ground, label):
    # The slim darker fold is visible around the cream plate in the street photographs.
    face(b,shape,y+.002,y+.020,RIM,label+" folded sheet")
    face(b,shape.buffer(-.0025,join_style=2),y,y+.003,ground,label+" face")

def add_gatehouse_signs(b,lod=False):
    for side, data in survey().items():
        name="West Xiai" if side=="west" else "East Hengai"
        boards=data["boards"]
        levels={"enamel":-.032,"name":-.047 if side=="west" else -.046,
                "number":-.055 if side=="west" else -.046}
        sign_board(b, Polygon(boards["enamel"]), levels["enamel"], GREEN, name+" green address plate")
        if side=="west":
            sign_board(b,Polygon(boards["name"]),levels["name"],CREAM,name+" vertical name board")
            sign_board(b,Polygon(boards["number"]),levels["number"],CREAM,name+" wider lower number board")
        else:
            shape=Polygon(boards["name"][:2]+boards["number"][2:])
            sign_board(b, shape, levels["name"], CREAM, name+" continuous name and number board")
        for i, row in enumerate(data["letters"]):
            board=row["board"];green=board=="enamel"
            font=SOURCE/"fonts"/("YongjiaBrush.ttf" if board=="name" else "YongjiaAddress.otf")
            x,z=row["center_xz_m"]
            y=levels[board]-.0015
            for j,(char,shape) in enumerate(lettering_shapes(row["text"],row["width_m"],row["height_m"],font=font)):
                # Preserve the two counters of the numbers and the distinct brush strokes at every distance.
                shape=shape.simplify(.00145 if lod else .00045,preserve_topology=True)
                shape=affinity.translate(shape,xoff=x,yoff=z)
                face(b,shape,y,levels[board]+.0002,WHITE if green else RED,
                     f"{name} {board} letter {i+1}.{j+1} {char}")
    # The fixed downpipe is visible in 2015 and 2020. It masks the right edge
    # of the east board as well as part of the green plate above it.
    pipe_x=2.13
    path=[(pipe_x+.09,-.05,3.78),(pipe_x+.012,-.106,3.61),(pipe_x,-.137,3.53),
          (pipe_x,-.137,1.045),(pipe_x+.018,-.139,1.006),(pipe_x+.080,-.15,.984)]
    b.tube(path,.026,PIPE,sides=9 if lod else 18,label="East plaque downpipe and turned lower shoe")
    for z in (1.04,2.14,2.85,3.52):
        b.tube([(pipe_x,-.137,z-.012),(pipe_x,-.137,z+.013)],.030,BAND,sides=8 if lod else 16,
               label=f"East plaque downpipe collar {z:.2f}")
