## 1.2 Motivation of Present Thesis <a id="section-1-2"></a>

The original motivation for this thesis was to develop and refine the current state of the art computational approaches used for the prediction of radiated sound. After three years of research, the following areas have been documented in this thesis:

(a) Development of a computationally efficient implementation of the Helmholtz' integral equations for three-dimensional structures of arbitrary geometry, including thin plate problems.
   
   i) Comparison and development of variational and collocation formulations.
   
   ii) The use of quadratic isoparametric elements.
   
   iii) Frequency interpolation of fluid matrices.

(b) Coupling of a consistent FEM formulation of the thin shell and plate structural problem to the boundary element formulations.
   
   i) Comparison of modal and Lanczos reduction of the structural formulations to improve solution efficiency.

A general review of the acoustic problem, along with the development of the various integral formulations, is given in Chapter 2. In Chapter 3, a collocation approach is presented for the numerical solution of the Burton and Miller formulation of the exterior acoustic problem. This work describes a novel approach to the hypersingular integral operator, based on the expression of the integral operator given by Maue [1949]. This approach is very similar to the work of Wu, Seybert, and Wan [1991], but without their additional regularization procedures. The resulting numerical implementation is applied to spherical, spheroidal, and cylindrical rigid radiation and scattering problems.

In Chapter 4, the variational method of Mariem and Hamdi [1987] for approximation of the hypersingular integral operator is described and numerically implemented using quadratic isoparametric boundary elements. The resulting thin shell acoustic formulation is applied to different closed and open thin shell problems and compared to the collocation formulation of the thin shell acoustic problem.

With renewed interest in superposition formulation of the acoustic problem, Chapter 5 is devoted to an examination of these methods. It was felt that these methods were not suitable for the general acoustic analysis of arbitrary structures, due to the inherent instabilities of the resulting integral expressions. Unfortunately, to support this viewpoint, a quantitative analysis of the method involved a substantial and disproportionate amount of research effort. However, the examination of the superposition method in this chapter necessitated introducing topics of matrix conditioning and accuracy of the general matrix routines that might not have been included otherwise.

The FEM is introduced in Chapter 6, and the theory behind the thin shell structural problem used in this study is outlined. The coupling procedure between the structural and acoustic problems is described, along with the various methodologies for solving the combined problem. In this chapter, eigenmode reduction of the structural problem and frequency interpolation of the fluid matrices are described. The resulting implementations are tested with the spherical shell problem for which there is an easily accessible analytical result, and results for a submerged cantilever plate are also presented. Significant work is also presented, detailing the behavior of the general elasto-acoustic problem at critical frequencies.

Chapter 7 introduces the theory of Lanczos vectors and describes their usefulness in coupled elasto-acoustic formulations. The resulting implementations are again applied to the spherical test case and compared to corresponding eigenvector reduction techniques. A fluid added mass formulation is described using the variational formulation of the thin shell acoustic problem, and the resulting symmetric structural equation is reduced using Lanczos vectors.

The final chapter is a summary of the thesis. Conclusions are made about the consequences and effectiveness of the presented results and finally proposals for future work are presented.

In Appendix I, the application of acoustic and geometric symmetry, applied to the acoustic boundary element problem is reviewed. Such use of symmetry is of considerable interest not only for the reduction of problem size but for the treatment of half space problems. Summarized in Appendix II are the analytical techniques applied to the spherical elasto-acoustic problem.