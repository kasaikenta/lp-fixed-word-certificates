"""Derive a cutoff-only public receipt archive without changing receipt blobs."""
from pathlib import Path
import gzip,hashlib,json,shutil,sqlite3,sys,tarfile,tempfile,time
import argparse
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source',required=True,type=Path,help='Original campaign export tar')
ap.add_argument('--workdir',required=True,type=Path,help='New, empty derivation workspace')
args=ap.parse_args()
ROOT=args.workdir.resolve();ROOT.mkdir(parents=True,exist_ok=False)
SOURCE=args.source.resolve()
RAW=ROOT/'raw_p25_m20_r4'
OUT=ROOT/'curated/receipts/p25_m20_r4'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
 return h.hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
RAW.mkdir(exist_ok=True)
with tarfile.open(SOURCE) as tf:
 members=tf.getmembers()
 assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and (m.isfile() or m.isdir()) for m in members)
 tf.extractall(RAW)
OUT.mkdir(parents=True,exist_ok=True)
shutil.copy2(RAW/'code.json',OUT/'code.json')
for p in sorted((RAW/'campaigns').iterdir()):shutil.copytree(p,OUT/'campaigns'/p.name)
db=sqlite3.connect(f'file:{(RAW/"queue.sqlite").resolve()}?mode=ro',uri=True)
tasks=db.execute('SELECT w,side,shard,status FROM tasks WHERE w>=2900 AND w<3000 ORDER BY w,side,shard').fetchall();db.close()
db=sqlite3.connect(OUT/'queue.sqlite');db.execute('CREATE TABLE tasks(w INTEGER,side TEXT,shard INTEGER,status TEXT)');db.executemany('INSERT INTO tasks VALUES(?,?,?,?)',tasks);db.commit();db.close()
count=0;chunks=[];start=time.time()
paths=sorted((RAW/'workers').glob('*/evidence*.sqlite.gz'))
with tempfile.TemporaryDirectory(prefix='lp-public-curation-') as td:
 tmp=Path(td)
 for i,p in enumerate(paths):
  meta=json.loads(p.with_suffix(p.suffix+'.json').read_text());assert sha(p)==meta['compressed_sha256']
  src=tmp/'source.sqlite'
  with gzip.open(p,'rb') as f,src.open('wb') as g:shutil.copyfileobj(f,g)
  assert src.stat().st_size==meta['uncompressed_bytes'] and sha(src)==meta['source_sha256']
  source=sqlite3.connect(f'file:{src}?mode=ro',uri=True)
  assert source.execute('PRAGMA quick_check').fetchone()[0]=='ok'
  rows=source.execute('SELECT * FROM attempts WHERE w>=2900 AND w<3000 ORDER BY id').fetchall()
  schema=source.execute("SELECT sql FROM sqlite_master WHERE name='attempts'").fetchone()[0];source.close()
  if rows:
   dst=tmp/'filtered.sqlite';target=sqlite3.connect(dst);target.execute(schema)
   target.executemany('INSERT INTO attempts VALUES('+','.join('?' for _ in rows[0])+')',rows);target.commit()
   assert target.execute('SELECT * FROM attempts ORDER BY id').fetchall()==rows;target.close()
   dest=OUT/p.relative_to(RAW);dest.parent.mkdir(parents=True,exist_ok=True)
   with dst.open('rb') as f,gzip.open(dest,'wb',compresslevel=6) as g:shutil.copyfileobj(f,g)
   info={'source_sha256':sha(dst),'compressed_sha256':sha(dest),'attempts':len(rows),'uncompressed_bytes':dst.stat().st_size,'compressed_bytes':dest.stat().st_size,'derived_from':str(p.relative_to(RAW)),'original_compressed_sha256':meta['compressed_sha256'],'original_uncompressed_sha256':meta['source_sha256'],'receipt_rows_preserved_byte_for_byte':True}
   dump(dest.with_suffix(dest.suffix+'.json'),info);chunks.append(info);count+=len(rows);dst.unlink()
  src.unlink()
  if i%100==0:print(json.dumps({'chunks_processed':i+1,'of':len(paths),'attempts_retained':count,'seconds':round(time.time()-start)}),flush=True)
dump(OUT/'curation.json',{'cutoff':29,'attempts':count,'source_tar_sha256':sha(SOURCE),'tasks':len(tasks),'chunks_retained':len(chunks),'receipt_rows_preserved_byte_for_byte':True,'other_cutoffs_removed':True})
files={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
dump(OUT/'SHA256.json',files)
asset=ROOT/'p25_m20_r4_w29_receipts.tar.gz'
with tarfile.open(asset,'w:gz',compresslevel=6) as tf:tf.add(OUT,arcname='receipts/p25_m20_r4')
print(json.dumps({'asset':str(asset),'bytes':asset.stat().st_size,'sha256':sha(asset),'attempts':count,'chunks':len(chunks)}),flush=True)
