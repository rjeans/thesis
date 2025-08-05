### 2.4.5 Hybrid boundary layer formulation <a id="section-2-4-5"></a>

The established technique for overcoming the problem of uniqueness in a boundary layer formulation is to express the surface velocity potential in terms of a hybrid combination of a single and double layer surface distribution. The exterior velocity potential is defined by,

$$\phi(P) = [L_k + \alpha M_k](v)(P), \quad P \in E. \tag{2.4.9}$$

Consequently, the boundary integral equations defining the acoustic problem are,

$$\phi = \{L_k + \alpha [M_k + (1 - c(p))]\} v, \tag{2.4.10}$$

$$\frac{\partial \phi}{\partial n} = \{[M_k^T - (1 - c(p))] + \alpha \, \nu_k^T \} v. \tag{2.4.11}$$

If the coupling constant, $\alpha$ is constrained to be imaginary, then the numerical solution of this hybrid formulation is unique at all frequencies. Again, the disadvantage of this formulation is that it requires the integration of the hypersingular kernel in the $N_k$ operator.