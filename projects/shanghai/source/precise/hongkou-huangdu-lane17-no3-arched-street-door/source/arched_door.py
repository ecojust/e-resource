"""The arched street doorway at 3 Lane 17 Huangdu Road, Shanghai."""
from math import cos,sin,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
ID='hongkou-huangdu-lane17-no3-arched-street-door'
ROUGH='Pebbled residential render';BRICK='Burnt red outer arch';INNER='Shaded red inner arch';BED='Mortar in red arch';BASE='Cream skirting brick';TRIM='Light projecting cap';DARK='Dark inner plane';GATE='Graphite gate metal';GRILLE='Raised iron in the fan';TAG='Green number plate';MARK='Pale enamel numeral'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(ROUGH,[1,1,1],.97),(BRICK,[.545,.19,.085],.89),(INNER,[.455,.15,.072],.91),(BED,[.333,.16,.099],.97),(BASE,[.655,.48,.30],.91),(TRIM,[.71,.55,.357],.89),(DARK,[.075,.067,.060],.8),(GATE,[.094,.093,.086],.58),(GRILLE,[.139,.131,.114],.61),(TAG,[.052,.24,.145],.53),(MARK,[.81,.819,.642],.56)]}
SPRING=1.91
def texture():
    p=Path(__file__).with_name('pebbled-render.png')
    if not p.exists():
        rng=np.random.default_rng(655);grain=rng.normal(0,10.6,(170,235,1));aggregate=np.array(Image.fromarray(rng.integers(0,255,(42,60),dtype='uint8')).resize((235,170),Image.Resampling.BILINEAR),float)
        Image.fromarray(np.clip(np.array([141,117,93])+grain+(aggregate[:,:,None]-128)*.10,0,255).astype('uint8')).save(p)
    PALETTE[ROUGH]['texture']=str(p)
def aperture(r,points=55):
    return Polygon([(-r,-.04),(r,-.04)]+[(r*cos(a),SPRING+r*sin(a))for a in np.linspace(0,pi,points)])
def add_building(b,far=False):
    texture();n=29 if far else 77
    def part(poly,bd,fd,mat,tag):b.prism(poly,bd,fd,lambda x,z,d:(x,-d,z),mat,tag)
    def rect(lo,hi,z,h,bd,fd,mat,name):part(box(lo,z,hi,h),bd,fd,mat,name)
    part(box(-1.09,0,1.09,3.02).difference(aperture(.811)), -.28,0,ROUGH,'Pebbled wall with true arched opening')
    part(aperture(.816,n).difference(aperture(.684,n)), -.211,.034,BED,'Continuous bedding behind the outer brick order')
    part(aperture(.684,n).difference(aperture(.569,n)), -.211,-.085,BED,'Recessed mortar beneath the inner arch')
    for rad0,rad1,back,front,mat,label,count in [(.687,.808,-.052,.050,BRICK,'Outer red brick order',21),(.574,.675,-.160,-.075,INNER,'Second arch set behind face',19)]:
        for j in range(count):
            a=(j+.009)*pi/count;c=(j+.991)*pi/count
            curve=np.linspace(a,c,3 if far else 5)
            pts=[(rad1*cos(t),SPRING+rad1*sin(t))for t in curve]+[(rad0*cos(t),SPRING+rad0*sin(t))for t in curve[::-1]]
            part(Polygon(pts),back,front,mat,label)
        for sign in(-1,1):
            a,c=sorted([rad0*sign,rad1*sign])
            for j in range(7):
                z=.98+j*(SPRING-.98)/7
                rect(a,c,z+.002,z+(SPRING-.98)/7-.001,back,front,mat,'Square pier below arch ring')
            aa,cc=sorted([.656*sign,.851*sign]);rect(aa,cc,1.889,1.929,back,.074,BRICK,'Projecting rectangular impost')
    for sign in(-1,1):
        a,c=sorted([.567*sign,1.008*sign]);rect(a,c,0,.979,-.156,.02,TRIM,'Stone backing of the plinth')
        for row in range(12):
            z=.005+row*.079
            for col in range(3):
                left=max(a,a+col*.264-(row%2)*.132);right=min(c,a+(col+1)*.264-(row%2)*.132)
                if right>left+.006:rect(left+.002,right-.001,z,z+.073,0,.049,BASE,'Cream brick in the door pier foot')
        rect(a-.014,c+.014,.948,.989,-.071,.066,TRIM,'Short cap on the pale plinth')
    part(aperture(.573,n),-.249,-.220,DARK,'Dark doorway recess behind iron leaves')
    for x in(-.539,0,.539):
        rect(x-.018,x+.018,.015,1.73,-.176,-.137,GATE,'Side and meeting stile on the gate')
    for z in(.040,.41,1.706):
        rect(-.558,.558,z,z+.032,-.174,-.136,GATE,'Long straight rail across door leaves')
    for a in[-.482,-.393,-.300,-.21,-.115,.115,.21,.300,.393,.482]:
        rect(a-.006,a+.006,.09,1.671,-.208,-.172,GATE,'Slender upright within paired leaves')
    def tube(points,rad,name):b.tube([(x,.143,z)for x,z in points],rad,GRILLE,sides=5 if far else 10,label=name)
    for rad in(.515,.429):
        tube([(rad*cos(t),1.762+rad*1.21*sin(t))for t in np.linspace(0,pi,25 if far else 55)],.016,'Concentric curved ironwork in the fanlight')
    for sign in (-1,1):
        for j in range(3):
            pts=[(sign*(.035+(.28-.046*j)*t),1.789+.115*j+(.225-.035*j)*sin(pi*t*.73))for t in np.linspace(0,1,7 if far else 18)]
            tube(pts,.012,'Foliate curved branch rising inside the semicircular fan')
    tube([(0,1.753),(0,2.293)],.017,'Stem dividing the curved fanlight')
    rect(.786,.951,1.594,1.815,.052,.063,TAG,'Small green enamel address plaque')
    # The address numeral can be read on the original, above the cream brick base.
    b.tube([(.865+.032*cos(a),-.067,1.751+.028*sin(a))for a in np.linspace(2.23,-1.23,11)]+[(.863+.033*cos(a),-.067,1.691+.034*sin(a))for a in np.linspace(1.25,-2.34,13)],.006,MARK,sides=5 if far else 9,label='Pale numeral three')
    for p in b.parts:
        if p['material']==ROUGH:p['texcoords']=[[(x+1.09)/2.18,z/3.02]for x,y,z in p['vertices']]
