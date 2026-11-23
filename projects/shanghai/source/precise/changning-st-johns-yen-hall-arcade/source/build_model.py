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
from arcade_details import pierced_parapet,white_panel
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
def roof_band(b,x0,x1,base,slope,name,y0,y1):
    # A hipped band bounded behind the visible gallery. Both endpoints have a sloped hip return.
    footprint=[(x0-.10,y0),(x1+.10,y0),(x1+.10,y1),(x1+.10-(y1-y0),y1),(x0-.10+(y1-y0),y1),(x0-.10,y1)]
    zs=[base,base,base,base+(y1-y0)*slope,base+(y1-y0)*slope,base]
    verts=[(x,y,z-.12)for(x,y),z in zip(footprint,zs)]+[(x,y,z)for(x,y),z in zip(footprint,zs)]
    top=[(0,1,3,4),(1,2,3),(0,4,5)]
    faces=[tuple(reversed(ids))for ids in top]+[tuple(k+6 for k in ids)for ids in top]+[(i,(i+1)%6,(i+1)%6+6,i+6)for i in range(6)]
    b.add(verts,faces,TILE,name+' / tiled front hip')
def add_building(b,lod=False):
    detail=json.loads((HERE.parent/'measurements/parapet-and-rail.json').read_bytes())
    tiers=[(H['deck'],H['lower_floor'],H['ground_apex'],.72,11),(H['lower_floor'],H['upper_floor'],H['middle_apex'],.69,11),(H['upper_floor'],H['high_eave'],H['upper_apex'],.83,7)]
    for level,(z0,z1,apex,rise,count) in enumerate(tiers):
        name='level '+str(level+1);x0=-WIDTH/2;x1=WIDTH/2 if count==11 else axis(7)+.57
        holes=[]; n=9 if lod else 23
        for i in range(count):
            cx=axis(i+.5);label=name+' / arch '+str(i+1);inner=opening(cx,SPAN,z0-.04,apex,rise,n);holes.append(inner)
            band=inner.buffer(.245,join_style='round',quad_segs=2 if lod else 5).difference(inner).intersection(rect(cx-2,apex-rise-.027,cx+2,apex+.27))
            wall(b,band,-.094,.01,RED,label+' / brick arch ring')
            if level>0:white_panel(b,cx,z0+.065,SPAN,label,lod,wall,TERRA,detail['white_guard'])
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
    # The lower front slab and the three risers visible between the lawn borders.
    shape_box(b,-WIDTH/2,WIDTH/2,-.10,2.82,0,H['deck']-.18,RED,'ground arcade / brick plinth')
    mid=axis(4)
    for i in range(3):
        y0=-.91+i*.30
        shape_box(b,mid-1.42,mid+1.42,y0,y0+.30,0,H['deck']*(i+1)/3,DECK,'lawn / measured stair '+str(i+1))
    xstep=axis(7)+.57
    for i,(x0,x1) in enumerate([(-WIDTH/2,xstep),(xstep,WIDTH/2)]):
        if i:
            pierced_parapet(b,detail['lower_wing'],H['upper_floor'],H['parapet'],x1,wall,shape_box,GREY,RED,lod)
        else:
            shape_box(b,x0-.11,x1+.11,-.15,.71,H['high_eave']-.03,H['high_eave']+.10,RED,'west / cornice')
        n=7 if lod else 19
        depth=3.15 if i==0 else 5.07
        tip=x0 if i==0 else x1
        for lev,(z0,z1,apex,rise,count) in enumerate(tiers[:2 if i else 3]):
            start=(-depth if i else 0);end=(0 if i else depth)
            xc=-1.40 if i else 1.40
            hole=opening(xc,1.73,z0+.04,apex-.08,rise*.80,n)
            face=rect(start,z0,end,z1).difference(hole)
            # Reflect the side polygon to keep both outward normals right-handed.
            from shapely.affinity import scale
            def oriented(u,z,d):return (tip-d,-u,z) if i==0 else (tip+d,u,z)
            circ=scale(face,xfact=-1,yfact=1,origin=(0,0))
            b.prism(circ,-.22,.0,oriented,RED if i else GREY,('east' if i else 'west')+' short return / arched side '+str(lev+1))
            ring=hole.buffer(.19,quad_segs=3).difference(hole).intersection(rect(start,apex-rise-.06,end,apex+.22))
            b.prism(scale(ring,xfact=-1,yfact=1,origin=(0,0)),-.015,.075,oriented,RED,('east' if i else 'west')+' short return / brick crown '+str(lev+1))
        if i==0:
            # The raised end forms the cheek visible above the lower roof.
            shape_box(b,x1-.21,x1,.61,3.15,H['parapet'],H['high_eave'],GREY,'change of level / short high wall return')
            roof_band(b,x0,x1,H['high_eave']+.18,.49,'west high roof',-.27,3.15)
        else:
            end_height=H['parapet']+1.65
            shape_box(b,x0,x1,2.59,2.82,H['upper_floor']-.02,H['parapet']+.06,SHADE,'east wing / inner rooftop limit')
            panel=Polygon([(0,H['upper_floor']),(-depth,H['upper_floor']),(-depth,end_height),(0,H['parapet'])])
            b.prism(scale(panel,xfact=-1,yfact=1,origin=(0,0)),-.22,0,oriented,RED,'east wing / stepped rooftop terminal')
            roof_band(b,x0,x1,H['parapet']+.13,.53,'east low roof',2.57,depth)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output,META)
if __name__=='__main__':main()
