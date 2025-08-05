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