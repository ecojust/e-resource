"""Rebuild Xinhua Village No. 11's four-bay garden front in its open-gallery phase."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from photo_architecture import Builder as GltfBuilder
from crown_builder import CrownBuilder
import garden_finishes as finish
ID='changning-xinhuacun-11-garden-front'
META=dict(id=ID,model_id=ID,name='新华村11号楼四跨院廊与坡屋面',heritage_id='sh-historic-b3-100',official_id='3M002',address='愚园路1320号（又称1320弄）11号楼',viewer_page='xinhuacun-11-garden-front.html',source='https://www.shcn.gov.cn/col7698/20211206/1118301.html',geometry_license='MIT',texture_license='MIT',photos_embedded=False,scope='Four-bay garden elevation of House 11 in its 2014 open-gallery state, paired flights to the terrace, four shed dormers and the visible hipped roof pitch. Only exterior parts of House 11 are included.',camera_views=json.loads((HERE/'cameras.json').read_bytes()))
BRICK=finish.BRICK;PEBBLE=finish.PEBBLE
STONE='Xinhua 11 | weathered pale stone';TILE='Xinhua 11 | aged terracotta tiles';WOOD='Xinhua 11 | painted dark timber';PLASTER='Xinhua 11 | pale roughcast';GLASS='Xinhua 11 | grey window glass';SHADE='Xinhua 11 | interior shade';METAL='Xinhua 11 | dark rainwater metal'
PALETTE={STONE:dict(color=[.55,.52,.46],roughness=.87),TILE:dict(color=[.45,.19,.13],roughness=.83),WOOD:dict(color=[.125,.145,.128],roughness=.71),PLASTER:dict(color=[.74,.73,.69],roughness=.9),GLASS:dict(color=[.16,.21,.20],alpha=.67,roughness=.28),SHADE:dict(color=[.085,.077,.070]),METAL:dict(color=[.075,.080,.075],roughness=.63),**finish.PALETTE}
fit=json.loads((HERE.parent/'measurements/garden-registration.json').read_bytes());p=fit['parameters'];pitch=fit['pitch']
E=p['eave'];U=p['upper_rail'];F=p['upper_soffit'];L=p['lower_rail'];D=p['platform'];AX=p['stair_axis'];ST=p['stair_y']
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in finish.STEMS:finish.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        GltfBuilder.save(self,path,metadata);return finish.writer.embed_normals(path)
def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    if min(x1-x0,y1-y0,z1-z0)<1e-5:raise ValueError((label,(x0,x1,y0,y1,z0,z1)))
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def front(b,poly,y0,y1,mat,label):
    b.prism(poly,-y1,-y0,lambda x,z,t:(x,-t,z),mat,label)
def skin(b,points,thick,mat,label):
    winding=sum(a[0]*q[1]-q[0]*a[1]for a,q in zip(points,points[1:]+points[:1]));pts=points if winding>0 else list(reversed(points))
    n=len(pts);low=[(x,y,z-thick)for x,y,z in pts]
    b.add(low+pts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)],mat,label)
def window(b,x0,x1,z0,z1,y,cols,rows,label,lod):
    t=.060
    for x in [x0,x1]:block(b,x-t,x+t,y-.06,y+.07,z0,z1,WOOD,label+' / jamb')
    for z in [z0,z1]:block(b,x0,x1,y-.06,y+.07,z-t,z+t,WOOD,label+' / frame')
    for j in range(1,cols):
        x=x0+(x1-x0)*j/cols;w=.042 if j%2==0 else .024
        block(b,x-w,x+w,y-.043,y+.025,z0+t,z1-t,WOOD,label+' / glazing bar '+str(j))
    for j in range(1,rows):
        z=z0+(z1-z0)*j/rows;w=.025
        if lod and j%2:continue
        block(b,x0+t,x1-t,y-.034,y+.022,z-w,z+w,WOOD,label+' / horizontal bar '+str(j))
    block(b,x0+t,x1-t,y+.071,y+.092,z0+t,z1-t,GLASS,label+' / glazing')
    block(b,x0-.02,x1+.02,y+.22,y+.29,z0-.01,z1+.01,SHADE,label+' / shade behind glass')
def galleries(b,lod):
    for j in range(5):
        x=(j-2)*pitch;name='gallery pier '+str(j+1);hw=.325
        # Rusticated square brick courses and the shallow bands hold both real gallery floors.
        block(b,x-hw,x+hw,0,.50,.06,E-.42,BRICK,name+' / brick shaft')
        for z in np.arange(D+.15,E-.45,.43):
            block(b,x-hw-.012,x+hw+.012,-.026,.515,z,z+.055,BRICK,name+' / proud brick course')
        for k,(dz,w) in enumerate([(0,.37),(.10,.41),(.19,.45)]):
            block(b,x-w,x+w,-.07-dz*.26,.58,E-.53+dz,E-.43+dz,STONE,name+' / projecting capital '+str(k))
        # Curved timber/stone brackets visible beneath the roof at each side of a shaft.
        for side in (-1,1):
            yzs=[(-.27,E-.08),(.51,E-.08),(.51,E-.84),(.31,E-.84),(.25,E-.62),(.15,E-.42),(-.02,E-.27),(-.27,E-.22)]
            x1=x+side*.19;b.prism(Polygon(yzs),x1-.065,x1+.065,lambda y,z,v:(v,y,z),WOOD,name+' / eave bracket')
    for deck,top,base in [('lower',L,D),('upper',U,F+.19)]:
        block(b,-10.34,10.34,-.015,2.47,base-.17,base+.025,STONE,deck+' / floor slab')
        for j in range(4):
            x0=(j-2)*pitch+.325;x1=x0+pitch-.65;name=deck+' bay '+str(j+1);n=14
            if deck=='upper':
                block(b,x0,x1,.012,.35,F,top-.53,STONE,name+' / deep spandrel')
            z0=top-.42
            block(b,x0,x1,.04,.32,base,top-.43,STONE if deck=='upper' else BRICK,name+' / solid parapet base')
            block(b,x0,x1,-.07,.40,top-.11,top+.015,STONE,name+' / stone coping')
            for i in range(n+1):
                x=x0+(x1-x0)*i/n
                a=max(x-.076,x0);c=min(x+.076,x1)
                block(b,a,c,.035,.28,z0-.02,top-.10,STONE,name+' / pierced balustrade '+str(i+1))
    # Recessed wall and double windows remain visible between the five piers.
    for k,(floor,ceiling) in enumerate([(D,F-.02),(F+.2,E-.12)],1):
        holes=[];y=2.42
        for j in range(4):
            cx=(j-1.5)*pitch
            for h,s in enumerate((-.95,.95)):
                x=cx+s;z0=floor+.48;z1=ceiling-.43
                holes.append(box(x-.59,z0,x+.59,z1));window(b,x-.59,x+.59,z0,z1,y+.10,2,3,f'gallery back level {k} bay {j+1} sash {h+1}',lod)
        front(b,box(-10.27,floor,10.27,ceiling).difference(unary_union(holes)),y,y+.30,PLASTER,'gallery back / pierced level '+str(k))
    # The near stair station shows a lower side-wall window beneath this left corner.
    for side in (-1,1):
        x=side*10.19;upper_y=2.83
        def section(poly,front_x,back_x,material,label):
            b.prism(poly,min(front_x,back_x),max(front_x,back_x),lambda y,z,d:(d,y,z),material,label)
        if side<0:
            opening=box(1.12,.66,1.96,1.79)
            section(box(.34,.03,upper_y,D).difference(opening),x-.13,x+.08,BRICK,'left return / pierced plinth')
            section(opening,x+.08,x+.105,GLASS,'left return / basement glazing')
            section(opening,x+.27,x+.32,SHADE,'left return / basement shade')
            for z in [.63,1.82]:
                block(b,x-.19,x+.13,1.02,2.06,z,z+.085,STONE,'left return / basement sill or lintel')
        else:
            section(box(.34,.03,upper_y,D),x-.08,x+.13,BRICK,'right return / plinth enclosure')
        for k,(floor,top) in enumerate([(D,L),(F+.20,U)]):
            holes=[box(.63+i*.34,top-.42,.79+i*.34,top-.13) for i in range(6)]
            section(box(.36,floor,upper_y,top).difference(unary_union(holes)),x-.13,x+.12,STONE,'end return '+str(side)+' / pierced rail '+str(k+1))
            block(b,x-.19,x+.17,.32,upper_y+.06,top-.08,top+.04,STONE,'end return / rail coping')
    block(b,-10.19,10.19,.37,.57,.03,D-.13,BRICK,'plinth / red facing')
    block(b,-10.17,10.17,2.60,2.81,.04,D-.13,BRICK,'plinth / short inner enclosure')
    block(b,-10.37,10.37,-.28,2.83,E-.165,E+.025,PLASTER,'upper gallery / continuous shaded plaster soffit')
    for z,front_edge in [(E-.16,-.30),(E-.085,-.34)]:
        block(b,-10.40,10.40,front_edge,.29,z,z+.052,WOOD,'upper eave / moulded dark cornice')
def terrace(b,lod):
    yr=ST+.30;y0=ST
    holes=[]
    for x in [-3.60,-1.90,2.0,3.58]:
        holes.append(box(x-.21,.53,x+.21,1.73));window(b,x-.21,x+.21,.53,1.73,y0+.11,1,2,'raised terrace / narrow plinth opening',lod)
        for z in [.48,1.75]:block(b,x-.29,x+.29,y0-.065,yr,z,z+.09,STONE,'plinth opening / hood or sill')
    front(b,box(-AX,0,AX,D).difference(unary_union(holes)),y0,yr,PEBBLE,'terrace / pierced pebble-dash face')
    block(b,-AX,AX,y0-.025,.20,D-.065,D+.025,STONE,'terrace / upper landing')
    count=12;outer=9.66;length=outer-AX
    for side in [-1,1]:
        tag=('left' if side<0 else 'right')+' exterior stair'
        for i in range(count):
            a=outer-length*i/count;c=outer-length*(i+1)/count;lo,hi=sorted([a*side,c*side])
            block(b,lo,hi,y0,.08,0,D*(i+1)/count,STONE,tag+' / individual tread '+str(i+1))
        def to_xz(r,z):return (side*r,z)
        poly=Polygon([to_xz(AX,0),to_xz(outer,0),to_xz(outer,.14),to_xz(AX,D)])
        front(b,poly,y0-.18,y0-.035,PEBBLE,tag+' / sloped cheek')
        # The 2014 Commons image shows pierced stone cheeks. Gao's separate near photograph has an iron railing here.
        for i in range(4):
            a=outer-length*i/4;c=outer-length*(i+1)/4;za=(outer-a)*D/length;zc=(outer-c)*D/length
            shape=Polygon([to_xz(a,za+.05),to_xz(c,zc+.05),to_xz(c,zc+.76),to_xz(a,za+.76)])
            e=a+(c-a)*.19;f=a+(c-a)*.81;ze=(outer-e)*D/length;zf=(outer-f)*D/length
            slot=Polygon([to_xz(e,ze+.30),to_xz(f,zf+.30),to_xz(f,zf+.51),to_xz(e,ze+.51)])
            front(b,shape.difference(slot),y0-.17,y0+.08,STONE,tag+' / pierced sloping outer rail '+str(i))
            front(b,Polygon([to_xz(a,za+.76),to_xz(c,zc+.76),to_xz(c,zc+.87),to_xz(a,za+.87)]),y0-.205,y0+.12,STONE,tag+' / sloping coping')
        for i in (0,2,4):
            a=outer-length*i/4;z=(outer-a)*D/length;cx=a*side
            block(b,cx-.14,cx+.14,y0-.23,y0+.12,z,z+.92,STONE,tag+' / square newel')
            block(b,cx-.18,cx+.18,y0-.27,y0+.16,z+.90,z+.99,STONE,tag+' / step cap')
    # Eight square/oblong apertures and intermediate square posts run across the upper landing.
    x0,x1=-AX,AX;n=10;holes=[]
    for i in range(n):
        x=x0+(i+.5)*(x1-x0)/n;holes.append(box(x-.19,D+.35,x+.19,D+.55))
    front(b,box(x0,D+.025,x1,L-.07).difference(unary_union(holes)),y0-.19,y0+.07,STONE,'landing / perforated straight parapet')
    block(b,x0-.04,x1+.04,y0-.23,y0+.11,L-.10,L+.045,STONE,'landing / continuous coping')
def roofs(b,lod):
    front_y=-.34;ridge_y=p['ridge_y'];ridge=p['ridge'];x0,x1=-10.73,10.73;rise=ridge-E
    def height(y):return E+(y-front_y)*rise/(ridge_y-front_y)
    # Shallow hips begin beyond the two end dormers. The back slope lies outside the measured study.
    outline=Polygon([(x0,front_y),(x1,front_y),(x1-3.26,ridge_y),(x0+3.26,ridge_y)])
    centers=[(j-1.5)*pitch for j in range(4)];yf=p['dormer_y'];sill=p['dormer_sill'];head=p['dormer_head']
    dormer_width=2.90;yb=min(ridge_y-.45,front_y+(head-E+.28)*(ridge_y-front_y)/rise)
    cut_y=min(yf-.12,front_y+(sill-E-.11)*(ridge_y-front_y)/rise)
    cuts=[box(cx-dormer_width/2,cut_y,cx+dormer_width/2,yb-.06)for cx in centers]
    slope=outline.difference(unary_union(cuts))
    # XY plan extruded vertically with the exact principal plane evaluated at each vertex.
    b.prism(slope,-.115,0,lambda x,y,t:(x,y,height(y)+t),TILE,'roof / continuous front hip pitch with four cutouts')
    for side in [-1,1]:
        x=side*10.73;top=x-side*3.26
        skin(b,[(x,front_y,E),(x,ridge_y,E),(top,ridge_y,ridge)],.115,TILE,'roof / visible hip side')
        b.tube([(x,front_y,E+.025),(top,ridge_y,ridge+.03)],.063,TILE,7,'roof / diagonal hip roll')
    block(b,x0,x1,front_y-.06,.37,E-.137,E+.02,WOOD,'eave / dark fascia')
    b.tube([(x0,front_y-.082,E+.04),(x1,front_y-.082,E+.04)],.075,METAL,9,'eave / gutter')
    b.tube([(x0+3.26,ridge_y,ridge+.026),(x1-3.26,ridge_y,ridge+.026)],.080,TILE,9,'roof / original ridge')
    # Overlapping tiles are visible as horizontal rows, interrupted by the four dormers.
    from shapely.geometry import LineString
    for n,y in enumerate(np.arange(front_y+.19,ridge_y,.23 if not lod else .45)):
        line=slope.intersection(LineString([(x0-1,y),(x1+1,y)]))
        for seg in getattr(line,'geoms',[line]):
            if seg.geom_type!='LineString' or seg.length<.05:continue
            a,c=seg.bounds[0],seg.bounds[2]
            b.tube([(a,y,height(y)+.011),(c,y,height(y)+.011)],.026,TILE,6,'roof / tile overlap '+str(n+1))
    for j,cx in enumerate(centers):
        tag='shed dormer '+str(j+1);lo,hi=cx-dormer_width/2,cx+dormer_width/2
        xx=hi-lo
        # Four four-light casements sit inside a projecting green timber surround.
        window(b,lo+.09,hi-.09,sill+.05,head-.07,yf+.04,8,4,tag,lod)
        block(b,lo-.06,hi+.06,yf-.06,yf+.21,sill-.12,sill+.053,WOOD,tag+' / lead sill')
        for side,x in [(-1,lo),(1,hi)]:
            prof=Polygon([(yf,min(sill-.07,height(yf)-.10)),(yb,min(head+.10,height(yb)-.10)),(yb,head+.22),(yf,head+.04)])
            if prof.is_valid:b.prism(prof,x-.08,x+.08,lambda y,z,d:(d,y,z),WOOD,tag+' / tapered side cheek')
        skin(b,[(lo-.15,yf-.19,head+.13),(hi+.15,yf-.19,head+.13),(hi+.17,yb+.24,head+.35),(lo-.17,yb+.24,head+.35)],.12,WOOD,tag+' / shallow pitch and fascia')
        skin(b,[(lo-.025,cut_y-.035,height(cut_y)-.005),(hi+.025,cut_y-.035,height(cut_y)-.005),(hi+.025,yf+.06,sill+.015),(lo-.025,yf+.06,sill+.015)],.058,METAL,tag+' / flashed apron')
    for j,cx in enumerate([-8.67,0,8.67]):
        z=ridge+(1.68 if j==1 else 1.02);low=ridge-.40 if j==1 else E+.63
        block(b,cx-.262,cx+.262,ridge_y-.30,ridge_y+.30,low,z-.10,BRICK,'roof / chimney '+str(j+1))
        block(b,cx-.296,cx+.296,ridge_y-.344,ridge_y+.344,z-.14,z,BRICK,'chimney / cap '+str(j+1))
    for x in [-9.73,.035,10.06]:
        b.tube([(x,-.35,E-.02),(x,-.25,E-.29),(x,-.115,E-.54),(x,-.105,.18)],.063,METAL,8,'gallery / downpipe')
def add_building(b,lod=False):
    galleries(b,lod);terrace(b,lod);roofs(b,lod)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output,META)
if __name__=='__main__':main()
