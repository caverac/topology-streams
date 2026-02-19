---
sidebar_position: 5
---

# Scaling Persistent Homology

How to compute persistent homology on large point clouds (>50K points) — a survey of methods, tools, and tradeoffs relevant to stellar stream detection.

## The Problem

Our Gaia queries return **100K+ stars** for even the smallest coordinate boxes. Ripser's Vietoris-Rips approach builds a dense $n \times n$ distance matrix, which means:

|   Stars | Distance matrix | Feasible? |
| ------: | --------------: | --------- |
|   5,000 |         ~200 MB | Yes       |
|  10,000 |         ~800 MB | Yes       |
|  50,000 |          ~20 GB | Barely    |
| 100,000 |          ~95 GB | No        |

Direct Rips PH in 5D on 50K+ points is **infeasible with current tools**, even with GPU acceleration. We need alternatives.

## Approaches That Scale

### 1. Subsampling + Rips

Compute PH on multiple random subsamples of 1K–5K points, then average the persistence landscapes.

**Key reference**: Chazal & Divol, "Subsampling Methods for Persistent Homology" (ICML 2015). Applied to approximate persistence diagrams of point clouds with 400K+ points.

**Tradeoffs**:

- Simple to implement, no new dependencies
- Risk of missing sparse structures (like streams) that may be underrepresented in random subsamples
- Multiple runs needed for statistical stability

### 2. Sparse Rips Filtration

Construct an $O(n)$-size filtered simplicial complex that approximates the Vietoris-Rips filtration, computed in $O(n \log n)$ time.

**Key reference**: Cavanna, Jahanseir & Sheehy (2015), "A Geometric Perspective on Sparse Filtrations."

**Implementations**: GUDHI (`SparseRipsComplex`), Sparips.jl (Julia).

**Tradeoffs**:

- Approximation quality depends on the doubling dimension of the metric space
- Significant speedup for well-behaved data; less predictable for noisy astronomical data

### 3. Density Field on Grid + Cubical Persistence

The **standard approach in cosmology** for TDA at scale:

1. Estimate a density field from the point cloud
2. Evaluate on a regular grid
3. Run **superlevel or sublevel set filtration** on the grid
4. Compute cubical persistent homology

Memory depends on **grid resolution**, not point count. A $256^3$ grid is ~16M cells — tractable regardless of whether the input has 100K or 10M points.

**Software**: GUDHI `CubicalComplex`, Cubical Ripser, Giotto-tda `CubicalPersistence` (all support parallelism via `n_jobs`).

**Tradeoffs**:

- Grid cells scale as $N^d$ — a 5D grid of $100^5 = 10$ billion cells is **infeasible**
- Practical only in 2D or 3D, which means **projecting** from 5D phase space to lower-dimensional subspaces
- Introduces discretization artifacts (grid-aligned features)
- Density estimation step introduces its own biases and parameters

### 4. Landmark-Based Methods

#### Witness Complex

Select a small set of **landmark points** (via maxmin or random selection). Build a simplicial complex where the full dataset "witnesses" simplices among landmarks.

#### Flood Complex (NeurIPS 2025)

Pellizzoni et al., "The Flood Complex: Large-Scale Persistent Homology on Millions of Points."

