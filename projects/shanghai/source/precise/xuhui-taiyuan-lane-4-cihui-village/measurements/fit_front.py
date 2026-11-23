"""Fit square-pixel photographs against the axes of the two adjoining street elevations."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
# Coordinates refer to the stored observation raster size, before any perspective correction.
# a/b = bottom left/right, c/d = upper left/right; h = crown or head centre.
SIZES={'p13':(667,500),'p14':(667,500),'j20':(650,487),'j18':(650,487),'p59':(550,412)}
# Compact records: label, local X or Y, nominal width, level.
GROUPS=[
 ('ag1',2.55,1.05,'ag'),('ag2',6.35,1.05,'ag'),('am1',3.60,.96,'am'),('am2',6.12,.96,'am'),
 ('rg1',9.10,.71,'rg'),('rg2',11.78,1.19,'rg'),('rm1',9.10,.71,'rm'),('rm2',11.78,1.19,'rm'),
 ('rt1',9.10,.71,'rt'),('rt2',11.78,1.19,'rt'),('bay',4.95,3.94,'bay'),
 ('sg1',1.86,1.10,'sg'),('sm1',1.86,1.10,'sm'),('st1',1.86,1.10,'st'),
 ('sg2',4.72,1.07,'sg'),('sm2',4.72,1.07,'sm'),('st2',4.72,1.07,'st')]
HEIGHTS={'ag':(.94,2.93),'am':(4.83,6.51),'rg':(1.12,2.81),'rm':(5.14,6.46),'rt':(7.94,9.07),'bay':(7.69,9.19),'sg':(1.07,2.65),'sm':(4.22,5.79),'st':(7.38,8.53)}
# Each opening stays on its surveyed wall. The projecting glazed upper bay has its own plane.
OBS={
'p13':{'ag1a':(111,413),'ag1b':(134,414),'ag1h':(127,346),'ag2a':(234,416),'ag2b':(262,418),'ag2h':(253,349),
'am1a':(155,275),'am1b':(175,274),'am1h':(168,222),'am2a':(231,269),'am2b':(256,269),'am2h':(248,214),
'rg1a':(343,416),'rg1c':(346,357),'rg2a':(434,417),'rg2b':(478,419),'rg2c':(434,360),'rg2d':(477,360),
'rm1b':(375,249),'rm1d':(375,215),'rm2a':(434,246),'rm2b':(474,245),'rm2d':(473,196),
'baya':(146,154),'bayb':(247,144),'edge0':(566,497)},
'p14':{'am1a':(83,440),'am1b':(119,438),'am1h':(113,335),'am2a':(224,429),'am2b':(278,426),'am2h':(263,320),'baya':(87,220),'bayb':(260,198),'rm1b':(505,395),'rm1d':(503,314)},
'j20':{'am1a':(268,229),'am1b':(304,230),'am1h':(285,165),'am2a':(371,234),'am2b':(396,237),'am2h':(385,176),
'rg1a':(489,366),'rg1b':(503,366),'rg1c':(490,325),'rg2a':(547,365),'rg2b':(568,363),'rg2c':(546,323),'rg2d':(567,322),
'rm1a':(474,232),'rm1b':(497,233),'rm1c':(472,194),'rm2a':(535,239),'rm2b':(552,239),'rm2c':(533,204),
'rt1a':(468,125),'rt1b':(482,127),'rt1c':(466,89),'rt2a':(520,130),'rt2b':(539,134),'rt2d':(538,101),
'baya':(275,87),'bayb':(407,108),'bayc':(274,47),'bayd':(407,66)},
'j18':{'edge0':(371,412),'edge1':(350,54),'rg2a':(303,361),'rg2b':(324,359),'rg2c':(301,321),'rg2d':(322,318),
'rg1a':(254,365),'rg1b':(264,364),'rg1c':(253,327),'rm2a':(301,235),'rm2b':(322,232),'rm2c':(299,200),'rt2a':(299,126),'rt2b':(319,121),'rt2c':(297,96),
'sm1a':(397,244),'sm1b':(409,249),'sm1c':(393,205),'sm1d':(407,210),'st1a':(389,140),'st1b':(403,146),'st1c':(386,104),'st1d':(400,110),
'sm2a':(439,209),'sm2b':(450,216),'sm2c':(436,174),'st2a':(431,114),'st2b':(441,122),'st2c':(429,87)},
'p59':{'sm1a':(50,259),'sm1b':(99,269),'sm1c':(68,205),'sm1d':(117,212),'st1a':(111,121),'st1b':(147,125),'st1c':(123,96),'st1d':(155,98),
'sg2a':(216,365),'sg2b':(275,368),'sg2c':(226,299),'sg2d':(279,302),'sm2a':(241,201),'sm2b':(285,203),'sm2c':(251,157),'sm2d':(288,160),
'st2a':(256,85),'st2b':(291,89),'st2c':(265,57),'st2d':(292,59)}}
# The first return bay is lower in all three levels. Its corner starts at the main front cornice.
# Window surrounds in the corner station were picked on their masonry lips in some vegetation.
HOLD={'p13':{'ag1h','am2b','rg2b'},'p14':{'am1b','am2h'},'j20':{'am2b','rg2d','rt2d'},'j18':{'rg2b','st1d','sm2b'},'p59':{'st1b','sm2d'}}
def camera(row,sz):
    eye=np.array(row[:3]);yaw,pitch,roll=row[3:6];f=row[6]
    fw=np.array([np.cos(pitch)*np.sin(yaw),np.cos(pitch)*np.cos(yaw),np.sin(pitch)])
    right=np.array([np.cos(yaw),-np.sin(yaw),0]);down=np.cross(fw,right)
    R=np.array([np.cos(roll)*right+np.sin(roll)*down,-np.sin(roll)*right+np.cos(roll)*down,fw])
    K=np.array([[f,0,sz[0]/2],[0,f,sz[1]/2],[0,0,1.]])
    return K@np.c_[R,-R@eye]
# The length value may be revised by the separately documented street-station survey.
NAMES=list(SIZES);REACH=13.6; INDEX={g[0]:i for i,g in enumerate(GROUPS)};L=list(HEIGHTS)
def build():
    initial={'p13':[12,-15,1.7,-.35,.22,-.02,550],'p14':[11,-10,1.7,-.52,.48,-.015,540],
      'j20':[-4,-18,1.65,.53,.16,0,650],'j18':[30,-19,1.55,-.83,.20,.01,820],
      'p59':[23,2.2,.95,-1.51,.52,.02,465]}
    n=len(GROUPS)
    pcs=np.array([initial[k] for k in NAMES]);geom=np.array([v[1:3] for v in GROUPS]);levels=np.array(list(HEIGHTS.values()))
    q0=np.r_[pcs.ravel(),geom.ravel(),levels.ravel(),9.64,.53,1.08]
    def unpack(q):return q[:35].reshape(-1,7),q[35:35+2*n].reshape(-1,2),q[35+2*n:-3].reshape(-1,2),q[-3:]
    def xyz(k,par):
        pc,g,lev,(edge,proj,step)=par
        if k.startswith('edge'):return (REACH,0,0 if k[-1]=='0' else edge)
        nm,c=k[:-1],k[-1];i=INDEX[nm];pos,width=g[i]
        bot,top=lev[L.index(GROUPS[i][3])]
        if nm[:1]=='s' and nm[-1]=='1':bot-=step;top-=step
        along=pos+width*({'a':-.5,'b':.5,'c':-.5,'d':.5,'h':0}[c]);z=bot if c in 'ab' else top
        if nm.startswith('s'):return (REACH,along,z)
        return (along,-proj if nm=='bay' else 0,z)
    def points(q):
        par=unpack(q);M={k:camera(row,SIZES[k]) for k,row in zip(NAMES,par[0])}
        xy={k:{} for k in NAMES}
        for k,obs in OBS.items():
            for key,uv in obs.items():
                p=M[k]@[*xyz(key,par),1];xy[k][key]=p[:2]/p[2]
        return xy
    def residual(q):
        par=unpack(q);xy=points(q);r=[]
        for k,obs in OBS.items():
            for key,uv in obs.items():
                if key not in HOLD[k]:r.extend((xy[k][key]-uv)/2.2)
        pc,g,lev,extra=par
        r.extend(((g-geom)/[1.0,.30]).ravel());r.extend(((lev-levels)/.48).ravel());r.extend((extra-q0[-3:])/[.48,.18,.28])
        for arr in pc:r.extend([(arr[2]-1.72)/.6,(arr[6]-610)/250,arr[5]/.14])
        # The side and front stacks share vertical jambs within each rectangular group.
        for a,b in [('rg1','rm1'),('rm1','rt1'),('rg2','rm2'),('rm2','rt2'),('sg1','sm1'),('sm1','st1'),('sg2','sm2'),('sm2','st2')]:
            r.append((g[INDEX[a],0]-g[INDEX[b],0])/.085)
        return r
    out=least_squares(residual,q0,loss='soft_l1',f_scale=2.5,max_nfev=420)
    pc,g,lev,extra=unpack(out.x);xy=points(out.x);wins={}
    for i,(name,_,__,level) in enumerate(GROUPS):
        lo,hi=lev[L.index(level)];off=extra[2] if name.startswith('s') and name.endswith('1') else 0
        wins[name]=dict(along=g[i,0],width=g[i,1],sill=lo-off,top=hi-off)
    rows={k:[dict(key=key,pixel=list(uv),predicted=xy[k][key].tolist(),error_px=round(float(np.linalg.norm(xy[k][key]-uv)),2),held_out=key in HOLD[k]) for key,uv in obs.items()] for k,obs in OBS.items()}
    return dict(width_assumption=REACH,units='approximate display metres',references={'p13':'paper-13','p14':'paper-14','p59':'people-59','j20':'jp-20','j18':'jp-18'},rasters=SIZES,cameras={k:camera(row,SIZES[k]).tolist() for k,row in zip(NAMES,pc)},camera_rows=dict(zip(NAMES,pc.tolist())),windows=wins,cornice_z=extra[0],bay_projection=extra[1],return_step_z=extra[2],observations=rows)
if __name__=='__main__':
    result=build();(HERE/'registered-street-cameras.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for k,rows in result['observations'].items():print(k,np.median([r['error_px'] for r in rows]),[r['error_px'] for r in rows if r['held_out']])
