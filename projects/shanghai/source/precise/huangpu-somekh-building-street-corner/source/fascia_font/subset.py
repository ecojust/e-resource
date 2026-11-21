"""Extract just the two public building-name inscriptions from Noto Serif CJK SC."""
from pathlib import Path
from hashlib import sha256
import json,sys
from fontTools import subset
from fontTools.ttLib import TTFont
directory=Path(__file__).parent
upstream=Path(sys.argv[1])
font=TTFont(upstream,fontNumber=2)
sub=subset.Subsetter()
sub.populate(text='THE SOMEKH BUILDING樓大美沙')
sub.subset(font)
for field in font['name'].names:
    if field.nameID in (1,3,4,6,16):field.string='SomekhFasciaStudy'.encode(field.getEncoding())
if 'CFF 'in font:
    font['CFF '].cff.fontNames=['SomekhFasciaStudy']
    top=font['CFF '].cff.topDictIndex[0]
    top.FamilyName='SomekhFasciaStudy';top.FullName='SomekhFasciaStudy'
target=directory/'SomekhFasciaStudy.otf'
font.save(target)
receipt=dict(font='Noto Serif CJK SC Regular',face_index=2,upstream='https://github.com/notofonts/noto-cjk/tree/main/Serif',licence='SIL Open Font License 1.1',source_sha256=sha256(upstream.read_bytes()).hexdigest(),output_sha256=sha256(target.read_bytes()).hexdigest(),characters='THE SOMEKH BUILDING樓大美沙',use='立体字排布据实照；使用许可字体近似原有字形。')
(directory/'provenance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
