### 2.1.4 Sommerfeld’s radiation condition <a id="section-2-1-4"></a>

For unbounded acoustic problems the pressure field must obey some boundary condition in the far field. This boundary condition is given by Sommerfeld’s radiation condition. This is defined by,

$$\lim_{{r \to \infty}} \int_S \left( \frac{{\partial \dot{p}}}{{\partial r}} - ik\dot{p} \right)^2 dS = 0 \tag{2.1.13}$$

The consequence of this condition is that it allows outward traveling waves to be the only valid physical solution for a radiated or scattered wave from a surface.

Eq. (2.1.10), Eq. (2.1.11) and Eq. (2.1.13) uniquely define the acoustic problem. For some simple geometries, it is possible to solve the acoustic problem analytically, however for the majority of realistic problems a numerical solution technique is needed. Analytical solutions for certain problems are useful in establishing the accuracy of various numerical strategies used to solve the acoustic problem.

At this stage, the concept of a velocity potential function will be defined. This function enables the fluid velocity and pressure fields to be evaluated from one potential function. The function is defined by, $\nabla^2 \phi + k^2 \phi = 0, \tag{2.1.14}$ with,

$$\mathbf{u} = \nabla \phi, \quad \dot{p} = i \omega \rho \phi. \tag{2.1.15}$$