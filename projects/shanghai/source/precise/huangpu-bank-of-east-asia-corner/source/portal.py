"""Street entrance of the Bank of East Asia, Sichuan Middle Road 299.

The 2019-published entrance photograph shows four pale, veined round columns,
a shallow peaked inscription, a central dark seal plaque and an open double door.
Stone figure, leaf dimensions and unreadable seal details are interpreted.
The facade coordinates are metres. Positive d faces the pavement.
"""
from base64 import b85decode
from functools import lru_cache
from io import BytesIO
import math
from random import Random
from zlib import decompress

from shapely import set_precision
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from sign_lettering import lettering_shapes

STONE = 'BEA light entrance stone'
TRIM = 'BEA warm cap stone'
MARBLE = 'BEA ivory veined marble'
GREY = 'BEA smoke marble veins'
HAIR = 'BEA grey gold vein'
FRIEZE = 'BEA blue grey frieze'
FLUTE = 'BEA silver grey frieze edge'
LETTERS = 'BEA dark engraved lettering'
SEAL = 'BEA oxblood entrance plaque'
WOOD = 'BEA dark timber door'
PANEL = 'BEA recessed timber panel'
SHADOW = 'BEA unlit door interior'
METAL = 'BEA old brass'

PORTAL_MATERIALS = {
    STONE: {'color': [.63, .60, .53], 'roughness': .83},
    TRIM: {'color': [.75, .72, .66], 'roughness': .78},
    MARBLE: {'color': [.79, .765, .685], 'roughness': .55},
    GREY: {'color': [.525, .514, .454], 'roughness': .59},
    FRIEZE: {'color': [.425, .434, .424], 'roughness': .78},
    FLUTE: {'color': [.516, .528, .513], 'roughness': .76},
    HAIR: {'color': [.645, .62, .546], 'roughness': .59},
    LETTERS: {'color': [.182, .134, .104], 'roughness': .62},
    SEAL: {'color': [.274, .135, .105], 'roughness': .64},
    WOOD: {'color': [.30, .18, .11], 'roughness': .61},
    PANEL: {'color': [.225, .135, .092], 'roughness': .67},
    SHADOW: {'color': [.052, .051, .050], 'roughness': .92},
    METAL: {'color': [.455, .377, .25], 'roughness': .49, 'metallic': .46},
}


def portal_opening(center_u, *, width, height):
    """The rectangular opening to subtract from the host street wall."""
    return center_u-.16*width, center_u+.16*width, 0.0, .43*height


@lru_cache(maxsize=40)
def _letters(text, width, height, lod):
    font = BytesIO(decompress(b85decode(_SUBSET)))
    glyphs = lettering_shapes(text, width, height, font=font)
    tolerance = min(.005 if lod else .0015, height*.020)
    return [(c, shape.simplify(tolerance, preserve_topology=True)) for c, shape in glyphs]


def bank_glyph(character, width, height, lod=False):
    """Return a centered (u,z) outline to orient independently along the curved bank fascia."""
    if character not in '東亞銀行大廈' or len(character) != 1:
        raise ValueError('Expected one bank inscription character')
    return _letters(character, width, height, lod)[0][1]


def _cut(shape):
    # Quantization removes touching contours created by transforming tiny serifs.
    return set_precision(shape, .00004)


