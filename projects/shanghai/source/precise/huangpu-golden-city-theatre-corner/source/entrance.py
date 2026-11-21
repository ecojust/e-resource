"""The projecting canopy, open vestibule, two poster cases and period-specific lettering."""
from pathlib import Path
from shapely import set_precision
from curved_front import finish
from sign_lettering import lettering_shapes

STONE='Theatre light entrance stone'
SOFFIT='Theatre shaded underside'
BAND='Theatre aluminium canopy fascia'
STONE_WHITE='Theatre white fascia lettering'
STEPS='Theatre warm entrance treads'
VEST='Theatre terracotta lobby plaster'
METAL='Theatre door bronze'
GLASS='Theatre door glazing'
BLACK='Theatre dark poster frame'
POSTER='Theatre poster paper'
SLATE='Theatre muted programme-blue panels'
MAROON='Theatre muted programme-red panels'
LETTERS='Theatre champagne lettering'
LIGHT='Theatre cream lightbox panels'
PALETTE={STONE:finish((189,181,161),.78),SOFFIT:finish((128,124,109),.83),BAND:finish((163,163,154),.55,.25),STONE_WHITE:finish((229,228,215),.48,.19),
         STEPS:finish((159,139,106),.80),VEST:finish((186,163,137),.83),METAL:finish((77,72,62),.48,.40),
         GLASS:finish((123,129,121),.42,.18),BLACK:finish((54,53,49),.65,.32),POSTER:finish((214,210,197),.83),
         SLATE:finish((91,111,125),.72),MAROON:finish((125,91,94),.75),LETTERS:finish((197,165,102),.48,.36),
         LIGHT:finish((223,214,187),.60)}
FOLDER=Path(__file__).parent


def character(frame,name,font,char,u,reach,z,w,h,mat):
    _,path=next(iter(lettering_shapes(char,w,h,font=FOLDER/font)))
    path=set_precision(path.simplify(.002 if frame.detail else .006),.0004)
    if mat==LETTERS:
        # The dimensional gold name catches a dark edge in both the daylight and night photographs.
        backing=path.buffer(.012,quad_segs=2,join_style='round')
        frame.glyph(name+' backing '+char,METAL,u,reach-.045,z,backing,.044)
    frame.glyph(name+' '+char,mat,u,reach,z,path,.025 if frame.detail else .020)


def lettering(frame,d,reach,top):
    center=d['door_center_u']
    for i,ch in enumerate('黃浦劇場'):
        axis=center+(1.5-i)*1.94
        z=top(axis);depth=reach(axis)-.23
        for dx in (-.14,.14):
            frame.flat('Brackets for the theatre name',METAL,axis,dx-.017,dx+.017,depth-.040,depth,z-.01,z+.27)
        character(frame,'Canopy name','calligraphy.ttf',ch,axis,depth+.016,z+.49,.70,.78,LETTERS)
    english='HUANGPU THEATRE'
    for i,ch in enumerate(english):
        if ch==' ':continue
        axis=center+((len(english)-1)/2-i)*.43
        character(frame,'Canopy fascia','canopy.ttf',ch,axis,reach(axis)+.048,top(axis)-.262,.300,.235,STONE_WHITE)


def poster_case(frame,u,z,h,w,index):
    frame.flat('Programme case black moulding',BLACK,u,-w/2,w/2,-.035,.073,z,z+h)
    frame.flat('Programme case paper',POSTER,u,-w/2+.048,w/2-.048,.073,.084,z+.049,z+h-.048)
    if frame.detail:
        # Graphic blocks stand in for film programmes, which change through the year.
        if index:
            for i,mat in enumerate([SLATE,MAROON,SLATE,MAROON]):
                x=(i-1.5)*w*.216
                frame.flat('Programme colour field',mat,u,x-w*.090,x+w*.090,.084,.086,z+h*.42,z+h*.78)
        else:
            for j in range(3):
                frame.flat('Programme information rule',SLATE,u,-w*.31,w*.25,.084,.086,z+h*(.44+.084*j),z+h*(.457+.084*j))


