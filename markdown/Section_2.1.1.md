### 2.1.1 Linear Approximation <a id="section-2-1-1"></a>

In a fundamental analysis [Pierce (1989)](#bib-pierce-1989) of the acoustic pressure field, the linear wave equation is developed from a consideration of mass and energy conservation. This analysis assumes that the acoustic pressure field is a small amplitude perturbation to the ambient state, characterized by those values that pressure, density, and fluid velocity have when the perturbation is absent. The fluid or acoustic medium is assumed to be homogeneous and quiescent; i.e., the ambient quantities are assumed to be independent of position and time with the ambient fluid velocity equal to zero.

Consider a body of fluid in a volume $V$, with density $\rho$, surrounded by a surface $S$. The fluid velocity at a point $P$ is given by $v(P)$ and the outward normal to the surface $S$ is defined by $\mathbf{n}$. Conservation of mass requires that the net mass leaving $V$ per unit time is equal to the rate at which mass decreases in $V$. This is expressed by the relationship,

$$- \frac{d}{dt} \int_V \rho \, dV = \int_S \rho v \cdot \mathbf{n} \, dS. \tag{2.1.1}$$

The right-hand side of this equation can be transformed to a volume integral by means of Gauss' theorem and Euler's differential equation for conservation of mass is obtained,

$$\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho v) = 0. \tag{2.1.2}$$

The pressure field at a point $P$ is given by $p(P)$. By considering the forces acting on the fluid, and neglecting body forces and viscosity, the fluid velocity and pressure are related by,

$$\rho \left( \frac{\partial v}{\partial t} + (v \cdot \nabla)v \right) = -\nabla p. \tag{2.1.3}$$

This equation represents an example of Reynolds' transport theorem.

The relationship between the pressure field and density in the fluid is obtained by making the assumption that the acoustic radiation is adiabatic in the linear approximation. Consequently, it is possible to write,

$$\frac{\partial p}{\partial t} = c^2 \frac{\partial \rho}{\partial t}, \quad c^2 = \left( \frac{\partial p}{\partial \rho} \right)_s. \tag{2.1.4}$$

The real constant $c$ is referred to as the speed of sound in the particular fluid medium and the subscript $s$ in Eq. (2.1.4) indicates that the differential is evaluated at constant entropy.

Writing the pressure, density, and velocity as small perturbations of the ambient state,

$$p = p_0 + p', \quad \rho = \rho_0 + \rho', \quad v = v'. \tag{2.1.5}$$

The linear differential equations governing these perturbations are defined as,

$$\frac{\partial p'}{\partial t} + c^2 \rho_0 \nabla \cdot v' = 0, \tag{2.1.6}$$

$$\nabla p' + \rho_0 \frac{\partial v'}{\partial t} = 0. \tag{2.1.7}$$