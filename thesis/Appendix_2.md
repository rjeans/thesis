# APPENDIX 2 Analytical Solutions <a id="section-a2"></a>

# Rigid Sphere <a id="section-a2.1"></a>

Throughout this study, the spherical radiator is used to validate the acoustic numerical methods since an analytical solution for the spherical problem is easily available. These results are covered in great depth by [Junger and Feit [1986]](#bib-junger-feit-1986), and they are summarized in this appendix.

The SHIE for the exterior problem is given by,

$$p(r) = \int_S \left( p(r_0) \frac{\partial G_k(r, r_0)}{\partial n_{r_0}} - \omega^2 \rho w G_k(r, r_0) \right) dS_{r_0} \quad r \in E$$

*(A2.1.1)*

where $w$ is the radial displacement. If the coordinate system of the problem allows variable separation of the Green's free space function, then an analytical solution is available. In spherical polar coordinates, the Green's free space function can be written in terms of **spherical Bessel functions and Legendre polynomials**,

$$
G_k(r, \theta, \phi | r_0, \theta_0, \phi_0) = -\frac{ik}{4\pi} \sum_{n=0}^{\infty} \sum_{m=-n}^{n} \frac{(n-m)!}{(n+m)!} (2n + 1) \cos m(\phi - \phi_0) P_n^m(\cos \theta) P_n^m(\cos \theta_0) j_n(kr_0) h_n(kr), \quad r \geq r_0. \tag{A2.1.2}
$$

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

# Asymptotic Solutions <a id="section-a2.2"></a>

The frequency dependence of the far field scattered pressure for an arbitrary geometry can be approximated by asymptotic solutions. Consider Eq. $A2.1.17$ in the far field,

$$p_s^{'}(R, \theta) = \frac{i p_i e^{ikR}}{kR} \sum_{n=0}^{\infty} (2n + 1) P_n(\cos \theta) \frac{j_n^{'}(kr)}{h_n^{(1)}(ka)}, \quad kR \gg n^2 + 1. \tag{A2.2.1}$$

At low frequencies the first two terms of this series expansion are $O((ka)^2)$ and the $n = 2$ term is only $O((ka)^5)$. Taking the first two terms gives the far field pressure at low frequencies,

