# Lock Russell's song files with his private code and write them, plus an
# index, into the site's private/ folder. Usage: python lock_songs.py <repo dir> <song files...>
# The code lives only in ~/.claude/middle-c-song-code.txt (never in git).
import os, sys, json, secrets, hashlib, re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CODE_FILE = os.path.expanduser('~/.claude/middle-c-song-code.txt')
ALPHA = 'abcdefghjkmnpqrstuvwxyz23456789'          # no 0/o/1/l/i to mistype
if not os.path.exists(CODE_FILE):
    raw = ''.join(secrets.choice(ALPHA) for _ in range(12))
    open(CODE_FILE, 'w').write(f'{raw[:4]}-{raw[4:8]}-{raw[8:]}\n')
code = open(CODE_FILE).read().strip()
norm = re.sub(r'[^a-z0-9]', '', code.lower())        # the app normalises the same way

repo, files = sys.argv[1], sys.argv[2:]
out = os.path.join(repo, 'private'); os.makedirs(out, exist_ok=True)
idx_path = os.path.join(out, 'index.json')
index = json.load(open(idx_path)) if os.path.exists(idx_path) else []
for f in files:
    name = os.path.basename(f)
    sid = re.sub(r'[^a-z0-9]+', '-', os.path.splitext(name)[0].lower()).strip('-')
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    key = hashlib.pbkdf2_hmac('sha256', norm.encode(), salt, 150000, 32)
    blob = salt + iv + AESGCM(key).encrypt(iv, open(f, 'rb').read(), None)
    open(os.path.join(out, sid + '.bin'), 'wb').write(blob)
    ver = hashlib.sha256(open(f, 'rb').read()).hexdigest()[:12]
    index = [e for e in index if e['id'] != sid] + [{'id': sid, 'file': sid + '.bin', 'name': name, 'v': ver}]
    print('locked', name, '->', sid + '.bin', len(blob), 'bytes')
json.dump(index, open(idx_path, 'w'), indent=1)
print('index:', [e['id'] for e in index])
