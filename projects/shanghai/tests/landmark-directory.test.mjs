import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile, stat, mkdtemp, mkdir, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {walkingPose} from '../src/precise-registration-ui.js';

const root = new URL('../', import.meta.url);
const landmarks = JSON.parse(await readFile(new URL('data/landmarks.json', root), 'utf8'));
const directory = await readFile(new URL('landmarks.html', root), 'utf8');

test('every published landmark has exactly one static direct walking link with its exact name', () => {
  const cards = [...directory.matchAll(/<a\b[^>]*data-landmark="([^"]+)"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g)];
  assert.equal(cards.length, landmarks.length);
  assert.equal(new Set(cards.map(row => row[1])).size, landmarks.length);
  const decode = value => value.replaceAll('&amp;', '&').replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&#x27;', "'").replaceAll('&quot;', '"');
  for (const row of cards) {
    const record = landmarks.find(p => p.id === row[1]);
    assert.ok(record, row[1]);
    const url = new URL(decode(row[2]), 'https://example.test/projects/shanghai/landmarks.html');
    assert.equal(url.pathname, '/projects/shanghai/index.html');
    const hash = new URLSearchParams(url.hash.slice(1));
    assert.equal(hash.get('landmark'), record.id);
    assert.equal(hash.get('mode'), 'walk');
    assert.equal(decode(row[3].match(/<h3>(.*?)<\/h3>/s)[1]), record.name);
    const pose = walkingPose(record);
    assert.ok(pose && Object.values(pose).every(Number.isFinite), `${record.id} needs a valid walking pose`);
    assert.ok(pose.lng > 120 && pose.lng < 123 && pose.lat > 30 && pose.lat < 33, record.id);
  }
});

test('directory is reproducible from current navigation metadata', () => {
  execFileSync('python', [new URL('tools/build_landmark_directory.py', root).pathname, '--check']);
});

test('all directory resource links exist and map entry remains available while loading', async () => {
  for (const path of ['src/landmark-directory.css', 'src/landmark-directory.js', 'src/landmark-entry.css']) {
    assert.ok((await stat(new URL(path, root))).size > 0, path);
  }
  const index = await readFile(new URL('index.html', root), 'utf8');
  assert.match(index, /class="landmark-directory-link" href="landmarks\.html"/);
  assert.match(index, /class="loading-directory-link" href="landmarks\.html"/);
  assert.match(index, /href="src\/landmark-entry\.css"/);
  assert.doesNotMatch(directory, /(?:three\.module|maplibre-gl|app\.js)/);
});


test('a newly accepted building appears as the latest direct destination without editing the generator', async () => {
  const temporary = await mkdtemp(join(tmpdir(), 'shanghai-directory-latest-'));
  try {
    await mkdir(join(temporary, 'data'));
    const next = {...landmarks.findLast(item => item.kind === 'building'), id: 'next-accepted-building', name: '下一栋已验收建筑'};
    await writeFile(join(temporary, 'data/landmarks.json'), JSON.stringify([...landmarks, next]));
    await writeFile(join(temporary, 'data/districts.json'), await readFile(new URL('data/districts.json', root)));
    const rendered = execFileSync('python', ['-c', `import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('directory', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module.render(Path(sys.argv[2])))`, new URL('tools/build_landmark_directory.py', root).pathname, temporary], {encoding: 'utf8'});
    assert.match(rendered, /href="#building-next-accepted-building">本轮新增：下一栋已验收建筑/);
    assert.match(rendered, /class="landmark-card featured" id="building-next-accepted-building"/);
    assert.equal((rendered.match(/class="new-tag"/g) || []).length, 1);
    assert.equal((rendered.match(/data-landmark="/g) || []).length, landmarks.length + 1);
    assert.ok(rendered.includes('index.html#landmark=next-accepted-building&amp;mode=walk'));
  } finally {
    await rm(temporary, {recursive: true, force: true});
  }
});
