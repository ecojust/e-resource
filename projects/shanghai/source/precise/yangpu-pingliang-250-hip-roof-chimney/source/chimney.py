"""The red brick stack on the documented north part of the Pingliang Road roof."""
from math import cos, pi

def material(rgb):
    return {'color':[(c/3294.6 if c<11 else ((c/255+.055)/1.055)**2.4) for c in rgb],'roughness':.93}

PALETTE={name:material(rgb) for name,rgb in {
    'deep brick':(145,74,58),'russet brick':(159,84,65),'brown brick':(139,71,57),
    'joint bed':(106,78,68),'cornice brick':(140,83,68),'shadow course':(96,67,58),
    'weathered cap':(159,150,131),'cap side':(148,141,124),
    'brown tile':(135,70,54),'red tile':(153,79,65),'dark tile':(126,69,61),
    'underlay':(102,73,63),'sheet flashing':(124,117,107)}.items()}
SHAFT_X=.55
SHAFT_Y=.405

def roof_z(x,y):
    # The smaller hipped slope returns toward the back of the photographed junction.
    return .54+.47*y+.18*max(0,x-.57)

def facet(b,base,thickness,mat,label):
    verts=[(x,y,z+dz) for dz in (-thickness,0) for x,y,z in base]
    n=len(base)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n))
    b.add(verts,faces,mat,label)

def roof_and_tiles(b,lod):
    length=.31; width=.235
    for left,right in ((-1.76,.57),(.57,1.76)):
        corners=[(x,y,roof_z(x,y)-.037) for x,y in ((left,-1.46),(right,-1.46),(right,1.402),(left,1.402))]
        facet(b,corners,.038,"underlay","roof bedding under the tiles")
    for row in range(12):
        y=-1.46+row*.232
        for col in range(-8,9):
            x=col*width+width*.5*(row%2)
            left=max(-1.76,x);right=min(1.76,x+width+.012)
            if right-left<.012:continue
            steps=3 if lod else 7
            mat=('brown tile','red tile','dark tile','red tile','brown tile')[(col*7+row*3)%5]
            for k in range(steps):
                l=left+(right-left)*k/steps;r=left+(right-left)*(k+1)/steps
                base=[]
                for a,t in ((l,0),(r,0),(r,1),(l,1)):
                    yy=y+t*length
                    wave=.021*(1-cos(2*pi*(a-x)/width))
                    base.append((a,yy,roof_z(a,yy)+wave+.005+.019*(1-t)))
                facet(b,base,.031,mat,'lapping clay tile row '+str(row+1))
    # Flashing rises behind the masonry on the two visible sides.
    for side in (-1,1):
        x=side*(SHAFT_X+.014)
        facet(b,[(x+dx,y,roof_z(x+dx,y)+h) for dx,y,h in
                 [(0,-.46,.094),(.065*side,-.46,.04),(.065*side,.47,.04),(0,.47,.094)]],
                 .018,'sheet flashing','side flashing')

def add_building(b,lod=False):
    roof_and_tiles(b,lod)
    b.box((0,0,1.325),(1.09,.80,2.57),'joint bed',label='masonry bed')
    bed=.078;length=.234
    red=('russet brick','deep brick','brown brick','russet brick','deep brick')
    for row in range(32):
        bottom=.102+row*bed
        for side in (-1,1):
            for k in range(-4,4):
                left=max(-SHAFT_X,k*length+length*.5*(row%2)+.004)
                right=min(SHAFT_X,(k+1)*length+length*.5*(row%2)-.004)
                if right>left:
                    b.box(((right+left)/2,side*(SHAFT_Y-.016),bottom+.034),
                          (right-left,.040,.068),red[(3*row+k)%5],label='bonded brick long face '+str(side))
            for k in range(-3,3):
                low=max(-SHAFT_Y+.026,k*length+length*.5*((row+1)%2)+.004)
                high=min(SHAFT_Y-.026,(k+1)*length+length*.5*((row+1)%2)-.004)
                if high>low:
                    b.box((side*(SHAFT_X-.012),(high+low)/2,bottom+.034),
                          (.030,high-low,.068),red[(row+3*k+1)%5],label='bonded brick return '+str(side))
    for z,h,x,y,m,label in [
        (2.62,.096,1.14,.86,'cornice brick','first brick course below cap'),
        (2.695,.065,1.21,.93,'shadow course','projecting dark bed'),
        (2.775,.094,1.28,.99,'weathered cap','outer edge of cap'),
        (2.865,.094,1.13,.86,'cap side','raised cap inset')]:
        b.box((0,0,z),(x,y,h),m,label=label)