def _round_column(face, u, radius, height, lod, index):
    """Lathed marble with a slightly tapered shaft, disk capital and plain foot."""
    sides = 20 if lod else 32
    d = .072
    name = 'main door column '+str(index+1)
    rings = [
        (.000, 1.19), (.009, 1.19), (.011, 1.16), (.022, 1.16), (.031, 1.03), (.043, 1.03),
        (.050, .98), (.27, 1.00), (.51, .955), (.642, .92),
        (.647, 1.02), (.654, 1.04), (.662, 1.14), (.670, 1.20),
        (.675, 1.22), (.684, 1.22), (.688, 1.16)
    ]
    def scale_at(frac):
        for (z0,r0),(z1,r1) in zip(rings,rings[1:]):
            if z0 <= frac <= z1:
                return r0+(r1-r0)*(frac-z0)/(z1-z0)
        return rings[-1][1]
    def vertex(theta, frac, extra=0.0):
        r = radius*scale_at(frac)+extra
        return face.point(u+math.sin(theta)*r, frac*height, d+math.cos(theta)*r)
    vertices = [vertex(2*math.pi*j/sides,z) for z,_ in rings for j in range(sides)]
    panels = []
    for i in range(len(rings)-1):
        for j in range(sides):
            a = i*sides+j
            b = i*sides+(j+1)%sides
            panels.append((a,b,b+sides,a+sides))
    panels.extend([tuple(reversed(range(sides))),tuple(range(len(vertices)-sides,len(vertices)))])
    face.builder.add(vertices, panels, MARBLE, name+' shaft and capital')

    # Short, uneven diagonal inclusions read as marble while maintaining the round silhouette.
    rng = Random(25600+index)
    strokes = 10 if lod else 28
    for n in range(strokes):
        center = rng.uniform(-2.65,2.65)
        start = rng.uniform(.061,.595)
        span = min(.635-start,rng.uniform(.035,.132))
        sweep = rng.uniform(.4,1.38)*(-1 if n%7==0 else 1)
        phase = rng.uniform(0,2*math.pi)
        width = rng.uniform(.018,.045) * (1.2 if lod else 1)
        verts = []
        steps = 4 if lod else 8
        for j in range(steps+1):
            t = j/steps
            angle = center + t*sweep + .075*math.sin(2*math.pi*t+phase) + .028*math.sin(16*t)
            band = width*(.20+.85*math.sin(math.pi*t))
            for sign in (-1,1):
                verts.append(vertex(angle+sign*band, start+t*span,.0018))
        faces = [(2*j,2*j+1,2*j+3,2*j+2) for j in range(steps)]
        face.builder.add(verts,faces,GREY if n%3==0 else HAIR,name+' natural veins')

    # Dark mottling is frequent in the photographed pale marble. Keep the pattern
    # irregular. Separate small inclusions around each patch interrupt the long veins.
    count = 14 if lod else 39
    vertices = []
    patches = []
    for _ in range(count):
        angle = rng.uniform(-2.32, 2.32)
        base = rng.uniform(.064, .618)
        for spot in range(3 if lod else 5):
            mid = angle + rng.gauss(0, .100)
            level = base + rng.gauss(0, .005)
            spread = rng.uniform(.016, .106) * (1.6 if lod else 1)
            depth = rng.uniform(.0008, .0044) * (1.35 if lod else 1)
            tilt = rng.uniform(-.65, .80)
            start = len(vertices)
            vertices.append(vertex(mid, level, .0022))
            edges = 5 if lod else 7
            for j in range(edges):
                theta = 2*math.pi*j/edges
                jitter = rng.uniform(.63, 1.22)
                vx = jitter * math.cos(theta)
                vy = jitter * math.sin(theta)
                vertices.append(vertex(mid + spread*(vx+tilt*vy), level+depth*vy, .0022))
            patches.extend((start, start+1+j, start+1+(j+1)%edges) for j in range(edges))
    face.builder.add(vertices, patches, GREY, name+' irregular marble inclusions')


def _open_leaves(face, center, width, height, lod):
    left,right,_,top = portal_opening(center,width=width,height=height)
    door_width = right-left
    leaf_width = door_width*.485
    depth = .96
    face.prism(box(left-.018,0,right+.018,top+.015),
               -depth-.05,-depth,SHADOW,'portal dark lining')
    for side, angle in [(-1,65),(1,46)]:
        hinge = center+side*(door_width/2-.036)
        ca, sa = math.cos(math.radians(angle)),math.sin(math.radians(angle))
        def project(x,z,d):
            # x runs from the hinge toward the meeting stile.
            return face.point(hinge-side*x*ca-side*d*sa, z, -.09-x*sa+d*ca)
        def piece(x0,x1,z0,z1,d0,d1,material,label):
            coords=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
            verts=[project(x,z,d) for d in (d0,d1) for x,z in coords]
            # Winding depends on whether this is the left or the right leaf.
            faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
            if side==1:faces=[tuple(reversed(poly)) for poly in faces]
            face.builder.add(verts,faces,material,label)
        label='portal '+('left' if side<0 else 'right')+' door'
        piece(0,leaf_width,.025,top-.035,-.058,0,WOOD,label+' leaf')
        if not lod:
            for z0,z1 in [(.16,top*.41),(top*.47,top-.18)]:
                piece(.072,leaf_width-.070,z0,z1,.003,.012,PANEL,label+' plain field')
            piece(leaf_width-.15,leaf_width-.115,top*.42,top*.52,.010,.044,METAL,label+' pull')


