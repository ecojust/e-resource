"""Three observed courtyard-side window assemblies of No.19, Alley 470, Yuyuan Road."""
import json
import math
from pathlib import Path

MEASUREMENT=Path(__file__).resolve().parents[1]/'measurements'/'side-window-measurements.json'
WHITE='No.19 windows | pale rendered surround'
EDGE='No.19 windows | warm white sill moulding'
RED='No.19 windows | deep red painted timber'
BLUEFRAME='No.19 windows | charcoal painted glazing bars'
BLUE='No.19 windows | blue sky reflection'
PALE='No.19 windows | grey blue bottom light'
GLASS='No.19 windows | dark reflective glazing'
WARM='No.19 windows | muted warm glazing'
SHADOW='No.19 windows | shaded pane'
DISC='No.19 windows | pale round fittings'
BEAD='No.19 windows | glazing putty'
def pigment(rgb,roughness,metallic=0.):
    c=[v/255. for v in rgb]
    return {'color':[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c],
            'roughness':roughness,'metallic':metallic}

PALETTE={WHITE:pigment((211,205,191),.88),EDGE:pigment((227,221,211),.82),
         RED:pigment((121,53,40),.61),BLUEFRAME:pigment((61,63,64),.52),
         BLUE:pigment((87,132,156),.21,.23),PALE:pigment((133,156,165),.37,.18),
         GLASS:pigment((63,66,65),.25,.20),WARM:pigment((115,105,85),.29,.22),
         SHADOW:pigment((40,43,43),.38,.12),DISC:pigment((197,196,180),.52),
         BEAD:pigment((113,89,73),.68)}

def openings():
    return [{k:r[k] for k in ('key','left','right','bottom','top')}
            for r in json.loads(MEASUREMENT.read_text())['windows']]

def _across(b,l,r,yz,material,name):
    # Positive area in Y/Z is a normal along positive X.
    area=sum(y*z2-y2*z for (y,z),(y2,z2) in zip(yz,yz[1:]+yz[:1]))
    if area<0:
        yz=list(reversed(yz))
    n=len(yz)
    vertices=[(x,y,z) for x in (l,r) for y,z in yz]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n))
    b.add(vertices,faces,material,name)

def _disc(b,x,y,z,r,material,label,steps):
    path=[(x+r*math.cos(i*2*math.pi/steps),z+r*math.sin(i*2*math.pi/steps)) for i in range(steps)]
    # X cross Z points outside the wall, toward -Y.
    vertices=[(a,yy,c) for yy in (y,y+.008) for a,c in path]
    faces=[tuple(range(steps)),tuple(reversed(range(steps,2*steps)))]
    faces.extend(((i+1)%steps,i,steps+i,steps+(i+1)%steps) for i in range(steps))
    b.add(vertices,faces,material,label)

