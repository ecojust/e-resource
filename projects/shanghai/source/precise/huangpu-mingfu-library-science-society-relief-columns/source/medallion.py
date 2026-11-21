"""Cast medallion reconstructed on a 400-unit grid from the rectified side photograph."""
from functools import lru_cache
from math import sin,cos,pi,radians
from pathlib import Path
from shapely import affinity
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union
from sign_lettering import lettering_shapes

FONT=Path(__file__).parent/'lettering/MingfuScienceMedal.otf'
BRASS='Raised warm brass';LIGHT='Polished edges';BLUE='Blue enamel field';AGED='Recessed aged brass'
PANEL=.455


def circle(x,y,r,segments):
    return Point(x,y).buffer(r,quad_segs=segments)


def stroke(points,width):
    return LineString(points).buffer(width/2,cap_style=2,join_style=1)


def arc(x,y,r,start,stop,n):
    return [(x+r*cos(radians(start+(stop-start)*i/n)),y+r*sin(radians(start+(stop-start)*i/n)))for i in range(n+1)]


@lru_cache(maxsize=32)
def letter(char,lod):
    shape=lettering_shapes(char,27,32,font=FONT)[0][1]
    return shape.simplify(.55 if lod else .19,preserve_topology=True)


def relief(face,centre_height,lod):
    """The blue field is recessed between positive circular lips and cast glyphs."""
    factor=PANEL/400
    def solid(shape,back,front,mat,name):
        # Positive sheet y points down over the reference photograph.
        mesh=affinity.affine_transform(shape,[factor,0,0,-factor,-PANEL/2,centre_height+PANEL/2])
        face.prism(mesh,back,front,mat,name)
    n=13 if lod else 32
    plate=box(0,0,400,400)
    solid(plate,-.008,0,AGED,'square cast plate')
    solid(plate.difference(plate.buffer(-4,join_style=2)),0,.005,BRASS,'square rim')
    outer=circle(201,202,191,n);inner=circle(201,202,154,n)
    solid(outer,0,.0018,BLUE,'blue circular enamel ground')
    for rad,width in [(192,4),(185,2),(157,4),(150,2)]:
        ring=circle(201,202,rad,n).difference(circle(201,202,rad-width,n))
        solid(ring,.001,.0055,BRASS,'four circular cast rims')
    for turn in range(4):
        decor=[]
        for angle in (7,26,45,64,83):
            a=radians(angle)
            decor.append(stroke([(3+28*cos(a),3+28*sin(a)),(3+70*cos(a),3+70*sin(a))],3.2))
        decor.append(stroke(arc(3,3,31,0,90,n//2+2),2.8))
        decor.append(circle(3,3,23,n//2+2).difference(circle(3,3,16,n//2+2)).intersection(plate))
        solid(affinity.rotate(unary_union(decor),turn*90,origin=(200,200)).difference(outer),.001,.006,
              LIGHT,'fan rays in plate corners')
    for text,angles,baseline in [('利用厚生',[-127,-147,-167,-187],-90),
                                 ('格物致知',[-52,-30,-9,12],-90),
                                 ('中國科學社',[49,69,90,111,131],90)]:
        for char,a in zip(text,angles):
            x=201+172*cos(radians(a));y=202+172*sin(radians(a))
            # Turn upright glyphs down into pixel space, then align to the circular band.
            glyph=affinity.scale(letter(char,lod),yfact=-1,origin=(0,0))
            glyph=affinity.translate(affinity.rotate(glyph,a-baseline,origin=(0,0)),x,y)
            solid(glyph,.0019,.0067,LIGHT,'cast inscription '+char)
    for x,y in [(74,292),(329,294)]:
        star=[]
        for k in range(10):
            a=-pi/2+k*pi/5;r=13 if k%2==0 else 5.6;star.append((x+r*cos(a),y+r*sin(a)))
        solid(Polygon(star),.002,.007,BRASS,'five pointed separator stars')
    # Celestial fan and mountain silhouettes above the telescope.
    sun=(211,3)
    rays=[stroke([sun,(211+85*cos(radians(t)),3+81*sin(radians(t)))],2.6)for t in range(41,145,12)]
    solid(unary_union(rays).intersection(inner),.002,.0053,BRASS,'rays over mountain crests')
    # The upper fan breaks the circle at twelve o'clock and rests on the skyline.
    crown=Polygon([(153,6),(266,6),(257,32),(248,54),(232,72),(220,63),
                   (209,76),(194,59),(180,65),(163,54)])
    solid(crown,.0051,.0096,BRASS,'rising sun in upper ring')
    fan=[]
    for x,y in [(164,50),(180,62),(194,58),(209,73),(221,60),(233,68),(249,46)]:
        fan.append(stroke([(209+(x-209)*.21,12),(x,y)],2.7))
    solid(unary_union(fan).intersection(crown),.0096,.0125,LIGHT,'sunburst fluting')
    solid(circle(210,3,21,n).intersection(plate),.0098,.014,BRASS,'upper sun boss')
    solid(circle(210,3,17,n).difference(circle(210,3,13,n)).intersection(plate),
          .014,.0158,LIGHT,'upper sun boss lip')
    front=[(50,142),(86,123),(120,124),(150,98),(161,107),(179,98),(193,115),
           (213,104),(224,109),(251,79),(262,84),(278,71),(298,95),(323,118),(347,136)]
    foothills=[(65,150),(120,129),(142,117),(155,129),(184,111),(209,115),(225,117),(262,101),
               (280,110),(298,103),(329,127)]
    silhouette=Polygon([*front,(344,143),(299,109),(273,91),(249,101),(222,126),
                        (195,124),(175,112),(156,123),(148,116),(122,134),(88,132)])
    solid(silhouette.buffer(0).intersection(inner),.002,.0057,BRASS,'faceted mountain slopes')
    solid(stroke(front,5).intersection(inner),.0057,.0078,LIGHT,'distant alpine ridge')
    solid(stroke(foothills,4).intersection(inner),.003,.0068,LIGHT,'foreground ridgeline')
    # The two squared ends and central table leave the scale pans legible.
    for x in (91,272):
        solid(box(x,165,x+58,264),.002,.0078,BRASS,'lectern side support')
        solid(box(x-3,159,x+62,176),.0075,.010,LIGHT,'lectern projecting top')
        solid(box(x-3,255,x+62,266),.0075,.0095,LIGHT,'lectern foot')
    solid(stroke([(124,162),(176,148),(230,148),(277,158)],8.3),.0025,.0089,BRASS,'curved table top')
    # Telescope tube, short collar, pivot, three individual legs and two open spaces.
    for line,width,depth in [
        ([(166,138),(226,88)],8,.013), ([(153,139),(169,127)],11,.0125),
        ([(220,85),(226,94)],10,.014), ([(182,130),(155,239)],4.5,.0105),
        ([(183,133),(184,224)],3.8,.0095), ([(187,132),(208,225)],4.8,.012)]:
        solid(stroke(line,width),.003,depth,BRASS,'telescope tube and tripod')
    solid(circle(184,130,8,n//2+1),.007,.015,LIGHT,'telescope axis pin')
    solid(stroke([(210,188),(240,192),(262,185)],4.5),.0045,.0098,BRASS,'balance beam')
    solid(stroke([(236,191),(237,263)],5.5),.003,.010,BRASS,'balance central post')
    solid(stroke(arc(237,244,24,27,153,n+2),6),.004,.0103,LIGHT,'curved balance base')
    for x in (216,254):
        y=190 if x==216 else 188
        solid(unary_union([stroke([(x,y),(x-8,223)],2.4),stroke([(x,y),(x+8,223)],2.4)]),
              .004,.008,BRASS,'suspended scale rods')
        bowl=Polygon([(x-10,223),(x+10,223),(x+8,230),(x+4,234),(x,235),(x-6,233)])
        solid(bowl,.004,.011,LIGHT,'hanging scale pans')
    left=Polygon([(163,281),(177,277),(193,278),(196,303),(181,299),(169,301)])
    right=Polygon([(194,278),(208,275),(222,279),(225,301),(208,298),(196,303)])
    solid(left.union(right),.002,.008,BRASS,'open book beneath telescope')
    solid(stroke([(194,279),(196,300)],1.9),.008,.0103,LIGHT,'book centre crease')
    sheets=unary_union([stroke([(167,295),(178,292),(192,295)],1.3),
                        stroke([(198,296),(208,292),(222,294)],1.2)])
    solid(sheets,.008,.0094,LIGHT,'open page edges')

