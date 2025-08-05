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