"""Download pinned axe-core for optional browser QA, never for the public site."""
from pathlib import Path
import hashlib
import io
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1] / '.artifacts'
root.mkdir(exist_ok=True)
url = 'https://registry.npmjs.org/axe-core/-/axe-core-4.10.3.tgz'
with urllib.request.urlopen(url, timeout=30) as response:
    archive = response.read()
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    script = tar.extractfile('package/axe.min.js').read()
if hashlib.sha256(script).hexdigest() != '880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb':
    raise RuntimeError('QA asset checksum mismatch')
(root / 'axe.min.js').write_bytes(script)
print('axe-core 4.10.3 verified and ready for QA')
