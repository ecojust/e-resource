"""Rebuild Seaman Hall's court arcade, East-Wind portal and hipped wings."""
import argparse,json,sys,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder as BaseBuilder
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
import seaman_finishes
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in seaman_finishes.STEMS:seaman_finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        BaseBuilder.save(self,path,metadata)
        return seaman_finishes.writer.embed_normals(path)
ID='changning-st-johns-seaman-hall-courtyard'
SCHOOL='https://www.ecupl.edu.cn/2022/1101/c13514a193952/page.htm'
META=dict(id=ID,name='圣约翰中学西门堂22号楼院廊与东风楼门额',heritage_id='sh-historic-b2-060',official_id='2M006',address='万航渡路1575号华东政法大学长宁校区（原名录1175号）',source=SCHOOL,photo_source=SCHOOL,geometry_license='MIT',texture_license='MIT',photos_embedded=False,viewer_page='st-johns-seaman-hall-courtyard.html',scope='Two-storey named school quadrangle, external street-facing bays, east-wind sign and passage, northern lower inner arcades and flanking roofs. The corner memorial stone is a separately identified sighting. Interiors are not surveyed.',camera_views=json.loads((HERE/'cameras.json').read_bytes()))
G=seaman_finishes.BRICK;R=seaman_finishes.RED;STONE='Seaman | pale stone';PLASTER='Seaman | whitewashed court';WOOD='Seaman | red window joinery';GLASS='Seaman | window glass';SHADE='Seaman | deep interior';TILE='Seaman | terracotta pan tiles';METAL='Seaman | grey metal';SIGN='Seaman | dark red inscription'
def surf(c,r=.87):return dict(color=c,roughness=r)
PALETTE={STONE:surf([.62,.57,.49]),PLASTER:surf([.79,.77,.71]),WOOD:surf([.29,.048,.024],.62),GLASS:dict(color=[.092,.17,.20],alpha=.68,roughness=.29),SHADE:surf([.051,.047,.038]),TILE:surf([.47,.18,.095],.93),METAL:surf([.14,.15,.16]),SIGN:surf([.30,.044,.023])}
PALETTE.update(seaman_finishes.PALETTE)
fit=json.loads((HERE.parent/'measurements/seaman-registration.json').read_bytes())
p=fit['parameters'];WIDTH=fit['width'];E=p['eave'];Z0=p['sill'];Z1=p['arcade crown'];Z2=p['upper sill'];Z3=p['upper crown'];C=p['entrance axis'];DX=p['opening pitch'];RIDGE=p['ridge'];COURT=p['court y'];CAP=p['court spring line'];PLATFORM=p['court platform'];CP=p['court pitch'];LOW=p['court eave']
def block(b,x0,x1,y0,y1,z0,z1,material,label):
    if min(x1-x0,y1-y0,z1-z0)<=0:raise ValueError(label)
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)
def span(cx,sill,half,rise,top,n):
    radius=(half*half+rise*rise)/(2*rise)
    xs=np.linspace(half,-half,n)
    return Polygon([(cx-half,sill),(cx+half,sill),*[(cx+u,top-radius+math.sqrt(max(0,radius*radius-u*u)))for u in xs]])
class Plane:
    def __init__(self,b,origin,axis):
        self.b=b;self.x,self.y=origin;self.u,self.v=axis
    def put(self,shape,front,back,mat,label):
        if shape.is_empty:return
        def xyz(x,z,d):return (self.x+x*self.u+d*self.v,self.y+x*self.v-d*self.u,z)
        self.b.prism(shape,-back,-front,xyz,mat,label)
def face_ring(w,opening,thick,spring,label):
    a,b,c,d=opening.bounds
    shape=opening.buffer(thick,join_style=2).difference(opening).intersection(box(a-thick-.01,spring,c+thick+.01,d+thick+.01))
    w.put(shape,-.13,.04,R,label+' / extruded brick archivolt')
