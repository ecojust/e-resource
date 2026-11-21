"""Generate the two lane names and address figures with an openly licensed Chinese typeface."""
from pathlib import Path
import hashlib, io, json, os, sys
import ctypes as C
from ctypes.util import find_library
from shapely.affinity import translate
from shapely.geometry import mapping
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
sys.path.insert(0,str(ROOT/'source/precise/hongkou-general-post-office/source/common'))
from sign_lettering import lettering_shapes
font=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
# HarfBuzz maps only the six required glyphs from the collection.
hb=C.CDLL(find_library('harfbuzz'));ss=C.CDLL(find_library('harfbuzz-subset'))
ptr=C.c_void_p;uint=C.c_uint
def api(lib,name,result,*args):
    fun=getattr(lib,name);fun.restype=result;fun.argtypes=args
    return fun
blob=api(hb,'hb_blob_create_from_file_or_fail',ptr,C.c_char_p)(os.fsencode(font))
face=api(hb,'hb_face_create',ptr,ptr,uint)(blob,2)
selection=api(ss,'hb_subset_input_create_or_fail',ptr)()
chars=api(ss,'hb_subset_input_unicode_set',ptr,ptr)(selection)
add=api(hb,'hb_set_add',None,ptr,uint)
for ch in '大德里恒安坊154弄':add(chars,ord(ch))
subface=api(ss,'hb_subset_or_fail',ptr,ptr,ptr)(face,selection)
assert subface
data_blob=api(hb,'hb_face_reference_blob',ptr,ptr)(subface)
size=uint();address=api(hb,'hb_blob_get_data',ptr,ptr,C.POINTER(uint))(data_blob,C.byref(size))
sub=io.BytesIO(C.string_at(address,size.value))
for ref in (data_blob,blob):api(hb,'hb_blob_destroy',None,ptr)(ref)
for ref in (subface,face):api(hb,'hb_face_destroy',None,ptr)(ref)
api(ss,'hb_subset_input_destroy',None,ptr)(selection)
rows=[]
for name,cx in [('大德里',-.498),('恒安坊',.514)]:
    for j,ch in enumerate(name):
        sub.seek(0)
        _,poly=lettering_shapes(ch,.226,.228,font=sub)[0]
        rows.append(dict(group='Lane title '+ch,material='charcoal lane inscription',front=-.039,geometry=mapping(translate(poly.simplify(.00065,preserve_topology=True),cx+(j-1)*.287,2.938))))
for cx in (-1.589,1.589):
    sub.seek(0)
    for i,(ch,poly) in enumerate(lettering_shapes('1545弄',.319,.093,font=sub)):
        rows.append(dict(group='Address '+str(cx)+' '+str(i),material='ivory enamel lettering',front=-.043,geometry=mapping(translate(poly.simplify(.00022,preserve_topology=True),cx,2.068))))
(HERE/'letter-contours.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n')
(HERE/'font-source.json').write_text(json.dumps(dict(typeface='Noto Serif CJK SC Regular',sha256=hashlib.file_digest(font.open('rb'),'sha256').hexdigest(),url='https://github.com/notofonts/noto-cjk',license='SIL Open Font License 1.1',layout='文字和排列以高参88与Fayhoo公开照片为据。各笔画以开放字体近似。'),ensure_ascii=False,indent=2)+'\n')