- Computes PH up to dimension 2 on **several million points** in 3D
- Takes a Delaunay triangulation of a small landmark subset, includes only simplices "flooded" by the union of balls centered on the full point cloud
- 1–2 orders of magnitude faster than Alpha complex PH
- GPU-parallelizable
- Code: [flooder](https://plus-rkwitt.github.io/flooder/)

**Limitation**: Currently demonstrated in 3D only.

### 5. GPU-Accelerated Rips

**Ripser++** (Zhang et al., SoCG 2020): Up to 30x speedup over Ripser, 2x CPU memory efficiency. Extracts "apparent pairs" (up to 99% of persistence pairs) on GPU.

Still limited by the fundamental $O(n^2)$ distance matrix — helps with compute time, not memory for very large $n$.

## Parallelization Options

| Tool               | Method               | Parallelism                     | Notes                                       |
| ------------------ | -------------------- | ------------------------------- | ------------------------------------------- |
| **Ripser++**       | Rips (GPU)           | GPU apparent pairs + clearing   | 30x speedup; same memory constraint         |
| **GUDHI**          | Sparse Rips, Cubical | Multi-threaded matrix reduction | `n_jobs` for cubical; sparse Rips is $O(n)$ |
| **Giotto-tda**     | Cubical              | joblib (`n_jobs=-1`)            | GUDHI C++ backend                           |
| **Cubical Ripser** | Cubical              | Single-threaded but fast        | Fastest cubical PH implementation           |
| **Flood Complex**  | Landmark + Delaunay  | GPU-amenable                    | Millions of points in 3D                    |
| **PixHomology**    | Distributed H0       | Apache Spark                    | For large batches of images                 |

## Density Estimation in High Dimensions

If we go the density field route, we need to estimate density from a 5D point cloud. This is non-trivial.

### KDE (Kernel Density Estimation)

Suffers from the **curse of dimensionality**. Optimal bandwidth scales as $h \sim n^{-1/(d+4)}$, which for $d = 5$ gives $h \sim n^{-1/9}$ — very slow convergence. You need exponentially more data to achieve the same quality as dimensions increase.

**Bandwidth selection**:

- **Scott's Rule**: $h_i = \left(\frac{4}{d+2}\right)^{1/(d+4)} n^{-1/(d+4)} \sigma_i$ — fast but assumes Gaussian-like distributions
- **Silverman's Rule**: Similar constant factor
- **Adaptive KDE (MBE)**: Varies bandwidth locally based on density — critical for astronomical data where density varies by orders of magnitude

**Verdict**: Problematic in 5D. Produces oversmoothed estimates unless you have enormous sample sizes.

### kNN Density Estimation

Density at each point estimated from the volume of the sphere containing its $k$ nearest neighbors:

$$\hat{\rho}(x) \sim \frac{k}{V_d \cdot r_k^d}$$

where $r_k$ is the distance to the $k$-th neighbor and $V_d$ is the $d$-dimensional unit ball volume.

**Advantages in high dimensions**:

- $k$ is **dimension-independent** (unlike KDE bandwidth which must be tuned per dimension)
- Truncated kNN estimators are **minimax rate optimal** while KDE is not (Zhao & Lai, 2020)
- Efficient with kd-trees: $O(n \log n)$
- No smoothing kernel to choose

**Disadvantages**: Heavy-tailed estimates, non-smooth, only asymptotically correct.

**Verdict**: Best general-purpose option for 5D. No bandwidth parameters, scales well, and is standard in astronomy.

### DTFE (Delaunay Tessellation Field Estimator)

The **standard tool in computational cosmology** for density field reconstruction from particle data.

Constructs a Delaunay tessellation; density at each vertex is proportional to the inverse volume of surrounding simplices. Produces a continuous, volume-covering field with adaptive resolution.

**Key references**:

- Cautun & van de Weygaert (2011), [arXiv:1105.0370](https://arxiv.org/abs/1105.0370)
- Software: [DTFE](https://github.com/MariusCautun/DTFE) (C++, CGAL, OpenMP)

**Limitation**: Works in **2D and 3D only**. Delaunay tessellation in 5D is computationally prohibitive — the number of simplices grows factorially with dimension.

### Voronoi-Based Density Estimation

Classic approach: density $\propto 1/\text{Voronoi cell volume}$. Does **not** scale beyond 2–3 dimensions because Voronoi cell complexity grows exponentially.

Recent alternatives that overcome this:

- **CVDE** (Polianskii et al., UAI 2022): Reformulates cell volumes as integrals over a sphere, approximated by Monte Carlo. Suitable for higher dimensions.
- **RVDE** (Marchetti et al., AISTATS 2023): Reduces the high-dimensional problem to 1D. **Computable in linear time** $O(n)$. Continuous output, avoids expensive volume computations.

**Verdict**: RVDE is promising for 5D but unproven in astronomy contexts.

### Comparison (Eardley et al. 2011)

Comparison of density estimators for astronomical datasets ranked: **MBE (adaptive KDE) $\geq$ DEDICA (adaptive Gaussian KDE) $\gg$ kNN $\sim$ DTFE** for density recovery accuracy. However, this was in 2–3D — in 5D, kNN may outperform KDE-based methods.

## What Cosmology Actually Does

The established pipeline in cosmic web analysis (Wilding, Pranav, van de Weygaert et al., MNRAS 2021):

1. **DTFE** on particle positions (3D) → continuous density field
2. **Superlevel set filtration** on the density grid
3. **Cubical PH** (GUDHI or Perseus)
4. Extract Betti curves, persistence diagrams, persistence pairs

This works because the cosmic web is inherently a 3D spatial structure. The density field captures clusters ($\beta_0$), filament loops ($\beta_1$), and voids ($\beta_2$).

**Our challenge**: Stellar streams live in **5D phase space** (position + kinematics). Projecting to 3D spatial coordinates loses the kinematic information that distinguishes stream members from field stars. This is precisely why the problem is hard.

## Practical Path Forward

Given our constraints (5D phase space, 100K+ stars, stream signatures are kinematic):

| Approach                                    | Feasibility   | Preserves 5D?             | Implementation effort     |
| ------------------------------------------- | ------------- | ------------------------- | ------------------------- |
| **Subsampling + Rips**                      | High          | Yes                       | Low — use existing ripser |
| **kNN density → 2D/3D grid → cubical PH**   | High          | Partial — loses some dims | Medium                    |
| **Sparse Rips (GUDHI)**                     | Medium        | Yes                       | Low — GUDHI API           |
| **kNN density → filtration on point cloud** | Medium        | Yes                       | Medium — DTM filtration   |
| **Ripser++ (GPU)**                          | Medium        | Yes                       | Low — drop-in replacement |
| **Flood Complex**                           | Low (3D only) | No                        | High — not yet 5D         |

The most promising directions:

1. **kNN density estimation on the full 5D space** — no curse-of-dimensionality issues, no grid, no projection. Use the density values as a filtration function directly on the point cloud (superlevel set), rather than gridding. This avoids the $N^d$ grid problem entirely.

2. **Subsampling with persistence landscape averaging** — simple, preserves full 5D geometry, statistically principled. Multiple runs on 5K-point subsamples with averaged persistence landscapes.

3. **Sparse Rips via GUDHI** — $O(n)$ complex size, preserves exact Rips topology up to approximation factor. Worth benchmarking on our data.

## References

- Chazal & Divol, "Subsampling Methods for Persistent Homology," ICML 2015
- Cavanna, Jahanseir & Sheehy, "A Geometric Perspective on Sparse Filtrations," SoCG 2015
- Pellizzoni et al., "The Flood Complex," NeurIPS 2025, [arXiv:2509.22432](https://arxiv.org/abs/2509.22432)
- Zhang et al., "Ripser++: GPU-Accelerated Computation of Vietoris-Rips Persistence Barcodes," SoCG 2020
- Wilding et al., "Persistent Homology of the Cosmic Web," MNRAS 507(2), 2021
- Pranav et al., "Topology of the Cosmic Web in Terms of Persistent Betti Numbers," MNRAS 465(4), 2017
- Cautun & van de Weygaert, "The DTFE public software," [arXiv:1105.0370](https://arxiv.org/abs/1105.0370)
- Zhao & Lai, "Analysis of kNN Density Estimation," [arXiv:2010.00438](https://arxiv.org/abs/2010.00438)
- Marchetti et al., "RVDE: Radial Voronoi Density Estimator," AISTATS 2023
- Polianskii et al., "CVDE: Compactified Voronoi Density Estimator," UAI 2022
- Eardley et al., "Comparison of Density Estimation Methods for Astronomical Datasets," A&A 2011
- Maciejewski et al., "Phase-space structures — I: 6D density estimators," MNRAS 393(3), 2009
- Feldbrugge et al., "Phase-Space DTFE," MNRAS 536(1), 2024, [arXiv:2402.16234](https://arxiv.org/abs/2402.16234)
- Heydenreich et al., "Persistent Homology in Cosmic Shear," A&A 2021
