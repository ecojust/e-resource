"""Three glazed bay facets, curved balcony cornice and its iron railing."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from house_fabric import Wall, xy, photo_wall, STUCCO, STONE, PLINTH, BRONZE, STAIR, TIMBER, DARKWOOD, GLASS, SHADOW

def round_veranda(b,lod,layout):
    bay=layout['east_photo_facing']['round_bay']
    r=bay['radius']
    def pt(deg,rad):
        a=math.radians(deg)
        return xy(layout,bay['s']+rad*math.cos(a),bay['t']+rad*math.sin(a))
    sep=np.linspace(-177,-33,4)
    def arc(rad,count):
        return [pt(a,rad) for a in np.linspace(sep[0],sep[-1],count)]
    def sector(rad):
        return Polygon([xy(layout,bay['s'],bay['t'])]+arc(rad,22 if lod else 48))
    for j in range(3):
        wall=Wall(b,pt(sep[j],r-.16),pt(sep[j+1],r-.16))
        opening=(.22,.965,wall.length-.22,2.985)
        tag=f'Bay {j+1} |'
        wall.masonry(.35,3.42,[opening],tag+' rendered wall')
        wall.sash(opening,2,3,tag+' red window',lod)
        wall.rect(0,.35,wall.length,.735,-.24,.035,PLINTH,tag+' apron')
        wall.rect(-.01,.745,wall.length+.01,.895,-.19,.07,STONE,tag+' lower belt')
        for edge in (0,wall.length):
            wall.rect(edge-.105,.88,edge+.105,3.27,-.22,.04,STONE,tag+' dressed pier')
    for i,(a,c,dr) in enumerate([(3.27,3.38,-.04),(3.38,3.44,.05),(3.44,3.62,-.01),(3.62,3.68,.07),(3.68,3.77,.096),(3.77,3.89,.158)]):
        b.plan_prism(sector(r+dr),a,c,STONE,'Bay | cornice course '+str(i+1))
    for i,a in enumerate(np.linspace(-174,-36,35 if not lod else 19)):
        x,y=pt(a,r+.052)
        b.box((x,y,3.555),(.092,.083,.110),STONE,label='Bay | stone dentil '+str(i+1))
    for z,rad in [(3.989,.023),(4.66,.026),(4.79,.036)]:
        b.tube([(*q,z) for q in arc(r+.025,24 if lod else 52)],rad,BRONZE,6 if lod else 10,'Balcony | curved iron rail')
    for j,a in enumerate(np.linspace(-177,-33,29)):
        x,y=pt(a,r+.025)
        b.tube([(x,y,3.905),(x,y,4.79)],.013 if j%7 else .021,BRONZE,6 if lod else 9,'Balcony | upright '+str(j+1))
    for i in range(2):
        curve=[]
        for aa in np.linspace(0,2*math.pi,19 if lod else 39):
            q=pt(-101+math.cos(aa)*4.3+math.sin(aa)*1.3*(-1 if i else 1),r+.045)
            curve.append((*q,4.34+math.sin(aa)*.20))
        b.tube(curve,.015,BRONZE,6 if lod else 9,'Balcony | central rolled oval '+str(i+1))
    for x in (-.16,.16):
        b.tube([(*pt(-101+np.rad2deg(s/r),r+.045),z) for s,z in [(x,4.06),(0,4.26),(-x,4.45)]],.015,BRONZE,6,'Balcony | crossed heel')
    rear=photo_wall(b,layout,-8.70,.015,-3.28,.015)
    op=(2.49,3.915,3.91,6.37)
    rear.masonry(.28,layout['z_eave'],[op],'East | upper door wall')
    rear.sash(op,2,3,'Balcony | landing doors',lod)

def portico(b,lod,layout):
    right=layout['east_photo_facing']['right_back_t']
    for i,s in enumerate((-2.95,-.04)):
        x,y=xy(layout,s,.04)
        for j,(z0,z1,w,d) in enumerate([(.25,.34,.53,.54),(.34,.47,.46,.49),(.47,3.12,.35,.394),(3.12,3.2,.40,.44),(3.2,3.29,.455,.48),(3.29,3.40,.54,.56)]):
            b.box((x,y,(z0+z1)/2),(d,w,z1-z0),STONE,label=f'Portico | pier {i+1} course {j+1}')
    for j in range(3):
        sheet=Polygon([xy(layout,s,t) for s,t in [(-3.30,-.99+.22*j),(.33,-.99+.22*j),(.33,2.56),(-3.30,2.56)]])
        b.plan_prism(sheet,.025+j*.087,.112+j*.087,STAIR,'Portico | entrance tread '+str(j+1))
    for j,(z0,z1,over) in enumerate([(3.375,3.47,.11),(3.47,3.64,.075),(3.64,3.71,.13),(3.71,3.79,.16),(3.79,3.905,.20)]):
        outline=Polygon([xy(layout,s,t) for s,t in [(-3.28-over,-over),(.05+over,-over),(.05+over,2.64),(-3.28-over,2.64)]])
        b.plan_prism(outline,z0,z1,STONE,'Portico | square cornice '+str(j+1))
    front=photo_wall(b,layout,-3.28,0,.05,0)
    op=(1.53,5.195,2.38,6.585)
    front.masonry(3.90,layout['z_eave'],[op],'Portico | upper front')
    front.sash(op,1,3,'Portico | upper casement',lod)
    end=photo_wall(b,layout,.05,0,.05,right)
    end.masonry(3.90,layout['z_eave'],[],'Portico | north return')
    back=photo_wall(b,layout,-3.47,2.53,.1,2.53)
    op=(1.02,.29,2.36,2.98)
    back.masonry(.275,3.40,[op],'Portico | recess back')
    u,z,v,h=op
    back.prism(box(*op).difference(box(u+.08,z+.02,v-.08,h-.08)),-.15,-.04,TIMBER,'Portico | door casing')
    for k in range(2):
        a=u+.08+k*(v-u-.16)/2;c=a+(v-u-.16)/2
        back.rect(a,z+.025,c,2.40,-.20,-.143,DARKWOOD,'Portico | door leaf '+str(k+1))
        for bottom,top in [(.56,1.17),(1.36,2.21)]:
            back.rect(a+.07,bottom,c-.07,top,-.15,-.114,TIMBER,'Portico | moulded door panel')
        back.rect(a,2.46,c,h-.08,-.18,-.15,GLASS,'Portico | transom glass')
    back.rect(u+.04,2.39,v-.04,2.47,-.18,-.075,TIMBER,'Portico | transom rail')
    north=photo_wall(b,layout,.05,right,5.30,right)
    ops=[(.87,4.86,2.14,6.55),(3.03,4.90,4.14,6.56),(1.28,1.37,4.23,3.14)]
    north.masonry(.18,layout['z_eave'],ops,'East wing | garden wall')
    for j,opening in enumerate(ops):
        north.sash(opening,4 if j==2 else 2,3,f'East wing | window {j+1}',lod)

def balcony_awning(b,lod,layout):
    """The thin, dark awning and its brackets are visible from below in 2016 views 03 and 07."""
    corrugation='Garden house | dark green canopy sheet'
    frame='Garden house | dark canopy iron'
    start,end=-7.15,-3.40
    for j in range(14 if lod else 36):
        count=14 if lod else 36
        p0=start+(end-start)*j/count;p1=start+(end-start)*(j+1)/count
        t0,t1=-.01,-1.73
        profile=[(p0,6.93),((p0+p1)/2,6.947),(p1,6.93),(p1,6.904),((p0+p1)/2,6.921),(p0,6.904)]
        near=[(*xy(layout,s,t0),z) for s,z in profile]
        front=[(*xy(layout,s,t1),z-.26) for s,z in profile]
        # Each half corrugation has a top and bottom skin and closed side edges.
        for half,(i,k,l,m) in enumerate([(0,1,4,5),(1,2,3,4)]):
            vs=[near[i],near[k],near[l],near[m],front[i],front[k],front[l],front[m]]
            fs=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
            import numpy as np
            vv=np.array(vs);volume=sum(np.dot(vv[f[0]],np.cross(vv[f[ii]],vv[f[ii+1]])) for f in fs for ii in range(1,len(f)-1))
            b.add(vs,fs if volume>0 else [tuple(reversed(f)) for f in fs],corrugation,'Balcony | pressed canopy sheet')
    for j,s in enumerate([start+.12,(start+end)/2,end-.12]):
        for line in [[(0,6.92),(-1.72,6.665)],[(0,6.13),(-1.23,6.69)]]:
            b.tube([(*xy(layout,s,t),z) for t,z in line],.025,frame,6 if lod else 10,'Balcony | canopy bracket '+str(j+1))