def add_portal(face, center_u, lod, *, width, height):
    """Build the isolated street doorway; width and height describe the outer surrounds."""
    u = center_u
    w,h = width,height
    left,right,bottom,top = portal_opening(u,width=w,height=h)
    inner = box(left,bottom-.01,right,top)
    # The rear field stays shallow. The actual opening continues into the interior lining.
    outer = Polygon([(u-.50*w,0),(u+.50*w,0),(u+.50*w,.836*h),(u+.243*w,.836*h),
                     (u+.092*w,.960*h),(u+.042*w,.991*h),(u-.042*w,.991*h),
                     (u-.092*w,.960*h),(u-.243*w,.836*h),(u-.50*w,.836*h)])
    face.prism(_cut(outer.difference(inner)),.008,.066,STONE,'portal ashlar backing')
    # Smooth outer sides enclose marble columns in two closely spaced pairs.
    for side in (-1,1):
        wing = u+side*.369*w
        face.box(wing,.756*h,.262*w,.140*h,.178,.123,FRIEZE,'portal flanking entablature')
        for z,th,depth in [(.690,.011,.232),(.809,.008,.224),(.819,.005,.247),(.832,.012,.275)]:
            face.box(wing,z*h,.262*w,th*h,depth,.092+depth/2,TRIM,'portal cornice courses')
        if not lod:
            for j in range(9):
                face.box(wing+(j-4)*.0231*w,.752*h,.0038*w,.100*h,.026,.216,FLUTE,'portal fluted frieze')
    for index,offset in enumerate((-.423,-.320,.320,.423)):
        _round_column(face,u+offset*w,.038*w,h,lod,index)

    # The light monolithic lintel has the same irregular stone figure as the jambs.
    # The thin inner rebate and the open, darker doors make the reveal perceptible.
    frame_left, frame_right = left-.032*w, right+.032*w
    lintel_top = top+.065*h
    door_frame = box(frame_left, 0, frame_right, lintel_top).difference(inner)
    face.prism(_cut(door_frame), .060, .181, MARBLE, 'portal marble jambs and lintel')
    inner_rim = box(left-.030, 0, right+.030, top+.030).difference(inner)
    face.prism(_cut(inner_rim), .160, .205, TRIM, 'portal inner reveal edge')
    if not lod:
        rng = Random(25699)
        stone_marks = []
        figured_stone = door_frame.difference(inner_rim)
        for _ in range(110):
            if rng.random() < .66:
                x = rng.uniform(frame_left+.007, frame_right-.007)
                z = rng.uniform(top+.032, lintel_top-.006)
            else:
                x = rng.choice([rng.uniform(frame_left+.008, left-.032),
                                rng.uniform(right+.032, frame_right-.008)])
                z = rng.uniform(.013, top)
            length = rng.uniform(.015, .099)
            rise = rng.uniform(.014, .085)
            offset = rng.uniform(-.025, .021)
            half = rng.uniform(.002, .009)
            line = LineString([(x-length*.5,z-rise*.5), (x+offset,z),
                               (x+length*.5,z+rise*.5)])
            patch = _cut(line.buffer(half, cap_style=2, join_style=2)).intersection(figured_stone)
            if not patch.is_empty and patch.area > 1e-6:
                stone_marks.append(patch)
        face.prism(_cut(unary_union(stone_marks)), .180, .1825, HAIR, 'portal figured lintel and jamb stone')
    # Dark near-square plaque between the central header and the door lintel.
    face.box(u,.576*h,.135*w,.153*h,.073,.111,TRIM,'portal seal border')
    face.box(u,.576*h,.119*w,.134*h,.055,.153,SEAL,'portal seal face')
    # Exposed square is clear in the photograph. Its inscription is unresolved.
    face.box(u,.704*h,.087*w,.047*h,.068,.119,TRIM,'portal number plaque')
    if not lod:
        for char,glyph in _letters('299',.054*w,.021*h,False):
            face.prism(_cut(translate(glyph,xoff=u,yoff=.710*h)),.150,.164,LETTERS,'portal number '+char)

    pediment=Polygon([(u-.240*w,.722*h),(u+.240*w,.722*h),(u+.240*w,.825*h),
                      (u+.058*w,.967*h),(u+.028*w,.984*h),(u-.028*w,.984*h),
                      (u-.058*w,.967*h),(u-.240*w,.825*h)])
    face.prism(_cut(pediment),.076,.177,STONE,'portal peaked tympanum')
    rim=pediment.difference(pediment.buffer(-.054,join_style=2))
    face.prism(_cut(rim),.167,.235,TRIM,'portal sloping stone rim')
    baseline=.765*h
    english=_letters('THE BANK OF EAST ASIA',.391*w,.034*h,lod)
    english_shapes=[_cut(translate(g,xoff=u,yoff=baseline)) for _,g in english]
    strip=box(u-.219*w,baseline-.023*h,u+.219*w,baseline+.023*h)
    face.prism(strip,.176,.182,LETTERS,'portal engraved line backing')
    face.prism(_cut(strip.difference(unary_union(english_shapes))),.177,.197,
               STONE,'portal incised English inscription')
    for j,(char,level) in enumerate(zip('東亞銀行大廈',(.825,.863,.902,.902,.863,.825))):
        size=.047*w
        letter=bank_glyph(char,size,.053*h,lod)
        face.prism(_cut(translate(letter,xoff=u+(j-2.5)*.064*w,yoff=level*h)),
                   .176,.204,LETTERS,'portal arched sign '+char)
    _open_leaves(face,u,w,h,lod)


