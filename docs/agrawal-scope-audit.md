# Agrawal: validation, source version and scope

Agrawal, Bose and Moin, *Nonequilibrium wall model for large eddy simulations of complex flows exhibiting turbulent smooth body separation*, Physical Review Fluids 9, 124603 (2024), [DOI](https://doi.org/10.1103/PhysRevFluids.9.124603), **contains coupled LES validation**.

The original coding used arXiv:2407.11390v1. A later accepted manuscript and the published article contain materially different comparisons. The corrected case discussion uses the version of record, published 20 December 2024, checked in the author's posted full text. See the [current comparison record](../data/revision/agrawal_validation.json).

Published Section V.A, Figures 6–9, compares surface pressure, skin friction, velocity and Reynolds shear stress for the speed bump. Downstream coarse/medium-grid velocity and shear-stress results improve relative to the equilibrium model while residual reference error remains. Fine-grid results are closer. Section V.C's Reynolds-number sweep must not be merged with a same-Re grid comparison; its reference does not provide a same-Re validation for every run.

Section VI contains transonic coupled validation. These cases are outside a low-Mach review's physical focus; that does not erase the validation. The compressible solver formulation alone does not determine the speed-bump flow's Mach regime. No case-specific Mach number is invented in the correction. Calibration independence is assessed separately from both physical scope and existence of validation.

The former two speed-bump pressure aggregates overlapped. The diagnostic recoding splits comparisons by quantity and setting and removes that duplicate unit. Comparison rows are not independent simulations.

The earlier 82-study sensitivity included unknown-scope rows only within a preselected cohort, omitting two wholly uncertain studies and four disputed statuses. The subsequent 84-study diagnostic still did not resolve wider eligibility inconsistencies. All of these calculations are historical diagnostics, not the current paper's denominator or a claim that fewer than half of papers validate their models.

The current manuscript withdraws the aggregate headlines and uses this case to explain why source version, review scope, validation and transfer must be recorded separately.
