"""Measure the UV period on every exported triangle of the four auditorium finishes."""
import argparse
import importlib.util
import json
from pathlib import Path

METRIC='source/precise/xuhui-jianguo-336-lane-one-villa/measurements/check_finish_scale.py'
PROJECT=next(p for p in Path(__file__).absolute().parents if (p/METRIC).is_file())
spec=importlib.util.spec_from_file_location('metric',PROJECT/METRIC)
metric=importlib.util.module_from_spec(spec);spec.loader.exec_module(metric)
metric.PERIODS={'Shanghai High School hall | '+name:period for name,period in [
    ('ochre render',1.12),('cool grey cast trim',.96),('dressed stair stone',1.04),('weathered red roof covering',2.64)]}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();report=metric.measure(args.mesh)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
