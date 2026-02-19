#ifndef TOPOSTREAMS_KNN_H
#define TOPOSTREAMS_KNN_H

#include "topostreams/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Compute k-nearest neighbors on GPU using brute-force distance computation.
 *
 * @param points   Row-major array of shape (n, d).
 * @param n        Number of points.
 * @param d        Dimensionality.
 * @param k        Number of neighbors (excluding self).
 * @param out_dist Output distances array of shape (n, k), row-major.
 * @param out_idx  Output index array of shape (n, k), row-major.
 * @return         TOPO_SUCCESS on success.
 */
TopoError topo_gpu_knn(const double* points, int n, int d, int k,
                       double* out_dist, int* out_idx);

#ifdef __cplusplus
}
#endif

#endif /* TOPOSTREAMS_KNN_H */
