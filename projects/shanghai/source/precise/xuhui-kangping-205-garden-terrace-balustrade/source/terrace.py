"""A cropped return of the 205 Kangping Road garden terrace railing."""
from pathlib import Path
from random import Random
from PIL import Image, ImageFilter
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

PIER = 'Warm grey cement pier'
BEAD = 'Pale collar and rim'
BODY = 'Pale cast baluster'
SILL = 'Dressed mineral slab'
FASCIA = 'Sand-grey cornice'
BRACKET = 'Stepped cornice modillions'
PALETTE = {
    PIER: dict(color=[.575,.550,.477],roughness=.92),
    BEAD: dict(color=[.750,.729,.660],roughness=.84),
    BODY: dict(color=[.735,.705,.622],roughness=.93),
    SILL: dict(color=[.608,.582,.514],roughness=.90),
    FASCIA: dict(color=[.468,.450,.383],roughness=.96),
    BRACKET: dict(color=[.589,.563,.486],roughness=.93),
}

# The section cuts off between balusters. These are approximate dimensions, in metres.
PITCH=.257
FRONT = [.381+PITCH*i for i in range(8)]
SIDE = [.37+PITCH*i for i in range(3)]
END=FRONT[-1]+PITCH/2
SIDE_END=SIDE[-1]+PITCH/2
BASE=.532
CAP=1.185
PROFILE = [
    (.000,.078),(.023,.079),(.039,.067),(.061,.062),
    (.090,.062),(.116,.068),(.144,.066),(.161,.055),
    (.179,.058),(.190,.069),(.206,.069),(.221,.058),
    (.236,.060),(.251,.077),(.273,.090),(.296,.096),
    (.316,.096),(.340,.089),(.371,.074),(.406,.058),
    (.443,.045),(.468,.040),(.494,.041),(.521,.047),
    (.546,.061),(.566,.074),(.583,.076),(.604,.070)]
FAR_STEPS = [0,2,4,5,7,9,11,13,15,17,19,21,23,25,27]

def finish(path):
    rng=Random(391)
    large=Image.new('L',(38,40))
    large.putdata([rng.randrange(232,248) for _ in range(38*40)])
    soft=large.resize((192,192),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(.6))
    img=Image.new('L',soft.size)
    img.putdata([min(255,max(0,value+rng.randrange(-3,4))) for value in soft.getdata()])
    img.convert('RGB').save(path)

def cube(b,name,material,x,y,z0,z1,width,depth=None):
    depth=width if depth is None else depth
    b.box((x,y,(z0+z1)/2),(width,depth,z1-z0),material,label=name)

def section(depth,inset):
    # Both visible faces meet at one mitre, with no coplanar overlapping corner cubes.
    outer=-depth
    return unary_union([box(outer,outer,END,inset),box(outer,outer,inset,SIDE_END)])

def layer(b,name,material,width,inside,z0,z1):
    b.prism(section(width,inside),z0,z1,lambda x,y,z:(x,y,z),material,name)

def bracket(b,i,pos,side,lod):
    # Profile is stepped then bevelled towards the wall at the bottom.
    profile=[(-.249,.323),(-.249,.364),(-.101,.364),(-.101,.217),
             (-.160,.217),(-.197,.240),(-.213,.264),(-.213,.282),
             (-.232,.282),(-.232,.312)]
    if lod:
        profile=[profile[n] for n in (0,1,2,3,4,6,7,8,9)]
    mapper=(lambda d,z,w:(d,pos-w,z)) if side else (lambda d,z,w:(pos+w,d,z))
    b.prism(Polygon(profile),-.047,.047,mapper,BRACKET,
            ('Return' if side else 'Front')+' / moulded bracket '+str(i))

def baluster(b,x,y,label,lod):
    cube(b,label+' / square foot',BEAD,x,y,BASE,BASE+.028,.171)
    stages=[PROFILE[n] for n in FAR_STEPS] if lod else PROFILE
    b.lathe((x,y),[(BASE+.026+z,r) for z,r in stages],BODY,
            segments=12 if lod else 28,label=label+' / turned stone')
    cube(b,label+' / square head',BEAD,x,y,BASE+.628,CAP,.174)

def add_building(b,lod):
    for name,material,depth,inside,z0,z1 in [
        ('Cornice below the brackets',FASCIA,.145,.30,.000,.201),
        ('Upper fascia and shadow joint',FASCIA,.129,.31,.201,.350),
        ('Bottom bed under projecting deck',BEAD,.210,.32,.350,.378),
        ('Projecting ledge',SILL,.261,.43,.378,.417),
        ('Front nosing',SILL,.247,.43,.417,.449),
        ('Support for the railing',FASCIA,.099,.093,.449,.490),
        ('Baluster sill',SILL,.126,.13,.490,BASE),
        ('Handrail lower bed',BODY,.107,.107,CAP,CAP+.032),
        ('Handrail lower moulding',BEAD,.123,.123,CAP+.032,CAP+.053),
        ('Handrail weathering',SILL,.132,.132,CAP+.053,CAP+.090)]:
        layer(b,name,material,depth,inside,z0,z1)
    for side,end in ((False,END),(True,SIDE_END)):
        for i in range(int((end+.07)/.224)):
            bracket(b,i,.025+i*.224,side,lod)
    for name,mat,size,z0,z1 in [
        ('Pier footing',BEAD,.526,.446,.492),('Pier plinth',SILL,.497,.492,.575),
        ('Pier lower bead',BEAD,.462,.575,.594),('Plain square pier',PIER,.426,.594,1.212),
        ('Pier capital bed',SILL,.461,1.212,1.243),('Pier cap',BEAD,.523,1.243,1.294),
        ('Pier weathering',SILL,.506,1.294,1.307)]:
        cube(b,name,mat,0,0,z0,z1,size)
    for i,x in enumerate(FRONT,1): baluster(b,x,0,f'Front baluster {i}',lod)
    for i,y in enumerate(SIDE,1): baluster(b,0,y,f'Return baluster {i}',lod)
    b.palette[PIER]['texture']=str(Path(__file__).with_name('mineral-finish.png'))
    b.palette[BODY]['texture']=str(Path(__file__).with_name('mineral-finish.png'))
    for part in b.parts:
        if part['material'] in (PIER,BODY):
            part['texcoords']=[[(x+.55*y+.38)/(END+.76),1.-z/1.34] for x,y,z in part['vertices']]