def add_windows(builder,lod=False):
    far=lod is True or lod in ('low','lod','far','distant')
    for w in json.loads(MEASUREMENT.read_text())['windows']:
        key=w['key'];left=w['left'];right=w['right'];bottom=w['bottom'];top=w['top']
        y=w['frame_depth_m'];base=w['rear_sill_z_m'];head=w['rear_head_z_m']
        p=w['features']
        sash=BLUEFRAME if key=='upper_glazed' else RED
        def box(l,r,front,back,b,t,mat,tag):
            builder.box(((l+r)/2,(front+back)/2,(b+t)/2),(r-l,back-front,t-b),mat,label=key+' | '+tag)

        # Profiles behind the front arrises meet the individual rear sill and head heights.
        jamb=left-p['jamb_edge'][0]
        nose=left-p['sill_nose_left'][0]
        outer=left-p['cap_outer_left'][0]
        # Six millimetres of return render covers the structural reveal. Its visible
        # edge was white in the three openings and must stand clear of the backing wall.
        return_coat=.006
        for label,l,r in [('left jamb',left-jamb,left+return_coat),
                          ('right jamb',right-return_coat,right+jamb)]:
            box(l,r,-.012,y+.083,bottom,top,WHITE,label)
        _across(builder,left,right,[(0,bottom-.045),(y+.080,base-.045),(y+.080,base),(0,bottom)],WHITE,key+' | sloping sill return')
        _across(builder,left,right,[(0,top),(y+.080,head),(y+.080,head+.10),(0,top+.10)],WHITE,key+' | head return')
        cap=p['cap_outer_left'][2]-top
        _across(builder,left-outer,right+outer,[(-.067,top+.008),(-.012,top),(.043,top+.005),
                (.043,top+cap),(-.092,top+cap),(-.092,top+cap-.014)],EDGE,key+' | cap moulding')
        _across(builder,left-nose,right+nose,[(-.082,bottom-.056),(-.041,bottom-.069),(.038,bottom-.067),
                (.038,bottom),(-.098,bottom+.006),(-.098,bottom-.029)],EDGE,key+' | projecting sill nose')
        if not far:
            box(left-outer+.012,right+outer-.012,-.073,-.041,top+.018,top+.030,WHITE,'head bead')
            box(left-nose+.015,right+nose-.015,-.077,-.038,bottom-.079,bottom-.065,WHITE,'sill fillet')

        # The apron below the near red double window is visible to its lower edge.
        if key=='near_red':
            l=p['apron_top_left'][0];r=p['apron_bottom_right'][0]
            b=p['apron_bottom_right'][2];t=p['apron_top_left'][2]
            box(l-.032,r+.032,-.032,.016,b-.030,t+.034,WHITE,'panelled apron')
            for xpos in (l,r-.030):
                box(xpos,xpos+.030,-.052,-.030,b,t,EDGE,'apron vertical rim')
            for z in (b,t-.033):
                box(l+.030,r-.030,-.052,-.030,z,z+.033,EDGE,'apron horizontal rim')

        # Continuous recess walls meet the sash. Straight sections behind the front timber
        # are intentionally simple because the photograph only resolves their outer edges.
        thick=.043 if key!='middle_round' else .056
        for xpos in (left,right-thick):
            box(xpos,xpos+thick,y,y+.068,base,head,sash,'fixed upright')
        l=left+thick;r=right-thick
        box(l,r,y,y+.068,base,base+.052,sash,'bottom rail')
        box(l,r,y,y+.068,head-.047,head,sash,'head rail')
        low=base+.052;high=head-.047
        def lights(edges_x,edges_z,columns,rows,shade,key_name):
            xcuts=[l]+list(edges_x)+[r]
            zcuts=[low]+list(edges_z)+[high]
            for i,xpos in enumerate(edges_x):
                width=columns[i]
                box(xpos-width/2,xpos+width/2,y+.006,y+.057,low,high,sash,key_name+' vertical rail '+str(i+1))
            for i,zpos in enumerate(edges_z):
                width=rows[i]
                box(l,r,y-.004,y+.060,zpos-width/2,zpos+width/2,sash,key_name+' horizontal rail '+str(i+1))
            for i,(a,b) in enumerate(zip(xcuts,xcuts[1:])):
                a+=columns[i-1]/2 if i else 0
                b-=columns[i]/2 if i<len(columns) else 0
                for j,(c,d) in enumerate(zip(zcuts,zcuts[1:])):
                    c+=rows[j-1]/2 if j else 0
                    d-=rows[j]/2 if j<len(rows) else 0
                    box(a,b,y+.036,y+.047,c,d,shade(i,j),f'{key_name} pane {i+1}.{j+1}')
                    if not far:
                        for xx in (a,b-.006):
                            box(xx,xx+.006,y+.027,y+.038,c,d,BEAD,f'{key_name} glazing rebate {i+1}.{j+1}')
        if key=='upper_glazed':
            # Only the two main tall lights have the photographed centre stile.
            z0=p['lower_rail'][2];z1=p['upper_rail'][2];x=p['middle_stile'][0]
            for z,h,label in [(z0,.048,'lower rail'),(z1,.05,'transom')]:
                box(l,r,y-.003,y+.060,z-h/2,z+h/2,sash,label)
            box(x-.022,x+.022,y+.002,y+.055,z0+.024,z1-.025,sash,'two tall lights | centre stile')
            box(l,r,y+.036,y+.047,low,z0-.024,PALE,'lower glazed spandrel')
            box(l,r,y+.036,y+.047,z1+.025,high,BLUE,'upper blue light')
            for a,b,tag in [(l,x-.022,'left'),(x+.022,r,'right')]:
                box(a,b,y+.036,y+.047,z0+.024,z1-.025,BLUE,tag+' tall blue light')
                if not far:
                    for xx in (a,b-.007):
                        box(xx,xx+.007,y+.026,y+.037,z0+.024,z1-.025,BEAD,tag+' putty line')
        elif key=='middle_round':
            z=p['transom_rail'][2];x=p['lower_stile'][0]
            box(l,r,y-.004,y+.061,z-.038,z+.038,RED,'transom')
            box(l,x,y+.006,y+.060,low,z-.038,RED,'visible broad side of lower frame')
            box(x,r,y+.037,y+.049,low,z-.038,SHADOW,'lower dark light')
            box(l,r,y+.037,y+.049,z+.038,high,GLASS,'dark transom glass')
            for n,name in enumerate(('disc_one','disc_two'),1):
                cx,_,cz=p[name]
                _disc(builder,cx,y+.019,cz,.057,DISC,f'{key} | pale circular fitting {n}',16 if far else 32)
        else:
            # Photograph resolves smaller divided lights above an undivided pair of lower panes.
            z=p['transom_rail'][2];x=p['central_stile'][0]
            box(l,r,y-.004,y+.061,z-.035,z+.035,RED,'transom')
            box(x-.025,x+.025,y+.001,y+.055,low,z-.035,RED,'meeting stile')
            for a,b,mat,tag in [(l,x-.025,WARM,'left'),(x+.025,r,GLASS,'right')]:
                box(a,b,y+.036,y+.047,low,z-.035,mat,tag+' tall lower glass')
            low=z+.035
            lights([p['transom_divider_west'][0],p['transom_divider_east'][0]],
                   [p['transom_lower_bar'][2],p['transom_upper_bar'][2]],
                   [.031,.031],[.022,.022],lambda i,j: GLASS if (i+j)%2 else SHADOW,'transom')
