"""Build the editable two-part frontage and retain all original object names."""
import json,sys
from pathlib import Path
p=next(p for p in Path(__file__).resolve().parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(p/'source/precise/hongkou-gongyi-fang-1297-1311-sichuan-road/source'))
from build_model import create,META
from package_architectural_model import group_parts
b=create(False)
g=group_parts(b)
assert len(g)==472 and len(b.parts)==770 and sum(len(v['f']) for v in g.values())==26968
print(json.dumps({'groups':g,'palette':b.palette,'metadata':META},default=lambda v:v.tolist(),separators=(',',':'),ensure_ascii=False))
