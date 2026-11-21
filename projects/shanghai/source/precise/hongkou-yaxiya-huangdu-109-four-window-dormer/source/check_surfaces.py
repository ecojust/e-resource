"""Independent first-hit tests for the four windows and two pitched portions."""
from pathlib import Path
import os,runpy
from huangdu_dormer import *
p=Path(os.environ['SHANGHAI_PROJECT_ROOT']) if 'SHANGHAI_PROJECT_ROOT' in os.environ else Path(__file__).resolve().parents[4]
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def test(name,origin,angle,expected,min_distance,max_distance):
        hit=reader.ray(origin,angle,4.0)
        good=hit is None if not expected else bool(hit and hit['material']in expected and min_distance <= hit['distance_m'] <= max_distance)
        rows.append(dict(part=name,origin=origin,direction=angle,expected=expected,hit=hit,passed=good))
    for idx,c in enumerate(CENTRES):
        mat=LIGHT if idx<2 else DARK
        glass=(GLASS_LIGHT,GLASS_LIGHT,GLASS_DARK,GLASS_GREEN)[idx]
        for z in (.41,.76,1.04,1.39):
            for sign in (-1,1):
                test('Side window frame',[c+sign*(W/2-.021),-1,z],[0,1,0],[mat],.96,1.05)
                test('Inset pane',[c+sign*.197,-1,z],[0,1,0],[glass],1.055,1.09)
        for z in (.38,.80,1.01):
            test('Meeting stile below top light',[c,-1,z],[0,1,0],[mat],.96,1.05)
        if idx>1:test('Horizontal top-light rail',[c+.20,-1,1.15],[0,1,0],[DARK],.97,1.025)
        test('Individual sill',[c+.09,-1,.193],[0,1,0],[FLASH],.88,.93)
    for x in (-2.055,-1.03,0,1.043,2.035):
        test('Roughcast piers',[x,-1,1.05],[0,1,0],[WALL],.995,1.005)
    for x in (-1.79,-.54,.51,1.63):
        test('Dark fascia',[x,-1,1.83],[0,1,0],[FLASH],.78,.81)
        test('Spandrel above windows',[x,-1,1.64],[0,1,0],[WALL],.995,1.005)
    for x in (-1.88,-.67,.46,1.73):
        for y in (.02,.31,.66,.89):
            top=1.855+.359*(y+.194)/1.184;test('Shallow clay covering',[x,y,3],[0,0,-1],list(TILES),3-top-.063,3-top+.003)
    for x in (-3.45,-3.10,-2.78,-2.39):
        for y in (-.01,.32,.69):
            top=.145+2.06*(y+.27)/1.26;test('Steep clay covering',[x,y,3],[0,0,-1],list(TILES),3-top-.065,3-top+.004)
    for y,z in ((.04,1.35),(.20,1.65),(.48,1.76)):
        test('Enclosed side of dormer',[-3.7,y,z],[1,0,0],[FLASH],1.48,1.54)
    test('Outside the isolated historic fragment',[-3.9,-1,.9],[0,1,0],[],0,0)
    return dict(passed=all(r['passed']for r in rows),samples=rows)
