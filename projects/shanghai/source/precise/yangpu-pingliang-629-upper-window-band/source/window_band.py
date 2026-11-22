"""Three measured bays in the upper street windows photographed in February 2021."""
from pathlib import Path
from math import pi,cos,sin
import json
trace=json.loads((Path(__file__).parent/'window-measurement.json').read_bytes())
def finish(rgb):
    return {'color':[(q/3294.6 if q<11 else ((q/255+.055)/1.055)**2.4) for q in rgb],'roughness':.74}
PALETTE={name:finish(rgb)for name,rgb in {
    'dark blue black frame':(47,53,55),'mullion edge':(60,65,65),'glazed sky':(118,141,151),
    'lower curtain glass':(153,161,157),'curtain fold':(127,140,139),'rust brown sill':(139,117,101),
    'soffit brown':(101,72,66),'deep soffit':(65,55,55),'green fascia':(72,99,86),
    'green relief':(91,117,101),'cornice green':(66,85,77),'stone band':(155,151,141)}.items()}
X0=(trace['posts'][0]['sill'][0]+trace['posts'][-1]['sill'][0])/2
W=trace['posts'][-1]['sill'][0]-trace['posts'][0]['sill'][0]
SILL=0.24
TOP=1.50
def block(b,x,y,z,width,depth,height,mat,label):
    b.box((x,y,z),(width,depth,height),mat,label=label)
def add_building(b,lod=False):
    posts=[v['sill'][0]-X0 for v in trace['posts']]
    rails=[v-2.255+.24 for v in sorted(trace['transom_z_over_camera_m'])]
    for index,x in enumerate(posts):
        width=.080 if index in (1,2) else .066
        block(b,x,-.042,(TOP+SILL)/2,width,.122,TOP-SILL,'dark blue black frame','main steel post '+str(index+1))
        block(b,x+.010,-.108,(TOP+SILL)/2,.016,.016,TOP-SILL,'mullion edge','exposed edge of post '+str(index+1))
    for ix,group in enumerate(trace['secondary_mullion_x_m']):
        xs=[posts[ix]]+[x-X0 for x in group]+[posts[ix+1]]
        for j,x in enumerate(xs[1:-1]):
            width=.036 if j==2 else .021
            block(b,x,-.005,(TOP+SILL)/2,width,.071,TOP-SILL,'dark blue black frame','bay '+str(ix+1)+' vertical bar '+str(j+1))
        for k,z in enumerate(rails):
            block(b,(xs[0]+xs[-1])/2,-.011,z,xs[-1]-xs[0],.062,.023,'dark blue black frame','horizontal glazing bar '+str(ix+1)+'-'+str(k+1))
        zz=[SILL]+rails+[TOP]
        for col,(low,high) in enumerate(zip(xs,xs[1:])):
            for row,(bot,top) in enumerate(zip(zz,zz[1:])):
                edge=.012 if col not in (0,5) else .022
                block(b,(low+high)/2,.055,(bot+top)/2,high-low-2*edge,.018,top-bot-.019,
                      'lower curtain glass' if row==0 else 'glazed sky','bay '+str(ix+1)+' glazing '+str(col+1)+'-'+str(row+1))
                if row==0 and not lod:
                    for q in (1,2):
                        x=low+(high-low)*q/3
                        block(b,x,.044,(bot+top)/2,.007,.006,(top-bot)*.87,'curtain fold','lower fabric fold behind glass')
    for z,mat,d,h,y,label in (
        (.084,'rust brown sill',.246,.130,-.04,'brown outer sill cover'),
        (.164,'stone band',.218,.044,-.032,'sill upper ledge'),
        (.222,'dark blue black frame',.13,.061,-.031,'window sill rail'),
        (1.510,'dark blue black frame',.115,.052,-.02,'continuous window upper rail'),
        (1.594,'mullion edge',.193,.068,-.045,'two-level head moulding'),
        (1.785,'deep soffit',.22,.324,-.02,'shadow below wide eaves'),
        (2.018,'soffit brown',.42,.169,-.102,'red-brown apron of eaves'),
        (2.132,'cornice green',.49,.064,-.13,'lower edge of green facing'),
        (2.255,'green fascia',.18,.19,-.251,'green fascia roll backing'),
        (2.387,'cornice green',.51,.073,-.134,'green coping above small relief')):
        block(b,0,y,z,W+.122,d,h,mat,label)
    # The photographed repeated green relief has a rising centre and two curved low sides.
    count=21
    spacing=W/count
    for j in range(count):
        x=-W/2+(j+.5)*spacing
        for raised in (0,.063):
            path=[]
            for k in range(9 if lod else 19):
                t=k/(8 if lod else 18);a=(t-.5)*2*pi
                path.append((x+(t-.5)*spacing*.95,-.355,2.188+raised+.034*(.5+.5*cos(a))))
            b.tube(path,.012 if raised else .014,'green relief',5 if lod else 8,'double undulating green relief '+str(j+1))
