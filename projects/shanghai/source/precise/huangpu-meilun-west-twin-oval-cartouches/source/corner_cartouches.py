"""Two carved cartouches situated on the actual adjoining stone faces of the west wing."""
from math import cos, sin, pi, sqrt
def material(rgb):
    cs=[c/255 for c in rgb]
    return dict(color=[c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in cs],roughness=.86,metallic=0)
PALETTE={k:material(c) for k,c in [
    ('grey ashlar',(154,151,146)),('mortar shadow',(111,110,108)),('capital stone',(149,147,141)),
    ('corded edge',(167,163,155)),('oval field',(151,149,143)),('scroll ridge',(162,158,150)),
    ('deep fold',(132,131,126)),('small flower',(171,165,155))]}

def build_face(builder,rot,side,lod):
    ca,sa=cos(rot),sin(rot);middle=side*.283
    def mesh(name,v,f,m):
        # Each local panel is centred on its face. Both tangents meet at the same corner.
        builder.add([((x+middle)*ca-y*sa,(x+middle)*sa+y*ca,z)for x,y,z in v],f,m,f'{name} face {side}')
    def slab(name,z0,z1,y,back,mat):
        # Miter both pier faces at the shared vertical ridge.
        corners=[]
        for z in (z0,z1):
            for d in (y,back):
                x0=-.283 + (d*.414213562 if side>0 else 0)
                x1=.283 - (d*.414213562 if side<0 else 0)
                corners.extend([(x0,d,z),(x1,d,z)])
        mesh(name,corners,[(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(4,5,7,6),(0,2,3,1)],mat)
    def dome(name,x,z,a,h,face,depth,mat,steps):
        vertices=[(x,face-depth,z)]
        for ratio,dy in [(.45,.9),(.82,.50),(1,0)]:
            for i in range(steps):
                t=i*2*pi/steps;vertices.append((x+ratio*a*cos(t),face-depth*dy,z+ratio*h*sin(t)))
        faces=[(0,1+i,1+(i+1)%steps)for i in range(steps)]
        for row in (0,1):
            first=1+row*steps
            faces.extend((first+i,first+steps+i,first+steps+(i+1)%steps,first+(i+1)%steps)for i in range(steps))
        mesh(name,vertices,faces,mat)
    def ring(name,z,a,h,width,front,depth,segments):
        v=[];f=[]
        for factor,y in [(1.10,front+.016),(1.025,front-depth),(.975,front-depth),(.90,front+.014)]:
            for i in range(segments):
                t=2*pi*i/segments;v.append((a*factor*cos(t),y,z+h*factor*sin(t)))
        for row in range(3):
            offset=row*segments
            f.extend((offset+i,offset+(i+1)%segments,offset+segments+(i+1)%segments,offset+segments+i)for i in range(segments))
        mesh(name,v,f,'corded edge')
    def leaf(name,points,width,base,depth,pieces):
        # Bezier centreline with a raised midrib. Each leaf narrows back to a cut point.
        v=[];faces=[]
        for j in range(pieces+1):
            t=j/pieces;u=1-t
            x=sum(wei*pt[0]for wei,pt in zip((u**3,3*u*u*t,3*u*t*t,t**3),points))
            z=sum(wei*pt[1]for wei,pt in zip((u**3,3*u*u*t,3*u*t*t,t**3),points))
            dx=3*sum(k*(b[0]-a[0]) for k,a,b in zip((u*u,2*u*t,t*t),points,points[1:]))
            dz=3*sum(k*(b[1]-a[1]) for k,a,b in zip((u*u,2*u*t,t*t),points,points[1:]))
            length=max(.00001,sqrt(dx*dx+dz*dz));spread=width*(.05+.95*sin(pi*t)**.7)
            nx=-dz*spread/length;nz=dx*spread/length
            v.extend([(x+nx,base,z+nz),(x,base-depth*(.26+.74*sin(pi*t)),z),(x-nx,base,z-nz)])
            if j:
                i=(j-1)*3;faces.extend([(i,i+3,i+4,i+1),(i+1,i+4,i+5,i+2)])
        mesh(name,v,faces,'scroll ridge')
    slab('pier core',0,.841,.045,.27,'mortar shadow')
    for i,(lo,hi,d,mat)in enumerate([(0,.105,0,'grey ashlar'),(.119,.248,-.002,'grey ashlar'),(.262,.728,-.009,'capital stone'),(.728,.751,-.025,'deep fold'),(.751,.769,-.043,'corded edge'),(.769,.826,-.054,'grey ashlar'),(.826,.841,-.045,'corded edge')]):
        slab('pier stone course '+str(i),lo,hi,d,.23,mat)
    ns=18 if lod else 42; curve=5 if lod else 12
    dome('shield face',0,.499,.12,.165,-.014,.031,'oval field',ns)
    ring('oval cord',.499,.124,.169,.024,-.029,.023,ns)
    for idx in range(6):
        theta=2*pi*idx/6+pi/2
        dome('flower petal '+str(idx),.014*cos(theta),.528+.014*sin(theta),.012,.010,-.047,.011,'small flower',6 if lod else 12)
    dome('flower heart',0,.528,.013,.011,-.052,.016,'small flower',8 if lod else 18)
    for sign in [-1,1]:
        leaves=[
          ((.061,.339),(.114,.298),(.178,.317),(.181,.378),.024),
          ((.094,.363),(.165,.336),(.200,.372),(.173,.431),.028),
          ((.120,.411),(.167,.38),(.218,.440),(.176,.476),.027),
          ((.129,.451),(.171,.446),(.211,.497),(.161,.534),.024),
          ((.127,.529),(.171,.549),(.216,.519),(.188,.493),.020),
          ((.110,.580),(.152,.627),(.215,.594),(.185,.555),.022),
          ((.091,.622),(.128,.665),(.167,.653),(.162,.615),.020),
          ((.051,.645),(.086,.708),(.15,.695),(.127,.651),.023),
          ((.012,.325),(.049,.305),(.050,.285),(.025,.275),.013),
          ((.015,.664),(.035,.705),(.061,.719),(.078,.694),.015)]
        for i,(*pts,width) in enumerate(leaves):
            leaf(f'folded leaf {sign} {i}',[(sign*x,z)for x,z in pts],width,-.018,.041,curve)
        dome('top spiral '+str(sign),sign*.09,.691,.027,.025,-.021,.025,'scroll ridge',10 if lod else 18)
    for a in [-.032,-.015,0,.015,.032]:
        leaf('crest flute '+str(a),[(a*.4,.635),(a*.6,.666),(a*1.14,.708),(a,.722)],.009,-.027,.032,curve)

def add_building(b,lod=False):
    build_face(b,-pi/4,-1,lod)
    build_face(b,0,1,lod)
