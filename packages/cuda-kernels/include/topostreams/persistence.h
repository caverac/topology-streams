#ifndef TOPOSTREAMS_PERSISTENCE_H
#define TOPOSTREAMS_PERSISTENCE_H

#include "topostreams/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Compute H0 persistent homology using union-find on sorted edges.
 *
 * @param vertex_filt  Filtration values for each vertex, length n.
 * @param edge_src     Source vertex for each edge, length m.
 * @param edge_dst     Destination vertex for each edge, length m.
 * @param edge_filt    Filtration value for each edge, length m.
 * @param n            Number of vertices.
 * @param m            Number of edges.
 * @param out_births   Output birth values (at most n-1 pairs).
 * @param out_deaths   Output death values (at most n-1 pairs).
 * @param out_count    Output number of finite persistence pairs.
 * @return             TOPO_SUCCESS on success.
 */
TopoError topo_gpu_persistence_h0(const double* vertex_filt, const int* edge_src,
                                  const int* edge_dst, const double* edge_filt,
                                  int n, int m, double* out_births,
                                  double* out_deaths, int* out_count);

/**
 * Compute H1 persistent homology via boundary matrix reduction.
 *
 * @param edge_src     Source vertex for each edge, length m.
 * @param edge_dst     Destination vertex for each edge, length m.
 * @param edge_filt    Filtration value for each edge, length m.
 * @param tri_v0       First vertex of each triangle, length t.
 * @param tri_v1       Second vertex of each triangle, length t.
 * @param tri_v2       Third vertex of each triangle, length t.
 * @param tri_filt     Filtration value for each triangle, length t.
 * @param m            Number of edges.
 * @param t            Number of triangles.
 * @param out_births   Output birth values.
 * @param out_deaths   Output death values.
 * @param out_count    Output number of H1 persistence pairs.
 * @return             TOPO_SUCCESS on success.
 */
TopoError topo_gpu_persistence_h1(const int* edge_src, const int* edge_dst,
                                  const double* edge_filt,
                                  const int* tri_v0, const int* tri_v1,
                                  const int* tri_v2, const double* tri_filt,
                                  int m, int t, double* out_births,
                                  double* out_deaths, int* out_count);

#ifdef __cplusplus
}
#endif

#endif /* TOPOSTREAMS_PERSISTENCE_H */
