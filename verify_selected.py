"""Standalone matrix reconstruction and upper-witness verification (stdlib only).
This does not rerun the exhaustive lower-bound search; see the audit records.
"""
from pathlib import Path
import json
R=Path(__file__).resolve().parent/'evidence/selected'
def read(p):return json.loads(p.read_text())
def supports(w):
 while w:
  low=w&-w;yield low.bit_length()-1;w^=low

def transpose(rows,n):
 out=[0]*n
 for i,row in enumerate(rows):
  for j in supports(row):out[j]^=1<<i
 return out

def basis(rows):
 out={}
 for v in rows:
  while v:
   k=v.bit_length()-1
   if k not in out:out[k]=v;break
   v^=out[k]
 return out

def remainder(v,b):
 while v:
  k=v.bit_length()-1
  if k not in b:return v
  v^=b[k]
 return 0

def matrices(d):
 p=d['p']
 if d['kind']=='group':
  m=d['m'];rho=d['rho'];q=p*m
  assert pow(rho,m,p)==1
  pairs=[(i,j) for i in range(p) for j in range(m)] if d['order']=='ij' else [(i,j) for j in range(m) for i in range(p)]
  index={x:i for i,x in enumerate(pairs)}
  def block(terms,right):
   out=[0]*q
   for col,(u,t) in enumerate(pairs):
    for i,j in terms:
     if right and d.get('inverse_right'):i,j=(-pow(rho,-j,p)*i)%p,(-j)%m
     dest=((u+pow(rho,t,p)*i)%p,(t+j)%m) if right else ((i+pow(rho,j,p)*u)%p,(j+t)%m)
     out[index[dest]]^=1<<col
   return out
  A=[[block(d['ring'][k],False) for k in ['a0','a1']]]
  B=[[block(d['ring'][k],True) for k in ['b0','b1']]]
 else:
  q=p
  def block(terms):
   out=[0]*q
   for col in range(q):
    for power,coef in terms:
     if coef%2:out[(col+power)%q]^=1<<col
   return out
  A=[[block(terms) for terms in row] for row in d['A']];B=A
 ra,sa,rb,sb=len(A),len(A[0]),len(B),len(B[0]);n=(sa*sb+ra*rb)*q
 AT=[[transpose(x,q) for x in row] for row in A];BT=[[transpose(x,q) for x in row] for row in B]
 hx=[];hz=[]
 for i in range(ra):
  for b in range(sb):
   for t in range(q):hx.append(sum(A[i][a][t]<<((a*sb+b)*q) for a in range(sa)) ^ sum(BT[j][b][t]<<((sa*sb+i*rb+j)*q) for j in range(rb)))
 for a in range(sa):
  for j in range(rb):
   for t in range(q):hz.append(sum(B[j][b][t]<<((a*sb+b)*q) for b in range(sb)) ^ sum(AT[i][a][t]<<((sa*sb+i*rb+j)*q) for i in range(ra)))
 return n,hx,hz

if __name__=='__main__':
 results=[]
 for r in read(R/'records.json'):
  ident=r['id'];doc=read(R/f'{ident}.json');n,hx,hz=matrices(read(R/f'{ident}_words.json'))
  assert n==doc['n']==r['n']
  assert [list(supports(v)) for v in hx]==doc['hx'] and [list(supports(v)) for v in hz]==doc['hz']
  assert all((x&z).bit_count()%2==0 for x in hx for z in hz)
  bx,bz=basis(hx),basis(hz);assert n-len(bx)-len(bz)==r['k']
  for s,checks,stab in [('X',hz,bx),('Z',hx,bz)]:
   positions=r['supports'][s];v=sum(1<<i for i in positions)
   assert v.bit_count()==len(set(positions))==r['upper'][s]
   assert all((v&w).bit_count()%2==0 for w in checks) and remainder(v,stab)
  results.append({'id':ident,'n':n,'k':r['k'],'ranks':[len(bx),len(bz)],'reconstructed':True,'upper_witnesses':r['upper']})
 print(json.dumps(results,indent=2))
