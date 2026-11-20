"""Install the SHA-bound streamed-group audit extension at its first dependent scene."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
hash_bytes = lambda data: sha256(data).hexdigest()


def install(project, check):
    changes = {}
    report = {}
    patches = json.loads((HERE/'patches.json').read_bytes())
    for name, variants in patches.items():
        target = project/name
        before = target.read_bytes() if target.exists() else b''
        original = hash_bytes(before)
        results = {row['result_sha256'] for row in variants.values()}
        if original in results:
            report[name] = {'before': original, 'after': original, 'already_installed': True}
            continue
        if original not in variants:
            raise ValueError(f'Unrecognized input {name} SHA-256 {original}')
        row = variants[original]
        parts = before.decode().splitlines(keepends=True)
        for chunk in reversed(row['edits']):
            at = chunk['line']
            old = chunk['remove'].splitlines(keepends=True)
            if parts[at:at+len(old)] != old:
                raise ValueError(f'Patch context differs in {name} line {at+1}')
            parts[at:at+len(old)] = chunk['insert'].splitlines(keepends=True)
        after = ''.join(parts).encode()
        if hash_bytes(after) != row['result_sha256']:
            raise ValueError(f'Patched SHA-256 differs for {name}')
        changes[target] = after
        report[name] = {'before':original, 'after':hash_bytes(after)}
    if not check:
        for target, data in changes.items():
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temp:
                temp.write(data)
                name = temp.name
            os.chmod(name, 0o644)
            # Replacing the name leaves any hard-linked predecessor snapshot intact.
            os.replace(name,target)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path,help='the projects/shanghai directory in the new scene')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    print(json.dumps(install(args.project.resolve(),args.check),indent=2))
