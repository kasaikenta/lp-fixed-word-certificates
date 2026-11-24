"""Audit complete saved records. This script never launches a distance search."""
from pathlib import Path
import argparse,hashlib,json,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'vendor/QEDist'))
from cssdist.code import CSSCode

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=1);ap.add_argument('--id',required=True,choices=['p25_m20_r4','Mitten-975_p22_r3_v0']);args=ap.parse_args()
 records=json.loads((R/'data/receipt_archives.json').read_text());entry=next(x for x in records if x['id']==args.id)
 root=R/'receipts'/args.id
 for name,want in json.loads((root/'SHA256.json').read_text()).items():assert sha(root/name)==want,name
 code=CSSCode.load(root/'code.json');assert code.fingerprint==entry['code_sha256']
 if args.id=='p25_m20_r4':
  import nested_audit
  if args.workers>1:
   from functools import partial
   from parallel_receipts import scan_archives
   nested_audit.scan_archives=partial(scan_archives,workers=args.workers)
  audit_stage=nested_audit.audit_stage
  folder=R/'evidence/mitten_2500_distance30'
  witness_files={'X':folder/'extra_witness_X.json','Z':folder/'witness.json'}
 else:
  assert args.workers==1,'Legacy archive uses the serial auditor'
  from legacy_nested_audit import audit_stage
  folder=R/'evidence/mitten_1650_distance30'
  witness_files={s:folder/('extra_witness_'+s+'.json') for s in ('X','Z')}
 result=audit_stage(root,29)
 assert result['complete'] and result['attempts']==entry['attempts']
 assert set(result['coverage'])=={'X-anchor','X-stripe','Z-anchor','Z-stripe'}
 matching=[]
 for sector,path in witness_files.items():
  witness=json.loads(path.read_text())
  assert witness.get('code_sha256',code.fingerprint)==code.fingerprint
  assert len(set(witness['support']))==len(witness['support']) and all(0<=i<code.n for i in witness['support'])
  v=sum(1<<i for i in witness['support']);assert v.bit_count()==witness['weight'] and code.is_logical(v,sector)
  if v.bit_count()<result['sector_bounds'][sector]['upper']:
   result['sector_bounds'][sector].update(upper=v.bit_count(),support=witness['support'])
  if v.bit_count()==30:matching.append(sector)
 assert matching
 result['audit_workers']=args.workers
 result['verified_global_distance']=30;result['matching_witness_sectors']=matching;result['exhaustive_search_rerun']=False;result['full_saved_receipt_audit_rerun']=True
 out=R/'verification_results';out.mkdir(exist_ok=True);(out/(args.id+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'id':args.id,'attempts':result['attempts'],'complete':True,'verified_global_distance':30,'code_sha256':code.fingerprint}),flush=True)
if __name__=='__main__':main()
