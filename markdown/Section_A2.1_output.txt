# Rigid Sphere <a id="section-a2.1"></a>

Throughout this study, the spherical radiator is used to validate the acoustic numerical methods since an analytical solution for the spherical problem is easily available. These results are covered in great depth by [Junger and Feit [1986]](#bib-junger-feit-1986), and they are summarized in this appendix.

The SHIE for the exterior problem is given by,

$$p(r) = \int_S \left( p(r_0) \frac{\partial G_k(r, r_0)}{\partial n_{r_0}} - \omega^2 \rho w G_k(r, r_0) \right) dS_{r_0}, \quad r \in E, \tag{A2.1.1}$$

where $w$ is the radial displacement. If the coordinate system of the problem allows variable separation of the Green's free space function, then an analytical solution is available. In spherical polar coordinates, the Green's free space function can be written in terms of **spherical Bessel functions and Legendre polynomials**,

$$G_k(r, \theta, \phi | r_0, \theta_0, \phi_0) = -\frac{ik}{4\pi} \sum_{n=0}^{\infty} \sum_{m=-n}^{n} \frac{(n-m)!}{(n+m)!} (2n + 1) \cos m(\phi - \phi_0) P_n^m(\cos \theta) P_n^m(\cos \theta_0) j_n(kr_0) h_n(kr), \quad r \geq r_0. \tag{A2.1.2}$$

The coordinate system $(r, \theta, \phi)$ describes the exterior domain and $(r_0, \theta_0, \phi_0)$ describes the surface of the sphere. For coordinate systems where an analytical solution exists, the Green's function in [Eq. (A2.1.1)](#equation-a2.1.1) can be written as,

$$g(r, r_0) = G_k(r, r_0) + \Gamma(r, r_0), \tag{A2.1.3}$$

where $\Gamma$ is a solution to the homogeneous Helmholtz' equation and the normal derivative of $\Gamma$ cancels the normal derivative of $G_k$ on $S$. Consequently, [Eq. (A2.1.1)](#equation-a2.1.1) can be rewritten as,

$$p(r) = -\omega^2 \rho \int_S w g(r, r_0) dS_{r_0}, \quad r \geq r_0. \tag{A2.1.4}$$

Taking the general case of $r_0 = a$, the correct expression for $g(r, r_0)$, satisfying the homogeneous Neumann boundary condition and the radiation condition, is given by,

$$g(r, \theta, \phi | a, \theta_0, \phi_0) = \frac{1}{4\pi ka^2} \sum_{n=0}^{\infty} \sum_{m=-n}^{n} \frac{(n-m)!}{(n+m)!} (2n + 1) \cos m(\phi - \phi_0) P_n^m(\cos \theta) P_n^m(\cos \theta_0) \frac{h_n(kr)}{h_n'(ka)}, \quad r \geq a. \tag{A2.1.5}$$

The exterior pressure field given in [Eq. (A2.1.4)](#equation-a2.1.4) can now be written in terms of this modified Green's function,

$$p(r, \theta, \phi) = -\frac{\omega^2 \rho}{4\pi k} \sum_{n=0}^{\infty} \sum_{m=-n}^{n} \frac{(n-m)!}{(n+m)!} (2n + 1) \frac{h_n(kr)}{h_n'(ka)} \int_0^{2\pi} \int_0^\pi \cos m(\phi - \phi_0) P_n^m(\cos \theta) P_n^m(\cos \theta_0) \sin \theta_0 d\theta_0 d\phi_0, \quad r \geq a. \tag{A2.1.6}$$

The radial displacement in [Eq. (A2.1.6)](#equation-a2.1.6) can also be written as a summation of modal displacements,

$$w = \sum_{n'=0}^{\infty} \sum_{m'=-n'}^{n'} W_{n'm'} P_{n'}^{m'}(\cos \theta_0) \cos m'\phi. \tag{A2.1.7}$$

When the modal expansion of $w$ is substituted into [Eq. (A2.1.7)](#equation-a2.1.7), the orthogonality of the functions simplifies the expression for the exterior pressure field,

$$p(r, \theta, \phi) = -\frac{\omega^2 \rho}{k} \sum_{n=0}^{\infty} \sum_{m=-n}^{n} W_{nm} P_n^m(\cos \theta) \cos m\phi \frac{h_n(kr)}{h_n'(ka)}, \quad r \geq a. \tag{A2.1.8}$$

where,

$$W_{nm} = \frac{1}{4\pi} \frac{(n-m)!}{(n+m)!} (2n + 1) \int_0^{2\pi} \int_0^\pi P_n^m(\cos \theta_0) \cos m\phi_0 \, w(a, \theta_0, \phi_0) \sin \theta_0 d\theta_0 d\phi_0. \tag{A2.1.9}$$

The pressure on the surface of the sphere can be expressed in terms of the modal impedance,

$$p^+(a, \theta, \phi) = \sum_{n=0}^{\infty} \sum_{m=-n}^{n} z_n^+ W_{nm} P_n^m(\cos \theta) \cos m\phi, \tag{A2.1.10}$$

with,

$$z_n^+ = i \rho c \frac{h_n(ka)}{h_n'(ka)}. \tag{A2.1.11}$$

The acoustic problem interior to the spherical shell can be analyzed in a similar way. The modified Green’s function in [Eq. (A2.1.5)](#equation-a2.1.5) must be constructed so that it satisfies the homogeneous Neumann boundary condition and be finite as $r \to 0$. The corresponding surface pressure on the interior surface is,

$$p^-(a, \theta, \phi) = \sum_{n=0}^{\infty} \sum_{m=-n}^{n} z_n^- W_{nm} P_n^m(\cos \theta) \cos m\phi, \tag{A2.1.12}$$

with,

$$z_n^- = i \rho c \frac{j_n(ka)}{j_n'(ka)}. \tag{A2.1.13}$$

A comparison of [Eq. (A2.1.11)](#equation-a2.1.11) and [Eq. (A2.1.13)](#equation-a2.1.13) shows that whilst the exterior pressure distribution is composed of a superposition of traveling waves, the interior pressure distribution is a superposition of standing waves. The eigenvalues of the interior spherical problem correspond to the solutions to,

$$z_n^-(k_D) = 0,$$ $\frac{1}{z_n^-(k_N)} = 0. \tag{A2.1.14}$ The interior eigenvalues for the spherical problem are tabulated in [Table A2.1](#table-a2-1) and the frequency dependence of $j_n$ and $j_n'$ is shown in [Figure A2.1](#figure-a2-1).

<a id="figure-a2-1"></a>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/figure-a2-1-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/figure-a2-1.png">
  <img alt="Figure A2.1. Plot of the first four spherical Bessel's functions and the derivatives." src="assets/figure-a2-1.png">
</picture>
**Figure A2.1**: Plot of the first four spherical Bessel's functions and the derivatives.

<a id="table-a2-1"></a>

| Dirichlet eigenvalues $k_D$ where $j_n((k_D)) = 0$. |
|-----------------------------------------------------|
| $n=0$ | $n=1$ | $n=2$ | $n=3$ | $n=4$ | $n=5$ | $n=6$ |
|-------|-------|-------|-------|-------|-------|-------|
| 1 | 3.141593 | 4.493409 | 5.763459 | 6.987932 | 8.182561 | 9.355812 | 10.512835 |
| 2 | 6.283185 | 7.725252 | 9.095011 | 10.417119 | 11.704907 | 12.966530 | 14.207392 |
| 3 | 9.424778 | 10.904122 | 12.322941 | 13.698023 | 15.039665 | 16.354710 | 17.647975 |
| 4 | 12.566371 | 14.066194 | 15.514603 | 16.923621 | 18.301256 | 19.653152 | 20.983463 |

**Table A2.1**: The resonant frequencies for the interior spherical Dirichlet and Neumann acoustic problems.

For any prescribed velocity distribution on the surface of the sphere, the surface pressure distribution may be calculated using [Eq. (A2.1.10)](#equation-a2.1.10). For scattering from rigid spheres, the surface velocity must be equal to zero. Therefore, the fluid particle velocity of the incident wave must cancel that of the scattered wave. From the uniqueness of the external acoustic problem, the scattered pressure field is obtained by solving the Helmholtz' reduced wave equation with the virtual acceleration boundary condition,

$$\dot{w_s} = -\dot{w_i} = \frac{1}{\rho} \frac{\partial p_i}{\partial r}, \quad \text{on } S. \tag{A2.1.15}$$

An incident plane wave can be expanded in terms of spherical harmonics by using an addition theorem,

$$p_i(r, \theta) = P_i \sum_{n=0}^{\infty} (2n + 1) i^n P_n(\cos \theta) j_n(kr). \tag{A2.1.16}$$

Substituting [Eq. (A2.1.16)](#equation-a2.1.16) into [Eq. (A2.1.15)](#equation-a2.1.15), [Eq. (A2.1.8)](#equation-a2.1.8) gives an expression for the axisymmetric scattered pressure field,

$$p_s(r, \theta) = -P_i \sum_{n=0}^{\infty} (2n + 1) i^n P_n(\cos \theta) \frac{j_n(kr)}{j_n'(ka)}. \tag{A2.1.17}$$

The external pressure distribution is given by,

$$p(r, \theta) = p_s + p_i = P_i \sum_{n=0}^{\infty} (2n + 1) i^n P_n(\cos \theta) \left[ j_n(kr) - \frac{h_n(kr)}{h_n(ka)} j_n'(kr) \right]. \tag{A2.1.18}$$