def sash(w,opening,label,lod,upper,sign_bay=False):
    a,b,c,d=opening.bounds;cx=(a+c)/2;inner=opening.buffer(-.072,join_style=2)
    w.put(opening.difference(inner),.074,.17,WOOD,label+' / sash surround')
    bars=[box(cx-.032,b,cx+.032,d)]
    if sign_bay:
        # School close-up 8 shows six tall glazed lights immediately above the name.
        for frac in [1/6, 2/6, 4/6, 5/6]:
            x=a+(c-a)*frac
            bars.append(box(x-.020,b,x+.020,d))
        for frac in [.43,.73]:
            z=b+(d-b)*frac
            bars.append(box(a,z-.023,c,z+.023))
    else:
        if not lod:
            for frac in [.24,.76]:
                x=a+(c-a)*frac
                bars.append(box(x-.022,b,x+.022,d))
        z=b+(d-b)*.68
        bars.append(box(a,z-.027,c,z+.027))
    w.put(inner.intersection(unary_union(bars)),.105,.153,WOOD,label+' / mullions and transom')
    w.put(inner,.17,.19,GLASS,label+' / inset glass')
    w.put(inner,.54,.58,SHADE,label+' / room behind sash')
    w.put(box(a-.085,b-.10,c+.085,b),-.14,.10,STONE if not upper else WOOD,label+' / sill')
def hip(b,x0,x1,y0,y1,eave,ridge,label,along_y=False):
    if along_y:x0,x1,y0,y1=y0,y1,x0,x1
    sx=x1-x0;sy=y1-y0;off=min(sy*.48,sx*.40);v=[(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave),(x0+off,(y0+y1)/2,ridge),(x1-off,(y0+y1)/2,ridge)]
    if along_y:v=[(y,x,z)for x,y,z in v]
    # Four distinct roof pitches with a closed inner skin, never a thin unbacked face.
    for k,ix in enumerate(((0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4))):
        top=[v[i]for i in ix];nv=len(top);lo=[(x,y,z-.15)for x,y,z in top]
        faces=[tuple(reversed(range(nv))),tuple(range(nv,nv*2))]+[(i,(i+1)%nv,(i+1)%nv+nv,i+nv)for i in range(nv)]
        if along_y:
            faces=[tuple(reversed(face)) for face in faces]
        b.add(lo+top,faces,TILE,label+' / pitch '+str(k+1))
    b.tube([v[4],v[5]],.07,TILE,8,label+' / ridge')
    for i,j in [(0,4),(3,4),(1,5),(2,5)]:b.tube([v[i],v[j]],.073,TILE,8,label+' / hip roll '+str(i))