$$p_s^{'}(R, \theta) = \frac{P_i e^{ikR}}{3R} k^2 a^3 \left( \frac{3}{2} \cos^2 \theta - 1 \right), \quad k^3 a^3 \ll 1, \quad kR \gg 1. \tag{A2.2.2}$$

The commensurate influence of monopole and dipole radiation in the far field, and the consequent $k^2$ dependence of the radiation amplitude is typical of Rayleigh Scatterers. A more general consideration of such scatterers shows that at low frequencies the far field pressure amplitude has the form,

$$p_s^{'} \propto \frac{k^2 V}{R}, \quad k^3 L^3 \ll 1, \quad kR \gg 1. \tag{A2.2.3}$$

where $V$ is the volume and $L$ is the characteristic dimension of the scatterer.

In the high frequency regime an approximation due to Kirchoff is appropriate. In this plane wave approximation it is assumed that each surface element radiates as if it were in an plane baffle,

$$dp_s^{'}(R) = \frac{p_i u^{2}(r_o) e^{2 \pi i (k |R - r_o|)}}{2 \pi R} dS, \quad k r_o \gg 1. \tag{A2.2.4}$$

The far field back scattered pressure is given by integrating Eq. $A2.2.4$ over the illuminated surface of the scatterer,

$$p_s^{'}(R) = -\frac{i P_i k}{2 \pi R} \int_{S_o} \mathbf{n} \cdot \mathbf{e_z} \exp(2ik|R - r_o|) dS, \quad k r_o \gg 1. \tag{A2.2.5}$$

In Eq. $A2.2.5$ the plane wave is incident along the direction of $\mathbf{e_z}$. Consider now the case of a spheroid shown in [Figure A2.1](#figure-a2-1). For end on incidence the problem is axysymmetric and so the cylindrical coordinate system, $(\eta, \phi, Z)$ is appropriate to form the Kirchoff integral. In this coordinate system, Eq. $A2.2.5$ becomes,

$$\left| \frac{p_s^{'}(R) R}{P_i} \right| = k \left| \int_{S_o} n_z \xi (Z) d \Gamma \right|, \quad kL \gg 1, \tag{A2.2.6}$$

where,

$$d \Gamma = \left( 1 + \left( \frac{\partial \eta}{\partial Z} \right)^2 \right)^{\frac{1}{2}} dZ, \tag{A2.2.7}$$

$$n_z = \frac{\partial \eta}{\partial Z} \left( 1 + \left( \frac{\partial \eta}{\partial Z} \right)^2 \right)^{-\frac{1}{2}}, \tag{A2.2.8}$$

$$\xi (Z) = 2ikZ. \tag{A2.2.9}$$

Eq. $A2.2.6$ now becomes,

$$\left| \frac{p_s^{'}(R) R}{P_i} \right| = k \left| \int_{S_o} \frac{\partial \eta}{\partial Z} e^{2ikZ} dZ \right|, \quad kL \gg 1, \tag{A2.2.10}$$

where for the spheroid,

$$\left| \frac{p_s^{'}(R) R}{P_i} \right| = \frac{k a^2}{b^2} \left| \int_{-b}^{0} Z e^{2ikZ} dZ \right|, \quad kb \gg 1. \tag{A2.2.11}$$

<a id="figure-a2-1"></a>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/figure-a2-1-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/figure-a2-1.png">
  <img alt="Figure A2.1. Geometry for the spheroidal Kirchoff problem." src="assets/figure-a2-1.png">
</picture>
Figure A2.1. Geometry for the spheroidal Kirchoff problem.

The integral in Eq. $A2.2.11$ can be done in parts, and neglecting the terms of $O((kb)^{-1})$ or higher the high frequency far field back scattering amplitude is given by,

$$\left| \frac{p_s^{'}(R) R}{P_i} \right| = \frac{a^2}{2b}, \quad kb \gg 1. \tag{A2.2.12}$$

This is the result used in Chapter 4, and for the special case of the sphere, with $b = a$, it reduces to the spherical result used in Chapter 3. If higher frequency terms are included an interference pattern is introduced into the farfield result. This interference corresponds to a path difference of $2b$; ie the path difference between a specular wave at $Z = -b$ and one at $Z = 0$. The numerical results contained in this thesis show such an interference pattern, however the period of the fluctuations are much less than those predicted by the Kirchoff approximation. The accepted explanation for the interference pattern (e.g. Varadan et al. [1982]) is that they are a result of the interference between the specular reflection at $Z = -b$ and a Franz or creeping wave originating at the circular cross section at $b = 0$. The predicted period of the interference is given by,

$$\Delta (kb) = \frac{2\pi}{D + 2}. \tag{A2.2.13}$$

where $D$ is one half the perimeter of the spheroid in the $X = 0$ plane. For the various aspect ratios used in this study this period is,

$$\begin{align*} \text{a/b} = 0.5, & \quad \Delta(kb) = 1.42, \quad \Delta(ka) = 0.71, \\ \text{a/b} = 1, & \quad \Delta(kb) = 1.22, \quad \Delta(ka) = 1.22, \\ \text{a/b} = 2, & \quad \Delta(kb) = 2.84, \quad \Delta(ka) = 1.42. \end{align*} \tag{A2.2.14}$$

# Elastic Sphere <a id="section-a2.3"></a>

For axisymmetric boundary conditions, there is a readily accessible analytical solution for the dynamic elastic response of the spherical elastic shell. This solution is described in greater depth in many standard texts and is summarized in this appendix. Membrane and flexural effects are included in the analytical model which can be derived from Hamilton's variational principle. Many of the thin shell approximations used for the finite element derivation are used for the analytical result; i.e., the deformation can be described in terms of the mid-shell displacements and the mid-shell normal remains straight after deformation.

Axisymmetric, nontortional motions are considered, and the shell displacements can be described in terms of the tangential and radial components: $u_r$ and $u_\theta$. A free dynamic analysis of the shell results in an expression for the dimensionless natural frequencies, $(\Omega^{(1)})^2$ and $(\Omega^{(2)})^2$, which are roots of a quadratic in $\Omega^2$,

$$\Omega^4 - [1 + 3\nu + \lambda_n - \beta^2(1 - \nu - \lambda_n^2 - \nu \lambda_n )] \Omega^2 + (\lambda_n - 2)(1 - \nu^2) + \beta^2 [\lambda_n^3 - 4\lambda_n^2 + \lambda_n (5 - \nu^2) - 2(1 - \nu^2)] = 0, \tag{A2.3.1}$$

where,

$$\Omega = \frac{\omega a}{c_p}, \quad \beta^2 = \frac{h^2}{12a^2}, \quad \lambda_n = n(n+1). \tag{A2.3.2}$$

The radial or normal and the tangential displacements can be expanded in terms of Legendre polynomials, $u_r = \sum_{n=0}^{\infty} W_n P_n(\mu),$ $$u_\theta = \sum_{n=0}^{\infty} V_n (1 - \mu^2)^{1/2} \frac{dP_n(\mu)}{d\mu}, \quad \mu = \cos \theta. \tag{A2.3.3}$$

For forced vibration of the spherical shell, the modal radial amplitude is related to the modal force amplitude by,

$$Z_n = -\frac{f_n}{i\omega W_n} = -\frac{i \rho_0 c_p \frac{h}{a} (\Omega^2 - (\Omega^{(1)})^2)(\Omega^2 - (\Omega^{(2)})^2)}{\Omega^2 - (1 - \beta^2)(\nu + \lambda_n - 1)}. \tag{A2.3.4}$$

where the modal excitation force is given by,

$$f_n = \left(\frac{2n + 1}{2}\right) \int_{-1}^{1} f(\mu)P_n(\mu)d\mu. \tag{A2.3.5}$$

Finally, the modal radial and tangential amplitudes are related by,

$$\frac{V_n}{W_n} = \frac{\beta^2(\nu + \lambda_n - 1) + (1 + \nu)}{\Omega^2 - (1 + \beta^2)(\nu + \lambda_n - 1)}. \tag{A2.3.6}$$

For a spherical shell vibrating in an acoustic fluid, the excitation force in Eq. (A2.3.5) consists of the applied force, $f^a$, modified by the fluid-structure interaction force, $f^i$. The modal normal velocity of the submerged spherical shell is given by,

$$Z_n W_n = f_n^a - f_n^i, \tag{A2.3.7}$$

where,

$$f_n^i = p_n^- - p_n^+ = [z_n^- - z_n^+]W_n. \tag{A2.3.8}$$

Therefore, by combining Eq. (A2.3.7) and Eq. (A2.3.8), the surface pressure and velocity fields for the excited spherical shell are given by,

$$u_n(a, \theta) = \sum_{n=0}^{\infty} \frac{f_n^a}{[z_n^+ + z_n^- - z_n^+]} P_n(\cos \theta),$$

$$p(a, \theta) = \sum_{n=0}^{\infty} \frac{z_n^+ f_n^a}{[z_n^+ + z_n^- - z_n^+]} P_n(\cos \theta). \tag{A2.3.9}$$

For the point excited spherical shell the modal excitation force is defined by,

$$f_n^a = \frac{(2n + 1) F}{4 \pi a^2}, \tag{A2.3.10}$$

and the resulting far field pressure field is,

$$p^f(R,\theta) = \frac{F p_ce^{i k R}}{4 \pi a^2 k R} \int_{n=0}^{\infty} \frac{(-i)^n (2n + 1) P_n(\cos \theta)}{(z_n^+ + z_n^- - z_n^+)} h_n^{(2)}(ka), \quad k R \gg 1. \tag{A2.3.11}$$

The case of scattering from an elastic spherical shell is more complicated. It is necessary to consider both the rigid body scattering component and the elastic radiated component. The surface pressure on the rigid body due to an incident plane wave is given in Eq. (A2.1.18) with $r = a$. This expression may be transformed by means of a Wronskian relationship to give,

$$p(a, \theta) = \frac{i^{n+1} (2n + 1) P_n(\cos \theta)}{(ka)^2 h_n^{(2)}(ka)}. \tag{A2.3.12}$$

Taking this to be the excitation force, the corresponding surface velocity distribution is arrived at by means of the modal impedances,

$$u_r = -\frac{P_i}{k^2 a^2} \sum_{n=0}^{\infty} \frac{i^{n+1} (2n + 1) P_n(\cos \theta)}{(z_n^+ + z_n^- - z_n^+)} h_n^{(2)}(ka). \tag{A2.3.13}$$

The radiated far field pressure can be obtained from Eq. (A2.1.8),

$$p^f(R,\theta) = -\frac{i p_0 e^{i k R} P_i}{k R} \sum_{n=0}^{\infty} \frac{i^{n+1} (2n + 1) P_n(\cos \theta)}{(z_n^+ + z_n^- - z_n^+)|k a h_n^{(2)}(ka)|^2}, \quad k R \gg n^2 + 1. \tag{A2.3.14}$$

The far field scattered pressure is obtained when this result is combined with the rigid-body scattered pressure distribution, Eq. (A2.2.1). This can be expressed as a form function,

$$|f(\theta)| = \left|\frac{2 p^f(R,\theta) R}{a P_i} \right| = \frac{2}{ka} \left| \sum_{n=0}^{\infty} \frac{(2n + 1) P_n(\cos \theta)}{h_n^{(2)}(ka)} \left| j_n^\prime(ka) - \frac{\rho c_p}{(ka)^2 h_n^{(2)}(ka) (z_n^+ + z_n^- - z_n^+)} \right| \right|. \tag{A2.3.15}$$

The analytical results presented in this study were calculated using FORTRAN code written by the author, J. James [1986] and T. L. Geers and C. A. Felippa [1983].

