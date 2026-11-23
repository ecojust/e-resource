"""Produce the redistributable OFL glyph subset for the photographed French entrance inscription."""
from pathlib import Path
from hashlib import file_digest
from fontTools import subset
from fontTools.ttLib import TTFont
import json,shutil
root=Path(__file__).resolve().parent;target=root/'fonts';target.mkdir(exist_ok=True)
reference=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc')
font=TTFont(reference,fontNumber=2,recalcTimestamp=False)
options=subset.Options();options.layout_features=[];options.name_IDs=['*'];options.name_languages=['*'];options.name_legacy=True
letters='CERCLE DE LA POLICEFOYER&DU SOLDAT'
sub=subset.Subsetter(options=options);sub.populate(text=letters);sub.subset(font)
for r in font['name'].names:
    if r.nameID in (1,3,4,6,16,17):
        label={1:'Shaoxing Entry Inscription',3:'ShaoxingEntry2026',4:'Shaoxing Entry Inscription',6:'ShaoxingEntry',16:'Shaoxing Entry Inscription',17:'Bold'}[r.nameID]
        r.string=label.encode(r.getEncoding(),errors='replace')
cff=font['CFF '].cff;cff.fontNames=['ShaoxingEntry']
cff.topDictIndex[0].FullName='Shaoxing Entry Inscription';cff.topDictIndex[0].FamilyName='Shaoxing Entry Inscription'
tt=target/'PoliceCercle.otf';font.save(tt)
project=next(p for p in root.parents if (p/'tools/package_architectural_model.py').is_file())
source=project/'source/precise/hongkou-general-post-office/source/common/fonts/OFL.txt'
shutil.copyfile(source,target/'OFL.txt')
def sha(path):
    with path.open('rb') as f:return file_digest(f,'sha256').hexdigest()
(target/'provenance.json').write_text(json.dumps(dict(source='Noto Serif CJK SC Bold, face 2',upstream='https://github.com/notofonts/noto-cjk',font_sha256=sha(reference),license='SIL Open Font License 1.1',characters=letters,change='Subset and renamed. Raised lettering transcribes the photo; the historic lettering weight and outlines are approximated.',subset_sha256=sha(tt)),ensure_ascii=False,indent=2)+'\n')
