"""Street-facing lintel from No. 53 in Sanduoli, measured from the 2015 photograph."""
from math import cos, pi, sin, sqrt


def stone(rgb):
    return {'color': [((value / 255 + .055) / 1.055) ** 2.4 for value in rgb],
            'roughness': .92}


PALETTE = {
    'weathered stone': stone((151, 145, 130)),
    'relief crest': stone((164, 157, 143)),
    'stone recess': stone((126, 121, 110)),
    'sheltered stone': stone((137, 133, 122)),
    'pot raised ribs':stone((160, 154, 141)),
}


def box(b, left, right, front, back, lower, upper, material, name):
    b.box(((right+left)/2, (front+back)/2, (lower+upper)/2),
          (right-left, back-front, upper-lower), material, label=name)


def band(b, left, right, profile, material, label):
    # profile is an ordered, closed section in depth and height.
    n = len(profile)
    points = [(x,y,z) for x in (left,right) for y,z in profile]
    faces = [tuple(range(n)), tuple(reversed(range(n,2*n)))]
    faces.extend((i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n))
    b.add(points,faces,material,label)


def frame(b, x, z, width, height, front, label):
    width_half, height_half = width/2,height/2
    k = .020
    for sign in (-1,1):
        edge=x+sign*(width_half-k/2)
        box(b,edge-k/2,edge+k/2,front,.032,z-height_half,z+height_half,'relief crest',label+' upright')
        edge=z+sign*(height_half-k/2)
        box(b,x-width_half+k,x+width_half-k,front,.032,edge-k/2,edge+k/2,'relief crest',label+' rail')


def leaf(b, u, z, du, dz, width, y, label, lod):
    rings = 4 if lod else 9
    norm = (du*du+dz*dz)**.5
    px,pz = -dz/norm,du/norm
    points=[]
    for i in range(rings+1):
        t=i/rings; radial=max(.015,sin(pi*t)**.80)
        cx=u+du*t; cz=z+dz*t+.019*sin(pi*t);hw=width*radial
        points.extend([(cx-hw*px,y,cz-hw*pz),
                       (cx,y-.031*radial,cz),
                       (cx+hw*px,y,cz+hw*pz)])
    faces=[]
    for i in range(rings):
        j=3*i;faces.extend([(j,j+3,j+4,j+1),(j+1,j+4,j+5,j+2),(j+2,j+5,j+3,j)])
    b.add(points,faces,'relief crest',label)


def planter(b,x,side,lod):
    # A fluted half vessel in relief, with a bottom foot, swelling bowl, and raised rim.
    profile=[(.215,.038),(.226,.073),(.244,.072),(.253,.047),(.263,.058),
             (.290,.117),(.348,.151),(.407,.166),(.425,.166),(.435,.175),(.456,.175)]
    cnt=18 if lod else 60
    vertices=[]
    for z,r in profile:
        for j in range(cnt+1):
            a=pi*j/cnt
            flute=.005*(1-cos(14*a)) if .260<=z<=.425 else 0
            vertices.append((x+(r-flute)*cos(a),-.032-(r-flute)*.46*sin(a),z))
    faces=[(k*(cnt+1)+j,(k+1)*(cnt+1)+j,(k+1)*(cnt+1)+j+1,k*(cnt+1)+j+1)
           for k in range(len(profile)-1) for j in range(cnt)]
    faces.extend([tuple(range(cnt,-1,-1)),tuple(range((len(profile)-1)*(cnt+1),len(profile)*(cnt+1)))])
    b.add(vertices,faces,'weathered stone',side+' fluted stone planter')
    # The vertical ribs swell towards the bowl's shoulder; the grooves remain open.
    for j in range(7):
        angle=pi*(j+.5)/7
        path=[]
        for z,r in profile:
            if .25 <= z <= .425:
                path.append((x+r*cos(angle),-.032-r*.46*sin(angle)-.0015,z))
        if len(path)>1:
            b.tube(path,.0055 if lod else .006,'pot raised ribs',5 if lod else 8,side+' projecting flutes')
    for j in range(9):
        a=pi*(j+.5)/9;u=x+.137*cos(a); y=-.036-.064*sin(a)
        path=[(u+.016*cos(pi*t/6),y-.005,.459+.016*sin(pi*t/6)) for t in range(13)]
        b.tube(path,.0037,'relief crest',4 if lod else 6,side+' beads below foliage')
    # Leaf tips visible in the two planters differ. Branches beyond the outline are estimates.
    for j,(du,dz,z0) in enumerate([(-.154,.112,.485),(-.139,.193,.49),(-.095,.166,.503),
                                    (-.051,.208,.497),(.007,.169,.515),(.062,.204,.506),
                                    (.126,.166,.494),(.152,.097,.493)]):
        base=x+du*.20
        leaf(b,base,z0,du*(.90 if side=='left' else 1),dz,.023,-.043-.012*(j%3),side+' leaves '+str(j+1),lod)
    for j in range(5):
        blade=(j-2)*.042
        leaf(b,x+blade/2,.452,blade,.099,.019,-.068,side+' low leaf '+str(j+1),lod)


