"""Independent first-hit checks of the released street walls, sign bands, shopfronts and open passage."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(HERE.parent/'source'))
from glb_triangles import SerialScene
import street_masonry as wall
import rongkang_window_sashes as frames
def check(mesh):
    scene=SerialScene(mesh);table=frames.schedule();physical=[];native=[]
    def hit(group,title,eye,vec,end,allowed,mask=None,**meta):
        eye=np.array(eye,float);vec=np.array(vec,float);r=scene.ray(eye,vec,end,mask)
        actual=None if r is None else r['material'];group.append(dict(feature=title,
          passed=actual in allowed,first_material=actual,allowed=allowed,eye=np.round(eye,4).tolist(),
          direction=np.round(vec,7).tolist(),limit=end,**meta))
    glazing=[frames.GLASS,frames.SHADE,frames.IRON,frames.WHITE]
    shop=[wall.TIN,wall.GLAZE,wall.SHADE,wall.WARM]
    for op in table['openings']:
        face=table['surfaces'][op['facade']]
        side=face.get('inward_sign',1);axis=1 if face['axis']=='X'else 0
        
        direction=np.zeros(3);direction[axis]=side
        for ufrac,zfrac in [(.28,.32),(.67,.55),(.43,.77)]:
            u=op['u0']+ufrac*(op['u1']-op['u0']);z=op['z0']+zfrac*(op['z1']-op['z0'])
            q=np.asarray(frames.frame_point(face,u,0,z),float);eye=q-direction*.30
            hit(physical,op['id']+' filled aperture',eye,direction,.56,glazing)
            hit(physical,op['id']+' opening through roughcast',eye,direction,.54,[None],lambda m:m==wall.PLASTER)
    for side,g in wall.LAYOUT['storefronts'].items():
        for b in g['bays']:
            for frac in [.18,.37,.68,.82]:
                u=b['left']+(b['right']-b['left'])*frac
                for hfrac in [.38,.71]:
                    z=b['base']+(b['head']-b['base'])*hfrac;eye=[u,-1.46,z]
                    hit(physical,b['id']+' shop glass',eye,[0,1,0],3.5,shop)
                    hit(physical,b['id']+' shop wall cropped around door',eye,[0,1,0],2.11,[None],lambda m:m in (wall.LIGHT,wall.ASH))
        for u in ([g['left']+.23,-9.82,-6.42,-2.46]if side=='south'else[2.05,4.42,8.54,11.38]):
            hit(physical,side+' opaque street pier',[u,-1.6,1.65],[0,1,0],3.1,[wall.LIGHT,wall.ASH])
        for f in [.062,.5,.96]:
            x=g['left']+(g['right']-g['left'])*f;z=wall.sign_slope(g,x,g['fascia_top'])-.021
            hit(physical,side+' fascia top finish',[x,-2,z],[0,1,0],4,[wall.STONE,wall.BLUE])
    for n,g in wall.LAYOUT['models'].items():
        face=table['surfaces'][g['front']]
        for band in ['raised','low']:
            a,c,z=g[band];u=a+.59*(c-a);y=wall.flat_depth(face,u)
            hit(physical,n+' '+band+' roof coping',[u,y-.055,z+.49],[0,0,-1],.82,[wall.TRIM])
            hit(physical,n+' '+band+' roof deck behind wall',[u,y+.83,z+.55],[0,0,-1],2,[wall.ROOF,wall.STEEL])
        a,c,z=g['fin'];u=(a+c)/2;y=wall.flat_depth(face,u)
        hit(physical,n+' fin cap',[u,y-.19,z+.45],[0,0,-1],.8,[wall.TRIM])
        for i in [0,1]:
            floor=str(3-i);ops=sorted([o for o in table['openings']if o['facade']==g['front']and o['front_pair']and o['id'].endswith(floor)],key=lambda o:o['u0'])
            u=(ops[0]['u1']+ops[1]['u0'])/2
            for pct in [.25,.55,.81]:
                z=ops[0]['z0']+(ops[0]['z1']-ops[0]['z0'])*pct
                hit(physical,n+' ribbed red field '+floor,[u,-1.55,z],[0,1,0],4,[wall.CLAY,wall.CLAY2,wall.MORTAR])
    for x in [-.66,-.12,.4,.77]:
        for z in [.41,1.28,2.1]:
            hit(physical,'passage remains open',[x,-1.46,z],[0,1,0],5.62,[None])
    plaque=json.loads((HERE/'south-shop-pier-panels.json').read_bytes())['world_panels']['green_address_plate']
    bl,br,tr,tl=np.array(plaque)
    for letter,lo,hi,u,v,expected in [('first numeral 1',.19,.34,.6,.50,wall.NUMERAL),('second numeral 1',.43,.57,.6,.50,wall.NUMERAL),('last numeral 8 left stroke',.665,.85,.18,.70,wall.NUMERAL),('last numeral 8 upper counter',.665,.85,.50,.73,wall.ENAMEL),('last numeral 8 lower counter',.665,.85,.50,.31,wall.ENAMEL)]:
        x=lo+(hi-lo)*u;h=.34+.47*v
        point=(1-x)*((1-h)*bl+h*tl)+x*((1-h)*br+h*tr)
        hit(physical,'118 enamel address '+letter,[point[0],-1.46,point[2]],[0,1,0],3.4,[expected])
    stations=json.loads((HERE/'streetfront-photo-controls.json').read_bytes())['stations']
    for k,lst in {
       'commons': [('south 2017 shop fascia',[(420,2190),(1010,2198),(1910,2211)],[wall.RED,wall.BLUE]),
                   ('south showroom glass',[(772,2542),(995,2595),(1152,2638)],shop),
                   ('south narrow shop displays',[(169,2648),(1862,2621)],shop),
                   ('green 118 shop plaque',[(1591,2417),(1614,2434),(1634,2422)],[wall.ENAMEL,wall.NUMERAL]),
                   ('north recessed signs',[(3324,2220),(4122,2263),(4690,2245)],wall.SIGNS+list(__import__('shop_signs').PALETTE)),
                   ('north 2017 glazing',[(3318,2692),(4109,2682),(4672,2660)],shop)],
       'winter21-north-north':[('north shop fascia coping',[(450,582),(690,581)],[wall.STONE,wall.TRIM]),
                   ('north 2021 dark window lights',[(407,480),(672,540),(512,320)],glazing),
                   ('north facade coarse render',[(456,386),(618,403),(749,482)],[wall.PLASTER])]} .items():
        P=np.array(stations[k]['matrix']);eye=-np.linalg.solve(P[:,:3],P[:,3])
        for label,pts,allowed in lst:
            for xy in pts:
                hit(native,label,eye,np.linalg.solve(P[:,:3],[*xy,1.]),90,allowed,source=k,native_uv=xy)
    return dict(asset=scene.asset,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),physical=physical,native=native,
                counts={k:[sum(a['passed']for a in arr),len(arr)]for k,arr in [('physical',physical),('native_pixels',native)]})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    j=check(a.mesh);a.output.write_text(json.dumps(j,indent=1)+'\n');print(j['counts'])
    for e in j['physical']+j['native']:
        if not e['passed']:print(e['feature'],e.get('native_uv',''),e['first_material'],e['eye']if 'native_uv'not in e else '')
