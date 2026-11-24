"""Download a hash-pinned release asset and safely unpack saved receipt files."""
from pathlib import Path
import argparse,hashlib,json,tarfile,urllib.request
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--id',required=True);a=ap.parse_args()
entry=next(x for x in json.loads((R/'data/receipt_archives.json').read_text()) if x['id']==a.id)
out=R/'downloads';out.mkdir(exist_ok=True);asset=out/entry['asset']
if not asset.exists():
 tmp=asset.with_suffix('.part');urllib.request.urlretrieve(entry['url'],tmp);tmp.replace(asset)
h=hashlib.sha256()
with asset.open('rb') as f:
 for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
assert h.hexdigest()==entry['sha256'] and asset.stat().st_size==entry['bytes'],'Asset identity mismatch'
with tarfile.open(asset) as tf:
 members=tf.getmembers();assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and (m.isfile() or m.isdir()) for m in members)
 assert all(m.name=='receipts' or (m.name=='receipts/'+entry['id'] or m.name.startswith('receipts/'+entry['id']+'/')) for m in members)
 tf.extractall(R)
print('Downloaded, hashed and unpacked',entry['id'])