def add_building(b,lod=False):
    box(b,-1.29,1.29,-.008,.225,.118,.786,'weathered stone','continuous lintel stone')
    box(b,-1.28,1.28,-.035,.225,.008,.119,'sheltered stone','bearing over door opening')
    lower=[(-.10,.110),(-.10,.148),(-.060,.151),(-.042,.174),(-.033,.183),(.22,.183),(.22,.110)]
    band(b,-1.30,1.30,lower,'relief crest','stepped sill below inscription and planters')
    box(b,-.388,.388,-.018,.018,.324,.559,'sheltered stone','worn inscription field')
    frame(b,0,.442,.84,.287,-.043,'low inscription frame')
    for side,x in [('left',-.643),('right',.643)]:
        planter(b,x,side,lod)
    for sign in (-1,1):
        x=sign*1.094
        box(b,x-.171,x+.171,-.052,.226,.003,.767,'weathered stone','end pier face')
        frame(b,x,.44,.186,.401,-.072,'recess surround on end pier')
        band(b,x-.206,x+.206,[(y-.044,z)for y,z in lower],'relief crest','returned sill of end pier')
    dentil= .079
    for i in range(32):
        x=(i-15.5)*dentil
        box(b,x-.016,x+.016,-.070,.064,.764,.815,'relief crest','cut dentil '+str(i+1))
    band(b,-1.315,1.315,[(-.082,.813),(-.084,.839),(-.095,.854),(-.134,.871),
                          (-.135,.906),(-.158,.914),(-.158,.951),(.235,.951),(.235,.813)],
         'relief crest','cornice with projecting lower lip')
    box(b,-.872,.872,.001,.215,.951,1.159,'sheltered stone','recessed upper carved panel')
    # The original upper panel contains coiling stems and raised flower heads.
    for side,sign in [('left',-1),('right',1)]:
        for k in range(3):
            cx=sign*(.106+.253*k);cz=1.044
            path=[]
            count=15 if lod else 40
            for j in range(count+1):
                t=j/count;angle=(.15+1.18*t)*2*pi;r=.071*(1-.66*t)
                path.append((cx+sign*r*cos(angle),-.018,cz+.86*r*sin(angle)))
            b.tube(path,.0085,'relief crest',5 if lod else 9,side+' upper scroll '+str(k+1))
            leaf(b,cx,.981,sign*.099,.065,.015,-.012,side+' folded upper leaf',lod)
            leaf(b,cx,.981,-sign*.096,.078,.015,-.012,side+' returning upper leaf',lod)
    band(b,-.921,.921,[(-.041,1.153),(-.054,1.177),(-.089,1.183),(-.089,1.215),
                        (-.115,1.226),(-.115,1.254),(.219,1.254),(.219,1.153)],
         'weathered stone','raised centre cap')
