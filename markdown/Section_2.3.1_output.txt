### 2.3.1 Surface Helmholtz Integral Equation <a id="section-2-3-1"></a>

The Surface Helmholtz' Integral equation (SHIE) forms the basis of most boundary element methods (BEM). This equation can be derived by considering the general acoustic geometry shown in [Figure 2.2](#figure-2-2). A spherical surface, $S_\Sigma$, contains two closed surfaces $S_i$ and $S$. The surface $S$ represents the acoustic surface of interest and the surface $S_i$ represents the surface of some acoustic source. The domain $E$ is the volume contained by $S_\Sigma$ excluding the volume contained by $S_i$ and $S$. The domain $D$ represents the volume contained by the surface $S$. A small spherical surface $S_\epsilon$ surrounds the field point $P$.

With the surface $S_\epsilon$ excluding the singular point $P$ from the domain $E$, both the Green's free space function and the velocity potential in $E$ satisfy the reduced wave equation, and so,

<a id="equation-2-3-1"></a>
$$\int_E \left( \phi(Q) \nabla^2 G_k(P, Q) - G_k(P, Q) \nabla^2 \phi(Q) \right) dV_Q = 0. \tag{2.3.1}$$

By using Green's formula, this volume integral may be converted to a combination of surface integrals over the surfaces bounding $E$,

<a id="equation-2-3-2"></a>
$$I_S(P) + I_{S_i}(P) + I_{S_\epsilon}(P) + I_{S_\Sigma}(P) = 0, \tag{2.3.2}$$

where the integrals $I(P)$ are of the form,

<a id="equation-2-3-3"></a>
$$I_S(P) = \int_{S} \left( \phi(q) \frac{\partial G_k(P, q)}{\partial n_q} - \frac{\partial \phi(q)}{\partial n_q} G_k(P, q) \right) dS_q. \tag{2.3.3}$$

The negative sign reflects the fact that the normals are defined to point into the domain $E$.

The SHIE for an infinite exterior domain is obtained when the radius of the surface $S_\Sigma$ is taken to infinity and the radius of $S_\epsilon$ is taken to zero. By the Sommerfeld radiation condition, $I_{S_\Sigma}$ will tend to zero. The integral $I_{S_\epsilon}$ has different values depending on the position of the field point $P$. For $P$ in $D$, its value must be zero since $I_{S_\epsilon}$ is no longer a bounding surface of $E$. For $P$ on $S$ or in $E$, its value can be evaluated in a similar way to the limiting procedures of section (1.2.2). The value of this integral as in the limit is given by,

<a id="equation-2-3-4"></a>
$$I_{S_\epsilon}(P) = \begin{cases} \phi(P) & P \in E \\ c(P) \phi(P) & P \in S \\ 0 & P \in D \end{cases}. \tag{2.3.4}$$

The integral $I_{S_i}$ may now be seen to be equivalent to the velocity potential that would exist in the absence of the surface $S$,

<a id="equation-2-3-5"></a> $I_{S_i}(P) = \phi_i(P). \tag{2.3.5}$ The SHIE for the infinite exterior domain can now be written as,

<a id="equation-2-3-6"></a>
$$\int_{S} \left( \phi(q) \frac{\partial G_k(P, q)}{\partial n_q} - \frac{\partial \phi(q)}{\partial n_q} G_k(P, q) \right) dS_q + \phi_i(P) = \begin{cases} \phi(P) & P \in E \\ c(P) \phi(P) & P \in S \\ 0 & P \in D \end{cases}. \tag{2.3.6}$$

Using a similar argument, the SHIE for the interior problem can be derived:

<a id="equation-2-3-7"></a>
$$\int_{S} \left( \phi(q) \frac{\partial G_k(P, q)}{\partial n_q} - \frac{\partial \phi(q)}{\partial n_q} G_k(P, q) \right) dS_q = \begin{cases} 0 & P \in E \\ -(1 - c(P))\phi(P) & P \in S \\ -\phi(P) & P \in D \end{cases}. \tag{2.3.7}$$

In terms of integral operator notation, the boundary integral equations on the surface $S$ are given by,

**Exterior:**

<a id="equation-2-3-8"></a>
$$L_k \frac{\partial \phi}{\partial n} - \phi_i = \left[-c(p)I + M_k\right]\phi, \tag{2.3.8}$$

**Interior:**

<a id="equation-2-3-9"></a>
$$L_k \frac{\partial \phi}{\partial n} = \left[(1 - c(p))I + M_k\right]\phi. \tag{2.3.9}$$

#### 2.3.2 Differentiated Surface Helmholtz' Integral Equation

The SHIE taken on the boundary surface may be differentiated with respect to the normal at $P$ to obtain the Differentiated Surface Helmholtz' Integral Equation (DSHIE),

<a id="equation-2-3-10"></a>
$$\int_{S} \left( \phi(q) \frac{\partial^2 G_k(P, q)}{\partial n_p \partial n_q} - \frac{\partial \phi(q)}{\partial n_q} \frac{\partial G_k(P, q)}{\partial n_p} \right) dS_q + \frac{\partial \phi_i(P)}{\partial n_p} = c(P) \frac{\partial \phi(P)}{\partial n_p}, \quad P \in S. \tag{2.3.10}$$

There is also a DSHIE for the interior problem, and the differentiated integral equations can be written in terms of integral operators,

**Exterior:**

<a id="equation-2-3-11"></a>
$$N_k \phi = [c(p)I + M_k^T] \frac{\partial \phi}{\partial n} - \frac{\partial \phi_i}{\partial n}, \tag{2.3.11}$$

**Interior:**

<a id="equation-2-3-12"></a>
$$N_k \phi = \left[-(1 - c(p))I + M_k^T\right] \frac{\partial \phi}{\partial n}. \tag{2.3.12}$$

---

<a id="figure-2-2"></a>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/figure-2-2-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/figure-2-2.png">
  <img alt="Figure 2.2. Geometry for deriving the surface Helmholtz' integral equations." src="assets/figure-2-2.png">
</picture>
Figure 2.2. Geometry for deriving the surface Helmholtz' integral equations.