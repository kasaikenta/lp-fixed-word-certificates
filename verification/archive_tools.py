"""Lossless closed-chunk compression with hashes and bounded scratch expansion."""
import gzip,hashlib,json,os,shutil,sqlite3,fcntl
from pathlib import Path
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()
def compress_worker(out):
    with (out.parent.parent/'archive.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        source=out/'evidence.sqlite'
        if not source.exists():return
        db=sqlite3.connect(source)
        assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
        db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        count=db.execute('SELECT count(*) FROM attempts').fetchone()[0];db.close()
        serial=1+max([int(p.name.split('-')[1].split('.')[0]) for p in out.glob('evidence-*.sqlite.gz')]+[0])
        dest=out/f'evidence-{serial:06d}.sqlite.gz';temp=dest.with_suffix('.tmp')
        digest=sha(source)
        with source.open('rb') as src,gzip.open(temp,'wb',compresslevel=3) as dst:shutil.copyfileobj(src,dst)
        with temp.open('rb') as f:os.fsync(f.fileno())
        h=hashlib.sha256()
        with gzip.open(temp,'rb') as f:
            for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
        assert h.hexdigest()==digest
        temp.replace(dest)
        meta={'source_sha256':digest,'compressed_sha256':sha(dest),'attempts':count,
              'uncompressed_bytes':source.stat().st_size,'compressed_bytes':dest.stat().st_size}
        dest.with_suffix(dest.suffix+'.json').write_text(json.dumps(meta,indent=2)+'\n')
        source.unlink()
        for suffix in ['-wal','-shm']:Path(str(source)+suffix).unlink(missing_ok=True)
        return meta
def archive_databases(snapshot,scratch):
    with (snapshot/'archive.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_SH)
        paths=sorted(p for p in (snapshot/'workers').glob('*/evidence*.sqlite*')
                     if p.name=='evidence.sqlite' or p.name.endswith('.sqlite.gz'))
        for i,path in enumerate(paths):
            expanded=None
            if path.name.endswith('.gz'):
                meta=json.loads(path.with_suffix(path.suffix+'.json').read_text())
                assert sha(path)==meta['compressed_sha256']
                expanded=scratch/f'expanded-{i}.sqlite'
                with gzip.open(path,'rb') as src,expanded.open('wb') as dst:shutil.copyfileobj(src,dst)
                assert expanded.stat().st_size==meta['uncompressed_bytes'] and sha(expanded)==meta['source_sha256']
                source=expanded
            else:source=path
            db=sqlite3.connect(f'file:{source.resolve()}?mode=ro',uri=True)
            try:yield path,db
            finally:
                db.close()
                if expanded:expanded.unlink()
