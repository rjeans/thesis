### 2.4.2 The CHIEF method <a id="section-2-4-2"></a>

One of the first methods proposed to remove the problem of non-uniqueness was that of Schenck [1968]. In this method, the algebraic equations generated from the SHIE are combined with additional equations generated from the interior Helmholtz' relationship,

$$\mathbf{M}_k [\phi](P) = \mathbf{L}_k \left[ \frac{\partial \phi}{\partial n} \right](P) - \phi_i(P), \quad P \in D, \tag{2.4.3}$$

evaluated at a number of interior points. The resulting overdetermined set of equations can be solved by a least squares method.

There are several problems with this method. When some of the interior points lie on nodal surfaces, it has been shown that this method may not remove the problem of uniqueness. Consequently, at high frequencies when the density of interior nodal surfaces is high, the choice of interior nodal position is difficult. Several methods for choosing these nodal points have been proposed, but this adds to the complexity of the solution. For an arbitrary selection of interior points, this method cannot be relied on to remove the problem of non-uniqueness.