def lobby(frame,d):
    u=0.;width=d['door_width_m'];half=width/2;high=d['door_height_m']
    # The 2024 front view shows daylight through both sets of open leaves and
    # the first flight of the entrance stair. Model the visible depth to its landing.
    frame.flat('Lobby floor',STEPS,u,-half,half,-3.0,.06,0,.055)
    for side in (-1,1):
        x=side*(half-.06)
        frame.flat('Stone entry jamb return',STONE,u,x-.065,x+.065,-.80,.015,0,high)
        frame.flat('Inner sides of the vestibule',VEST,u,x-.059,x+.059,-3.05,-.78,.04,high)
        frame.flat('Open bronze door leaf',METAL,u,x-.019,x+.019,-1.04,-.24,.12,high-.12)
        frame.flat('Glazing in open leaf',GLASS,u,x-side*.035-.012,x-side*.035+.012,-1.0,-.30,.30,high-.36)
    frame.flat('Entry stone soffit',STONE,u,-half,half,-.81,-.006,high-.06,high+.06)
    frame.flat('Foyer ceiling',SOFFIT,u,-half,half,-3.04,-.78,high-.11,high)
    frame.flat('Visible plaster landing wall',VEST,u,-half,half,-3.12,-3.02,.05,high-.08)
    for side in (-1,1):
        x=side*half*.32
        frame.flat('Central open leaf upper rail',METAL,u,x-.034,x+.034,-.98,-.36,high-.16,high-.09)
        frame.flat('Central open leaf bottom rail',METAL,u,x-.034,x+.034,-.98,-.36,.08,.16)
        for y in (-.97,-.38):
            frame.flat('Open leaf bronze side stile',METAL,u,x-.032,x+.032,y-.023,y+.023,.14,high-.14)
        frame.flat('Central open glass door',GLASS,u,x-.010,x+.010,-.947,-.404,.16,high-.16)
    frame.flat('Bronze entrance head',METAL,u,-half,half,-.21,-.08,high-.11,high)
    for i in range(6):
        front=-1.13-i*.255
        frame.flat('First entrance stair flight',STEPS,u,-half*.60,half*.65,front-.265,front,.055,.165+i*.13)
    for side in (-1,1):
        x=side*half*.65
        # A continuous dark stone stair stringer bounds the visible steps.
        for i in range(6):
            y=-1.13-i*.255
            frame.flat('Stair edge',METAL,u,x-.027,x+.027,y-.260,y,.08,.24+i*.13)


def projecting_sign(frame,d):
    axis=0.;lo=d['blade_bottom_m'];hi=d['blade_top_m']
    # The tall sign is a separate slab with a narrow dark frame. Its broad
    # illuminated face turns towards the intersection beside the corner wall.
    high=d['blade_width_m']/2;low=-high
    frame.flat('Full-height sign dark casing',BLACK,axis,low-.035,high+.035,-.22,0.,lo,hi)
    frame.flat('Vertical lightbox',LIGHT,axis,low,high,.0,.018,lo+.05,hi-.05)
    for z in [lo,*d['blade_grid_z_m']]:
        frame.flat('Segmented sign metal rim',METAL,axis,low,high,.018,.044,z-.025,z+.025)
    for i,ch in enumerate('黃浦劇場'):
        bars=d['blade_grid_z_m']
        z=(bars[2*i+1]+bars[2*i+2])/2
        character(frame,'Upright theatre name','calligraphy.ttf',ch,axis,.048,z,.76,.99,METAL)


def build(frame,wall,doorway,blade,d):
    a,b=d['canopy_stations_m']
    def interp(u,left,right):
        return left+(right-left)*(u-a)/(b-a)
    def reach(u):
        return interp(u,*d['canopy_reach_m'])
    def soffit(u):
        return interp(u,*d['canopy_soffits_m'])
    def top(u):
        return interp(u,*d['canopy_tops_m'])
    frame.strip('Canopy underside',SOFFIT,a,b,lambda u:wall.setback(u)-.19,reach,soffit,lambda u:soffit(u)+.117)
    frame.strip('Canopy aluminium band',BAND,a,b,lambda u:wall.setback(u)-.14,lambda u:reach(u)+.033,
                lambda u:soffit(u)+.113,lambda u:top(u)-.048)
    frame.strip('Canopy upper flashing',STONE,a,b,lambda u:wall.setback(u)-.42,lambda u:reach(u)+.069,
                lambda u:top(u)-.05,lambda u:top(u)+.006)
    for i in range(10):
        u=a+(b-a)*(i+.5)/10
        depth=reach(u)*.64
        frame.flat('Recessed canopy light',LIGHT,u,-.14,.14,depth-.10,depth+.10,soffit(u)-.017,soffit(u)+.006)
    lobby(doorway,d)
    for i,u in enumerate(d['poster_centres_m']):
        poster_case(frame,u,1.05,1.39,1.67,1-i)
    lettering(frame,d,reach,top)
    projecting_sign(blade,d)