def cross_apron(b,x,half,label):
    """Short cross-hip and its raking eaves, constrained by the aerial and the street silhouette."""
    # At y=4.52 the three visible shallow triangular breaks lie near photo pixels
    # (116,271), (274,271), (430,273). The street eave bounds their forward height.
    front,vent,crest,back=-.72,4.52,7.22,14.73
    z0,z1,z2=E+.19,11.34,RIDGE+.12
    tip=11.67
    def panel(vertices,name):
        n=len(vertices);base=[(u,y,z-.115)for u,y,z in vertices]
        winding=sum(vertices[i][0]*vertices[(i+1)%n][1]-vertices[(i+1)%n][0]*vertices[i][1] for i in range(n))
        if abs(winding)<1e-8:raise ValueError(name)
        face=[tuple(reversed(range(n))),tuple(range(n,n+n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
        if winding<0:face=[tuple(reversed(t))for t in face]
        b.add(base+vertices,face,TILE,label+' / '+name)
    fl=(x-half,front,z0);fr=(x+half,front,z0);vl=(x-.90,vent,z1);vr=(x+.90,vent,z1)
    top=(x,vent,tip);ridge=(x,crest,z2);rl=(x-half,back,z0);rr=(x+half,back,z0)
    panel([fl,fr,vr,vl],'front apron')
    panel([fl,vl,ridge,rl],'west fold');panel([fr,rr,ridge,vr],'east fold')
    panel([vl,top,ridge],'west cap');panel([top,vr,ridge],'east cap');panel([rl,ridge,rr],'rear hip')
    g=Plane(b,(0,vent),(1,0))
    g.put(Polygon([(x-.90,z1-.04),(x+.90,z1-.04),(x,tip-.07)]),.008,.112,SHADE,label+' / recessed triangular vent')
    for k,(u,t)in enumerate([(fl,vl),(fr,vr),(vl,top),(top,vr),(top,ridge)]):
        b.tube([u,t],.044,TILE,7,label+' / tile verge '+str(k+1))
def plaque(w):
    z=p['sign centre'];cx=C
    w.put(box(cx-1.56,z-.35,cx+1.56,z+.35),-.16,-.04,WOOD,'portal sign / red surround')
    w.put(box(cx-1.51,z-.295,cx+1.51,z+.295),-.183,-.15,STONE,'portal sign / pale plaque')
    # Interpret the three readable characters from photo 8 with simple authored pen strokes.
    chars=[[
        [(0.12,.50),(.80,.83)],[(.70,.96),(.30,.32),(.55,.44)],[(.52,.59),(.45,.10),(.32,.14)],[(.32,.31),(.10,.12)],[(.58,.31),(.77,.16)]],
        [[(.12,.09),(.13,.65),(.72,.89),(.68,.58),(.73,.2),(.93,.09),(.90,.22)],[(.24,.53),(.60,.62),(.43,.42),(.32,.33),(.59,.14)],[(.73,.57),(.53,.42),(.25,.10)]],
        [[(.03,.55),(.39,.61)],[(.28,.88),(.27,.11)],[(.27,.47),(.07,.18)],[(.25,.48),(.40,.30)],[(.44,.73),(.55,.62)],[(.66,.88),(.65,.42)],[(.85,.73),(.70,.60)],[(.40,.51),(.87,.63)],[(.64,.52),(.43,.37)],[(.65,.51),(.83,.38)],[(.43,.28),(.91,.37),(.78,.20),(.48,.06)],[(.58,.41),(.48,.23),(.79,.17)]]]
    for i,strokes in enumerate(chars):
        center=cx+(i-1)*.90
        shape=unary_union([LineString([(center+(u-.5)*.64,z+(v-.5)*.58)for u,v in stroke]).buffer(.020,quad_segs=3)for stroke in strokes])
        w.put(shape,-.211,-.180,SIGN,'portal sign / East-Wind inscription character '+str(i+1))
def south(b,lod):
    w=Plane(b,(0,0),(1,0));n=9 if lod else 17;holes=[]
    # Ground photo 10 identifies the six bays just west of the entrance.
    # The university's long historical negative and aerial view extend the count along both halves.
    for i in range(-11,12):
        # The small group of end bays foreshortens on the oblique entrance view.
        # Keep the calibrated central pitch and distribute the remaining width to the end pier.
        sign=1 if i>0 else -1
        end_axis=WIDTH-1.70 if i>0 else 1.70
        if abs(i)<=7:
            cx=C+DX*i
        else:
            start=C+sign*7*DX
            cx=start+(end_axis-start)*(abs(i)-7)/4
        half=1.20 if abs(i)>7 else (1.28 if i else 1.58)
        lower=span(cx,-.04 if i==0 else Z0,half,.37 if i else .49,Z1,n)
        upper=span(cx,Z2,half,.38,Z3,n)
        for j,opening in enumerate([lower,upper]):
            label=f'front bay {i+12:02} / level {j+1}';holes.append(opening)
            face_ring(w,opening,.19,(Z3 if j else Z1)-(.55 if i else .63),label)
            if i or j:sash(w,opening,label,lod,bool(j),sign_bay=(i==0 and j==1))
            crown=Z3 if j else Z1
            keystone=Polygon([(cx-.105,crown-.04),(cx+.105,crown-.04),(cx+.145,crown+.23),(cx-.145,crown+.23)])
            w.put(keystone,-.168,-.128,R,label+' / projecting crown brick')
        if -11<=i<11:
            k=i+1;sgn=1 if k>0 else -1
            endpoint=WIDTH-1.70 if k>0 else 1.70
            start=C+sgn*7*DX
            nxt=C+DX*k if abs(k)<=7 else start+(endpoint-start)*(abs(k)-7)/4
            xx=(cx+nxt)/2
            for k,(z,width,height) in enumerate([(Z1-.56,.43,.19),(Z1-.35,.55,.10),(Z3-.53,.47,.19),(Z3-.35,.56,.10)]):
                w.put(box(xx-width/2,z,xx+width/2,z+height),-.16,.025,R,f'front pier {i+12} / impost {k+1}')
    w.put(box(-.15,-.02,WIDTH+.16,E+.04).difference(unary_union(holes)),0,.39,G,'south front / pierced grey brick')
    for j,(z,h,front,mat) in enumerate([(0,.25,-.12,STONE),(.54,.105,-.08,R),(4.14,.13,-.10,R),(4.32,.16,-.18,R),(4.52,.095,-.23,R),(E-.24,.17,-.17,R),(E-.05,.14,-.27,R)]):
        strip=box(-.23,z,WIDTH+.22,z+h)
        if z<Z1:strip=strip.difference(span(C,-.1,1.58,.49,Z1,n))
        w.put(strip,front,.15,mat,'street front / string '+str(j+1))
    for x in [C-1.78,C+1.78]:
        block(b,x-.16,x+.16,.38,11.2,0,4.0,G,'entrance passage / side wall '+str(x))
    block(b,C-1.96,C+1.96,.38,11.2,3.96,4.16,PLASTER,'entrance passage / soffit')
    block(b,C-1.94,C+1.94,-.08,12.2,-.08,-.015,STONE,'entrance passage / paving')
    # Between the lower return and the white East-Wind sign, photo 8 resolves four projecting string courses.
    for k,(z,h,front) in enumerate([(4.11,.07,-.22),(4.23,.06,-.245),(4.37,.065,-.255),(4.51,.07,-.29)]):
        w.put(box(C-1.77,z,C+1.77,z+h),front,front+.15,R,'portal sign / stepped cornice '+str(k+1))
    plaque(w)
def courtyard(b,lod):
    n=11 if lod else 23
    for side,x0,x1 in [('west',12.7,36.2),('east',41.55,64.24)]:
        count=round((x1-x0)/CP);pitch=(x1-x0)/count;h=CAP+.72;w=Plane(b,(0,COURT),(1,0))
        openings=[]
        for j in range(count):
            x=x1-(j+.5)*(CP if side=='east'else pitch)
            opening=span(x,PLATFORM-.03,(CP if side=='east'else pitch)/2-.26,.72,h,n);openings.append(opening)
            face_ring(w,opening,.22,CAP-.08,f'{side} court opening {j+1}')
        # Underside stays open, with the shaded white wall set back behind the masonry arcade.
        w.put(box(x0,PLATFORM,x1,LOW).difference(unary_union(openings)),0,.44,G,side+' lower arcade / pierced grey face')
        for j in range(count+1):
            x=x1-j*(CP if side=='east' else pitch)
            if x<x0-.30:continue
            for k,(z0,z1,hw,mat)in enumerate([(PLATFORM,PLATFORM+.30,.33,STONE),(PLATFORM+.30,CAP-.27,.245,G),(CAP-.28,CAP-.18,.30,R),(CAP-.18,CAP+.06,.36,R),(CAP+.06,CAP+.14,.41,R),(CAP+.14,CAP+.29,.35,R),(CAP+.29,CAP+.34,.37,R)]):
                block(b,x-hw,x+hw,COURT-.13,COURT+.51,z0,z1,mat,f'{side} arcade post {j+1} / course {k+1}')
        back=Plane(b,(0,COURT+2.25),(1,0));back.put(box(x0,PLATFORM,x1,LOW-.15),.0,.23,PLASTER,side+' north gallery / back wall')
        block(b,x0,x1,COURT-.35,COURT+2.55,0,PLATFORM,STONE,side+' north gallery / raised floor')
        block(b,x0,x1,COURT+.42,COURT+2.55,LOW-.21,LOW-.09,PLASTER,side+' north gallery / undercroft ceiling')
        w.put(box(x0-.13,LOW-.17,x1+.13,LOW+.04),-.18,.28,R,side+' north gallery / fascia')
        hip(b,x0-.19,x1+.2,COURT-.42,49.55,LOW+.03,p['north ridge'],side+' north roof')
        if side=='east':
            for j in [0,3]:
                cx=x1-(j+1.50)*CP
                for k in range(4):
                    lo=(k+1)*.185
                    block(b,cx-1.22,cx+1.22,COURT-.35-(4-k)*.30,COURT-.34-k*.02,0,lo,STONE,f'courtyard approach {j+1} / tread {k+1}')
    for label,x,facing in [('east',64.24,(0,-1)),('west',12.73,(0,1))]:
        # The perpendicular return carries open pillars below red-framed upper glazing.
        start=COURT if label=='east' else 15.12;w=Plane(b,(x,start),facing);length=COURT-15.12;pitch=length/6;holes=[]
        for i in range(6):
            u=(i+.5)*pitch;low=span(u,PLATFORM-.05,pitch/2-.25,.70,CAP+.83,n);up=span(u,4.85,pitch/2-.28,.52,7.55,n)
            holes.extend([low,up]);face_ring(w,low,.21,CAP-.08,label+f' return / ground {i+1}');face_ring(w,up,.17,7.00,label+f' return / upper {i+1}');sash(w,up,label+f' upper court sash {i+1}',lod,True)
        w.put(box(0,PLATFORM,length,E).difference(unary_union(holes)),0,.42,G,label+' return / arcade and upper wall')
        for i in range(1,6):
            u=i*pitch
            w.put(box(u-.34,2.39,u+.34,2.64),-.145,.045,R,label+f' return / red impost {i}')
            w.put(box(u-.415,2.64,u+.415,2.78),-.173,.04,R,label+f' return / red impost cap {i}')
        w.put(box(0,3.58,length,3.86),-.17,.12,R,label+' return / sill course')
        inside=Plane(b,(x+(2.36 if label=='east' else -2.36),start),facing);outline=box(0,PLATFORM,length,4.24)
        lower=[]
        for i in range(6):
            u=(i+.5)*pitch;pane=box(u-.65,1.0,u+.65,2.65);lower.append(pane);sash(inside,pane,label+f' recessed gallery room {i+1}',lod,False)
        inside.put(outline.difference(unary_union(lower)),0,.26,PLASTER,label+' return / courtyard room wall')
        xa,xb=(x,x+2.77)if label=='east' else (x-2.77,x)
        block(b,xa,xb,15.1,COURT+.24,.01,PLATFORM,STONE,label+' return / court floor')
def add_building(b,lod=False):
    south(b,lod);courtyard(b,lod)
    # Only the plan and roof are known behind the outer elevations.
    for label,xa,xb in [('west',-.34,.03),('east',WIDTH-.04,WIDTH+.30)]:
        block(b,xa,xb,.39,50.03,0,E,G,label+' outer wall / plan envelope')
    hip(b,-.38,WIDTH+.38,-.35,14.45,E+.12,RIDGE,'south court roof')
    hip(b,-.54,12.76,6.92,50.53,E+.08,RIDGE-.18,'west wing roof',True)
    hip(b,64.06,WIDTH+.54,7.0,50.38,E+.08,RIDGE-1.13,'east wing roof',True)
    for i,(x,half)in enumerate([(3.33,3.25),(25.23,3.60),(46.98,3.58),(68.22,3.28)]):
        cross_apron(b,x,half,'front roof cross return '+str(i+1))
    for j,(xa,xb)in enumerate([(-.06,C-1.62),(C+1.62,WIDTH+.07)]):
        block(b,xa,xb,12.40,12.76,0,E-.16,G,'south wing / court envelope '+str(j+1))
    block(b,C-1.62,C+1.62,12.40,12.76,Z1+.15,E-.16,G,'south wing / upper wall over passage')
    # The photographed passage remains open through both faces.
    # Exterior rear skin is split at the same axis as the portal.
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output,META)
if __name__=='__main__':main()
