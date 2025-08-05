### 2.4.4 Boundary layer formulations <a id="section-2-4-4"></a>

The boundary layer formulations for the exterior acoustic problem also exhibit similar non-uniqueness properties at the critical wavenumbers described above. A similar argument to show this non-uniqueness to that for the SHIE and DSHIE can be used. However, another argument is illustrated in [Figure 2.3](#figure-2-3) and [Figure 2.4](#figure-2-4). These arguments use the jump properties of the integral operators derived in [Section 1.2.2](#section-1-2-2).

**Single layer:** $\phi^+ = L_k \mu = \sigma^-, \tag{2.4.5}$ $$\frac{\partial \phi^+}{\partial n} + (1 - c(p))\mu = M_k^T \mu = \frac{\partial \sigma^-}{\partial n} - c(p)\mu. \tag{2.4.6}$$

**Double layer:**

$$\phi^+ - (1 - c(p))\sigma = M_k \sigma = \sigma^- + c(p)\sigma, \tag{2.4.7}$$

$$\frac{\partial \phi^+}{\partial n} = N_k \sigma = \frac{\partial \sigma^-}{\partial n}. \tag{2.4.8}$$

The single layer formulation proves to be non-unique at eigenvalues of the interior Dirichlet problem, and the double layer formulation proves to be non-unique at eigenvalues of the interior Neumann problem.

#### 2.4.5 Hybrid boundary layer formulation

The established technique for overcoming the problem of uniqueness in a boundary layer formulation is to express the surface velocity potential in terms of a hybrid combination of a single and double layer surface distribution. The exterior velocity potential is defined by,

$$\phi(P) = [L_k + \alpha M_k]\{v\}(P), \quad P \in E. \tag{2.4.9}$$

Consequently, the boundary integral equations defining the acoustic problem are,

$$\phi = \{L_k + \alpha [M_k + (1 - c(p))]\} v, \tag{2.4.10}$$

$$\frac{\partial \phi}{\partial n} = \{[M_k^T - (1 - c(p))] + \alpha N_k^T \} v. \tag{2.4.11}$$

If the coupling constant, $\alpha$ is constrained to be imaginary, then the numerical solution of this hybrid formulation is unique at all frequencies. Again, the disadvantage of this formulation is that it requires the integration of the hypersingular kernel in the $N_k$ operator.