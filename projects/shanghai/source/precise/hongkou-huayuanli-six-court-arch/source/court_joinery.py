"""Oak-coloured paired casements, stepped plaster sill and the photographed entry surround."""
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

PAINT='Oxide red painted joinery'
EDGE='Worn reddish bead'
DARK='Recess at frame'
GLASS='Smoky teal glazing'
GLASS_LIGHT='Pale grey green glazing'
PUTTY='Brown linseed putty'
STONE='Grey sill stone'
LIME='Buff lime finish'
CHIP='Pale cast coping'
SHADOW='Recessed brown jamb'
FLOOR='Grey tread'
METAL='Dark edge metal'


def frame(f, center, sill, width, height, jamb, head, foot, back, front, mat, label):
    outer=box(center-width/2,sill,center+width/2,sill+height)
    inner=box(center-width/2+jamb,sill+foot,center+width/2-jamb,sill+height-head)
    f.prism(outer.difference(inner),back,front,mat,label)


def stepped_sill(builder, center, z, width, section, mat, name):
    """Extrude a measured side profile along the window width; tuples are (depth, height)."""
    builder.prism(Polygon(section),-width/2,width/2,
                  lambda depth,height,along:(center-along,-depth,z+height),mat,name)


def paired_window(builder,f,d,lod):
    x=d['upper_center'];sill=d['upper_frame_sill'];top=d['upper_frame_top'];width=d['upper_frame_width']
    reference=-d['upper_wall_recess']
    # A narrow dark reveal separates the externally painted door-like sashes from the roughcast.
    frame(f,x,sill-.014,width+.028,top-sill+.028,.017,.017,.017,reference-.084,reference-.051,DARK,'Paired sash/dark reveal')
    frame(f,x,sill,width,top-sill,.069,.066,.072,reference-.082,reference-.010,PAINT,'Paired sash/outer case')
    clear=width-.138;gap=.018;leaf_w=(clear-gap)/2
    bars=d['upper_dividers_z']
    for k,side in enumerate((-1,1)):
        cx=x+side*(leaf_w+gap)/2
        bottom=sill+.074;head=top-.068
        frame(f,cx,bottom,leaf_w,head-bottom,.055,.070,.078,reference-.10,reference-.023,PAINT,'Casement '+str(k+1)+'/rebated leaf')
        for i,z in enumerate(bars):
            f.box(cx,z,leaf_w-.108,.033,.048,reference-.048,PAINT,'Casement '+str(k+1)+'/three horizontal rails')
        inner_left=cx-leaf_w/2+.055;inner_right=cx+leaf_w/2-.055
        edges=[bottom+.078,*bars,head-.070]
        for i,(zl,zu) in enumerate(zip(edges,edges[1:])):
            low=zl+(.017 if i else 0);high=zu-(.017 if i<3 else 0)
            outer=box(inner_left,low,inner_right,high)
            inset=.011 if lod else .015
            inside=box(inner_left+inset,low+inset,inner_right-inset,high-inset)
            name='Casement '+str(k+1)+'/light '+str(i+1)
            f.prism(outer.difference(inside),reference-.076,reference-.058,PUTTY,name+' putty')
            f.prism(inside,reference-.086,reference-.079,GLASS if (i+k)%3 else GLASS_LIGHT,name+' glass')
            if not lod:
                f.box(cx,low+.008,inner_right-inner_left-.010,.009,.012,reference-.054,EDGE,name+' lower bead')
        if not lod:
            f.box(cx+side*(leaf_w/2-.026),(bottom+head)/2,.012,head-bottom-.06,.013,reference-.020,EDGE,'Casement '+str(k+1)+'/rubbed stile')
    # The two independent closing stiles leave a visible, narrow central joint.
    f.box(x,(sill+top)/2,gap-.002,top-sill-.139,.012,reference-.112,DARK,'Paired sash/central joint')
    bottom_profile=[(-.055,-.102),(.128,-.102),(.170,-.057),(.182,-.025),(.182,-.010),(-.053,.035)]
    stepped_sill(builder,x,sill-.030,width+.185,bottom_profile,STONE,'Upper window/canted stone sill')
    stepped_sill(builder,x,sill-.130,width+.080,[(-.055,-.06),(.107,-.06),(.126,-.026),(.126,0),(-.055,0)],LIME,'Upper window/sill underset')
    # A fragment of the projecting lintel is visible at the top of the photograph.
    stepped_sill(builder,x,top+.028,width+.218,[(-.10,0),(.120,0),(.135,.024),(.146,.115),(-.10,.115)],STONE,'Upper window/top lintel')


def entry(builder,f,d,lod):
    width=d['door_clear_width'];z=d['threshold_height'];head=z+d['door_clear_height']
    post=.091
    for side in (-1,1):
        x=side*(width+post)/2
        f.box(x,(z+head)/2,post,head-z,.142,-.031,PAINT,'Door surround/reddish upright')
        f.box(side*(width/2+.011),(z+head)/2,.018,head-z-.020,.024,.033,SHADOW,'Door surround/dark stop')
        if not lod:
            f.box(side*(width/2+post-.009),(z+head)/2,.012,head-z-.018,.009,.048,EDGE,'Door surround/worn moulding')
    f.box(0,head+.047,width+2*post,.094,.141,-.031,SHADOW,'Door surround/square head')
    f.box(0,head+.101,width+2*post+.020,.025,.091,-.003,LIME,'Door surround/slender lintel')
    stepped_sill(builder,0,z,width+.17,[(-.25,-.105),(.263,-.105),(.290,-.072),(.290,-.025),(.278,-.002),(-.25,0)],FLOOR,'Entry/single worn threshold')
    # A limited floor and two jamb returns give the open threshold a real depth.
    # The photographic record does not determine how rooms continue farther in.
    for side in(-1,1):
        f.box(side*(width/2+.028),(z+head)/2,.045,head-z,.72,-.69,SHADOW,'Door recess/lining')
    f.box(0,head+.021,width,.037,.76,-.70,DARK,'Door recess/soffit')
    builder.plan_prism(box(-width/2,.235,width/2,d['section_back_m']),.067,.099,FLOOR,'Entry/recessed floor')
