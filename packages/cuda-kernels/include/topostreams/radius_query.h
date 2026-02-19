#ifndef TOPOSTREAMS_RADIUS_QUERY_H
#define TOPOSTREAMS_RADIUS_QUERY_H

#include "topostreams/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Find all points within a given radius of a query point.
 *
 * @param points      Row-major array of shape (n, d).
 * @param query       Query point of length d.
 * @param n           Number of data points.
 * @param d           Dimensionality.
 * @param radius      Search radius.
 * @param out_indices Output array of matching indices (pre-allocated to n).
 * @param out_count   Output number of matching points.
 * @return            TOPO_SUCCESS on success.
 */
TopoError topo_gpu_radius_query(const double* points, const double* query,
                                int n, int d, double radius,
                                int* out_indices, int* out_count);

#ifdef __cplusplus
}
#endif

#endif /* TOPOSTREAMS_RADIUS_QUERY_H */
