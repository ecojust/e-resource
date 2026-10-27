#!/usr/bin/env python3
"""Serve only actual bytes lazily extracted from a fully verified launcher ZIP.

This is a QA harness, not a new runtime dependency. No MAIN/project fallback.
The complete archive must already have passed check_launcher_zip_v6.py.
"""
from __future__ import annotations
import argparse, hashlib, json, os, threading, time, zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--validation',type=Path,required=True)
    p.add_argument('--extract-to',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--port',type=int,default=8876)
    a=p.parse_args()
    archive=a.archive.resolve();check=json.loads(a.validation.read_text())
    assert check.get('passed') is True and check.get('publishable') is True
    archive_sha=digest(archive)
    assert archive_sha==check['archive_sha256'] and archive.stat().st_size==check['archive_bytes']<100_000_000
    root=a.extract_to.absolute()
    assert not root.exists() and not root.is_symlink(), 'New extraction directory required'
    assert root.parent.is_dir() and root.parent.resolve()==root.parent
    assert not a.report.exists(), 'Preserve prior extraction proof'
    with zipfile.ZipFile(archive) as z:
        manifest_bytes=z.read('shanghai/LAUNCHER-MANIFEST.json');manifest=json.loads(manifest_bytes)
        assert manifest['commit']==check['expected_commit']==check['manifest_commit']
        expected={r['file']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in manifest['files']}
        expected['LAUNCHER-MANIFEST.json']={'bytes':len(manifest_bytes),'sha256':hashlib.sha256(manifest_bytes).hexdigest()}
        assert len(expected)==len(z.infolist())==check['zip_crc_streams_verified']
        assert {'shanghai/'+f for f in expected}==set(z.namelist())
    root.mkdir(mode=0o700);(root/'shanghai').mkdir()
    lock=threading.Lock();extracted={}
    report={'schema':'launcher-lazy-actual-extraction-v13','archive':str(archive),
            'archive_sha256':archive_sha,'commit':manifest['commit'],'root':str(root),
            'archive_validation':str(a.validation.resolve()),
            'archive_validation_sha256':digest(a.validation),'full_archive_crc_prevalidated':True,
            'serves_only_archive_members':True,'main_fallback':False,'files':[],
            'scope':'Only requested members are extracted and SHA-verified; this does not claim full-disk extraction or any browser result.'}
    def save():
        report['files']=[{'file':k,**v} for k,v in sorted(extracted.items())]
        report['extracted_count']=len(extracted);report['extracted_bytes']=sum(x['bytes'] for x in extracted.values())
        report['updated_at']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        temporary=a.report.with_suffix(a.report.suffix+'.tmp')
        temporary.write_text(json.dumps(report,indent=2)+'\n');temporary.replace(a.report)
    save()
    def resolve_request(url):
        relative=unquote(urlsplit(url).path).lstrip('/') or 'index.html'
        path=PurePosixPath(relative)
        if relative not in expected or path.as_posix()!=relative or '..' in path.parts:return None
        destination=root/'shanghai'/relative
        with lock:
            if relative in extracted:
                assert destination.is_file() and not destination.is_symlink()
                assert destination.stat().st_size==expected[relative]['bytes'] and digest(destination)==expected[relative]['sha256']
                return destination
            with zipfile.ZipFile(archive) as z:content=z.read('shanghai/'+relative)
            assert len(content)==expected[relative]['bytes'] and hashlib.sha256(content).hexdigest()==expected[relative]['sha256']
            destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open('xb') as f:f.write(content)
            os.chmod(destination,0o644)
            assert digest(destination)==expected[relative]['sha256']
            extracted[relative]=expected[relative];save()
            return destination
    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self,path):
            destination=resolve_request(path)
            return str(destination) if destination else str(root/'__not_an_archive_member__')
        def end_headers(self):
            self.send_header('Cache-Control','no-cache');super().end_headers()
        def list_directory(self,path):
            self.send_error(404);return None
    print(f'Archive-only lazy extraction HTTP http://127.0.0.1:{a.port}/; commit {manifest["commit"]}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()

if __name__=='__main__':main()
