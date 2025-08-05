## 2.3 Helmholtz’ Integral Equations <a id="section-2-3"></a>

2.3.1 Surface Helmholtz Integral Equation

The Surface Helmholtz’ Integral equation (SHIE) forms the basis of most boundary element methods (BEM). This equation can be derived by considering the general acoustic geometry shown in figure [2.2](#figure-2-2). A spherical surface, $S_e$ contains two closed surfaces $S_i$ and $S$. The surface $S$ represents the acoustic surface of interest and the surface $S_i$ represents the surface of some acoustic source. The domain $E$ is the volume contained by $S_e$ excluding the volume contained by $S_i$ and $S$. The domain $D$ represents the volume contained by the surface $S$. A small spherical surface $S_\epsilon$ surrounds the field point $P$.

With the surface $S_\epsilon$ excluding the singular point $P$ from the domain $E$, both the Green’s free space function and the velocity potential in $E$ satisfy the reduced wave equation and, so:

**Mathematical Content**

$$c(p) = 1 + \int_S \frac{\partial G_0(p, q)}{\partial n_q} ds_q. \tag{2.2.13}$$

Using the arguments described above, it is possible to evaluate the discontinuity properties of all the integral equations and these are summarized below,

$$L_k[\phi](p^+) = L_k[\phi](p) = L_k[\phi](p^-), \tag{2.2.14}$$

$$M_k[\phi](p^+) - (1 - c(p))\phi(p) = M_k[\phi](p^-) + c(p)\phi(p), \tag{2.2.15}$$

$$M^T_k[\phi](p^+) + (1 + c(p))\phi(p) = M^T_k[\phi](p^-) - c(p)\phi(p), \tag{2.2.16}$$

$$N_k[\phi](p^+) = N_k[\phi](p) = N_k[\phi](p^-). \tag{2.2.17}$$

It is important to realize that $M_k[\phi](p^+)$ represents the limiting value of $M_k[\phi](P)$ as $P$ tends to $p^+$, whilst $M_k[\phi](p)$ represents the principal value of the integral operation; that is the limit value of an integration over a surface $S - S_\epsilon$, as $\epsilon$ goes to zero.