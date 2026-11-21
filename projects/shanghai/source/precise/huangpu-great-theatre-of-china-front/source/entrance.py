"""China Theatre's central Niuzhuang Road entrance after the 2018 conservation work."""
from math import cos, pi, sin
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from sign_lettering import lettering_shapes
from brick import wall_uv
from repeat import repeat_only_texture

HERE=Path(__file__).parent
BRICK='dark red facing brick'
BASE='course jointed grey stone'
PALE='pale carved window stone'
GLASS='recessed amber glazing'
FRAME='dark painted metal'
DOOR='warm timber door leaves'
ROOF='muted grey spire facing'
REAR='neutral rear cut'
PALETTE={BRICK:{'color':[1,1,1],'texture':str(HERE/'brick.png'),'roughness':.91},
         BASE:{'color':[.54,.54,.51],'roughness':.86},PALE:{'color':[.72,.69,.61],'roughness':.82},
         GLASS:{'color':[.21,.25,.24],'metallic':.18,'roughness':.28},
         FRAME:{'color':[.10,.096,.084],'metallic':.37,'roughness':.45},
         DOOR:{'color':[.42,.25,.12],'roughness':.67},ROOF:{'color':[.40,.41,.40],'metallic':.2,'roughness':.71},
         REAR:{'color':[.45,.44,.41],'roughness':.92}}
HALF=5.4
TOWERS=(-3.50,3.50)
CENTRE=(-1.58,0,1.58)

def project(x,z,d):return (x,-d,z)

def plate(b,shape,back,front,material,name):
    if not shape.is_empty:b.prism(shape,back,front,project,material,name)

def rect(b,left,bottom,right,top,back,front,material,name):
    plate(b,box(left,bottom,right,top),back,front,material,name)

def loop(b,shape,thick,back,front,material,name):
    plate(b,shape.buffer(thick,join_style=2).difference(shape),back,front,material,name)

def bay(b,x,z,width,height,back,lod,name):
    hole=box(x-width/2,z,x+width/2,z+height)
    plate(b,hole,back-.036,back,GLASS,name+' panes')
    sash=hole.difference(hole.buffer(-.047,join_style=2))
    if width>.75:
        sash=sash.union(box(x-.026,z,x+.026,z+height))
    for f in ([.72] if lod else [.35,.72]):
        sash=sash.union(box(x-width/2,z+height*f-.026,x+width/2,z+height*f+.026))
    plate(b,sash,back+.024,back+.095,FRAME,name+' sash')
    return hole

def pediment(b,x,z,r,lod):
    span=10 if lod else 20
    outline=Polygon([(x+r*cos(pi*i/span),z+r*.64*sin(pi*i/span)) for i in range(span+1)])
    inset=affinity.translate(affinity.scale(outline,.78,.62,origin=(x,z)),yoff=.026)
    plate(b,outline,.12,.23,PALE,'Segmental hood backing')
    plate(b,outline.difference(inset),.23,.32,PALE,'Raised hood rim')
    rect(b,x-r-.035,z-.07,x+r+.035,z+.02,.08,.36,PALE,'Projecting hood sill')

def crown(b,x,lod):
    for z,width,h in [(17.40,1.95,.16),(17.56,2.10,.14),(17.70,1.91,.16),(17.86,1.73,.52),(18.38,1.89,.14)]:
        b.box((x,.27,z+h/2),(width,1.53+(width-1.73),h),PALE,label='Tower cap courses')
    base=[(x-.86,-.62),(x+.86,-.62),(x+.86,1.16),(x-.86,1.16)]
    cap=[(x-.095,.175),(x+.095,.175),(x+.095,.365),(x-.095,.365)]
    xyz=[(u,v,18.52) for u,v in base]+[(u,v,22.68) for u,v in cap]
    b.add(xyz,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],ROOF,'Restored pyramidal spires')
    for a,q in zip(xyz[:4],xyz[4:]):
        b.tube([a,q],.027 if lod else .035,FRAME,5 if lod else 8,'Spire edge strips')
    b.lathe((x,.27),[(22.65,.11),(22.76,.15),(22.91,.12),(23.08,.08),(23.20,.012)],ROOF,8 if lod else 16,'Spire finials')

def type_on_front(b,text,font,width,height,z,d,lod,name):
    paths=lettering_shapes(text,width,height,font=HERE/font)
    for glyph,outline in paths:
        outline=affinity.translate(outline,yoff=z).simplify(.011 if lod else .003,preserve_topology=True)
        plate(b,outline,d,d+.046,FRAME,name)

