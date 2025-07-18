
# CHAPTER 2.  Acoustic Problem

## 2.1 Fundamental Equations

The analysis of any acoustic problem involves the solution of a differential equation relating fluid variables in the medium of interest, subject to certain boundary conditions. This work is primarily concerned with the interaction of acoustic radiation with submerged structures and the appropriate differential equation is the linear wave equation subject to a velocity boundary condition on the submerged structure.

### 2.1.1 Linear Approximation

In a fundamental analysis (Pierce [1989]) of the acoustic pressure field, the linear wave equation is developed from a consideration of mass and energy conservation. This analysis assumes that the acoustic pressure field is a small amplitude perturbation to the ambient state, characterized by those values that pressure, density and fluid velocity have when the perturbation is absent. The fluid or acoustic medium is assumed to be homogeneous and quiescent; ie the ambient quantities are assumed to be in...

Consider a body of fluid in a volume $V$, with density $\rho$, surrounded by a surface $S$. The fluid velocity at a point $P$ is given by $\mathbf{v}(P)$ and the outward normal to the surface $S$ is defined by $\mathbf{n}$. Conservation of mass requires that the net mass leaving $V$ per unit time is equal to the rate at which mass decreases in $V$. This is expressed by the relationship:

$$\frac{d}{dt} \int_V \rho dV = - \int_S \rho \mathbf{v} \cdot \mathbf{n} \, dS \quad \tag{2.1.1}$$

The right hand side of this equation can be transformed to a volume integral by means of Gauss' theorem and Euler's differential equation for conservation of mass is obtained:

$$\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{v}) = 0 \quad (2.1.2)$$

The pressure field at a point $P$ is given by $p(P)$. By considering the forces acting on the fluid, and neglecting body forces and viscosity, the fluid velocity and pressure are related by:

$$
\rho \left( \frac{\partial \mathbf{v}}{\partial t} + (\mathbf{v} \cdot \nabla) \mathbf{v} \right) = -\nabla p \quad (2.1.3)
$$

This equation represents an example of Reynolds' transport theorem.

The relationship between the pressure field and density in the fluid is obtained by making the assumption that the acoustic radiation is adiabatic in the linear approximation. Consequently it is possible to write:

$$
\frac{\partial p}{\partial t} = c^2 \frac{\partial \rho}{\partial t} \quad (2.1.4)
$$

The real constant $c$ is referred to as the speed of sound in the particular fluid medium and the subscript $s$ in Eq. (2.1.4) indicates that the differential is evaluated at constant entropy.

Writing the pressure, density and velocity as small perturbations of the ambient state,

$$
p = p_0 + p', \quad \rho = \rho_0 + \rho', \quad \mathbf{v} = \mathbf{v}'
$$

the linear differential equations governing these perturbations are defined as:

$$
\frac{\partial \rho'}{\partial t} + \rho_0 \nabla \cdot \mathbf{v}' = 0 \quad (2.1.6)
$$

$$
\rho_0 \frac{\partial \mathbf{v}'}{\partial t} = -\nabla p' \quad (2.1.7)
$$

### 2.1.2 Wave Equation

The wave equation results when $\mathbf{v}'$ is eliminated from Eq. (2.1.6) and Eq. (2.1.7). From now on the prime notation will be neglected when indicating ambient state perturbations. The wave equation is given by:

$$
\nabla^2 p = \frac{1}{c^2} \frac{\partial^2 p}{\partial t^2} \quad (2.1.8)
$$

Since the fluid velocity and pressure are given by a linear differential equation, it is possible to assume a harmonic time dependency of the form $e^{-i \omega t}$, where $\omega$ is the circular frequency of the pressure field. The time independent fluid variables are:

$$
p = \hat{p} e^{-i \omega t}, \quad \mathbf{v} = \hat{\mathbf{v}} e^{-i \omega t} \quad (2.1.9)
$$

Substituting Eq. (2.1.9) into Eq. (2.1.8) results in the expression:

$$
\nabla^2 \hat{p} + k^2 \hat{p} = 0 \quad (2.1.10)
$$

where the wave number $k = \omega / c$. This equation is known as the reduced wave equation or Helmholtz' equation.

### 2.1.3 Neumann boundary condition

The reduced wave equation is solved in terms of the Neumann boundary condition which relates the fluid velocity to the normal velocity prescribed on $S$. This boundary condition is defined by:

$$
\frac{\partial p}{\partial n} = -i \omega \rho v_n \quad (2.1.11)
$$

where:

$$
v_n = \mathbf{n} \cdot \mathbf{v}, \quad \frac{\partial p}{\partial n} = \mathbf{n} \cdot \nabla p \quad (2.1.12)
$$

This boundary condition is sufficient for the solution of Helmholtz' equation for a finite body of fluid. For unbounded fluid problems another boundary condition is needed to uniquely specify the solution to Helmholtz' equation.

### 2.1.4 Sommerfeld's radiation condition

For unbounded acoustic problems the pressure field must obey some boundary condition in the far field. This boundary condition is given by Sommerfeld's radiation condition. This is defined by:

$$
\lim_{r \to \infty} r \left( \frac{\partial p}{\partial r} - ikp \right) = 0 \quad (2.1.13)
$$

The consequence of this condition is that it allows outward travelling waves to be the only valid physical solution for a radiated or scattered wave from a surface.

...

*(This section continues with derivations of integral operators, Helmholtz integral equations, and thin shell formulations.)*
