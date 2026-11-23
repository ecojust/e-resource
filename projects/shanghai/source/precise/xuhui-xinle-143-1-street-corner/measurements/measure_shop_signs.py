"""Trace the two distinct shop inscriptions visible on the 2018 street photograph."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from measure_number_plates import measure

# Each quadrilateral follows its own physical plane. The hood carries white
# ink across its right-hand end, and the smaller sign sits below the 143-1 plate.
SIGNS = {
    'canopy': {'tl_tr_br_bl': [(2567,2042),(2754,2024),(2755,2062),(2567,2080)],
               'ink_box': (.019,.045,.988,.95), 'line_thresholds': (100.,100.),
               'grid': (216,44),'inscription':['CUBTINA']},
    'illuminated': {'tl_tr_br_bl': [(2727,2387),(2872,2382),(2878,2449),(2733,2455)],
                    'ink_box': (.035,.16,.936,.80), 'line_thresholds': (133.,133.),
                    'grid': (190,86),'inscription':['CUBTINA']},
}

if __name__ == '__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('photograph',type=Path)
    cli.add_argument('output',type=Path)
    args=cli.parse_args()
    digest=hashlib.sha256(args.photograph.read_bytes()).hexdigest()
    if digest!='e8a4184455de6777e39ec3f993557f5b8de8d7753ca9a5fe166082ae3f35a93f':
        raise ValueError('Use the original 2018 Xinle Road 143 photograph by Antigng.')
    with Image.open(args.photograph) as image:
        signs={key:measure(image,params) for key,params in SIGNS.items()}
    result=dict(photo='https://commons.wikimedia.org/wiki/Special:Redirect/page/66206083',
                author='Antigng',date='2018-02-07',license='CC BY-SA 4.0',source_sha256=digest,signs=signs)
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print([(k,s['traced_regions'],s['median_letter_srgb']) for k,s in signs.items()])
