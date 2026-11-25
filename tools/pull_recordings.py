"""Download new "Teach it your piano" recordings from the app's private storage.

usage: python tools/pull_recordings.py [destination folder]

Default destination: OneDrive/Desktop/Claude Stuff/Middle C recordings.
Needs the song code in ~/.claude/middle-c-song-code.txt (never in this repo):
the upload folder and the read key are both derived from it. The Supabase
address and its public key are read from index.html.
"""
import hashlib, json, pathlib, re, sys, urllib.request

repo = pathlib.Path(__file__).resolve().parent.parent
page = (repo / 'index.html').read_text(encoding='utf-8')
SUPA = re.search(r"SUPA:'([^']+)'", page).group(1)
ANON = re.search(r"ANON:'([^']+)'", page).group(1)
code = re.sub(r'[^a-z0-9]', '', (pathlib.Path.home() / '.claude' / 'middle-c-song-code.txt').read_text().strip().lower())
FOLDER = hashlib.sha256(('middle-c-uploads:' + code).encode()).hexdigest()[:32]
READ = hashlib.sha256(('middle-c-read:' + code).encode()).hexdigest()[:40]
H = {'apikey': ANON, 'Authorization': 'Bearer ' + ANON, 'x-middle-c-key': READ}

dest = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path.home() / 'OneDrive' / 'Desktop' / 'Claude Stuff' / 'Middle C recordings'
dest.mkdir(parents=True, exist_ok=True)

def call(path, body=None):
    r = urllib.request.Request(SUPA + path, data=body, method='POST' if body else 'GET',
                               headers={**H, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r) as f:
        return f.read()

names = [o['name'] for o in json.loads(call('/storage/v1/object/list/middle-c',
         json.dumps({'prefix': FOLDER + '/', 'limit': 1000, 'sortBy': {'column': 'name', 'order': 'asc'}}).encode()))]
new = [n for n in names if not (dest / n).exists()]
for n in new:
    (dest / n).write_bytes(call(f'/storage/v1/object/authenticated/middle-c/{FOLDER}/{n}'))
print(f'{len(names)} files online, {len(new)} new, saved to {dest}')
for n in new:
    print('  ' + n)
