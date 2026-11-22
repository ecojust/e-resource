"""Two recessed window bays of the Changhua Road return, drawn from rectified street photographs."""
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'grey cement': {'color':[.56,.55,.51], 'roughness':.93},
    'light mortar': {'color':[.55,.53,.47], 'roughness':.97},
    'ochre facing brick': {'color':[.77,.74,.65], 'roughness':.89},
    'cream facing brick': {'color':[.81,.78,.69], 'roughness':.89},
    'weathered facing brick': {'color':[.71,.69,.61], 'roughness':.92},
    'dark metal frame': {'color':[.20,.21,.19], 'metallic':.25, 'roughness':.53},
    'window recess': {'color':[.23,.22,.20], 'roughness':.94},
    'dark glass': {'color':[.19,.22,.22], 'roughness':.28},
    'sky glass': {'color':[.39,.43,.44], 'roughness':.23},
    'concrete sill edge': {'color':[.56,.55,.50], 'roughness':.86},
    'weathered downpipe': {'color':[.58,.56,.49], 'metallic':.25, 'roughness':.75},
}
WIDTH=8.36
CENTERS=(-2.15,2.15)
SILLS=(.94,4.88)
OPENING_WIDTH=1.05
OPENING_HEIGHT=1.99
HEIGHT=7.73
BRICK=('ochre facing brick','cream facing brick','weathered facing brick')

def facing_bricks(f,z0,z1,lod):
    """Lay bed joints and vertical end joints around the openings, with a soldier course above."""
    low=z0-.02
    high=z1+.035
    holes=unary_union([box(x-OPENING_WIDTH/2-.025,z0-.08,x+OPENING_WIDTH/2+.025,z1+.015)for x in CENTERS])
    strips=[(-WIDTH/2,-.99),(-.86,.95),(1.10,WIDTH/2)]
    for col,(start,end) in enumerate(strips):
        outline=box(start,low,end,high).difference(holes)
        label='storey '+str(1+int(z0>3))+' section '+str(col+1)
        if lod:
            f.prism(outline,-.013,.012,'ochre facing brick',label+' brick facing')
            step=.19
            k=0
            while low+step*(k+1)<high:
                y=low+step*(k+1);line=outline.intersection(box(start,y-.006,end,y+.006))
                if not line.is_empty:f.prism(line,.012,.015,'light mortar',label+' bed joints')
                k+=1
            continue
        f.prism(outline,-.018,.003,'light mortar',label+' joint backing')
        pitch=.205
        course=.082
        rows=max(1,int((high-low)/course))
        for row in range(rows):
            zz=low+(high-low)*row/rows
            top=low+(high-low)*(row+1)/rows
            x=start-(pitch/2 if row%2 else 0)
            i=0
            while x<end:
                left=max(start,x+.008);right=min(end,x+pitch-.006)
                if right>left+.008:
                    tile=box(left,zz+.006,right,top-.005).intersection(outline)
                    if tile.area>.0004:
                        mi=(row*17+col*7+i*11)%11
                        mat=BRICK[1 if mi in (0,4,5) else 2 if mi in (2,7) else 0]
                        f.prism(tile,.002,.016,mat,label+' running bond')
                x+=pitch;i+=1
        # A row of upright bricks separates the running bond from the cement band.
        x=start
        while x<end:
            right=min(x+.074,end)
            if right>x+.010:f.prism(box(x+.003,high+.003,right-.003,high+.112),.002,.016,'cream facing brick',label+' soldier course')
            x+=.074

def glazed_opening(f,x,sill,level,col,lod):
    wide=OPENING_WIDTH;high=OPENING_HEIGHT;bottom=sill+.04
    group=f'window {level}-{col} '
    edge=box(x-wide/2,sill,x+wide/2,sill+high)
    frame=edge.buffer(-.047,join_style=2)
    f.prism(edge.difference(frame),-.23,-.147,'dark metal frame',group+'outer sash')
    f.prism(frame,-.255,-.242,'sky glass' if (level,col)==(2,2) else 'dark glass',group+'glazing')
    bar=.029 if lod else .021
    f.box(x,sill+high*.50,bar,high-.077,.042,-.162,'dark metal frame',group+'mullion')
    for at in [.34,.74]:
        f.box(x,sill+high*at,wide-.077,bar,.046,-.164,'dark metal frame',group+'transoms')
    f.box(x,sill-.033,wide+.17,.068,.26,-.012,'concrete sill edge',group+'projecting sill')
    if not lod:
        for side in [-1,1]:
            f.box(x+side*(wide/2-.029),sill+high/2,.011,high-.16,.016,-.138,'window recess',group+'putty line')
        f.box(x,sill+high*.74+.014,wide-.11,.007,.016,-.139,'concrete sill edge',group+'meeting rail')

def add_building(builder,lod=False):
    f=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'window wall')
    apertures=[box(x-OPENING_WIDTH/2,z,x+OPENING_WIDTH/2,z+OPENING_HEIGHT) for z in SILLS for x in CENTERS]
    shell=box(-WIDTH/2,0,WIDTH/2,HEIGHT).difference(unary_union(apertures))
    f.prism(shell,-.36,-.015,'grey cement','wall with four openings')
    for level,z in enumerate(SILLS,1):
        facing_bricks(f,z,z+OPENING_HEIGHT,lod)
        for col,x in enumerate(CENTERS,1):glazed_opening(f,x,z,level,col,lod)
    # The narrow vertical cement joint and pipe can be followed continuously between both rows.
    for x in (-.93,1.03):
        f.box(x,HEIGHT/2,.135,HEIGHT,.067,0,'grey cement','vertical cement joint')
    x=-.87
    f.line((x,.03,.062),(x,HEIGHT-.03,.062),.039,'weathered downpipe',8 if lod else 16,'rain pipe')
    if not lod:
        for z in (.65,2.68,4.52,6.98):
            f.box(x,z,.136,.034,.10,.050,'dark metal frame','pipe saddle')
