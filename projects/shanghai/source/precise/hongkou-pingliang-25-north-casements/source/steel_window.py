"""The central steel sash and recessed stone pilasters on the north side, 25 Pingliang Road."""
from math import cos, sin, radians


def finish(rgb, metal=0, rough=.86):
    return {'color': [((c/255+.055)/1.055)**2.4 for c in rgb], 'roughness':rough, 'metallic':metal}


PALETTE={'stone face':finish((183,172,152)), 'panel inset':finish((157,145,126)), 'stone arris':finish((194,184,164)),
         'red steel':finish((129,62,53),.26,.68),'steel edge':finish((146,73,60),.22,.66),
         'reflected glass':finish((84,105,105),.13,.38),'deep reveal':finish((87,80,72)),
         'aged glass':finish((100,117,114),.10,.38)}


def box(b,left,right,front,back,bottom,top,mat,label):
    b.box(((left+right)/2,(front+back)/2,(bottom+top)/2),(right-left,back-front,top-bottom),mat,label=label)


def ruled_box(b,coords,mat,label):
    b.add(coords,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],mat,label)


def frame(b,width,height,cols,rows,position,label,lod):
    # Pane depths, outer frame, and delicate glazing bars are physically distinct.
    def local(l,r,front,back,bottom,top,mat,part):
        pts=[position(x,y,z) for y in (front,back) for x,z in ((l,bottom),(r,bottom),(r,top),(l,top))]
        ruled_box(b,pts,mat,label+' '+part)
    edge=.025;rail=.012
    for l,r in [(0,edge),(width-edge,width)]:
        local(l,r,-.010,.025,0,height,'red steel','outer vertical rebate')
    for bottom,top in [(0,edge),(height-edge,height)]:
        local(edge,width-edge,-.010,.025,bottom,top,'red steel','outer rail')
    for c in range(1,cols):
        x=c*width/cols;local(x-rail/2,x+rail/2,-.005,.019,edge,height-edge,'steel edge','slender mullion')
    for row in range(1,rows):
        z=row*height/rows;local(edge,width-edge,-.006,.018,z-rail/2,z+rail/2,'steel edge','glazing bar')
    for c in range(cols):
        for r in range(rows):
            l=max(edge*.86,width*c/cols+rail*.4);rr=min(width-edge*.86,width*(c+1)/cols-rail*.4)
            z=max(edge*.86,height*r/rows+rail*.4);t=min(height-edge*.86,height*(r+1)/rows-rail*.4)
            local(l,rr,.017,.023,z,t,('reflected glass','aged glass')[(r+c)%2],'individual pane')
    if not lod:
        # Narrow rolled edge can be seen in the oblique view while behind the sash stile.
        for x in (.021,width-.021):
            local(x-.0025,x+.0025,-.012,-.008,.029,height-.029,'steel edge','projecting edge of stile')


def add_building(b,lod=False):
    half=.748;top=2.13;transom=.378;z0=.253
    for x in (-.936,.936):
        left=x-.176;right=x+.176
        box(b,left,right,-.084,.19,0,top+.21,'stone face','pilaster block')
        box(b,left+.034,right-.034,-.095,-.080,.30,top+.043,'panel inset','recessed pilaster panel')
        for pos in (left+.034,right-.038):
            box(b,pos,pos+.014,-.113,-.083,.294,top+.058,'stone arris','pilaster panel raised margin')
        for z in (.294,top+.044):
            box(b,left+.032,right-.030,-.114,-.083,z,z+.014,'stone arris','pilaster panel head or toe')
        for z in (top+.063,top+.084):
            box(b,left+.023,right-.020,-.122,-.082,z,z+.010,'stone arris','fine hood above vertical panel')
    box(b,-1.125,1.125,-.144,.22,.115,.175,'stone arris','continuous sill cap')
    box(b,-1.12,1.12,-.121,.214,.060,.116,'stone face','projecting sill bed')
    box(b,-1.12,1.12,-.084,.21,top+.149,top+.219,'stone face','stone window lintel')
    for a,c in [(-.76,-half),(half,.76)]:
        box(b,a,c,-.07,.256,.178,top+.149,'deep reveal','side reveal')
    box(b,-half,half,-.065,.278,top+.088,top+.15,'deep reveal','upper reveal and lintel underside')
    # The camera shows the right-hand leaf swinging toward the street from the right jamb.
    width=half-.008;height=top-transom-z0+.01
    frame(b,width,height,2,3,lambda x,y,z:(-half+x,.085+y,z0+z),'closed left casement',lod)
    yaw=radians(14)
    frame(b,width,height,2,3,lambda x,y,z:(half-width*cos(yaw)+x*cos(yaw),.078-(width-x)*sin(yaw)+y,z0+z),
          'projected right casement',lod)
    box(b,-half,half,.062,.124,top-transom+.021,top-transom+.062,'red steel','fixed transom bar')
    height=transom+.035;tilt=radians(17)
    frame(b,2*half,height,4,2,lambda x,y,z:(-half+x,.064-(height-z)*sin(tilt)+y,top+.085-(height-z)*cos(tilt)),
          'top-hung projecting upper light',lod)
    box(b,-half,half,.131,.182,.177,z0,'stone face','inner window sill')
    # Simple dark surface approximates the interior behind the glazing and hinged light.
    box(b,-half,half,.318,.342,z0,top+.089,'deep reveal','shadow behind existing sash')
