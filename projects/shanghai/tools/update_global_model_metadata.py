"""Record city placement separately from the original candidate delivery status."""
import argparse
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    catalog = json.loads((PROJECT / 'data/candidate-city-integrations.json').read_text())
    models = {row['id']: row for row in catalog['models']}
    queue_path = PROJECT / 'data/model-todo/queue.json'
    queue = json.loads(queue_path.read_text())
    seen = set()
    for row in queue['production_queue'] + queue['existing_models']:
        if row['id'] not in models:
            continue
        model = models[row['id']]
        seen.add(row['id'])
        if 'next_action_before_city_integration' not in row:
            row['next_action_before_city_integration'] = row.get('next_action', '')
        row['city_integration'] = {
            'catalog': 'projects/shanghai/data/candidate-city-integrations.json',
            'preview': 'https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=' + row['id'] + '&mode=overview',
            'status': 'approximate-placement',
            'walk_enabled': model.get('navigation', {}).get('listed') is True,
            'note': model.get('registration_note', '近似定位；尺寸与未见构造仍含估计'),
        }
        row['next_action'] = '已接入全局场景（近似定位）；继续核验原址坐标、尺寸与未见细节，原单体来源及范围限制仍保留'
    assert seen == set(models), 'City integration lacks a production-queue record'
    payload = json.dumps(queue, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert queue_path.read_text() == payload, 'Outdated queue city integration metadata'
    else:
        queue_path.write_text(payload)
    print(json.dumps({'city_integrated_candidates': len(seen)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
