"""Resolve the versioned metadata requests made by a released main-map module."""
import re
from urllib.parse import urlsplit


def scene_metadata_urls(app_url, source, prefix):
    """Read the release key from the same entry URL or fallback used by the browser."""
    if 'const metadataRevision=' in source:
        fallback, = re.findall(r"const metadataRevision=new URL\(import\.meta\.url\)\.search \|\| '(\?v=[a-z0-9-]+)';", source)
        query = urlsplit(app_url).query
        suffix = '?' + query if query else fallback
        paths = re.findall(r"\['(data/[a-z0-9-]+\.json)',metadataRevision\]", source)
        expected = {'data/landmarks.json', 'data/precise-buildings-v6.json', 'data/candidate-city-integrations.json'}
        assert len(paths) == len(expected) and set(paths) == expected, paths
    else:
        suffix, = re.findall(r"candidate-city-integrations\.json'\?'(\?[^']+)'", source)
        paths = ['data/candidate-city-integrations.json']
    return [prefix + path + suffix for path in paths]
