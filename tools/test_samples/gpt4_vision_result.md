As the boundary layer formulation are related to the SHIE and the DSHIE, this hybrid formulation is analogous to the Burton and Miller formulation described above.

## 2.5 Thin shell formulation

A prime motivation for this project was the analysis of thin shell acoustic problems. In this work a thin shell is defined as a shell for which the through shell displacement field is assumed to be constant. Acoustically this means that the normal derivative of pressure is the same on both sides of the shell.

### 2.5.1 Boundary integral formulation

The geometry of the thin shell is illustrated in figure (2.5). On such a shell three closely associated points may be defined. The points are $p$, $p^-$, and $p^+$, where $p$ represents a point midway through the thickness of the shell, $p^+$ is a point on one surface, and $p^-$ is the corresponding point on the other surface. The normal $n_p$ is defined to be in the direction from $p^-$ to $p^+$. The Green's function and the normal derivative of Green's function at these points will have the following simple relationships:

$$\begin{align*}
\frac{\partial \phi (q^+)}{\partial n_q} &= \frac{\partial \phi (q^-)}{\partial n_q}, \\
G_k(P, q^+) &= G_k(P, q), \\
\frac{\partial G_k(P, q^+)}{\partial n_{q^*}} &= \pm \frac{\partial G_k(P, q)}{\partial n_q}. \tag{2.5.1}
\end{align*}$$

![Figure 2.5. The thin shell geometry.](../../images/figure-2-5.png)