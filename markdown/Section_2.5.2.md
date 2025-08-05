### 2.5.2 Edge conditions <a id="section-2-5-2"></a>

When considering thin shells which do not enclose an interior volume, it is important to consider the behavior of the integral equations at the edge of this shell. It has been proposed in previous work [Warham (1988)](#bib-warham-1988) that by taking the limit of $P$ to $p$ in from $D$ and $E$, results in two equations that give a condition on $\Phi$. However, if the limits are taken correctly then,

$$\lim_{P \to p^+} M_k[\Phi](P) = \Phi^-(p) = M_k[\Phi](P) + (1 - c_+(p))(\Phi_+(p) - \Phi_-(p)), \tag{2.5.7}$$

$$\lim_{P \to p^-} M_k[\Phi](P) = \Phi^-(p) = M_k[\Phi](P) - (1 - c_-(p))(\Phi_+(p) - \Phi_-(p)), \tag{2.5.8}$$

which leads to the identity, $(c_+(p) + c_-(p) - 1) \Phi(p) = 0. \tag{2.5.9}$ This equation simply states the fact that $c_-(p) = 1 - c_+(p)$ and gives no condition on $\Phi$. A more sophisticated argument is needed to define the edge conditions for the open plate problem.

When the thickness of the plate is taken to zero, the edge around the plate becomes an additional boundary. Consequently, there needs to be a supplementary boundary condition specified on this boundary. In his recent paper, Martin [1991] discusses the behavior of one-dimensional hypersingular integral equations over finite intervals and this idea is discussed in more detail. This edge boundary condition is arbitrary in the mathematical sense, but for this case, is governed by the original physical problem. Continuity of the pressure difference across the plate means that $\Phi$ must be zero at the edge of the shell;

$$\Phi(p) = 0, \quad p \text{ on the edge}. \tag{2.5.10}$$

In past work (e.g., Pierce [1987]), this edge boundary condition has been satisfied by the choice of appropriate fluid basis functions. In most numerical work for arbitrary thin plates (e.g., Terai [1981] and Warham [1988]), the edge boundary condition is essentially ignored since there are no nodes on the edge of the plate. In the numerical work described in later chapters, the presence of nodes on the edge of the plate means that this boundary condition must be imposed upon the numerical formulation.