def add_building(b,lod):
    repeat_only_texture(b,'brick.png')
    entrance=box(-2.65,.025,2.65,3.43)
    holes=[entrance]
    for x in (-4.25,4.25):
        holes.append(bay(b,x,.72, .72,2.12,-.31,lod,'Ground side window'))
    base=box(-HALF,0,HALF,5.0).difference(unary_union(holes))
    plate(b,base,-1.16,0,BASE,'Ground entrance ashlar')
    for i in range(1,10):
        plate(b,base.intersection(box(-HALF,i*.50,HALF,i*.50+.024)),.002,.015,REAR,'Ashlar joint shadows')
    rect(b,-2.65,.025,2.65,3.43,-.97,-.92,DOOR,'Recessed timber entrance')
    for i in range(4):
        x=(i-1.5)*1.26
        h=box(x-.43,.96,x+.43,2.66)
        plate(b,h,-.91,-.89,GLASS,'Door glazing')
        loop(b,h,.048,-.89,-.835,DOOR,'Door glaze surrounds')
        if not lod: b.tube([(x+.47,.79,1.17),(x+.47,.79,1.60)],.029,FRAME,8,'Door pulls')
    for x in (-2.48,-1.255,0,1.255,2.48):
        rect(b,x-.034,.025,x+.034,3.05,-.92,-.81,FRAME,'Entrance door stiles')
    rect(b,-2.64,2.96,2.64,3.04,-.90,-.76,FRAME,'Entrance transom rail')
    # The bilingual marquee has independent raised letters on the fascia and above it.
    rect(b,-HALF,4.18,HALF,4.45,-.08,.84,PALE,'Canopy soffit')
    rect(b,-HALF,4.46,HALF,4.64,-.02,.90,PALE,'Canopy projecting lip')
    rect(b,-3.36,4.64,3.36,5.52,-.03,.70,BASE,'Raised Chinese marquee')
    rect(b,-3.42,5.49,3.42,5.59,-.01,.74,PALE,'Marquee cap')
    type_on_front(b,'中国大戏院','calligraphy.ttf',5.65,.56,5.05,.72,lod,'Chinese theatre lettering')
    type_on_front(b,'GREAT THEATRE OF CHINA','canopy.ttf',6.69,.30,3.91,.03,lod,'English theatre lettering')
    # Measured on the published street view: three long panes below three shorter panes.
    center_holes=[]
    for x in CENTRE:
        for z,w,h in [(6.02,.99,3.52),(10.66,.79,1.34)]:
            hole=bay(b,x,z,w,h,-.55,lod,'Central street window');center_holes.append(hole)
            rect(b,x-w/2-.08,z-.09,x+w/2+.08,z,-.33,-.12,PALE,'Central sill')
    plate(b,box(-2.58,5,2.58,14.94).difference(unary_union(center_holes)),-1.18,-.27,BRICK,'Recessed central brickwork')
    for x in CENTRE:
        if not lod:
            loop(b,box(x-.47,9.79,x+.47,10.36),.053,-.27,-.205,BRICK,'Raised brick spandrel')
    for lo,hi,front in [(13.48,13.71,-.01),(13.78,14.07,.035),(14.15,14.40,.085)]:
        rect(b,-2.62,lo,2.62,hi,-.32,front,PALE,'Central raised stone bands')
    ped=Polygon([(-2.6,14.4),(2.6,14.4),(2.6,15.16),(1.78,15.95),(-1.78,15.95),(-2.6,15.16)])
    plate(b,ped,-1.07,-.11,PALE,'Central shaped parapet')
    loop(b,ped,.084,-.11,.05,PALE,'Parapet border')
    for x in TOWERS:
        holes=[]
        for z,width,h in [(6.20,.66,2.1),(10.18,.64,1.48),(15.10,.50,.75)]:
            hole=bay(b,x,z,width,h,-.21,lod,'Tower narrow window');holes.append(hole)
            loop(b,hole,.105,.08,.21,PALE,'Tower window surrounds')
            rect(b,x-width/2-.14,z-.12,x+width/2+.14,z-.01,.05,.28,PALE,'Tower window sills')
            if z<15:pediment(b,x,z+h+.13,width*.82,lod)
        poly=box(x-.90,5.0,x+.90,17.40).difference(unary_union(holes))
        plate(b,poly,-1.17,.09,BRICK,'Paired masonry towers');crown(b,x,lod)
    for left,right in [(-HALF,-4.40),(4.40,HALF)]:
        plate(b,box(left,5,right,13.77),-1.16,-.22,BRICK,'Short adjoining wall')
        rect(b,left,13.77,right,13.95,-1.16,.015,PALE,'Street return cornice')
    rect(b,-HALF,0,HALF,.13,-1.15,.12,BASE,'Entrance foot')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[wall_uv(*q) for q in part['vertices']]
