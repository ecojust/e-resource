"""Generate the small, renamed SIL OFL type subset used to approximate the photographed lettering."""
import argparse, hashlib, json
from pathlib import Path
from fontTools import subset, version
from fontTools.ttLib import TTFont

HERE = Path(__file__).parent
TEXT = '沁園邨1124弄1–59号新闸路优秀历史建筑阮玲玉故居'
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source', type=Path, nargs='?', default=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'))
    source=parser.parse_args().source
    font=TTFont(source,fontNumber=2,recalcTimestamp=False)
    opts=subset.Options();opts.layout_features=[]
    cut=subset.Subsetter(options=opts);cut.populate(text=TEXT);cut.subset(font)
    for rec in font['name'].names:
        if rec.nameID in (1,2,3,4,6,16,17):
            replacement='Regular' if rec.nameID in (2,17) else 'QinyuanGateSubset'
            rec.string=replacement.encode(rec.getEncoding())
    top=font['CFF '].cff.topDictIndex[0]
    top.FullName='QinyuanGateSubset';top.FamilyName='QinyuanGateSubset';font['CFF '].cff.fontNames=['QinyuanGateSubset']
    target=HERE/'QinyuanGateSubset.otf';font.save(target)
    def digest(p):
        with p.open('rb')as src:return hashlib.file_digest(src,'sha256').hexdigest()
    result={'source':'Noto Serif CJK SC Regular, collection face 2','source_url':'https://github.com/notofonts/noto-cjk/tree/main/Serif',
            'source_sha256':digest(source),'sha256':digest(target),'text':TEXT,'typeface':'Approximate typesetting based on visible markings.',
            'fonttools':version,'license':'SIL OFL 1.1'}
    (HERE/'provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