# Six traditional Chinese forms, the documented English words and the 299 street number.
# The embedded OFL subset keeps this one-file component reproducible on machines with
# different system fonts. Geometry is typeset to the photographic character positions.
FONT_PROVENANCE = {'original': 'Noto Serif CJK TC Bold, face 3', 'upstream': 'https://github.com/notofonts/noto-cjk', 'source_sha256': '1505ee3b9c0890fae6302ee0e9c6fd74d690f4a55a6ace1d9944f3f6352d622d', 'renamed_subset_sha256': 'acfb24d572243cd1cfddcef09d3e3c0b0b135f3b0a35b73bdfed536e1eff2ac9', 'license': 'SIL Open Font License 1.1'}
FONT_LICENSE = """Copyright © 2017–2024 Adobe (http://www.adobe.com/).
Typeface copyright is also preserved in the subset font name metadata.
Upstream: https://github.com/notofonts/noto-cjk

License: SIL-1.1
 -----------------------------------------------------------
 SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
 -----------------------------------------------------------

 PREAMBLE

 The goals of the Open Font License (OFL) are to stimulate worldwide
 development of collaborative font projects, to support the font
 creation efforts of academic and linguistic communities, and to provide
 a free and open framework in which fonts may be shared and improved in
 partnership with others.

 The OFL allows the licensed fonts to be used, studied, modified and
 redistributed freely as long as they are not sold by themselves. The
 fonts, including any derivative works, can be bundled, embedded,
 redistributed and/or sold with any software provided that any reserved
 names are not used by derivative works. The fonts and derivatives,
 however, cannot be released under any other type of license. The
 requirement for fonts to remain under this license does not apply to
 any document created using the fonts or their derivatives.

 DEFINITIONS

 "Font Software" refers to the set of files released by the Copyright
 Holder(s) under this license and clearly marked as such. This may
 include source files, build scripts and documentation.

 "Reserved Font Name" refers to any names specified as such after the
 copyright statement(s).

 "Original Version" refers to the collection of Font Software components
 as distributed by the Copyright Holder(s).

 "Modified Version" refers to any derivative made by adding to,
 deleting, or substituting -- in part or in whole -- any of the
 components of the Original Version, by changing formats or by porting
 the Font Software to a new environment.

 "Author" refers to any designer, engineer, programmer, technical writer
 or other person who contributed to the Font Software.

 PERMISSION & CONDITIONS

 Permission is hereby granted, free of charge, to any person obtaining a
 copy of the Font Software, to use, study, copy, merge, embed, modify,
 redistribute, and sell modified and unmodified copies of the Font
 Software, subject to the following conditions:

 1) Neither the Font Software nor any of its individual components, in
 Original or Modified Versions, may be sold by itself.

 2) Original or Modified Versions of the Font Software may be bundled,
 redistributed and/or sold with any software, provided that each copy
 contains the above copyright notice and this license. These can be
 included either as stand-alone text files, human-readable headers or
 in the appropriate machine-readable metadata fields within text or
 binary files as long as those fields can be easily viewed by the user.

 3) No Modified Version of the Font Software may use the Reserved Font
 Name(s) unless explicit written permission is granted by the
 corresponding Copyright Holder. This restriction only applies to the
 primary font name as presented to the users.

 4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
 Software shall not be used to promote, endorse or advertise any
 Modified Version, except to acknowledge the contribution(s) of the
 Copyright Holder(s) and the Author(s) or with their explicit written
 permission.

 5) The Font Software, modified or unmodified, in part or in whole, must
 be distributed entirely under this license, and must not be distributed
 under any other license. The requirement for fonts to remain under this
 license does not apply to any document created using the Font Software.

 TERMINATION

 This license becomes null and void if any of the above conditions are
 not met.

 DISCLAIMER

 THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
 OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
 COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
 DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
 OTHER DEALINGS IN THE FONT SOFTWARE.

"""
_SUBSET = (
    b'c-o~{2~-qU)_%QIRa=EbX<A#Px*KFsWD^k;S3tpqfC6e<qUo@s&;(F1Ms4?{0g)Xv5*Gp(P)IZqSKN)6j7yS9{)sv>'
    b'CNt4w#x2I%<dO7$t1!uAl5_qu=kGf8-o5WG@4NTCdUd<vlak`ebHqwiBsVf5adPAr@%IVo_mB{BJ1RQbwD+Gw;|XDr'
    b'??Yl{#3xQ#7Q2*?{?|}$ib<RmdF_vXIE%cbKP5gfC?t7;-J1}_OUS=8J3b*s^$Jo%KMEU7a<(~l<fK^}(4Rl@`!iC_'
    b'DT6l_`Xb$pcUT4vXcj4NqJ1dxUK!a1g+u?Td>`#6B0nwLT$oFAGmuogfDM~t&Q4vpY)vEborI{D<XZ9z933PCMKZo+'
    b'=#RPW(iiQEB!A1$AAegdAm4_(KT%+-B<FkeOKDy7+}Q7kN_AI4d*{-C3qSY09s5<+RkKi6g}OaIv{SG7@eU!V-<v2@'
    b'*JV%t{_8^s;?yCfQr%RZAPi2lO(~(C-qR}<k`O6MrIP!_N}>5T7cueiF~menWmZ+LV~aGS!q79fWTpHcDMG?x+l%BO'
    b'Hifzu(n->cGOZxN$o0@lq9Gfe(JJCaik{JGGMKbIqZ#r7`Rp0Z{+mv3WtAfM8SP9$RToJ!&KrW>hmnyaK&C=SD2_#t'
    b'6k;JSlT@S!lMGUTS1t)BL3k~fuRvn{StpPrBbAM^AxI}6olF*^WGTr(9TS<1y7}nAL?V&OL79mpBEJ-+D{#z0mLT<$'
    b')=xUWXaxL5=l4CCe%70fsPa%V6ZsrD#z2fMm<%UlFd7S5B+HUzC>w^do_h?&U`C&*vPK&Ag>nWY>oD0v5?W`XUlWOz'
    b'?F;1jEvQ?7IWgm$l75fI66}+a&p|F#&O=W=BxEMk&yaN!$y5@HeLUtjRmS>@=h$C)@W+w=jO!=trvD0Airg3ASf;#6'
    b'1<&yH_%zF{C+>kn?5ASuDQ7l9#+oSOn1fUjnS!WiVK4C!xb6wq#vwly*C|nsDFNFk?BmEJ*<z|p_sF8<eHKUNVm}=v'
    b'l8)p%6;btMCr{=IF*6eSd>Ok%9?is+%9S%LArF*eO_d}3@AGQH99e#~Ci${WGHRvCn$lWISxLuSnX&Czi(DCDww%kK'
    b'RwVyf{!*T;f3_Tp8Sh`@=}0Y;ZF6u`@@m4pYeC<6@*e5IB&}QzqW^1E1OMas%tyr1%I4x&K1wBQOR$$>Oh>tt`B?e1'
    b'l+G7IT%{91?$xAJK8Z|75qaN_#&wUzOio9uq`2L4eHUI%e`QN-nbqO=St9~hdkSjcy8c?j@i)gc#}&sp#~DYb<Fw<X'
    b'<5>GEZ{FK8wPw%qOW75_IcI<SQ}uL?Bhq`|w?73@D~Up(aE-GRSQ1n7GSi}_P0z{=h_oz8k;X^b2io0jP6oTEup5+i'
    b'qss28t_k`+wd)>Z@FNqPj3WAWIC<LdKG)UP$=kixk4|1)#=b<OP_WL)E4DS9`ywL6@^b3bl+>Jp%z_nBmfRJ2ndun?'
    b'rjX!aBLhN$Lqbimf@yF@K|yYKP|)(_%LC2QNMN!hJ7`FtNkV4I%r}`$1$pL_)NFI!Vv{A!6l1ZZFG)2`%}EZFHDvH6'
    b'L~oil!z97~&FJrh7!Z@1gCohmCql@U^gMHJM*i<fXXIIOEqMi*mK^gEGFYMDdb_xpeEfn(ginZhK5@>A$(fe?!d2_H'
    b'6qQ!g);BaCJpA6N^B;VC^Gk>0o|Om=@*=hj9m)z^{r1|59pyMQUlxR5%a-RL<%^X5g+xXutt>I3@++wPdPzmu_6ni8'
    b'yn4G)a5z3kmC~vbq&}3)>Z(esknWHjy@9Qd$Ov3{4kPHwEey&lQLdBtV>UM-P&5i>u`jJEHVRygBy$iiv~nGczRJ+R'
    b'K?WcjEaLPw!)gwBZ{+uGs@$=oQZhHcJt<riw!$o?`z$Mrxny&j9Ks0FuF?`WJn{w+AL5HIG(UXUgYf7NB_q6l4Esl9'
    b'(ahNG>b-%gp53WXlIIjy9O#sCRl(vjd4c?qTqm~_V-yn<Qxww`a}@Iw*A*Wt>r}nf1<Z@gkKAOFbN58&k+vsxM~lL)'
    b'15tIkpMCk0?qK%xiBrc9ys3dm@VoWtV>jTVZc;z$Ocn8zS!*b$+_Q53z{bY93zfz__nFdNyNY)Wymfr0kN1Kpl+eD$'
    b'c?mOO;$k$;ql=fpm813nEsCQs0IVRo>c1=0LBn~N0Fz;*8_XUGz350fkg7+}P-^@t9JCjX?`mu@<j^qxK{Pr}1DBy&'
    b'SCE@+O&>Ta=_BY3Zk_LcaP4FiO~~51WJ`|G`Kk{OH@lRB_~udkni0JAh{=A!-r>P#+uGriLl6M7Qrk^DjPBUyB|02`'
    b'u#(fRH(h&a|7AaG@6erQwYRoOslS}X`tn)uxP_z2N@m+b+hb6>fj?VgVmhE`A-l@cQ+#TBRCM2<y$!2aXNVik)6zh`'
    b'qw57v{>#Zch~s!|tkwSA=3xHm7(Tr4aM$ziD6T*sSPwcCG-K409^HX{pqO)!4*k$LcMlW!mig@)ZhwCN=$FlVH(U1^'
    b'-lfBsPPPn!nL~4?){h%Vhf)$r`&0JnRL~_D-&@Z7J*7E4+HGX~eD9YQm)2z%UV@R#Y<43Z#iX6PQ*djb^R94yK@*fU'
    b'!KS9%CWvix0cYs-6{x=h_Ac<Q53H^)5ba;A_IP`W4yriq1M3qS$*x-W+M0E1!FjsA?F@5=ZW_y?4s|`w(7$-V`eFQS'
    b'ebP*3G;IDVW-M<X)ICra70j5R?Cz9$w*BIs9YsbsI!M%@Gs@nX70-->IM~Y8R*x3v9gY!y7{XRq7}zHJj2*>Mms1SA'
    b'!pU=5p^rT0-)K4Q94>zE9wE*<68^r;&Dp-QQDF}Sy~=*G>$;AP-N_6p^4$<%=;kJf@FTmF7LKFy=v#Db#cO(SfX4$^'
    b'bO6>h(glB_n_wmNsJhm6=yFwYwVu8O4DAKeGayc5HwN(YI!56W78%6QrEJ;FqQ4e@v9F|}vZPMqTv-jq#!s70Hl1lY'
    b'*Lb7p(n$VaPw#;O&I04QCRgjo?RwgE(!|p@SS@+uYDE($X?*F1je2ck?(Tx!=Hj&Kb=8}yw`%AyZ=PP|=#(vV!T1q8'
    b'j0OKPSPJ9aU}Kk>TM*B5pB^qkHEW&3M6;AT#?T)|^QCp%%B+I4ob<xll{;7MTD?|Zv$S@3-HMkN%w3d}S+-Vxt^P{$'
    b'*@KOF&C6N}hnY>;lv!4ap?j1=zdfLS=Y9%sOF_G;;&j8IqqUl9&c}C0ZIJO;<B^tw?fZ+Wip#3}ztFdow$~PwYM_wY'
    b'y}hQqw44$Tp2o0m);Bja?AL_zmi^||S8Fwo!|<@efQRz*@((L@^J^CFOsTK0+g-P7rv~EL?2NR<i!7Ra7@|8+R8_XU'
    b'nu^VOsL!uwD~q0=&CszdEPzjSiS+C_j^?OO!r8eTJ^N?f88|zObB5+7P&a|9>0VP#h!`M_6J1~;IDr>F+CK1{>$g@d'
    b'SnX5bqK<lj8oXHO9m0bTRdd~q(5ma!yw08IY^XNw`+|$2y{Q(jp<~Nd>ml?Mh@U*Vr=eT-bMKwpUuA?(xDToSQ%b;R'
    b'TJ42H?H$#{ReI`kfQEe*@>B!b1#hrNE;f|o_HD%XM@@NIIqmhOJ~57=?)Sjq$-g`HGM>f344v~etNq6M=Jv9xl3E&4'
    b'r$>O)*sTo}?Lq)`58`1LohhMJ$!J3*v?|VdH0bPcjj*su0WrYaUBSuK4s~63bms6N+IPg*3acK3PSD)CadncYIl6MB'
    b'Xis5lsz!@1w?_}+yEhEd&G#5YM-MVpuGM!opE`8BUDG{#57%*GPerlOo<CGH*XdhZ547xW-nY4OM`@*I$%`XIIMN-?'
    b'uG+A1MGhU}#a~_9v}(_*^{-ZBm!xT6NafzMpS#(|gZFqob~NJ*nmyoN{*R{8#wSgcjm3?iY;yVJ@2@|EY2SebRIa+*'
    b'@uK#dT>D%&r=w2o8=}^ZUXwIn=Y~T^S}*NCH(-yysQsj^yZ^y){PzPBb(H;lS=#)`=D7nFUC6k)^ivJ^&fCqlckY)G'
    b'{FU^AF5iJ0?zVn*0z>Drlt01zu$jx-xHfHt;Ura5mR47k*ABRI_OtVEH*Lms>bIDIZ_jaUbmI*g07C+5&$k{rEIrYq'
    b'nj%imyneOe#^Kg|yEau9l~riEJ?+uD17M*hYT+zuB)q7F)%s1O@4=H%{0hGW8WtB+xk3NN&iY;TyEV6|A&{r%+39O%'
    b'Z&<wLIPDwEL%?MqCqF*8wMI{e<uh;ujK2KAnS=SIU;y<Pp8B%qFQ2^8^1<8l8<VQjKaYmKFoM2$P2)^d3I(rqx0{@N'
    b'8r*r4i`~P?r^%fUcd>gq`E<Aou`aa4=FUXh*mwAMgm*r7a>BcJkyGFAzta6AY2u#>O}m|({`6LTkLWemCM_{y{l`1I'
    b'^mF&{9Xc#5JR&AGVO~mB?y^<uw^qL1*w*pkN4oeijBs<XC`5?!g)?EiP!TB#EbZID2<<UgRgA?4Ia4?_gcodXFGMmz'
    b'>x@yNknF<?bPy|5Fu31_h=M;41JTO$1S9CHN~$VKYvh7TdLW2E)jCiMW5f(Uv{LCnCD7r9>h%nIj33JgO*s(YBIp{5'
    b'E6Yo&X+WD^sN>!{zOT|Kz$vyC%ONa#upiFPiD86#_Co9HrA9%wdh^a%)#ElyAMnR9kHC*khJG4>tF4+W3WdAvZ|#J{'
    b'*IByHR%L6now0Fm^I#C(ZfJ0F0(FC&p010oUE#V8Eg3FVI~<lp5hMmH|8)Fkv4(6QJ4hYbM-Gsa<P!OabSe5Pd=-I;'
    b'Fhz_a7OS9dl(UrW%EQVN%B#w|%KOTvSVHwu^-;O0tg3QVy{b*ssk*4Ts=B56Mg?l3=F~1~Jfu8ekT9Lsw)V;5uu`!9'
    b'iPL8H@#nP%Ck9D_Ly_t;1Su;Nvd+4%{doU%Ocs1Gfq!g!R6L3I;<XRGdEIzS;;J8JhFMXzyoC#>dLQO8u!;SE&h@r3'
    b'&J%gMyer+cQ+rqVdL2_VlixPjfPRFF3uAa;l_x{}*q$OpSjQC4<hKqs2(`Xgpln>o3PmuVnZpXYczy~`ci`r9hgf5q'
    b'dKj+#a9#nP;HeUlX&6Iokv#aJ;zwQa?EM->+dx|AzAR3=-x|$pE38v_?OrSFZDDaBj;H$R;E(6|{132_(u4jA4WRSs'
    b'f>`QL^+utvtt+WbaU6!&2ZEn#un;A71xATNJ1lCoXDt_OVK~!Z-nEsus!guyKEm_7i5DK)9zAqB&S72z+oAM!_-iY4'
    b'wn_OlK^BN!;O+XVtCRLstgLiW5`1jFzHVmD!{)ioOG<|JSQcF7py=Z#_a9BVK_hk<wI^U`!>MbZxjl;dm`*d$zp-HL'
    b'=5*&+?J?+oc@||UiJ3`RV=SvZvE_*k2=sO<fjg)Gs-ts4d=h6;m2m<4*ml3<Uj}De8+>*MF10BTk0+b~4_CW=HDdYu'
    b'dZxt3=Huf=&#;ed4@({xzAR^2=&da7t{)#LE%vPzE~K2<@&IecUT$y(&p4acmcfQ$>w9E@70lL=eDMRr-3rN$bGAi^'
    b'4#fj2ft1vCmx-dc7$ka#5Q4LY+?{(;`|)0Tv#yiX9()(ZGZ4%cd)d6a+~#xMHt(&z5xhqN|E=wD@goC@v=`o`<FR<u'
    b'9@z*f%nw@Dc`WZ7!rR5d0A85EJCtXv#8*sf%W8?`UDZ|r)bxR$2(xIT4nAvP$CcCdT}jMvR=_QpfEy;1cd3Epg26)y'
    b'>-!c?V7EQCJptBDkaqI}gYdv`PYU7-3}PI<#M{z_^I0v@8j9Lb`^A3n600q0;iAguW_vtDL&hWAXQ3^$lGFNUao?_{'
    b'o!ty`mD7e!<K+xWrS~T-+z8CjUu>UWcl+x@Mw<lD^viMU(Jl+ChW@J=x|J)Tb=}X|Pck%*6*}tw5#=Qg6HhNbEx-;s'
    b'0^DgVUL&Z1ZWpq++v_V|!%T2~tC=iLh~g2iAZ4@F6fFuaF!1<%h=3Pi;>(AHwltUzq0jy*2()hv1B<!!b|t<dpNCKo'
    b'p;WN>iY9TH;BE8q#uf0gc?$>?H}WI5W1Jv=LC}y4l0wvkn-m?JMEsLi<SilN)ALdnlkpkmoOI%kZ6@(wY|b$g|0U*v'
    b'95P=1(kgxbP!j|G(eoiS&qh=@;zaroSF(vH9B&eZDgpZ~INFb>Gn3O^#=9UB|61o+vUC1lGy45zMm<Jjz!|T|Q7K5_'
    b'v+u(^ahJyBxis>386tmsAwSC}k?3Dx36rse$ymZ<EMYR1Fd0kOfB1OjN0lpo0Z$>{Bg_OcMv2~(Uz6U-^CUo7hxZl|'
    b'pn8b}C=MX)Kst!{sQQv%<t!4aJWBebt&xbt1+n%;#OSjRQ9Sw4N%lIBxU2r~)A#OQW|h9s<Gd^J+DvS}x>n$2!$04H'
    b'(AJ0<^ZZ}vD`m9'
)
