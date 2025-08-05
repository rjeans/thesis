### 2.4.1 SHIE and DSHIE formulations <a id="section-2-4-1"></a>

For given boundary conditions, the velocity potential for the exterior problem is unique. However, it has long been recognized that when expressed in terms of a boundary integral formulation, the solution to the exterior problem may not be unique. Non-uniqueness of the solution occurs at critical wavenumbers $k_n$, and for the acoustic problem, these wavenumbers correspond to interior resonant frequencies. It needs to be emphasized that this problem of non-uniqueness does not imply non-uniqueness of a physical solution, but a breakdown of the theoretical formulation at critical frequencies. A numerical implementation of an unmodified exterior boundary integral formulation will result in ill-conditioning of the matrices at a range of frequencies, centered around the critical frequency.

The problem of non-uniqueness can be illustrated by considering the exterior Neumann problem, Eq. (2.3.11), for a ‘smooth surface’. There will be a unique solution as long as there are no non-trivial solutions to the homogeneous equation,

$$\left( \frac{1}{2} I + M_T^+ \right) \nu = 0. \tag{2.4.1}$$

The non-trivial solutions to this equation occur at the eigenvalues $k_n$. By the Fredholm Alternative theorems, the eigenvalue spectrum of this equation is the same as that of the transpose of

$$\left( \frac{1}{2} I + M_k \right) \nu' = 0. \tag{2.4.2}$$

The eigenvalues of this equation correspond to the eigenvalues for the unrelated interior Neumann problem, Eq (2.3.9). Similarly, the critical wavenumbers for the exterior Dirichlet problem correspond to the eigenvalues of the interior Dirichlet problem.