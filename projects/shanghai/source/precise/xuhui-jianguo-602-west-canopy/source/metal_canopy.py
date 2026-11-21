"""Build the folded, concave canopy over the west entrance from the photographed outline."""
from math import cos, pi, sin, sqrt
import numpy as np
from shapely.geometry import Polygon

SHEET = 'Green painted sheet metal'
SEAM = 'Dark green folded steel'
EDGE = 'Green enamel edges'
SOFFIT = 'Shadowed metal soffit'


def build_canopy(b, D, photo, lod):
    radius = D['canopy_width']/2
    reach = D['canopy_projection']
    base, top = D['canopy_eave'], D['canopy_crown']
    bottom = D['canopy_ceiling']
    count = int(D['sheet_sectors'])
    steps = 3 if lod else 7
    # The cropped photo starts below the finial. Its first consistently separated horizontal
    # section and the eave are both visible. The intact side photograph sets the crown height.
    sample = list(reversed(photo['portrait_profile_px']))
    outline = [(base,1.)]
    for y,left,right in sample[1:]:
        level = (sample[0][0]-y)/(sample[0][0]-sample[-1][0])
        outline.append((base + (top-base)*level, (right-left)/(sample[0][2]-sample[0][1])))
    if lod:
        outline = [p for i,p in enumerate(outline) if i%2==0 or i==len(outline)-1]

    def point(t,r,z):
        return (r*radius*cos(t), -.014-r*reach*sin(t), z)

    for sector in range(count):
        a,beta=sector*pi/count,(sector+1)*pi/count
        angles=np.linspace(a,beta,steps+1)
        verts=[];faces=[]
        for side,inset,dz in [('top',0.,0.),('under',-.012,-.023)]:
            offset=len(verts)
            for z,r in outline:
                for i,t in enumerate(angles):
                    bulge=.017*sin(pi*i/steps)*sqrt(r)
                    verts.append(point(t,max(.035,r+bulge+inset),z+dz))
            for j in range(len(outline)-1):
                for i in range(steps):
                    k=offset+j*(steps+1)+i
                    f=(k,k+steps+1,k+steps+2,k+1)
                    faces.append(f if side=='top' else tuple(reversed(f)))
        n=len(outline)*(steps+1)
        for i in range(steps):
            faces.append((i,i+1,n+i+1,n+i))
            k=(len(outline)-1)*(steps+1)+i
            faces.append((k+n,k+1+n,k+1,k))
        for j in range(len(outline)-1):
            l=j*(steps+1);k=l+steps
            faces.extend([(l,l+n,l+n+steps+1,l+steps+1),
                          (k+steps+1,k+n+steps+1,k+n,k)])
        b.add(verts,faces,SHEET,f'Canopy / curved sheet {sector+1:02}')
    for i in range(count+1):
        theta=pi*i/count
        line=[point(theta,r+.007,z+.009) for z,r in outline]
        b.tube(line,.012 if i not in (0,count) else .017,SEAM,5 if lod else 8,
               f'Canopy / standing seam {i+1:02}')
    # The scallops are cut into the actual outside band. Its inner and outer edges form one strip.
    teeth=D['valance_pendants']
    res=3 if lod else 7
    verts=[];faces=[]
    for i in range(teeth*res+1):
        t=pi*i/(teeth*res);phase=i%res/res
        drop=.041*(1-abs(2*phase-1))**.78
        low=bottom+.022-drop
        verts.extend((point(t,1.001,base-.006),point(t,1.001,low),
                      point(t,.979,low),point(t,.979,base-.006)))
        if i:
            k=(i-1)*4
            for edge in range(4):
                j=(edge+1)%4
                faces.append((k+edge,k+4+edge,k+4+j,k+j))
    faces.extend([(0,1,2,3),tuple(reversed(range(len(verts)-4,len(verts))))])
    b.add(verts,faces,EDGE,'Canopy / continuous scalloped steel valance')
    angles=np.linspace(0,pi,49 if lod else 95)
    soffit=Polygon([point(t,.977,0)[:2] for t in angles])
    b.plan_prism(soffit,bottom+.047,bottom+.073,SOFFIT,'Canopy / shaded underside')
    for z,r,width in ((base+.008,1.004,.022),(bottom+.127,1.004,.013)):
        b.tube([point(t,r,z)for t in angles],width,SEAM,5 if lod else 8,'Canopy / rolled perimeter beads')
    # A half-cap closes the gathered sheets against the upright wall.
    finial=[(top-.024,.105),(top+.011,.100),(top+.031,.070),(top+.047,.059),
            (top+.057,.064),(top+.095,.048),(D['canopy_finial'],.012)]
    vs=[];fs=[];n=8 if lod else 18
    for z,r in finial:
        for t in np.linspace(0,pi,n+1):
            vs.append((r*cos(t),-.014-r*sin(t),z))
    for j in range(len(finial)-1):
        for i in range(n):
            k=j*(n+1)+i;fs.append((k,k+n+1,k+n+2,k+1))
    fs.append(tuple((len(finial)-1)*(n+1)+i for i in reversed(range(n+1))))
    b.add(vs,fs,EDGE,'Canopy / crown socket and half finial')
    # Both photographed end brackets sit just beyond the moulded outer jambs.
    for hand,side in ((-1,'left'),(1,'right')):
        x=hand*(radius-.125)
        label='Canopy bracket / '+side
        b.box((x,-.042,bottom-.115),(.112,.073,.36),SEAM,label=label+' wall socket')
        pts=[(x,-.061,bottom-.247),(x,-.105,bottom-.244),(x,-.113,bottom-.164),
             (x,-.185,bottom-.136),(x,-.243,bottom-.107),(x,-.312,bottom+.025),(x,-.397,bottom+.049)]
        b.tube(pts,.035,SEAM,6 if lod else 9,label+' rising support')
        for z,dep in ((bottom-.26,.07),(bottom-.14,.14),(bottom+.018,.26)):
            b.box((x,-dep/2-.043,z),(.124,dep,.043),EDGE,label=label+' stepped shoe')
