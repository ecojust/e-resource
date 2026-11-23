"""Build the portions of the first visible east-row end recorded by Livelikerw in 2014."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
ID='changning-huxi-villas-east-row-gable'
W='Huxi | light mineral render';B='Huxi | red facing brick';T='Huxi | red roof tile';S='Huxi | grey cement';J='Huxi | green steel';G='Huxi | grey-green glazing';F='Huxi | light spandrel';D='Huxi | white rainwater pipe';M='Huxi | dark soffit';H='Huxi | shadow';A='Huxi | condenser casing'
COLORS={W:[.68,.632,.574],B:[.40,.185,.12],T:[.34,.154,.106],S:[.41,.403,.38],J:[.13,.23,.215],G:[.255,.41,.415],F:[.62,.65,.65],D:[.78,.76,.725],M:[.18,.138,.11],H:[.064,.06,.055],A:[.55,.535,.51]}
PALETTE={k:dict(color=v,roughness=.88)for k,v in COLORS.items()}
PALETTE[G]['roughness']=.28
META=dict(model_id=ID,id=ID,name='沪西别墅东侧临弄山墙与跨层钢窗',heritage_id='sh-historic-b3-106',official_id='3M008',viewer_page='huxi-villas-east-row-gable.html',geometry_license='MIT',texture_license='MIT',photos_embedded=False,scope='最近一处可见的西山墙及南向相邻端开间。南数第一或第二排，具体门牌仍待可读同院照片。',photo_source='Livelikerw, Hu-Xi Bieshu Shanghai, 2014-02-08, CC BY-SA 3.0, https://commons.wikimedia.org/wiki/File:Hu-Xi_Bieshu_Shanghai.JPG')
def block(b,name,material,x0,x1,y0,y1,z0,z1):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],material,label=name)
def west(b,name,shape,outer,inner,material):
    b.prism(shape,outer,inner,lambda u,z,d:(d,u,z),material,name)
def south(b,name,shape,outer,inner,material):
    b.prism(shape,-inner,-outer,lambda u,z,d:(u,-d,z),material,name)
def roof_strip(b,name,y0,y1,z0,z1,x0,x1,material,thickness):
    corners=np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z1],[x0,y1,z1]])
    b.add(np.r_[corners,corners-[0,0,thickness]],[[0,1,2,3],[7,6,5,4],[4,5,1,0],[5,6,2,1],[6,7,3,2],[7,4,0,3]],material,name)
def west_aperture(b,name,u0,u1,z0,z1,lod):
    rim=box(u0,z0,u1,z1).difference(box(u0+.046,z0+.045,u1-.046,z1-.045))
    west(b,name+'/recessed steel window frame',rim,.105,.145,J)
    west(b,name+'/glazing',box(u0+.046,z0+.045,u1-.046,z1-.045),.147,.165,G)
    for i in range(1,3):
        k=z0+(z1-z0)*i/3;west(b,name+'/horizontal sash '+str(i),box(u0+.046,k-.013,u1-.046,k+.013),.111,.140,J)
    if not lod:
        west(b,name+'/bottom lip',box(u0-.025,z0-.05,u1+.025,z0),-.028,.17,S)
def south_light(b,name,u0,u1,z0,z1,cols,rows,lod):
    contour=box(u0,z0,u1,z1).difference(box(u0+.05,z0+.04,u1-.05,z1-.04))
    south(b,name+'/steel casing',contour,.053,.094,J)
    south(b,name+'/glass',box(u0+.05,z0+.04,u1-.05,z1-.04),.101,.122,G)
    for i in range(1,cols):
        x=u0+(u1-u0)*i/cols;south(b,name+'/stile '+str(i),box(x-.015,z0+.04,x+.015,z1-.04),.053,.093,J)
    for j in range(1,rows):
        z=z0+(z1-z0)*j/rows;south(b,name+'/rail '+str(j),box(u0+.05,z-.012,u1-.05,z+.012),.047,.082,J)
def add_building(b,lod=False):
    # The west gable stops at the rear return whose outer edge disappears into foliage.
    low=box(3.88,4.50,4.40,5.58);upper=box(3.56,7.65,4.12,8.67)
    vent=Polygon([(3.69,10.77),(3.94,10.77),(3.85,10.56)])
    panel=Polygon([(0,2.95),(6.27,2.95),(6.27,10.24),(3.92,11.83),(.0,10.28)])
    west(b,'lane end/pierced rendered gable',panel.difference(unary_union([low,upper,vent])),0,.19,W)
    west(b,'lane end/brick base',box(0,0,6.27,2.95),0,.19,B)
    for name,shape in [('lower narrow light',low),('upper narrow light',upper)]:
        u0,z0,u1,z1=shape.bounds;west_aperture(b,name,u0,u1,z0,z1,lod)
    west(b,'lane end/small triangular ventilation passage',vent,.17,.19,H)
    ridge=Polygon([(-.18,10.23),(3.92,11.83),(6.43,10.17),(6.43,10.32),(3.93,11.98),(-.18,10.39)])
    west(b,'lane end/projecting cement coping',ridge,-.095,.26,S)
    # An uninterrupted solid grey spandrel separates the lights in this brick enclosure.
    windows=box(1.13,4.18,2.97,8.47)
    south(b,'south bay/rendered front wall',box(.19,2.95,4.58,10.04).difference(windows),0,.19,W)
    south(b,'south bay/lower red brick',box(.19,0,4.58,2.95),0,.19,B)
    trim=box(1.01,4.05,3.09,8.59).difference(windows)
    south(b,'south bay/continuous brick reveal',trim,-.049,.004,B)
    south_light(b,'upper green steel sash',1.13,2.97,6.92,8.47,4,4,lod)
    south(b,'south bay/opaque panel between windows',box(1.13,5.33,2.97,6.92),.048,.14,F)
    south_light(b,'lower green steel sash',1.13,2.97,4.18,5.33,4,3,lod)
    roof_strip(b,'front plane/visible clay tiles',-.22,3.92,10.03,11.63,.19,4.63,T,.13)
    roof_strip(b,'rear plane/visible clay tiles',3.92,6.44,11.63,10.02,.19,4.63,T,.13)
    block(b,'front eave/wood fascia',M,.19,4.63,-.27,-.20,9.86,10.01)
    for i,u in enumerate(np.arange(.42,4.63,.42)):
        block(b,'front eave/exposed rafter tail '+str(i+1),M,u-.045,u+.045,-.246,.11,9.76,9.89)
    if not lod:
        for j in range(1,12):
            f=j/12;y=-.22+4.14*f;z=10.03+1.60*f
            b.tube([(.19,y,z+.008),(4.63,y,z+.008)],.014,T,6,'south roof/tile course '+str(j))
    rails=[(-.04,-.27,9.93),(-.04,-.27,9.62),(-.04,-.095,9.47),(-.04,-.095,2.78),(-.05,-.095,2.73),(-.39,-.095,2.42),(-.39,-.095,.08)]
    b.tube(rails,.082,D,8 if lod else 12,'front corner/offset white downpipe')
    b.tube([(.03,-.29,10.03),(4.63,-.29,10.03)],.061,D,8 if lod else 12,'front eave/white gutter')
    # The offset return has its own window, sill bands and flat apron. It is distinct from the next row.
    y0,y1=6.27,7.95
    west(b,'rear return/short upper wall',box(y0,6.32,y1,8.89).difference(box(6.49,7.13,6.88,8.08)),.39,.57,W)
    west(b,'rear return/insert glazing',box(6.49,7.13,6.88,8.08),.50,.545,G)
    for j,z in enumerate([6.32,6.63,6.87]):
        block(b,'rear return/projecting sill band '+str(j+1),S,.11,.58,y0,y1,z,z+.080)
    west(b,'rear return/lower adjoining wall',box(y0,0,y1,6.32),.40,.56,W)
    roof_strip(b,'rear return/shallow eave',y0,y1,9.0,8.71,.18,1.12,S,.105)
    for index,(y,z) in enumerate([(4.17,7.33),(4.41,4.30)]):
        block(b,'west condenser '+str(index+1)+'/case',A,-.40,-.07,y-.42,y+.42,z-.235,z+.235)
        for n in range(4 if lod else 9):
            yy=y-.33+n*(.66/(3 if lod else 8));block(b,'west condenser '+str(index+1)+'/front slat '+str(n),H,-.409,-.40,yy-.012,yy+.012,z-.17,z+.17)
        for k in (-.29,.29):
            block(b,'west condenser '+str(index+1)+'/bracket '+str(k),M,-.47,.03,y+k-.03,y+k+.03,z-.29,z-.245)
    # Facing the lane, the separate garden wall carries a projecting grey cap.
    block(b,'small garden/red brick boundary wall',B,-.38,4.58,-.55,-.38,0,1.81)
    block(b,'small garden/roughcast top band',W,-.40,4.60,-.58,-.35,1.81,2.07)
    block(b,'small garden/grey top coping',S,-.45,4.60,-.64,-.32,2.07,2.18)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');args=p.parse_args()
    b=Builder(PALETTE);add_building(b,args.lod);result=b.save(args.output,META);print(result['sha256'],result['parts'],result['triangles'])
if __name__=='__main__':main()
