"""Subset and rename the freely licensed letters used on the Science Society medal."""
from pathlib import Path
from hashlib import sha256
import argparse,ctypes,ctypes.util,io,json
from fontTools.ttLib import TTFont

parser=argparse.ArgumentParser()
parser.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'))
args=parser.parse_args()
location=Path(__file__).resolve().parent
text='格物致知利用厚生中國科學社'
name='Mingfu Science Medal'
post='MingfuScienceMedal'
# HarfBuzz can subset a single TTC face without expanding every CJK outline in Python.
hb=ctypes.CDLL(ctypes.util.find_library('harfbuzz'))
sub=ctypes.CDLL(ctypes.util.find_library('harfbuzz-subset'))
ptr=ctypes.c_void_p
def api(lib,name,result,*args):
    fn=getattr(lib,name);fn.restype=result;fn.argtypes=list(args);return fn
blob=api(hb,'hb_blob_create_from_file_or_fail',ptr,ctypes.c_char_p)(str(args.font).encode())
assert blob
original=api(hb,'hb_face_create',ptr,ptr,ctypes.c_uint)(blob,3)
choices=api(sub,'hb_subset_input_create_or_fail',ptr)()
charset=api(sub,'hb_subset_input_unicode_set',ptr,ptr)(choices)
include=api(hb,'hb_set_add',None,ptr,ctypes.c_uint)
for char in text:include(charset,ord(char))
small=api(sub,'hb_subset_or_fail',ptr,ptr,ptr)(original,choices)
assert small
output=api(hb,'hb_face_reference_blob',ptr,ptr)(small)
count=ctypes.c_uint()
data=api(hb,'hb_blob_get_data',ptr,ptr,ctypes.POINTER(ctypes.c_uint))(output,ctypes.byref(count))
face=TTFont(io.BytesIO(ctypes.string_at(data,count.value)),recalcTimestamp=False)
assert all(ord(char) in face.getBestCmap() for char in text)
for lib,func,obj in ((hb,'hb_blob_destroy',output),(hb,'hb_face_destroy',small),
                     (sub,'hb_subset_input_destroy',choices),(hb,'hb_face_destroy',original),(hb,'hb_blob_destroy',blob)):
    api(lib,func,None,ptr)(obj)
for record in face['name'].names:
    value={1:name,2:'Regular',3:post,4:name,6:post,16:name,17:'Regular'}.get(record.nameID)
    if value:record.string=value.encode(record.getEncoding())
cff=face['CFF '].cff
cff.fontNames[0]=post
cff.topDictIndex[0].FamilyName=name
cff.topDictIndex[0].FullName=name
target=location/(post+'.otf')
face.save(target)
def digest(path):
    checksum=sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(131072),b''):
            checksum.update(block)
    return checksum.hexdigest()
(location/'provenance.json').write_text(json.dumps(dict(characters=text,source='Noto Serif CJK TC Regular, face 3',
   upstream='https://github.com/notofonts/noto-cjk/tree/main/Serif',license='SIL Open Font License 1.1',
   original_sha256=digest(args.font),subset_sha256=digest(target),use='Raised traditional Chinese characters on the Science Society ring. The shapes approximate the cast letters in the photograph.'),
   indent=2,ensure_ascii=False)+'\n')
