"""Two storeys on the southwestern pair of window axes in the Hengshan Road stairwell.

X increases southwest as seen from the street, Y into the building, Z from
the lower edge of the selected spandrel. The glass is set behind the fins.
"""
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
PALETTE={
 'pale cast cement':{'color':[.64,.602,.525],'roughness':.91},
 'buff stair spandrel':{'color':[.51,.422,.33],'roughness':.92},
 'dark reveal':{'color':[.235,.206,.167],'roughness':.9},
 'weathered steel':{'color':[.115,.111,.095],'metallic':.42,'roughness':.59},
 'shaded glass':{'color':[.097,.122,.136],'metallic':.24,'roughness':.28},
 'slate grey glass':{'color':[.128,.145,.151],'metallic':.20,'roughness':.30},
 'sloping cement sill':{'color':[.45,.418,.355],'roughness':.9}}
BAYS=(-.655,.655)
FINS=(-1.31,0,1.31)
OPENINGS=((.28,3.28),(4.29,6.96))
WIDTH=.92
HEIGHT=7.56
# Calibrate the along-street axis against the three fins on the published standard floor.
X_SCALE=0.842491166990
# Relative heights come from the 2015 and 2020 sidewalk and fin-axis fits.
Z_SCALE=0.756751055254
def face(builder,polygon,front,back,material,name):
    builder.prism(polygon,-back,-front,lambda x,z,d:(x*X_SCALE,-d,z*Z_SCALE),material,name)
def block(builder,name,material,x,width,z,height,front,back):
    builder.box((x*X_SCALE,(front+back)/2,z*Z_SCALE),(width*X_SCALE,back-front,height*Z_SCALE),material,label=name)
def add_stair_windows(builder,lod=False):
    holes=[box(x-WIDTH/2,lo,x+WIDTH/2,hi) for x in BAYS for lo,hi in OPENINGS]
    face(builder,box(-1.48,0,1.48,HEIGHT).difference(unary_union(holes)),0,.30,'buff stair spandrel','Rendered wall with four open reveals')
    for i,x in enumerate(FINS):
        plan=[(x-.145,0),(x-.145,-.116),(x-.122,-.145),(x+.121,-.145),(x+.146,-.118),(x+.146,0)]
        if lod:plan=[(x-.145,0),(x-.133,-.14),(x+.133,-.14),(x+.145,0)]
        builder.prism(Polygon(plan),0,HEIGHT,lambda x,y,z:(x*X_SCALE,y,z*Z_SCALE),'pale cast cement',f'Cement fin {i+1}')
    for level,(sill,head) in enumerate(OPENINGS):
        for col,x in enumerate(BAYS):
            tag=f'Floor {level+1} window {col+1}'
            outline=box(x-WIDTH/2,sill,x+WIDTH/2,head)
            frame=outline.buffer(-.032,join_style=2)
            glass=outline.buffer(-.057,join_style=2)
            face(builder,outline.difference(frame),.025,.235,'dark reveal',tag+' reveal')
            face(builder,frame.difference(glass),.154,.232,'weathered steel',tag+' perimeter')
            lx,lo,rx,hi=glass.bounds
            block(builder,tag+' vertical mullion','weathered steel',x,.026,(lo+hi)/2,hi-lo,.162,.225)
            pitch=(hi-lo)/8
            for row in range(8):
                for col2,(left,right) in enumerate(((lx,x-.013),(x+.013,rx))):
                    bottom=lo+pitch*row+(.017 if row else 0)
                    top=lo+pitch*(row+1)-(.017 if row<7 else 0)
                    tint='slate grey glass' if (row+col2+col+level)%5 in (0,2) else 'shaded glass'
                    block(builder,tag+' glazing',tint,(left+right)/2,right-left,(bottom+top)/2,top-bottom,.226,.242)
                    if row<7:
                        front=.146 if row in (1,5) else .174
                        block(builder,tag+f' crossbar {row+1}','weathered steel',(left+right)/2,right-left,lo+pitch*(row+1),.034,front,.225)
            section=Polygon([(-.075,sill-.059),(.22,sill-.059),(.22,sill+.01),(-.075,sill-.015)])
            builder.prism(section,x-WIDTH/2,x+WIDTH/2,lambda y,z,d:(d*X_SCALE,y,z*Z_SCALE),'sloping cement sill',tag+' pitched sill')
            if not lod:
                for z in (lo+pitch*2,lo+pitch*6):
                    block(builder,tag+' raised meeting rail','weathered steel',x,.024,z,.075,.139,.155)
