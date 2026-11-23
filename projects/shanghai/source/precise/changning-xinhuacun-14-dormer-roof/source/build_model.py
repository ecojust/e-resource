"""Rebuild the photographed four garden-facing dormers of Xinhua Village, municipal House 14."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = next(parent for parent in HERE.parents if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0, str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
from photo_architecture import Builder as GltfBuilder
import roof_finishes as finish

ID = 'changning-xinhuacun-14-dormer-roof'
META = dict(id=ID, model_id=ID, heritage_id='sh-historic-b3-102', official_id='3M004',
            name='新华村14号楼南坡四座老虎窗', address='愚园路1320号，长宁区政府14号楼',
            viewer_page='xinhuacun-14-dormer-roof.html', geometry_license='MIT', texture_license='MIT',
            photos_embedded=False, source='https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html',
            scope='Four front-facing shed dormers, upper open-gallery band with its five pier heads, three chimneys and their visible front hip. The taller roofs behind are outside this study.',
            camera_views=json.loads((HERE/'cameras.json').read_text()))
M= json.loads((HERE.parent/'measurements/roof-registration.json').read_text())['parameters']
X=M['pitch']; E=M['eave_z']; R=M['ridge_z']; Y=M['ridge_y']; H=M['head_z']; B=M['sill_z']; F=M['sash_y']; A=M['half_sash']
FRONT=-.48; END=2*X+M['overhang']; HIPS=2.35
BRICK=finish.BRICK; TILE=finish.TILE
GREEN='Xinhua 14 | weathered green sash'; STEEL='Xinhua 14 | dark metal edge'; GLASS='Xinhua 14 | garden window glass'
SHADE='Xinhua 14 | shadow in roof'; OCHRE='Xinhua 14 | painted dormer cheeks'; STONE='Xinhua 14 | warm coping stone'
PALETTE={**finish.PALETTE, GREEN:dict(color=[.16,.22,.20],roughness=.74), STEEL:dict(color=[.10,.13,.12],roughness=.64),
         GLASS:dict(color=[.36,.48,.51],alpha=.63,roughness=.29), SHADE:dict(color=[.105,.118,.12],roughness=.96),
         OCHRE:dict(color=[.53,.37,.26],roughness=.90), STONE:dict(color=[.56,.51,.46],roughness=.91)}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in finish.STEMS:finish.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        GltfBuilder.save(self,path,metadata);return finish.writer.embed_normals(path)

def cuboid(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)

def slope(y):
    return E+(R-E)*(y-FRONT)/(Y-FRONT)

def roof_sheet(b,shape,top,thickness,mat,label):
    b.prism(shape,-thickness,0.,lambda x,y,t:(x,y,top(y)+t),mat,label)

def sash(b,cx,lod,prefix):
    clear=2*A
    for leaf in range(4):
        left=cx-A+clear*leaf/4;right=cx-A+clear*(leaf+1)/4
        for edge in (left,right):
            cuboid(b,edge-.027,edge+.027,F-.05,F+.055,B,H,GREEN,prefix+' / leaf stile')
        for edge in (B,H):
            cuboid(b,left+.027,right-.027,F-.055,F+.055,edge-.042,edge+.042,GREEN,prefix+' / leaf rail')
        centre=(left+right)/2
        cuboid(b,centre-.014,centre+.014,F-.048,F+.039,B+.04,H-.04,GREEN,prefix+' / lead vertical')
        for row in range(1,4):
            z=B+(H-B)*row/4; thick=.019 if not lod else .016
            cuboid(b,left+.026,right-.026,F-.062,F+.009,z-thick,z+thick,GREEN,prefix+' / lead crossbar')
        cuboid(b,left+.022,right-.022,F+.060,F+.082,B+.035,H-.035,GLASS,prefix+' / eight lights')
    cuboid(b,cx-A-.045,cx+A+.045,F+.26,F+.315,B-.01,H+.03,SHADE,prefix+' / dark interior')
    for edge in [cx-A-.07,cx+A+.07]:
        cuboid(b,edge-.051,edge+.051,F-.09,F+.13,B-.075,H+.09,GREEN,prefix+' / outside lining')

def dormer(b,cx,lod,prefix,back):
    sash(b,cx,lod,prefix);half=A+.16
    cuboid(b,cx-half-.035,cx+half+.035,F-.21,F+.12,B-.094,B+.015,STEEL,prefix+' / projecting sill nose')
    cheek=Polygon([(F,B-.045),(back,slope(back)-.07),(back,H+.30),(F,H+.08)])
    for x in (cx-half,cx+half):
        b.prism(cheek,x-.060,x+.060,lambda y,z,t:(t,y,z),OCHRE,prefix+' / tapered rendered cheek')
        b.tube([(x,F-.03,B),(x,back,slope(back))],.042,STEEL,6,prefix+' / cheek flashing')
    cap=box(cx-half-.18,F-.24,cx+half+.18,back+.08)
    def top(y):return H+.203+.23*(y-F)/(back-F)
    roof_sheet(b,cap,top,.108,TILE,prefix+' / shed cap')
    cuboid(b,cx-half-.18,cx+half+.18,F-.267,F-.171,H+.065,H+.195,STEEL,prefix+' / cap fascia')
    # The apron fills the vertical change in level between the low sash and the tile face.
    lip_y=FRONT+(B-.13-E)*(Y-FRONT)/(R-E)
    roof_sheet(b,box(cx-half,lip_y,cx+half,F+.005),
               lambda y:B-.117+.087*(y-lip_y)/(F-lip_y),.062,STEEL,prefix+' / dark sill apron')

def front_pitch(b,lod):
    outline=Polygon([(-END,FRONT),(END,FRONT),(END-HIPS,Y),(-END+HIPS,Y)])
    centres=[(i-1.5)*X for i in range(4)]
    lip_y=FRONT+(B-.13-E)*(Y-FRONT)/(R-E)
    back=FRONT+(H+.245-E)*(Y-FRONT)/(R-E)
    cut=unary_union([box(cx-A-.10,lip_y,cx+A+.10,back) for cx in centres])
    skin=outline.difference(cut)
    roof_sheet(b,skin,slope,.12,TILE,'south pitch / open dormer cuts')
    for sign in (-1,1):
        x=sign*END;rid=x-sign*HIPS
        shp=Polygon([(x,FRONT),(x,Y),(rid,Y)])
        b.prism(shp,-.12,0.,lambda xx,y,t:(xx,y,E+(R-E)*abs(xx-x)/HIPS+t),TILE,'side hip / visible return')
        b.tube([(x,FRONT,E+.025),(rid,Y,R+.025)],.073,TILE,8,'hip ridge / roll')
    for j,y in enumerate(np.arange(FRONT+.24,Y,.26 if not lod else .52)):
        strip=skin.intersection(LineString([(-END-1,y),(END+1,y)]))
        for segment in getattr(strip,'geoms',[strip]):
            if segment.geom_type=='LineString' and segment.length>.12:
                x0,x1=segment.bounds[0],segment.bounds[2]
                b.tube([(x0,y,slope(y)+.014),(x1,y,slope(y)+.014)],.025,TILE,6,'roof / lap course '+str(j+1))
    b.tube([(-END+HIPS,Y,R+.023),(END-HIPS,Y,R+.023)],.095,TILE,8,'ridge / ceramic roll')
    cuboid(b,-END,END,FRONT-.06,.31,E-.165,E-.015,GREEN,'eave / continuous painted fascia')
    b.tube([(-END,FRONT-.07,E-.018),(END,FRONT-.07,E-.018)],.067,STEEL,8,'eave / rain gutter')
    for i,cx in enumerate(centres):dormer(b,cx,lod,'dormer '+str(i+1),back)
    for j,cx in enumerate([-1.56*X,0,1.56*X]):
        base=R-.38;z=R+(1.56 if j==1 else .93)
        cuboid(b,cx-.24,cx+.24,Y-.32,Y+.30,base,z-.10,BRICK,'chimney '+str(j+1)+' / stack')
        cuboid(b,cx-.29,cx+.29,Y-.35,Y+.34,z-.15,z,BRICK,'chimney '+str(j+1)+' / brick cap')
        cuboid(b,cx-.14,cx+.14,Y-.16,Y+.16,z,z+.008,SHADE,'chimney '+str(j+1)+' / dark opening')

def gallery_band(b,lod):
    rail=M['rail_z'];base=rail-.64;deck=rail-.83
    cuboid(b,-2*X-.21,2*X+.21,0,1.55,deck-.16,deck,STONE,'upper gallery / floor edge')
    cuboid(b,-2*X-.20,2*X+.20,1.54,1.69,deck,E-.15,SHADE,'upper gallery / recessed unmeasured shade')
    for i in range(5):
        x=(i-2)*X
        cuboid(b,x-.235,x+.235,.035,.61,deck,E-.26,BRICK,'pier '+str(i+1)+' / upper shaft')
        for dz,half in [(.40,.28),(.31,.32),(.22,.365)]:
            cuboid(b,x-half,x+half,-.032,.67,E-dz,E-dz+.10,STONE,'pier '+str(i+1)+' / flared capital')
        profile=Polygon([(-.46,E-.16),(.32,E-.16),(.32,E-.93),(.13,E-.93),(.07,E-.75),(-.045,E-.59),(-.18,E-.44),(-.39,E-.34)])
        for offset in (-.16,.16):
            b.prism(profile,x+offset-.073,x+offset+.073,lambda y,z,t:(t,y,z),OCHRE,'pier '+str(i+1)+' / paired eave corbel')
    for i in range(4):
        x0=(i-2)*X+.24;x1=x0+X-.48
        cuboid(b,x0,x1,-.055,.33,rail-.08,rail+.02,STONE,'upper gallery / coping')
        cuboid(b,x0,x1,0,.30,deck,base+.09,STONE,'upper gallery / rail base')
        for k in range(13):
            xx=x0+(x1-x0)*k/12
            cuboid(b,max(x0,xx-.075),min(x1,xx+.075),.03,.23,base+.09,rail-.08,STONE,'upper gallery / upright')

def add_building(b,lod=False):
    gallery_band(b,lod);front_pitch(b,lod)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--lod',action='store_true')
    args=parser.parse_args();builder=Builder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
