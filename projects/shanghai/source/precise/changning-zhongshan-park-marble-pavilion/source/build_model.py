"""Build the measured pergola, terrace and arched marble screen of the Jessfield Park pavilion."""
import argparse
import json
import math
import sys
from pathlib import Path

from shapely.geometry import box,Polygon
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
MEASUREMENTS=HERE.parent/'measurements'
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder as BaseBuilder,opening
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
sys.path.insert(0,str(HERE))
from crown_builder import CrownBuilder
import marble_finishes
from niche_figures import add_figures

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in marble_finishes.STEMS:
            marble_finishes.metric_uv(self.parts[-1])

    def save(self,path,metadata=None):
        BaseBuilder.save(self,path,metadata)
        return marble_finishes.writer.embed_normals(path)

ID='changning-zhongshan-park-marble-pavilion'
STONE='Pavilion | pale carved marble'
SCREEN='Pavilion | grey screen stone'
PLINTH='Pavilion | step and landing stone'
DARK='Pavilion | niche backing'
PALETTE={STONE:{'color':[.71,.68,.58],'roughness':.68},SCREEN:{'color':[.31,.30,.25],'roughness':.88},
         PLINTH:{'color':[.62,.60,.53],'roughness':.83},DARK:{'color':[.22,.218,.185],'roughness':.89}}
PALETTE.update(marble_finishes.PALETTE)
META={'id':ID,'name':'中山公园大理石亭','address':'上海市长宁区长宁路780号中山公园内','heritage_id':'sh-historic-b3-124',
      'official_id':'3M026','source':'https://www.shcn.gov.cn/col6991/20210301/867422.html','photo_source':'https://commons.wikimedia.org/wiki/File:Marble_Pavilion_of_Jessfield_Park.jpg',
      'geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'camera_views':json.loads((HERE/'cameras.json').read_bytes()),
      'viewer_page':'zhongshan-park-marble-pavilion.html','scope':'The measured four-column open pergola, pierced arched screen with statue recesses, front stair and short terrace side returns. Foliage, plaza and other buildings lie outside the pavilion model.'}

def block(b,label,material,x1,x2,y1,y2,z1,z2):
    b.box([(x1+x2)/2,(y1+y2)/2,(z1+z2)/2],[x2-x1,y2-y1,z2-z1],material,label=label)

