"""The seven photographed window axes at the junction of Ningbo and Henan roads."""
from math import floor
from street_finish import BRICK,STONE,TRIM,JOINT,BASE,IRON
from curved_front import StreetCorner
from brick_uv import brick_uv
from windows import frame
from street_services import add_outdoor_unit,add_downpipe
from shop_sign import sign,side_shop_sign

def add_building(builder,lod,dimensions):
    street=StreetCorner(builder)
    left,right=dimensions['extent']
    centers=dimensions['centers']
    widths=dimensions['opening_widths']
    rows=dimensions['rows']
    h=dimensions['levels']
    holes=[];resolution=.71 if lod else .36
    for row,(bottom,top) in enumerate(rows):
        for bay,(s,width) in enumerate(zip(centers,widths[row])):
            if width<=0:continue
            opening_bottom=h['threshold'] if row==0 and bay==3 else bottom
            holes.append((s-width/2,opening_bottom,s+width/2,top))
            wing=('Ningbo','West shoulder','West bay','Corner','East bay','East shoulder','Henan')[bay]
            face=street.flat(s,width,0,f'{wing} level {row+1}')
            style=('door' if bay==3 else 'shop') if row==0 else ('attic' if row==3 else 'steel')
            frame(face,face.length,opening_bottom,top,lod,style)
            if row==0 and bay==3:sign(face,2.865,min(1.42,width*.52),lod)
            if row==0 and bay==1:side_shop_sign(face,2.44,2.10,lod)

    def panel(a,b,low,high,inner,outer,material,name,openings=()):
        street.shell(a,b,low,high,inner,outer,material,name,openings,resolution)
    roof=h['roof']
    # The shallow inner return closes the photographed section, with the
    # adjacent unmodelled wings supplied by the original city building.
    panel(left,right,.005,roof,-1.50,-1.42,BASE,'Envelope/Inward return')
    panel(left,right,.005,.12,-1.42,-.33,BASE,'Envelope/Threshold return')
    panel(left,right,.005,roof,-.34,0,STONE,'Envelope/Perforated street wall',holes)
    panel(left,right,roof-.125,roof,-1.42,-.34,BASE,'Envelope/Flat roof return')
    for a,b in ((left,left+.075),(right-.075,right)):
        panel(a,b,.005,roof,-1.42,-.34,STONE,'Envelope/Wall end return')
    panel(left,right,.02,.37,-.015,.038,BASE,'Stone/Ground plinth',holes)
    for z,depth,height in [(h['band'],.122,.16),(h['band']+.13,.083,.10),(h['crown_line'],.093,.115),(roof-.15,.14,.16)]:
        panel(left,right,z-height/2,z+height/2,-.035,depth,TRIM,'Stone/Continuous curved cornices')
    for z in [h['brick_foot'],h['belt'],*dimensions['cladding_courses']]:
        panel(left,right,z-.010,z+.010,-.006,.012,JOINT,'Stone/Horizontal bed joint',holes)
    # Short vertical joints have a running offset between the broad courses.
    for row,(lo,hi) in enumerate([(rows[0][1]+.12,h['belt']-.1),(h['belt']+.05,rows[1][0]-.14),(rows[1][1]+.16,rows[2][0]-.23),(rows[3][0]-.64,rows[3][0]-.13),(rows[3][1]+.10,roof-.54)]):
        if hi<lo+.02:continue
        p=left+.7+(row%2)*.68
        while p<right-.06:
            panel(p-.009,p+.009,lo,hi,-.006,.012,JOINT,'Stone/Short vertical joint',holes)
            p+=1.57
    # Both edges of the central crown step up, with a slim projecting coping.
    middle=centers[3]
    for span,rise in [(5.1,.12),(3.67,.226)]:
        panel(middle-span/2,middle+span/2,roof-.05,roof+rise,-.41,.025,STONE,'Crown/Stepped parapet')
        panel(middle-span/2-.035,middle+span/2+.035,roof+rise-.052,roof+rise+.014,-.46,.078,TRIM,'Crown/Coping')
    # Each fin occupies the masonry between two window jambs. The middle
    # two floors share one continuous length of facing brick.
    brick_lo=h['brick_foot'];brick_hi=h['band']-.080
    for i,(a,b) in enumerate(zip(centers,centers[1:])):
        l=a+widths[1][i]/2+.12;r=b-widths[1][i+1]/2-.12
        if r-l<=.12:continue
        pad=min(.20,(r-l)*.15)
        l+=pad;r-=pad
        limits=[l,r,brick_lo,brick_hi]
        label=f'Facing brick/Strip {i+1}'
        panel(l,r,brick_lo,brick_hi,-.022,.075,BRICK,label)
        part=builder.parts[-1]
        part['texcoords']=[(u,1-v) for u,v in (brick_uv(v,limits,street.reg)for v in part['vertices'])]
        for x in (l-.039,r+.039):
            panel(x-.033,x+.033,brick_lo-.016,brick_hi+.014,-.021,.111,TRIM,'Stone/Brick strip jamb')
    for i,entry in enumerate(dimensions['outdoor_units']):
        bay,dx,z,width,height,twin=entry
        s=centers[bay]+dx
        wall=street.flat(s,width,0,f'Condenser {i+1:02}')
        add_outdoor_unit(wall,0,z,width,height,lod,double=twin)
    for i,route in enumerate(dimensions['pipes']):
        add_downpipe(builder,[street.point(x,z,d) for x,z,d in route],lod)
        s,z,_=route[0]
        street.flat(s,.23,0,'Roof drainage').box(0,z+.042,.235,.12,.21,.12,IRON,'hopper head')
