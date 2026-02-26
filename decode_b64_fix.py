import base64, sys, os
fn='cbt.db.b64'
out='cbt.db'
if not os.path.exists(fn):
    print('MISSING',fn)
    sys.exit(2)
b=open(fn,'rb').read()
# Remove whitespace/newlines and any non-base64 characters
import re
b = re.sub(b"[^A-Za-z0-9+/=]", b"", b)
# Fix padding
missing = (-len(b)) % 4
if missing:
    print('Adding padding of', missing)
    b += b'=' * missing
try:
    dec = base64.b64decode(b, validate=False)
except Exception as e:
    print('Decode error:', e)
    sys.exit(1)
open(out,'wb').write(dec)
print('Wrote', out, 'size', len(dec))
