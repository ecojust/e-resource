"""Reconstruct the west gallery of the 1899 Science Hall from its registered archive photographs."""
from pathlib import Path
import sys,json,argparse,math
import numpy as np
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from inscription import add_inscription
from hipped_eaves import add_hipped_eave
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder as Base
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
import science_finishes as finishes
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in finishes.STEMS:finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        Base.save(self,path,metadata)
        return finishes.writer.embed_normals(path)
ID='changning-st-johns-gezhi-science-hall';GREY,RED=finishes.STEMS
WOOD='Science Hall | dark casement timber';GLASS='Science Hall | gallery glazing';IRON='Science Hall | open geometric guard';STONE='Science Hall | pale step stone';BACK='Science Hall | gallery interior';TILE='Science Hall | dark glazed roof';CREAM='Science Hall | white inscription tablet'
PALETTE={**finishes.PALETTE,WOOD:{'color':[.27,.234,.19],'roughness':.70},GLASS:{'color':[.38,.52,.57],'alpha':.68,'roughness':.30},IRON:{'color':[.35,.31,.25],'roughness':.64},STONE:{'color':[.59,.58,.54],'roughness':.91},BACK:{'color':[.14,.129,.12],'roughness':.94},TILE:{'color':[.19,.175,.16],'roughness':.82},CREAM:{'color':[.88,.84,.735],'roughness':.78}}
META={'id':ID,'name':'圣约翰大学科学馆（格致楼42号）西院券廊','heritage_id':'sh-historic-b2-060','official_id':'2M006','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'viewer_page':'st-johns-gezhi-science-hall.html','photo_source':'http://www.ecupl.edu.cn/2022/1101/c13514a193943/page.htm','camera_views':json.loads((HERE/'cameras.json').read_bytes()),'scope':'West-facing arcade, unequal casements, the circular opening and two raised roof sections. The building dates from 1899. The New Science Hall across the river is outside this reconstruction.'}
book=json.loads((HERE.parent/'measurements/front-observations.json').read_bytes());reg=json.loads((HERE.parent/'measurements/science-registration.json').read_bytes());measured=json.loads((HERE.parent/'measurements/west-front-openings.json').read_bytes());unit=reg['metres_per_reference_pixel'];xmin,xmax=[(u-323)*unit for u in reg['extent_reference_u']]
def x(u):return (u-323)*unit
def z(v):return (405-v)*reg['vertical_metres_per_reference_pixel']
def wall(b,poly,y0,y1,mat,label):b.prism(poly,-y1,-y0,lambda xx,zz,dd:(xx,-dd,zz),mat,label)
def cuboid(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def arch(cx,half,base,apex,rise,n):
    radius=(half*half+rise*rise)/(2*rise);path=[]
    for dx in np.linspace(-half,half,n):path.append((cx+dx,apex-radius+math.sqrt(max(0.,radius*radius-dx*dx))))
    return Polygon([(cx-half,base),(cx+half,base),*path[::-1]])
def ring(b,inner,cx,base,apex,rise,label,lod):
    band=inner.buffer(.23,quad_segs=3 if lod else 7).difference(inner)
    wall(b,band.intersection(box(cx-2.4,apex-rise-.025,cx+2.4,apex+.25)),-.105,.018,RED,label+' / brick arch voussoirs')
def roof_strip(b,x0,x1,y0,y1,base,raised,label,lod):
    # Roof fronts curve up at the ends. The narrow higher roofs carry their own four upturned tips.
    n=9 if lod else 19;m=3 if lod else 6;verts=[];faces=[]
    for bottom in [True,False]:
        for j in range(m):
            v=j/(m-1)
            for i in range(n):
                t=i/(n-1);end=abs(2*t-1);rise=(1.48 if raised else .48)*end**(6 if raised else 16)*(1-.45*v)
                top=base+(y1-y0)*.59*v+rise
                # At each raised eyebrow its underside is the continuous timber return to the main roof.
                # The main eave bears directly on the top brick course and keeps a closed soffit.
                bearing=z(129)-.083+max(0.,y0+(y1-y0)*v+.59)*(.51 if raised else 0.)
                h=bearing if bottom else top
                verts.append([x0+(x1-x0)*t,y0+(y1-y0)*v,h])
    cap=n*m
    for j in range(m-1):
        for i in range(n-1):
            a=j*n+i;quad=(a,a+1,a+n+1,a+n);faces.extend([tuple(reversed(quad)),tuple(t+cap for t in quad)])
    boundary=[*range(n),*(j*n+n-1 for j in range(1,m)),*(n*(m-1)+i for i in range(n-2,-1,-1)),*(j*n for j in range(m-2,0,-1))]
    for a,c in zip(boundary,boundary[1:]+boundary[:1]):faces.append((a,c,c+cap,a+cap))
    b.add(verts,faces,TILE,label)
def tile_rolls(b,x0,x1,y0,y1,base,raised,label,lod):
    """Shallow rounded channels follow the draped leading eave and the rake of the photo roof."""
    pitch=.225 if not lod else .45
    count=round((x1-x0)/pitch)
    vertices=[];faces=[];rings=3 if lod else 6
    for i in range(1,count):
        t=i/count;xx=x0+(x1-x0)*t;end=abs(2*t-1)
        offset=len(vertices);radius=.033 if lod else .042
        for v in (0.,1.):
            rise=(1.48 if raised else .48)*end**(6 if raised else 16)*(1-.45*v)
            zz=base+v*(y1-y0)*.59+rise
            for ang in np.linspace(0.,math.pi,rings+1):
                vertices.append((xx+radius*math.cos(ang),y0+(y1-y0)*v,zz+.026+radius*math.sin(ang)))
        n=rings+1;faces.append(tuple(offset+i for i in range(n)))
        faces.append(tuple(offset+n+i for i in range(n-1,-1,-1)))
        for j in range(n):
            k=(j+1)%n;faces.append((offset+j,offset+j+n,offset+k+n,offset+k))
    b.add(vertices,faces,TILE,label+' / rounded tile rolls')
def lattice(b,cx,width,base,height,name,lod):
    # The guard has a running row of nested rectangular fretwork, separated by open fields.
    left=cx-width/2;right=cx+width/2;bars=[box(left,base,right,base+.044),box(left,base+height-.055,right,base+height),box(left,base+height*.46,right,base+height*.46+.039)]
    count=max(3,round(width/.37));step=width/count
    for i in range(count):
        a=left+i*step;bars.append(box(a,base,a+.038,base+height));mid=a+.51*step
        bars.extend([box(mid,base+height*.46,mid+.029,base+height*.80),box(mid,base+height*.76,a+.78*step,base+height*.80)])
    bars.append(box(right-.035,base,right,base+height));wall(b,unary_union(bars),.058,.133,IRON,name+' / pierced geometric guard')
def add_building(b,lod=False):
    tiers=[(z(387),z(288)),(z(288),z(208)),(z(208),z(129))];n=11 if lod else 28
    for level,(z0,z1) in enumerate(tiers):
        name=['ground arcade','middle windows','top windows'][level];holes=[]
        for bay in measured['bays']:
            key=bay['id'];label=name+' / '+key;c=x(bay['axis']);half=bay['opening_width']*unit/2
            if key=='A' and level==1:
                radius=.64;centre=z(241);opening=Point(c,centre).buffer(radius,quad_segs=6 if lod else 18);holes.append(opening)
                wall(b,opening.buffer(.19,quad_segs=4).difference(opening),-.095,.010,RED,label+' / round brick surround');wall(b,opening,.23,.25,GLASS,label+' / round glazing');continue
            if key=='A' and level!=1:continue
            wide=bay['opening_width']>60
            if level==0:
                rise=.9 if wide else .66;base=z0-.015;top=z(bay['ground_crown']);th=half
            else:
                th=half*(.93 if wide else .88);top=z((222 if wide else 225) if level==1 else (156 if wide else 160));rise=(.58 if wide else .42);base=z0+.19
            inner=arch(c,th,base,top,rise,n);holes.append(inner);ring(b,inner,c,base,top,rise,label,lod)
            if level:
                wall(b,inner,.222,.245,GLASS,label+' / inset glazed sash')
                frame=inner.difference(inner.buffer(-.064,join_style='mitre'));wall(b,frame,.125,.22,WOOD,label+' / enclosing frame')
                div=4 if wide else 2;bars=[box(c-th,top-rise-.16,c+th,top-rise-.09)]
                for j in range(1,div):
                    u=c-th+2*th*j/div;bars.append(box(u-.025,base,u+.025,top+.01))
                wall(b,unary_union(bars).intersection(inner),.140,.200,WOOD,label+' / transom and mullions')
                lattice(b,c,2*th,base,.55,label,lod)
            elif key!='F':lattice(b,c,2*th,z0+.02,.63,label,lod)
            else:
                wall(b,inner,2.18,2.31,WOOD,label+' / recessed entrance')
                halfdoor=th*.78;cuboid(b,c-halfdoor,c+halfdoor,2.10,2.18,z0+.29,top-.77,GLASS,label+' / entrance glazing');cuboid(b,c-.046,c+.046,2.056,2.115,z0+.08,top-.79,WOOD,label+' / joining stile')
        wall(b,box(xmin,z0,xmax,z1).difference(unary_union(holes)),0,.55,GREY,name+' / measured open facade')
        cuboid(b,xmin-.035,xmax+.035,-.082,.67,z1-.155,z1-.015,RED,name+' / red brick course')
        cuboid(b,xmin,xmax,.54,2.65,z0-.15,z0,STONE,name+' / gallery deck')
        cuboid(b,xmin,xmax,2.62,2.81,z0,z1,BACK,name+' / bounded gallery interior')
    cuboid(b,xmin,xmax,.0,2.81,0,z(387)-.15,STONE,'continuous raised gallery base')
    for i in range(4):cuboid(b,x(282),x(368),-1.12+i*.28,-.84+i*.28,0.,z(387)*(i+1)/4,STONE,'west door / stair tread '+str(i+1))
    cuboid(b,x(286),x(360),-.13,.02,z(282),z(265),RED,'central door / red frame of masonry plaque');cuboid(b,x(289),x(357),-.165,-.13,z(280),z(268),CREAM,'central door / pale tablet')
    add_inscription(b,wall,x,z)
    roof_strip(b,xmin-.50,xmax+.50,-.59,3.84,z(128),False,'gallery / main upswept tiled eave',lod)
    tile_rolls(b,xmin-.50,xmax+.50,-.59,3.84,z(128),False,'gallery / main roof',lod)
    for c in [x(69),x(509)]:
        add_hipped_eave(b,c,z(116),lod,cuboid,TILE,WOOD,z(129))
    for i,c in enumerate([xmin,xmax]):cuboid(b,c-.06,c+.06,.52,2.81,z(387),z(129),GREY,'gallery / bounded end '+str(i))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output,META)
if __name__=='__main__':main()
