"""Rebuild the photographed eleven-bay south arcade of St John's University Yen Hall."""
import argparse,json,sys,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box as rect
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder as BaseBuilder
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
import arcade_finishes
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in arcade_finishes.STEMS:arcade_finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        BaseBuilder.save(self,path,metadata)
        return arcade_finishes.writer.embed_normals(path)
ID='changning-st-johns-yen-hall-arcade'
GREY='Yen Hall | filled grey brick';RED='Yen Hall | red arch brick';TILE='Yen Hall | dark roof tiles';TERRA='Yen Hall | perforated cream balustrade';SHADE='Yen Hall | shaded passage wall';DECK='Yen Hall | gallery flooring';TIMBER='Yen Hall | roof soffit'
PALETTE={**arcade_finishes.PALETTE,TILE:{'color':[.15,.132,.116],'roughness':.90},TERRA:{'color':[.83,.78,.66],'roughness':.83},SHADE:{'color':[.17,.148,.127],'roughness':.93},DECK:{'color':[.43,.395,.344],'roughness':.92},TIMBER:{'color':[.29,.176,.115],'roughness':.87}}
register=json.loads((HERE.parent/'measurements/arcade-registration.json').read_bytes())['parameters']
WIDTH=register['total_width_m'];PITCH=register['pitch_m'];H=register['levels'];SPAN=2.47
META={'id':ID,'name':'圣约翰大学思颜堂四十号楼草坪前廊','heritage_id':'sh-historic-b2-060','official_id':'2M006','address':'华东政法大学长宁校区40号楼，校方门牌万航渡路1575号，房管局历次名录使用1175号','source':'https://www.ecupl.edu.cn/2022/1101/c13514a193945/page.htm','photo_source':'https://www.ecupl.edu.cn/2022/1101/c13514a193945/page.htm','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'viewer_page':'st-johns-yen-hall-arcade.html','camera_views':json.loads((HERE/'cameras.json').read_bytes()),'scope':'Grass-facing seven-bay three-storey arcade, four-bay two-storey continuation, real open balustrades and bounded front roof band. Other sides of the courtyard and the adjacent Hall 41 are outside this reconstruction.'}
def axis(i):return -WIDTH/2+.58+i*PITCH
def xyz(x,z,d):return x,-d,z
def wall(builder,wallshape,ymin,ymax,material,name):
    builder.prism(wallshape,-ymax,-ymin,xyz,material,name)
def shape_box(b,x0,x1,y0,y1,z0,z1,material,name):
    b.box(((x1+x0)/2,(y1+y0)/2,(z1+z0)/2),(x1-x0,y1-y0,z1-z0),material,label=name)
def curve(cx,a,top,rise,samples):
    radius=(a*a+rise*rise)/(2*rise)
    return [(cx+x,top-radius+math.sqrt(max(0,radius*radius-x*x)))for x in np.linspace(-a,a,samples)]
def opening(cx,width,base,top,rise,n):
    a=width/2;arc=curve(cx,a,top,rise,n)
    return Polygon([(cx-a,base),(cx+a,base),*reversed(arc)])
def rail(b,cx,z,k,lod):
    width=SPAN+.14;height=.68;face=rect(cx-width/2,z,cx+width/2,z+height)
    # Sunlit through-holes are set in staggered rows, leaving an unbroken bottom and top rail.
    holes=[]
    for r in range(3):
        for n in range(9):
            x=cx+(n-4+(.5 if r%2 else 0))*.268;zmid=z+.14+r*.20
            if x+.114>cx+width/2-.04:continue
            holes.append(Polygon([(x-.111,zmid),(x,zmid-.083),(x+.111,zmid),(x,zmid+.083)]))
    wall(b,face.difference(unary_union(holes)),.035,.205,TERRA,k+' / perforated cream railing')
def roof_band(b,x0,x1,base,slope,name):
    y0=-.27;y1=3.15
    # A hipped band bounded behind the visible gallery. Both endpoints have a sloped hip return.
    footprint=[(x0-.10,y0),(x1+.10,y0),(x1+.10,y1),(x1+.10-(y1-y0),y1),(x0-.10+(y1-y0),y1),(x0-.10,y1)]
    zs=[base,base,base,base+(y1-y0)*slope,base+(y1-y0)*slope,base]
    verts=[(x,y,z-.12)for(x,y),z in zip(footprint,zs)]+[(x,y,z)for(x,y),z in zip(footprint,zs)]
    top=[(0,1,3,4),(1,2,3),(0,4,5)]
    faces=[tuple(reversed(ids))for ids in top]+[tuple(k+6 for k in ids)for ids in top]+[(i,(i+1)%6,(i+1)%6+6,i+6)for i in range(6)]
    b.add(verts,faces,TILE,name+' / tiled front hip')
def add_building(b,lod=False):
    tiers=[(H['deck'],H['lower_floor'],H['ground_apex'],.72,11),(H['lower_floor'],H['upper_floor'],H['middle_apex'],.69,11),(H['upper_floor'],H['high_eave'],H['upper_apex'],.83,7)]
    for level,(z0,z1,apex,rise,count) in enumerate(tiers):
        name='level '+str(level+1);x0=-WIDTH/2;x1=WIDTH/2 if count==11 else axis(7)+.57
        holes=[]; n=9 if lod else 23
        for i in range(count):
            cx=axis(i+.5);label=name+' / arch '+str(i+1);inner=opening(cx,SPAN,z0-.04,apex,rise,n);holes.append(inner)
            band=inner.buffer(.245,join_style='round',quad_segs=2 if lod else 5).difference(inner).intersection(rect(cx-2,apex-rise-.027,cx+2,apex+.27))
            wall(b,band,-.094,.01,RED,label+' / brick arch ring')
            if level>0:rail(b,cx,z0+.03,label,lod)
        wall(b,rect(x0,z0,x1,z1).difference(unary_union(holes)),0,.65,GREY,name+' / open brick arcade')
        shape_box(b,x0-.02,x1+.02,.01,2.72,z0-.18,z0,DECK,name+' / gallery slab')
        shape_box(b,x0,x1,2.60,2.82,z0,z1,SHADE,name+' / shaded inner limit')
        for i in range(count+1):
            c=axis(i);w=PITCH-SPAN
            if i==0:lo,hi=x0,c+w/2
            elif i==count:lo,hi=c-w/2,x1
            else:lo,hi=c-w/2,c+w/2
            shape_box(b,lo-.033,hi+.033,-.124,.65,apex-rise-.13,apex-rise+.04,RED,name+' / springing '+str(i+1))
        shape_box(b,x0-.05,x1+.05,-.125,.73,z1-.22,z1-.025,RED,name+' / projecting horizontal string')
    for i,xx in enumerate([(-WIDTH/2,axis(7)+.57),(axis(7)+.57,WIDTH/2)]):
        x0,x1=xx;z=H['high_eave'] if i==0 else H['parapet']
        if i:
            shape_box(b,x0,x1,0,.65,H['upper_floor'],z-.05,GREY,'four-bay wing / low parapet')
        shape_box(b,x0-.11,x1+.11,-.15,.71,z-.03,z+.10,RED,'roof level '+str(i+1)+' / brick cornice')
        roof_band(b,x0,x1,z+.18,.43 if i==0 else .40,'west high roof' if i==0 else 'east low roof')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output,META)
if __name__=='__main__':main()
