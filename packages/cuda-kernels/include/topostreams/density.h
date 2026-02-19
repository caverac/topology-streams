#ifndef TOPOSTREAMS_DENSITY_H
#define TOPOSTREAMS_DENSITY_H

#include "topostreams/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Compute density-based filtration values from kth-neighbor distances.
 *
 * filtration[i] = -1.0 / max(kth_distances[i], 1e-10)
 *
 * @param kth_distances  Array of length n with k-th neighbor distances.
 * @param n              Number of points.
 * @param out_filtration Output array of length n with filtration values.
 * @return               TOPO_SUCCESS on success.
 */
TopoError topo_gpu_density_filtration(const double* kth_distances, int n,
                                      double* out_filtration);

#ifdef __cplusplus
}
#endif

#endif /* TOPOSTREAMS_DENSITY_H */
