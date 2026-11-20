"""Apply the optional residualCutProbe to a private copy of the runtime checker."""
import argparse
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

BEFORE = '      assert.equal(candidateGeometryContains(retained,point(0,0)),false);'
AFTER = '''      const cutProbe=spec.residualCutProbe===undefined?[0,0]:spec.residualCutProbe;
      if(spec.residualCutProbe!==undefined){
        assert.ok(Array.isArray(cutProbe)&&cutProbe.length===2&&cutProbe.every(Number.isFinite),'Expected finite residualCutProbe in local metres');
        const removedPoint=point(...cutProbe);
        assert.ok(candidateGeometryContains(geometry,removedPoint),'Removed probe outside original owner');
        assert.ok(candidateGeometryContains(clip.geometry,removedPoint),'Removed probe outside replacement cut');
      }
      assert.equal(candidateGeometryContains(retained,point(...cutProbe)),false,'Removed probe still inside residual');'''


def apply(checker):
    contents = checker.read_text()
    if AFTER in contents:
        return
    if contents.count(BEFORE) != 1:
        raise ValueError('Expected one original residual assertion')
    with NamedTemporaryFile('w', dir=checker.parent, delete=False) as output:
        output.write(contents.replace(BEFORE, AFTER))
    os.chmod(output.name, checker.stat().st_mode)
    os.replace(output.name, checker)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checker', type=Path)
    apply(parser.parse_args().checker)
