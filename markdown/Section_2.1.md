## 2.1 Fundamental Equations <a id="section-2-1"></a>

The analysis of any acoustic problem involves the solution of a differential equation relating fluid variables in the medium of interest, subject to certain boundary conditions. This work is primarily concerned with the interaction of acoustic radiation with submerged structures and the appropriate differential equation is the linear wave equation subject to a velocity boundary condition on the submerged structure.

### 2.1.1 Linear Approximation <a id="section-2-1-1"></a>

In a fundamental analysis [Pierce (1989)](#bib-pierce-1989) of the acoustic pressure field, the linear wave equation is developed from a consideration of mass and energy conservation. This analysis assumes that the acoustic pressure field is a small amplitude perturbation to the ambient state, characterized by those values that pressure, density, and fluid velocity have when the perturbation is absent. The fluid or acoustic medium is assumed to be homogeneous and quiescent; i.e. the ambient quantities are assumed to be independent of position and time with the ambient fluid velocity equal to zero.

Consider a body of fluid in a volume $V$, with density $\rho$, surrounded by a surface $S$. The fluid velocity at a point $P$ is given by $v(P)$ and the outward normal to the surface $S$ is defined by $\mathbf{n}$. Conservation of mass requires that the net mass leaving $V$ per unit time is equal to the rate at which mass decreases in $V$. This is expressed by the relationship:

$$- \frac{d}{dt} \int_V \rho \; dV = \int_S \rho v \cdot \mathbf{n} \; dS. \tag{2.1.1}$$

The right-hand side of this equation can be transformed to a volume integral by means of Gauss' theorem and Euler's differential equation for conservation of mass is obtained:

$$\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{v}) = 0. \tag{2.1.2}$$

The pressure field at a point $P$ is given by $p(P)$. By considering the forces acting on the fluid, and neglecting body forces and viscosity, the fluid velocity and pressure are related by,