"""Trace the two stair flights, open balustrade, glazing, original roof and raised letters."""
from pathlib import Path
import argparse,json,runpy,sys

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/huangpu-guangci-maternity-pavilion-twin-stair/source'
sys.path.insert(0,str(SOURCE))
from build_model import META
from pavilion_materials import BRICK,CREAM,EDGE,WOOD,GLASS,REFLECT,DARK,TILE,ROOF_SHADE,BLACK,MOSAIC,MOSAIC_DARK,FONT
from courtyard_stairs import TREAD,PALE,EDGE as RAIL_EDGE
from sign_lettering import lettering_shapes
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def probes():
    cases=[]
    def check(name,pos,vector,length,mats=None,interval=None):
        cases.append(dict(name=name,origin=pos,direction=vector,length=length,allowed=mats,range_m=interval))
    for hand in [-1,1]:
        for step in range(12):
            y=-6.25+(step+.5)*3.07/12
            top=2.20*(step+1)/12
            check(f'lower tread {hand} {step+1}',[hand*10.475,y,5],[0,0,-1],5,[TREAD],[5-top-.003,5-top+.003])
        for step in range(9):
            x=8.81-(step+.5)*(8.81-6.58)/9
            top=2.20+(step+1)*1.60/9
            check(f'upper tread {hand} {step+1}',[hand*x,-1.65,5],[0,0,-1],5,[TREAD],[5-top-.003,5-top+.003])
        for x in [8.81,12.14]:
            check('ground-level post cap '+str(hand*x),[hand*x,-6.25,2.40],[0,0,-1],2.40,[RAIL_EDGE,PALE],[.68,.75])
        check('intermediate landing '+str(hand),[hand*10.48,-2.11,5],[0,0,-1],5,[TREAD],[2.797,2.803])
    for x in [-6.58,-2.30,2.30,6.58]:
        check('terrace post crown '+str(x),[x,-3.18,6],[0,0,-1],2,[RAIL_EDGE,PALE],[.66,.72])
    for left,right,count in [(-6.58,-2.30,9),(-2.30,2.30,10),(2.30,6.58,9)]:
        width=(right-left-.58)/count
        for slot in range(count):
            x=left+.29+(slot+.5)*width
            check(f'baluster neck {left} {slot}',[x,-4.00,4.64],[0,1,0],1.15,[PALE],[.742,.785])
            if slot+1<count:
                check(f'open balustrade {left} {slot}',[x+width/2,-4.00,4.64],[0,1,0],1.15)
    for x in [-4.64,-1.18,.85,4.88]:
        for y in [-2.61,-1.71,-.41]:
            check(f'terrace paving {x} {y}',[x,y,4.03],[0,0,-1],.35,[TREAD],[.225,.235])
    for x in [-.95,-.38,.42,.96]:
        for z in [.41,1.65,2.98]:
            check(f'lower door approach {x} {z}',[x,-6.55,z],[0,1,0],3.30)
            check(f'lower door timber {x} {z}',[x,-6.55,z],[0,1,0],3.78,[WOOD,DARK,BLACK],[3.44,3.65])
    for centre,wall_y in [(-16.12,.48),(-10.56,.48),(-5.18,0),(5.18,0),(10.56,.48),(16.12,.48)]:
        for dx in [-.34,.34,-1.21,1.21]:
            check(f'tall window pane {centre} {dx}',[centre+dx,-.37,7.35],[0,1,0],1.35,[GLASS,REFLECT],[.54+wall_y,.66+wall_y])
        for dx in [-.78,.78]:
            check(f'continuous stone mullion {centre} {dx}',[centre+dx,-.37,7.35],[0,1,0],1.1,[CREAM],[.31+wall_y,.32+wall_y])
    for x in [-.85,-.28,.28,.85]:
        check('upper glazed fanlight '+str(x),[x,-.54,8.52],[0,1,0],.94,[GLASS,REFLECT],[.72,.79])
    for x in [-1.59,1.59,-2.13,2.13]:
        check('brick between door and tall windows '+str(x),[x,-.31,8.39],[0,1,0],.44,[BRICK],[.305,.315])
    for text,u,z,width,height,face_y,expected,mat in [
        ('MATERNITÉ',0,15.31,5.25,.49,0,.135,EDGE),
        ('慈',-4.30,13.10,.53,.55,0,.112,EDGE),('科',-2.45,14.19,.53,.55,0,.112,EDGE),
        ('產',2.45,14.19,.53,.55,0,.112,EDGE),('廣',4.30,13.10,.53,.55,0,.112,EDGE),
        ('8',0,10.07,.43,.59,0,.185,BLACK)]:
        for i,(letter,glyph) in enumerate(lettering_shapes(text,width,height,font=FONT)):
            point=max(getattr(glyph,'geoms',(glyph,)),key=lambda poly:poly.area).representative_point()
            hit=.55+face_y-expected
            check(f'raised {text} letter {i+1} {letter}',[u+point.x,-.55,z+point.y],[0,1,0],.66,[mat],[hit-.009,hit+.009])
    for side in [-1,1]:
        for y in [3.56,4.62]:
            x=side*18.75
            z=11.38+(y+1.25)*(16.45-11.38)/7.10
            check(f'outer tile channel {x} {y}',[x,y,18.2],[0,0,-1],9,[TILE,ROOF_SHADE],[18.2-z-.15,18.2-z-.032])
        attics=[(side*16.14,.48,12.21,13.89)]
        if side<0:attics.append((0,0,12.52,13.86))
        for centre,front,sill,top in attics:
            for dx in [-.87,.83]:
                for z in [sill+.19,top-.44]:
                    check(f'attic glazing beyond full apron {centre} {dx} {z}',
                          [centre+dx,-1.45,z],[0,1,0],2.34,[GLASS,REFLECT],[1.63+front,1.67+front])
        for centre,half,peak,base,ys in [(0,8.62,16.10,11.79,[.65,2.23]),(side*16.14,3.89,14.87,11.68,[1.13,1.77])]:
            for dx,y in zip([.58,.92],ys):
                x=centre+side*dx
                z=peak-dx*(peak-base)/half
                check(f'intersecting secondary roof {x} {y}',[x,y,17.7],[0,0,-1],8,
                      [TILE,ROOF_SHADE],[17.7-z-.15,17.7-z-.032])
    for x,y,wall,base in [(0,-.64,0,11.79),(-16.14,-.23,.48,11.68),(16.14,-.23,.48,11.68)]:
        z=11.38+(base-.15-11.38)*(y+1.25)/(wall+.03+1.25)
        check(f'tiled apron below attic window {x}',[x,y,18],[0,0,-1],9,[TILE,ROOF_SHADE],[18-z-.15,18-z-.032])
    for x,y in [(-20.7,-1),(21,-1),(-15,-5),(15,-5),(0,-7),(5,6.3)]:
        check(f'beyond model scope {x} {y}',[x,y,19],[0,0,-1],19.5)
    return cases


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for role in ['raw','full','lod','output']:p.add_argument(role,type=Path)
    args=p.parse_args()
    expected=probes();reports={role:inspect(getattr(args,role),expected) for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(reports,ensure_ascii=False,indent=1)+'\n')
    for role,report in reports.items():print(role,len(report['cases']),[(c['name'],c['first_hit'])for c in report['cases'] if not c['passed']][:22],flush=True)
    raise SystemExit(not all(r['passed'] for r in reports.values()))