def add_building(b,lod=False):
    p=json.loads((MEASUREMENTS/'pavilion-cameras.json').read_bytes())['parameters']
    base,head,y=p['landing_z'],p['column_head_z'],p['screen_y']
    outer,inner=p['outer_x'],p['inner_x'];niche=p['niche_x'];sill,arch=p['sill_z'],p['arch_z']
    # The successive visible horizontal noses spread laterally toward the square.
    count=6
    for j in range(count):
        t=j/(count-1);halfwidth=9.35+(7.84-9.35)*t
        ymin=-p['front_run']+(p['front_run']-.24)*t
        block(b,f'terrace / tread {j+1}',PLINTH,-halfwidth,halfwidth,ymin,y+.54,base*j/count,base*(j+1)/count)
    for i,x in enumerate([-outer,-inner,inner,outer]):
        profile=[(base,.277),(base+.050,.277),(base+.064,.287),(base+.102,.275),
                 (base+.123,.240),(base+.151,.259),(base+.192,.222),(head-.225,.184),
                 (head-.194,.200),(head-.155,.203),(head-.129,.226),(head-.076,.250),(head-.052,.250)]
        if lod:profile=[profile[k]for k in (0,1,3,5,6,7,9,11,12)]
        b.lathe((x,0),profile,STONE,14 if lod else 28,f'colonnade / turned column {i+1}')
        block(b,f'colonnade / square abacus {i+1}',STONE,x-.258,x+.258,-.258,.258,head-.052,head)
    span=outer+.32
    block(b,'pergola / continuous front architrave',STONE,-span,span,-.162,.162,head,head+.173)
    block(b,'pergola / rear bearing over screen',STONE,-span,span,y-.045,y+.279,head,head+.173)
    # Twenty-nine distinct tips can be read between the outer column axes. A short
    # overrun at both ends is included. The eave is an open timber-like stone pergola.
    rafter_sections=31
    soff=head+.173
    profile=Polygon([(-.46,soff+.059),(-.25,soff),(y+.13,soff),
                     (y+.395,soff+.05),(y+.395,soff+.182),
                     (y+.292,soff+.208),(-.36,soff+.208),(-.46,soff+.178)])
    for i in range(rafter_sections):
        x=-span+.051+i*(2*span-.102)/(rafter_sections-1)
        b.prism(profile,x-.050,x+.050,lambda v,z,xx:(xx,v,z),STONE,
                f'pergola / open rafter with splayed tip {i+1:02d}')
    # The two sculpture bays have returns and back slabs. The three smaller passages remain open.
    r=.32;half=span*.985
    windows=[(-niche,.98),(-niche*.489,.59),(0,1.06),(niche*.489,.59),(niche,.98)]
    holes=[opening(x,sill,w,arch-sill,arch=w*.46,segments=10 if lod else 23) for x,w in windows]
    surface=box(-half,base,half,head).difference(unary_union(holes))
    b.prism(surface,-(y+.31),-y,lambda u,z,d:(u,-d,z),SCREEN,'screen / masonry with five apertures')
    for side,x in [('left',-niche),('right',niche)]:
        block(b,'screen / '+side+' niche back',DARK,x-.56,x+.56,y+.52,y+.66,sill-.03,arch+.06)
        for edge in (-1,1):
            pos=x+edge*.50
            block(b,'screen / '+side+f' niche return {edge}',SCREEN,pos-.048,pos+.048,y+.31,y+.52,sill-.03,arch+.06)
    for i,x in enumerate((-half+.14,-niche+.89,niche-.89,half-.14)):
        block(b,f'screen / engaged jamb pier {i+1}',SCREEN,x-.13,x+.13,y-.115,y,base,head)
    add_figures(b,p,lod,STONE)
    for side in (-1,1):
        x=side*p['urn_x'];ur=p['urn_y']
        block(b,'stone rail / plinth '+str(side),STONE,x-.294,x+.294,ur-.294,ur+.294,base,base+.125)
        b.lathe((x,ur),[(base+.125,.282),(base+.201,.261),(base+.55,.190),(base+.66,.258),(base+.75,.280)],STONE,12 if lod else 24,'stone rail / pedestal '+str(side))
        zy=base+.75;ht=p['urn_top_z']-zy
        b.lathe((x,ur),[(zy+v*ht,r)for v,r in [(0,.143),(.09,.159),(.16,.105),(.29,.081),(.34,.117),(.48,.210),(.69,.263),(.90,.272),(.94,.302),(1,.301)]],STONE,14 if lod else 32,'stone rail / turned flower urn '+str(side))
        y1=ur+.294;y2=y+.32
        block(b,'stone rail / side cap '+str(side),STONE,x-.116,x+.116,y1,y2,base+.64,base+.73)
        block(b,'stone rail / side curb '+str(side),STONE,x-.119,x+.119,y1,y2,base,base+.085)
        for i in range(16):
            yy=y1+(i+.5)*(y2-y1)/16
            b.lathe((x,yy),[(base+h,r)for h,r in [(.085,.075),(.129,.076),(.188,.043),(.278,.037),(.423,.077),(.504,.083),(.544,.065),(.615,.041),(.64,.066)]],STONE,8 if lod else 14,f'stone rail / side {side} baluster {i+1}')
        lo,hi=sorted((x,side*half))
        block(b,'stone rail / rear cap '+str(side),STONE,lo,hi,y+.32,y+.53,base+.64,base+.73)
        block(b,'stone rail / rear curb '+str(side),STONE,lo,hi,y+.32,y+.53,base,base+.085)
        for i in range(8):
            xx=lo+(i+.5)*(hi-lo)/8
            b.lathe((xx,y+.425),[(base+h,r)for h,r in [(.085,.069),(.17,.055),(.27,.036),(.46,.08),(.55,.059),(.64,.054)]],STONE,8 if lod else 14,f'stone rail / rear {side} baluster {i+1}')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('path',type=Path,nargs='?');parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');a=parser.parse_args()
    if not(a.output or a.path):parser.error('an output GLB path is required')
    b=Builder(PALETTE);add_building(b,a.lod);b.save(a.output or a.path,META)
if __name__=='__main__':main()
