"""Shoot the eight 2016 condensers, dated window cages and their western wall junctions in a delivered mesh."""
import argparse
import hashlib
import json
from pathlib import Path
from check_stacked_balconies import proof

HERE=Path(__file__).absolute().parent
CASE='1230 attachments | warm-grey condenser'
FAN='1230 attachments | shaded fan grille'
EDGE='1230 attachments | pale edge rail'
ZINC='1230 attachments | dull zinc-grey guard'
FOOT='Guangming | grey painted base and bands'
CAST='Guangming | grey precast balcony'
IRON='Guangming | dark iron railing'


def controls():
    doc=json.loads((HERE/'attachment-observations.json').read_bytes())
    rows=[]
    for item in doc['condenser_cases']:
        ring=item['pixels']
        # The white case covers the entire photographed quadrangle. The round
        # fan is left of centre. Sample it and the right-hand body separately.
        for category,u in [('fan',.40),('body',.82)]:
            xy=[round(.5*((1-u)*(ring[0][k]+ring[3][k])+u*(ring[1][k]+ring[2][k]))) for k in (0,1)]
            rows.append(dict(feature=item['name']+' '+category,uv=xy,wanted=FAN if category=='fan' else CASE,
                             allowed=[FAN,CASE],class_name='condenser',tolerance=2))
    samples=[
        ('west guard east return', (273,394), [ZINC,EDGE]),
        ('west guard shallow turned base', (244,425), [ZINC,EDGE]),
        ('west guard upper lip', (230,356), [ZINC,EDGE]),
        ('west guard west upright', (165,389), [ZINC,EDGE]),
        ('metal top east of the door', (441,363), [ZINC,EDGE]),
        ('metal lower edge east of the door', (451,434), [ZINC,EDGE]),
        ('later guard over projection', (544,397), [ZINC,EDGE,IRON]),
        ('masonry under west-returning basket', (178,446), [FOOT,CAST])]
    for name,uv,mats in samples:
        rows.append(dict(feature=name,uv=list(uv),wanted=mats[0],allowed=mats,class_name='cage or western wall',tolerance=3))
    return rows


def run(mesh):
    base=controls()
    batch=[]
    for idx,row in enumerate(base):
        r=row['tolerance'];x,y=row['uv']
        for dx,dy in sorted(((dx,dy) for dx in range(-r,r+1) for dy in range(-r,r+1) if dx*dx+dy*dy<=r*r),
                            key=lambda d:d[0]**2+d[1]**2):
            batch.append(dict(index=idx,feature=row['feature'],uv=[x+dx,y+dy],wanted=row['wanted']))
    # Select the closest admissible sample while preserving the unshifted result.
    # The original first hit always remains part of the public record.
    checked=proof(mesh,'25',batch)
    groups=[[] for row in base]
    for ray in checked['rays']:
        groups[ray['index']].append(ray)
    out=[]
    for row,shots in zip(base,groups):
        actual=shots[0]
        found=next((hit for hit in shots if hit['actual'] in row['allowed']),None)
        out.append({**row,'direct':actual['actual'] in row['allowed'],'original_hit':actual,'nearest':found,'passed':bool(found)})
    historic_pixels = [
        ('2013 visible upper horizontal rail', (260,573)),
        ('2013 visible left second rail', (270,592)),
        ('2013 visible middle cross rail', (314,611)),
        ('2013 lower horizontal rail', (323,647)),
        ('2013 centre upright', (290,627)),
        ('2013 right upright', (365,655))]
    earlier=proof(mesh,'04',[dict(feature=n,uv=list(uv),wanted=ZINC) for n,uv in historic_pixels])
    for r in earlier['rays']:
        r.pop('passed',None)
    return dict(model_sha256=checked['sha256'],station='Masa 2016 at original 650×487',
                input_sha256=hashlib.sha256((HERE/'attachment-observations.json').read_bytes()).hexdigest(),
                original_count=len(base),subsample_casts=len(batch),exact=sum(r['direct'] for r in out),
                within_tolerance=sum(r['passed'] for r in out),checks=out,
                earlier_photo_on_2016_mesh=earlier['rays'],
                earlier_state='Gao’s photograph published in 2013 shows an inset grille beside the entrance. The projecting 2016 basket is separately modelled and can occlude this earlier plane.')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();result=run(args.mesh)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['exact'],result['within_tolerance'],result['original_count'])
