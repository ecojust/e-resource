"""Common wall of the courtyard entrances, with through-cuts for both numbered doors and upper windows."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from courtyard_materials import PALETTE,PLASTER,RED,WHITE,WOOD,SOFFIT,STONE,GUTTER,PIPE
from paired_entrances import door_openings
from upper_sashes import opening_profiles
def wall(b,section,y0,y1,mat,label):
    if not section.is_empty:b.prism(section,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)
def block(b,left,right,front,back,low,high,mat,label):
    b.box(((left+right)/2,(front+back)/2,(low+high)/2),(right-left,back-front,high-low),mat,label=label)
def add_wall(b,lod=False):
    left,right=-1.57,5.18
    bottom=-.71
    # The top line of the limewash sweeps slightly upwards across the court.
    white_top=[(left,4.03),(-.70,4.17),(1.02,4.16),(2.19,4.23),(3.92,4.24),(right,4.26)]
    white=Polygon([(left,bottom),(right,bottom),*reversed(white_top)])
    wall_shape=Polygon([(left,bottom),(right,bottom),(right,8.86),(left,8.67)])
    openings=unary_union([Polygon(d['outline_xz']) for d in door_openings()]+list(opening_profiles().values()))
    wall(b,white.difference(openings),0.,.35,WHITE,'Courtyard face | limewashed lower masonry')
    wall(b,wall_shape.difference(white).difference(openings),0.,.35,PLASTER,'Courtyard face | dark upper brickwork')
    def band(z0,z1,rise,mat,projection,label):
        skin=Polygon([(left,z0),(right,z0+rise),(right,z1+rise),(left,z1)])
        wall(b,skin.difference(openings),-projection,.001,mat,label)
    band(5.57,5.74,.20,RED,.021,'Courtyard face | red horizontal window belt')
    band(5.72,5.79,.20,RED,.041,'Courtyard face | projecting sill course')
    band(8.47,8.56,.19,RED,.024,'Courtyard eaves | brick fillet')
    band(8.55,8.69,.19,RED,.052,'Courtyard eaves | red top courses')
    # The original shows a narrow timber fascia and a shallow projecting eave.
    # Preserve the visible cut at its rear. The hidden main roof is outside this exhibit.
    def eave(yy,z):return z+.19*(yy-left)/(right-left)
    def slant_box(xa,xb,ya,yb,za,zb,mat,title):
        pp=Polygon([(xa,eave(xa,za)),(xb,eave(xb,za)),(xb,eave(xb,zb)),(xa,eave(xa,zb))])
        wall(b,pp,ya,yb,mat,title)
    slant_box(left-.06,right+.055,-.35,.36,8.66,8.744,SOFFIT,'Courtyard eaves | timber soffit')
    # This board is seen edge-on against the grey underside. Its independently
    # recorded boundary drops towards the left corner; trace it on its front plane.
    P=np.asarray(json.loads((Path(__file__).resolve().parents[1]/'measurements/paired-entrance-cameras.json').read_bytes())['camera_P'])
    def unproject(u,v,y):
        A=P[:2]-np.array([[u],[v]])*P[2]
        x,z=np.linalg.solve(A[:,[0,2]],-A[:,3]-y*A[:,1])
        return x,y,z
    fy=-.405
    marks=[(95,44),(120,38),(145,32),(180,26),(205,20)]
    xz=np.array([unproject((u+.5)*3264/459-.5,(v+.5)*4912/690-.5,fy)[::2] for u,v in marks])
    slope,intercept=np.polyfit(xz[:,0],xz[:,1],1)
    xa,xb=left-.06,right+.055
    z0,z1=intercept+slope*xa,intercept+slope*xb
    wall(b,Polygon([(xa,z0),(xb,z1),(xb,z1+.182),(xa,z0+.182)]),fy,fy+.067,WOOD,'Courtyard eaves | painted fascia')
    for i in range(44):
        a=left+(right-left)*i/44+.006;c=left+(right-left)*(i+1)/44-.006
        slant_box(a,c,-.332,-.008,8.646,8.664,SOFFIT,'Courtyard eaves | underside board joints')
    # The two short wall returns close the locally observed facade section at the alley corners.
    for side,x0,x1 in [('left',left,left+.21),('right',right-.21,right)]:
        block(b,x0,x1,.35,.69,bottom,4.14,WHITE,'Courtyard '+side+' | shallow lower return')
        block(b,x0,x1,.35,.69,4.14,8.69,PLASTER,'Courtyard '+side+' | shallow upper return')
    # The western pipe clamp is independently visible in both source photographs.
    # The partly cropped east pipe is fitted to both observed axes with a near-vertical prior.
    pipe_fit=json.loads((Path(__file__).resolve().parents[1]/'measurements/pipe-centrelines.json').read_bytes())
    for side,base,high,rad in [('west',3.73,6.64,.049),('east',3.79,6.62,.047)]:
        fit=pipe_fit[side]
        x,y,z=fit['axis_at_5.244m'];sx,sy=fit['delta_xy_per_m_z']
        def on_axis(h):return(x+(h-z)*sx,y+(h-z)*sy,h)
        tracked=[on_axis(base),on_axis(high)]
        if side=='west':
            for ux,vy,depth in [(47,170,-.251),(68,113,-.264),(97,85,-.289),(109,65,-.324),(112,49,-.369)]:
                q=unproject(ux*3264/720,vy*4912/(690*720/459),depth)
                if q[2]>tracked[-1][2]+.055:tracked.append(q)
        else:
            tracked.append(on_axis(8.26))
            xx,yy,zz=on_axis(8.54)
            tracked.extend([(xx,yy+.14,zz),(xx,yy+.31,zz+.17)])
        b.tube(tracked,rad,PIPE,10 if lod else 16,'Courtyard '+side+' | pale downpipe')
        for h in ([5.244,6.51] if side=='west' else [4.99,6.31]):
            b.tube([on_axis(h-.018),on_axis(h+.024)],rad+.005,PIPE,10 if lod else 16,'Courtyard '+side+' | joint collar')
    # The 2015 full-height view shows the landing beyond the open door and a grey
    # interior wall. Only this shallow visible portion of the entryway is represented.
    from courtyard_materials import INTERIOR,FLOOR,RECESS,INNERWOOD
    yback=2.02
    block(b,2.46,4.89,.28,yback+.13,-.27,-.159,FLOOR,'No 11 | floor inside open entry')
    block(b,2.46,4.89,yback,yback+.12,-.20,3.25,INTERIOR,'No 11 | wall at back of photographed recess')
    block(b,2.39,2.50,.31,yback,-.20,3.25,INTERIOR,'No 11 | west passage return')
    block(b,4.83,4.94,.31,yback,-.20,3.25,INTERIOR,'No 11 | east passage return')
    block(b,2.46,4.89,.31,yback,3.20,3.31,RECESS,'No 11 | passage soffit')
    def backpoint(u,v):
        m=P[:2]-np.array([u,v])[:,None]*P[2];return np.linalg.solve(m[:,[0,2]],-m[:,1]*yback-m[:,3])
    # This small dark-edged rectangle is visible on the rear plaster to the left of the door centre.
    native=[(2126,3181),(2427,3117),(2412,3426),(2115,3475)]
    panel=Polygon([backpoint(u,v)for u,v in native])
    wall(b,panel.difference(panel.buffer(-.035,join_style='mitre')),yback-.039,yback+.008,INNERWOOD,'No 11 | outline on rear plaster')
    block(b,-1.04,1.02,.78,.90,-.13,3.13,RECESS,'No 9 | shade behind closed metal gate')

    # The red wall cabinet between the doorways is legible in the 2015 wide view.
    from cabinet import add_hose_cabinet
    add_hose_cabinet(b,unproject,lod)
