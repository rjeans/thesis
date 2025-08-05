### 2.3.2 Differentiated Surface Helmholtz’ Integral Equation <a id="section-2-3-2"></a>

The SHIE taken on the boundary surface may be differentiated with respect to the normal at $P$ to obtain the Differentiated surface Helmholtz' integral equation (DSHIE),

$$\int_{S} \left( \phi(q) \frac{\partial^2 G_k(P,q)}{\partial n_p \partial n_q} - \frac{\partial \phi(q)}{\partial n_q} \frac{\partial G_k(P,q)}{\partial n_p} \right) dS_q + \frac{\partial \phi_i(P)}{\partial n_p} = c(P) \frac{\partial \phi(P)}{\partial n_p}, \quad P \in S. \tag{2.3.10}$$

There is also a DSHIE for the interior problem and the differentiated integral equations can be written in terms of integral operators,

**Exterior:**

$$N_k \phi = [c(p)I + M_k^T] \frac{\partial \phi}{\partial n} - \frac{\partial \phi_i}{\partial n}, \tag{2.3.11}$$

**Interior:**

$$N_k \phi = [- (1 - c(p))I + M_k^T] \frac{\partial \phi}{\partial n}. \tag{2.3.12}$$