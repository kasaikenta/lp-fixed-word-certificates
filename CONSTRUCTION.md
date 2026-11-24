# Code definition and coordinate convention

The finite group is

`G(p,m,rho) = <x,w | x^p = w^m = 1, w x w^-1 = x^rho>`.

Require gcd(rho,p)=1 and rho^m=1 modulo p. Coordinates `(i,j)=x^i w^j` are ordered lexicographically, with local index `i*m+j`. The multiplication rule is `(i,j)(u,v)=(i+rho^j*u mod p,j+v mod m)`.

The fixed constituent expressions are:

```text
a0 = x^11 w^7 + x^11 w^11 + x^5 w^14
a1 = 1 + x^9 + x^4 w^14
b0 = w^-7 x^-1 + w^-3 x^-3 + w^-12 x^-9
b1 = 1 + w^-2 x^-9 + w^-14 x^-6
```

Negative powers and factor order are retained literally. The right action is `R_h e_u=e_(u h)`, so the displayed b-entries already contain the inverse convention needed for reconstruction. The five physical blocks each have size q=p*m; the first four have coordinates `(a,b,u)` for a,b=0,1, followed by the distinguished fifth block. The exact binary assembly is implemented in `verify_selected.py`.

All constituent entries have three distinct evaluated terms for the three selected groups. Each check has weight nine. Both check matrices have full row rank, giving k=q and n=5q. Orthogonality follows from commuting left and right regular actions.

The result depends on these formal representatives. For example, replacing x^11 by x^24 in the first term leaves the p=13 parent unchanged, but can change the p=25 target. The procedure is not a canonical operation on binary-code equivalence classes.

The original code matrices are reproduced under the documented qubit/check ordering. The machine-readable data are the definitive fixed instances for the receipt hashes. A portable checksum manifest accompanies this release.
