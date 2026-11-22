"""The southeast cut corner of the former Nanshi office, with its first Fangbang and Renmin bays."""
import json,math,sys
from pathlib import Path
from shapely.geometry import Polygon,Point,box as rect
from shapely.affinity import scale
from shapely.ops import unary_union
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
sys.path.insert(0,str(SOURCE.parents[1]/'hongkou-general-post-office/source/common'))
from photo_architecture import Facade,opening
from package_architectural_model import build
import bank_signage
import corner_stonework as stone
from bank_finishes import (PALETTE,WALL,LIMESTONE,DEEP,PALE,JOINT,OCHRE,FRAME,GLASS,RED,PLINTH,TOP)
D=json.loads((SOURCE/'dimensions.json').read_bytes())
ID='huangpu-nanshi-bank-southeast-corner'
META={'id':ID,'name':'人民路1号中国银行南市办事处旧址东南转角立面','viewer_page':'nanshi-bank-southeast-corner.html',
      'scope':'小东门旧址切角面与两侧首开间、弧形铁栏、童涵春堂四字、1783圆徽和小型透空柱亭。',
      'model_scope_zh':'东南转角及方浜中路、人民路各第一开间，按2015–2021实拍，底层为2021封板。其余两翼、隐蔽后屋及历史高钟楼另列。',
      'status':'photograph-derived-corner',
      'geometry_license':'MIT for original architectural geometry; CC BY-SA 4.0 for the photographed sign, monogram and associated relief.',
      'copyright':'Original architectural geometry: MIT. Gilt sign, monogram and date relief adapted from Legolas1024, Tonghanchun pharmacy, Renmin Rd, Shanghai.jpg (2015), CC BY-SA 4.0. Map data: OpenStreetMap contributors, ODbL 1.0. See extras.third_party_materials for the source, licence and modifications.',
      'third_party_materials':[{'title':'Tonghanchun pharmacy, Renmin Rd, Shanghai.jpg','author':'Legolas1024','date':'2015-02-21','license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/','url':'https://commons.wikimedia.org/wiki/File:Tonghanchun_pharmacy,_Renmin_Rd,_Shanghai.jpg','used_for':'gold sign strokes, round monogram and four year numerals','modifications':'cropped, masked, vectorized, repaired across wires, scaled and extruded into relief'}]}
def plaque(f,shape,depth,material,label):
    f.prism(shape,-.015,depth,material,label)

def center_front(f,lod):
    shop=rect(-.86,.15,.86,4.39)
    upper=scale(Point(0,10.90).buffer(1,quad_segs=10 if lod else 24),xfact=.48,yfact=.69,origin=(0,10.9))
    lower=rect(-.43,6.94,.43,8.57)
    # Xing Qianli photographed the wall after the letters were removed. The fascia has an oval
    # oculus, a rectangular window and a small hanging garland, each visible around the older gilt sign.
    f.wall(0,17.32,[shop,lower,upper],.44,WALL)
    stone.closed_shop(f,shop)
    f.prism(shop.buffer(.09,join_style=2).difference(shop),-.01,.10,DEEP,'street opening/stone reveal')
    f.box(0,.12,1.90,.24,.37,.02,PLINTH,'street threshold')
    f.prism(upper,-.382,-.345,GLASS,'oval oculus/dark glazing')
    plaque(f,upper.buffer(.13).difference(upper),.145,OCHRE,'oval oculus/gilt frame')
    plaque(f,upper.buffer(.185).difference(upper.buffer(.127)),.106,PALE,'oval oculus/pale outer lip')
    f.window(lower,1,2,FRAME,False,GLASS,'lower rectangular window')
    plaque(f,lower.buffer(.095,join_style=2).difference(lower),.098,PALE,'lower window/stone jamb')
    f.box(0,8.83,1.38,.36,.135,.045,LIMESTONE,'lower window/frieze')
    f.box(0,9.09,1.77,.15,.23,.083,OCHRE,'lower window/isolated cornice')
    cap=opening(0,9.11,1.62,.53,.45,10 if lod else 24)
    cap_in=opening(0,9.10,1.35,.42,.36,10 if lod else 24)
    f.prism(cap.difference(cap_in),.003,.16,OCHRE,'lower window/segmental pediment')
    f.prism(cap_in,-.012,.04,LIMESTONE,'lower window/tympanum')
    def swag(z,half,drop,label):
        pts=[f.point(u*half,z-drop*(1-u*u),.126)for u in [(-1+2*i/(9 if lod else 20))for i in range((9 if lod else 20)+1)]]
        f.builder.tube(pts,.032 if lod else .043,OCHRE,6 if lod else 10,f.label+'/'+label)
        for u in (-half,half):
            f.line((u,z,.13),(u*.95,z-.26,.13),.043,OCHRE,6,label+'/ribbon')
    swag(6.40,.46,.23,'swag under street-facing rectangular window')
    swag(11.61,.69,.12,'oculus head festoon')
    for x in (-.76,.76):
        f.box(x,11.28,.072,.60,.112,.08,OCHRE,'oculus/pendant')
        f.builder.lathe(f.point(x,0,.13)[:2],[(10.93,.018),(10.99,.060),(11.09,.065),(11.13,.045)],OCHRE,8 if lod else 14,f.label+'/oculus pendant drop')
    stone.ledges(f,central=True)
    stone.band(f,6.79,.10,.17,PALE,'belt below rectangular window')
    for side in (-1,1):
        stone.pilaster(f,side*(f.length/2-.32),.55,lod)
        f.box(side*(f.length/2-.13),15.42,.20,2.98,.115,.053,LIMESTONE,'corner attic bound')
        for shift in (-.082,0,.082):
            f.box(side*1.22+shift,15.48,.028,1.92,.042,.060,DEEP,'shallow vertical attic flute')
    for z,h,d,m in [(14.0,.62,.11,LIMESTONE),(14.38,.105,.16,OCHRE),(16.86,.08,.11,OCHRE),(17.14,.18,.16,PALE),(17.32,.12,.23,OCHRE),(17.46,.16,.27,PALE)]:
        stone.band(f,z,h,d,m,'attic moulding')
    rim=opening(0,14.63,2.38,2.36,.97,14 if lod else 30)
    inside=opening(0,14.60,2.19,2.20,.86,14 if lod else 30)
    plaque(f,rim.difference(inside),.110,OCHRE,'moulded arch above round monogram')
    bank_signage.add(f,lod)

