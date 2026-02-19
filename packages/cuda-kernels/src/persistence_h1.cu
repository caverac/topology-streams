#include <cstdlib>
#include <cstring>
#include <cuda_runtime.h>

#include "topostreams/persistence.h"

/**
 * H1 persistence via boundary matrix column reduction.
 *
 * Strategy (sequential-on-GPU, can be optimized with "apparent pairs" later):
 * 1. Sort triangles by filtration.
 * 2. Build boundary matrix (each triangle's boundary = 3 edges).
 * 3. Reduce boundary matrix using left-to-right column reduction.
 * 4. Paired columns give (birth, death) pairs for H1.
 *
 * Current implementation runs on CPU due to the inherently sequential nature
 * of standard column reduction. GPU acceleration via apparent pairs or
 * chunk-parallel reduction can be added as a future optimization.
 */

struct TriSortKey {
    double filt;
    int v0, v1, v2;
    int original_idx;
};

struct EdgeInfo {
    int src, dst;
    double filt;
    int sorted_idx;
};

static int tri_compare(const void* a, const void* b) {
    double fa = ((const TriSortKey*)a)->filt;
    double fb = ((const TriSortKey*)b)->filt;
    if (fa < fb) return -1;
    if (fa > fb) return 1;
    return 0;
}

static int edge_info_compare(const void* a, const void* b) {
    double fa = ((const EdgeInfo*)a)->filt;
    double fb = ((const EdgeInfo*)b)->filt;
    if (fa < fb) return -1;
    if (fa > fb) return 1;
    return 0;
}

// Find edge index for a pair (u, v) where u < v
static int find_edge(const EdgeInfo* sorted_edges, int m, int u, int v) {
    if (u > v) { int t = u; u = v; v = t; }
    for (int i = 0; i < m; i++) {
        int su = sorted_edges[i].src;
        int sv = sorted_edges[i].dst;
        if (su > sv) { int t = su; su = sv; sv = t; }
        if (su == u && sv == v) return i;
    }
    return -1;
}

extern "C" TopoError topo_gpu_persistence_h1(
    const int* edge_src, const int* edge_dst, const double* edge_filt,
    const int* tri_v0, const int* tri_v1, const int* tri_v2,
    const double* tri_filt, int m, int t,
    double* out_births, double* out_deaths, int* out_count)
{
    if (!out_births || !out_deaths || !out_count) return TOPO_ERROR_INVALID_ARGUMENT;
    *out_count = 0;

    if (t == 0 || m == 0) return TOPO_SUCCESS;
    if (!edge_src || !edge_dst || !edge_filt) return TOPO_ERROR_INVALID_ARGUMENT;
    if (!tri_v0 || !tri_v1 || !tri_v2 || !tri_filt) return TOPO_ERROR_INVALID_ARGUMENT;

    // Sort edges by filtration
    EdgeInfo* edges = (EdgeInfo*)malloc(m * sizeof(EdgeInfo));
    for (int i = 0; i < m; i++) {
        edges[i].src = edge_src[i];
        edges[i].dst = edge_dst[i];
        edges[i].filt = edge_filt[i];
        edges[i].sorted_idx = 0;
    }
    qsort(edges, m, sizeof(EdgeInfo), edge_info_compare);
    for (int i = 0; i < m; i++) edges[i].sorted_idx = i;

    // Sort triangles by filtration
    TriSortKey* tris = (TriSortKey*)malloc(t * sizeof(TriSortKey));
    for (int i = 0; i < t; i++) {
        tris[i].filt = tri_filt[i];
        tris[i].v0 = tri_v0[i];
        tris[i].v1 = tri_v1[i];
        tris[i].v2 = tri_v2[i];
        tris[i].original_idx = i;
    }
    qsort(tris, t, sizeof(TriSortKey), tri_compare);

    // Boundary matrix: each triangle column has 3 edge entries
    // Represented as a sparse column list
    // boundary[col] = list of row indices (sorted descending for reduction)
    int** boundary = (int**)calloc(t, sizeof(int*));
    int* boundary_len = (int*)calloc(t, sizeof(int));

    for (int col = 0; col < t; col++) {
        boundary[col] = (int*)malloc(3 * sizeof(int));
        boundary_len[col] = 0;

        int v[3] = { tris[col].v0, tris[col].v1, tris[col].v2 };
        // 3 boundary edges: (v0,v1), (v0,v2), (v1,v2)
        int pairs[3][2] = { {v[0], v[1]}, {v[0], v[2]}, {v[1], v[2]} };

        for (int e = 0; e < 3; e++) {
            int eidx = find_edge(edges, m, pairs[e][0], pairs[e][1]);
            if (eidx >= 0) {
                boundary[col][boundary_len[col]++] = eidx;
            }
        }

        // Sort row indices descending (pivot = largest)
        for (int a = 0; a < boundary_len[col]; a++) {
            for (int b = a + 1; b < boundary_len[col]; b++) {
                if (boundary[col][a] < boundary[col][b]) {
                    int tmp = boundary[col][a];
                    boundary[col][a] = boundary[col][b];
                    boundary[col][b] = tmp;
                }
            }
        }
    }

    // Column reduction (left-to-right)
    // pivot_col[row] = column index that has this row as its pivot, or -1
    int* pivot_col = (int*)malloc(m * sizeof(int));
    memset(pivot_col, -1, m * sizeof(int));

    int count = 0;
    for (int col = 0; col < t; col++) {
        while (boundary_len[col] > 0) {
            int pivot = boundary[col][0]; // largest row index
            if (pivot_col[pivot] < 0) {
                // This column's pivot is unique — record the pair
                pivot_col[pivot] = col;
                // H1 pair: born at edge (pivot row), dies at triangle (col)
                out_births[count] = edges[pivot].filt;
                out_deaths[count] = tris[col].filt;
                count++;
                break;
            } else {
                // Add the column with matching pivot (XOR in Z/2Z)
                int other = pivot_col[pivot];
                // Symmetric difference of the two column sets
                int* merged = (int*)malloc((boundary_len[col] + boundary_len[other]) * sizeof(int));
                int mi = 0;
                int ai = 0, bi = 0;
                while (ai < boundary_len[col] && bi < boundary_len[other]) {
                    if (boundary[col][ai] > boundary[other][bi]) {
                        merged[mi++] = boundary[col][ai++];
                    } else if (boundary[col][ai] < boundary[other][bi]) {
                        merged[mi++] = boundary[other][bi++];
                    } else {
                        // Cancel (XOR)
                        ai++; bi++;
                    }
                }
                while (ai < boundary_len[col]) merged[mi++] = boundary[col][ai++];
                while (bi < boundary_len[other]) merged[mi++] = boundary[other][bi++];

                free(boundary[col]);
                boundary[col] = merged;
                boundary_len[col] = mi;
            }
        }
    }

    *out_count = count;

    // Cleanup
    for (int col = 0; col < t; col++) free(boundary[col]);
    free(boundary);
    free(boundary_len);
    free(pivot_col);
    free(edges);
    free(tris);

    return TOPO_SUCCESS;
}
