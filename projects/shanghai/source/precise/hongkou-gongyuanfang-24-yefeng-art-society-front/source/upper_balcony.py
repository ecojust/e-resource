"""The photographed third-storey open balcony of Gongyuanfang No. 24."""
import numpy as np

from frontage_coordinates import bay_y
from material_names import PLASTER, TEXTURES

LIP = 'No. 24 veranda | pale cement lip'
EDGE = 'No. 24 veranda | muted grey fascia'
JOINT = 'No. 24 veranda | dark drip groove'
LOW = 'No. 24 veranda | red brown plaster return'
IRON = 'No. 24 veranda | dark iron'
WHITE = 'No. 24 veranda | ivory screen'
FLOOR = 'No. 24 veranda | worn cement floor'
FASCIA = 'No. 24 veranda | oxblood eaves'
SOFFIT = 'No. 24 veranda | painted soffit'
COVER = 'No. 24 veranda | dark crown edge'
CUT = 'No. 24 veranda | shaded rear study cut'

def finish(rgb, rough=.85, metal=0.):
    return dict(color=[((v/255+.055)/1.055)**2.4 for v in rgb],
                roughness=rough,metallic=metal)

PALETTE = {
    LIP:finish((202,196,179)), EDGE:finish((153,146,135)), JOINT:finish((97,88,83)),
    LOW:finish((132,92,85)), IRON:finish((90,78,73),.67,.32),
    WHITE:finish((204,197,171)), FLOOR:finish((147,139,128)), FASCIA:finish((100,67,64)),
    SOFFIT:finish((164,142,122)), COVER:finish((75,72,68)), CUT:finish((71,62,57)),
    PLASTER:dict(texture=str(TEXTURES[PLASTER]),color=[1.,1.,1.],roughness=.94,metallic=0.)
}
LEFT,RIGHT = 0.,3.915
SCREEN_RIGHT, PIER_LEFT = .378,3.368
DECK_Z, RAIL_Z = 2.174,2.920

def front_y(x,radius):
    # The curved bow terminates at short flat returns beneath the two end walls.
    return bay_y(min(3.445,max(.100,x)),radius)

def block(b,x0,x1,y0,y1,z0,z1,material,name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
          (x1-x0,y1-y0,z1-z0),material,label='24 balcony | '+name)

def strip(b,start,end,profile,material,name,lod):
    """Sweep a closed Y-Z profile through both tangencies of the shallow bow."""
    regular=np.linspace(start,end,15 if lod else 43)
    along=sorted(set([*regular,*[x for x in (.100,3.445) if start<x<end]]))
    vertices=[(x,y,z)for x in along for y,z in profile(x)]
    size=len(profile(along[0]))
    faces=[list(reversed(range(size))),list(range(len(vertices)-size,len(vertices)))]
    for i in range(len(along)-1):
        off=i*size
        for j in range(size):
            k=(j+1)%size
            faces.append([off+j,off+k,off+size+k,off+size+j])
    b.add(vertices,faces,material,'24 balcony | '+name)

def band(b,lower,upper,radius,front,back,material,name,lod):
    def section(x):
        y=front_y(x,radius)
        return [(y+front,lower),(back,lower),(back,upper),(y+front,upper)]
    strip(b,LEFT,RIGHT,section,material,name,lod)

def add_balcony(b,lod=False):
    # The photographed painted return descends below the two cement lips.
    band(b,1.400,1.691,4.051,0.,1.172,LOW,'painted return above brickwork',lod)
    band(b,1.691,1.978,4.078,0.,1.172,EDGE,'projecting fascia',lod)
    band(b,1.978,2.023,4.104,0.,1.172,LIP,'lower pale nosing',lod)
    band(b,2.023,2.071,4.069,0.,1.172,JOINT,'recess between the pale nosings',lod)
    band(b,2.071,DECK_Z,4.086,0.,1.172,LIP,'upper pale nosing',lod)
    def floor_profile(x):
        front=front_y(x,3.980)
        return [(front,DECK_Z),(1.175,DECK_Z),(1.175,DECK_Z+.015),(front,DECK_Z+.015)]
    strip(b,LEFT,RIGHT,floor_profile,FLOOR,'floor behind the front lip',lod)
    def screen_profile(x):
        y=front_y(x,4.010)
        return [(y,DECK_Z+.01),(y+.16,DECK_Z+.01),(y+.16,3.141),(y,3.141)]
    strip(b,.020,SCREEN_RIGHT,screen_profile,WHITE,'short solid screen at the left',lod)
    block(b,PIER_LEFT,RIGHT,.035,1.172,DECK_Z+.014,4.862,PLASTER,'exposed pebble-dash end pier')
    block(b,.0,.044,.045,1.174,DECK_Z+.014,4.837,WHITE,'left inner wall return')
    # The rear cut lies at the measured back beam. No openings are discernible in its shadow.
    block(b,.044,PIER_LEFT,1.145,1.18,DECK_Z+.014,4.74,CUT,'shaded back of the cut model')
    block(b,.01,4.10,-.010,1.175,4.808,4.865,SOFFIT,'pale canopy soffit')
    block(b,0.,4.145,-.017,.070,4.818,5.032,FASCIA,'red brown straight eaves fascia')
    block(b,.0,4.145,.070,1.175,4.865,5.032,FASCIA,'enclosed depth behind the fascia')
    block(b,-.003,4.154,-.028,1.175,5.032,5.075,COVER,'visible roof edge and upper cut')
    block(b,.018,4.10,1.075,1.175,4.635,4.813,FASCIA,'visible rear beam')
    for x in (.10,.17,3.25):
        block(b,x,x+.035,.050,1.089,4.780,4.810,SOFFIT,'shallow ceiling rib')
    # Photo 6 retains isolated upright pairs above the middle rail. Plant-obscured rails
    # continue the measured spacing. The sheet-metal drying racks belong to the foreground.
    rail_start,rail_end=SCREEN_RIGHT-.012,PIER_LEFT+.012
    xvals=np.linspace(rail_start,rail_end,21 if lod else 43)
    for z,radius,label in [(RAIL_Z,.021,'rounded top rail'),(2.738,.012,'rail at the foot of the narrow upper lights')]:
        b.tube([(x,front_y(x,4.0),z) for x in xvals],radius,IRON,8 if lod else 12,'24 balcony | '+label)
    full_intervals=23
    main=np.linspace(rail_start+.022,rail_end-.022,full_intervals+1)
    for i,x in enumerate(main):
        y=front_y(x,4.0);radius=.010 if i%3 else .016
        b.tube([(x,y,DECK_Z+.012),(x,y,RAIL_Z)],radius,IRON,6 if lod else 9,
               '24 balcony | full-height iron upright '+str(i+1))
    for i in range(full_intervals):
        x=(main[i]+main[i+1])/2;y=front_y(x,4.0)
        b.tube([(x,y,2.738),(x,y,RAIL_Z)],.008,IRON,6 if lod else 8,
               '24 balcony | short top-band upright '+str(i+1))