def footprint():
    half=D['front_width']/2;dx,dy=D['street_edge_xy']
    a=[-half,0];b=[half,0]
    l=D['fangbang_first_bay'];r=D['renmin_first_bay']
    return [[-half-l*dx,l*dy],a,b,[half+r*dx,r*dy]]
def add_gallery_roof(builder,points):
    # Only the edge strip actually visible immediately behind the parapets is included.
    from shapely.geometry import LineString
    edge=LineString(points)
    stone_strip=edge.buffer(.64,single_sided=True,join_style='mitre')
    builder.plan_prism(stone_strip,14.97,15.07,TOP,'first bays/roof-edge strip')
    for i,index in enumerate([0,2]):
        a,b=points[index:index+2]
        dx=b[0]-a[0];dy=b[1]-a[1];ln=math.hypot(dx,dy)
        n=(-dy/ln,dx/ln)
        f=Facade(builder,a,b,'Fangbang first bay'if i==0 else'Renmin first bay')
        end=-ln/2 if i==0 else ln/2
        # Short physically closed cut ends beneath the roof edge prevent a view through the thin wall.
        start=f.point(end,.025,0);back=f.point(end,.025,-.42)
        builder.plan_prism(LineString([start[:2],back[:2]]).buffer(.032,cap_style='flat'),.02,15.41,DEEP,f.label+'/end return')

def pavilion(builder,lod):
    # The cornice is polygonal and flat below a series of semicircular raised shields.
    # The 2015 exposure shows sky between the slender columns and below the roof.
    cx,cy=.0,1.10
    def ring(rx,ry):
        return [(cx+rx*math.cos(math.pi/8+i*math.pi/4),cy+ry*math.sin(math.pi/8+i*math.pi/4))for i in range(8)]
    levels=[(1.42,1.05,17.36,17.55,TOP),(1.38,1.02,17.55,17.64,PALE),(1.52,1.12,18.86,19.00,DEEP),
            (1.59,1.18,19.00,19.10,OCHRE),(1.60,1.18,19.10,19.17,PALE)]
    for rx,ry,z1,z2,material in levels:
        builder.plan_prism(Polygon(ring(rx,ry)),z1,z2,material,'open crown/octagonal podium and eaves')
    columns=ring(1.27,.93)
    for x,y in columns:
        profile=[(17.62,.188),(17.70,.188),(17.74,.144),(17.79,.135),(18.62,.110),(18.68,.136),(18.73,.145),(18.78,.192),(18.86,.192)]
        builder.lathe((x,y),profile,LIMESTONE,10 if lod else 18,'open crown/tapered column with base and capital')
    loop=ring(1.55,1.14)
    for i,start in enumerate(loop):
        face=Facade(builder,start,loop[(i+1)%len(loop)],'open crown/scalloped parapet')
        cap=opening(0,19.12,face.length*.91,.31,.28,7 if lod else 15)
        face.prism(cap,-.105,.006,TOP,'individual segmental shield')
    for x,y in [(-1.41,.14),(1.41,.14),(-1.61,.90)]:
        builder.lathe((x,y),[(17.42,.18),(17.51,.18),(17.57,.125),(17.68,.09),(17.79,.17),(17.95,.22),(18.06,.17),(18.12,.10),(18.19,.09),(18.23,.025)],PALE,10 if lod else 18,'terrace/photographed stone urn')

def add_geometry(builder,lod):
    pts=footprint()
    faces=[Facade(builder,a,b,name)for a,b,name in zip(pts,pts[1:],['Fangbang first bay','Southeast chamfer','Renmin first bay'])]
    # Distances toward the adjacent streets were triangulated independently from the door centres.
    stone.return_bay(faces[0],faces[0].length/2-1.46,lod)
    center_front(faces[1],lod)
    stone.return_bay(faces[2],-faces[2].length/2+1.65,lod)
    add_gallery_roof(builder,pts)
    pavilion(builder,lod)

if __name__=='__main__':
    import argparse
    import os
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--out',type=Path)
    args,remaining=parser.parse_known_args()
    os.environ['NANSHI_BANK_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    if args.out is not None:
        sys.argv[1:]+=['--out',str(args.out)]
    build(SOURCE,META,PALETTE,add_geometry)
    # The common packager defaults to MIT for entirely original models. Record the relief exception.
    manifest=args.out/'manifest.json'
    authoritative=json.loads(manifest.read_bytes())
    authoritative['geometry_license']=META['geometry_license']
    authoritative['copyright']=META['copyright']
    temp=manifest.with_suffix('.licence-new')
    temp.write_text(json.dumps(authoritative,ensure_ascii=False,indent=2)+'\n')
    temp.replace(manifest)
