#include <cstdlib>
#include <cstring>
#include <cuda_runtime.h>
#include <cub/cub.cuh>

#include "topostreams/persistence.h"

/**
 * H0 persistence via GPU-sorted edges + sequential union-find.
 *
 * Strategy:
 * 1. Copy edges to GPU, sort by filtration using CUB DeviceRadixSort.
 * 2. Copy sorted edges back to CPU.
 * 3. Run union-find with path compression to track component merges.
 * 4. Record (birth, death) for each merge where birth < death.
 */

// Union-find with path compression and union by rank
struct UnionFind {
    int* parent;
    int* rank;
    double* birth; // birth filtration of each component
    int n;

    void init(int n_, const double* vertex_filt) {
        n = n_;
        parent = (int*)malloc(n * sizeof(int));
        rank = (int*)calloc(n, sizeof(int));
        birth = (double*)malloc(n * sizeof(double));
        for (int i = 0; i < n; i++) {
            parent[i] = i;
            birth[i] = vertex_filt[i];
        }
    }

    void destroy() {
        free(parent);
        free(rank);
        free(birth);
    }

    int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]]; // path halving
            x = parent[x];
        }
        return x;
    }

    // Returns true if a merge occurred (components were different)
    // older_birth and younger_birth are set for the persistence pair
    bool unite(int a, int b, double edge_filt, double& dying_birth, double& death_filt) {
        int ra = find(a);
        int rb = find(b);
        if (ra == rb) return false;

        // The component with the higher (later) birth dies
        // In superlevel-set filtration, higher birth = smaller negative = less dense
        // The "younger" component (born later = higher filtration value) dies
        if (birth[ra] < birth[rb]) {
            // ra born earlier (more negative = denser), rb dies
            dying_birth = birth[rb];
        } else {
            // rb born earlier, ra dies
            dying_birth = birth[ra];
            int tmp = ra; ra = rb; rb = tmp;
        }
        death_filt = edge_filt;

        // Union by rank, ra survives
        if (rank[ra] < rank[rb]) { int t = ra; ra = rb; rb = t; }
        parent[rb] = ra;
        if (rank[ra] == rank[rb]) rank[ra]++;
        // Surviving component keeps its birth
        // (already has the earlier birth due to swap above)

        return true;
    }
};

// Sort key structure for edges
struct EdgeSortKey {
    double filt;
    int src;
    int dst;
};

// Comparator for qsort fallback
static int edge_compare(const void* a, const void* b) {
    double fa = ((const EdgeSortKey*)a)->filt;
    double fb = ((const EdgeSortKey*)b)->filt;
    if (fa < fb) return -1;
    if (fa > fb) return 1;
    return 0;
}

extern "C" TopoError topo_gpu_persistence_h0(
    const double* vertex_filt, const int* edge_src, const int* edge_dst,
    const double* edge_filt, int n, int m,
    double* out_births, double* out_deaths, int* out_count)
{
    if (!vertex_filt || !out_births || !out_deaths || !out_count)
        return TOPO_ERROR_INVALID_ARGUMENT;
    if (n <= 0) return TOPO_ERROR_INVALID_ARGUMENT;

    *out_count = 0;

    if (m == 0) return TOPO_SUCCESS;
    if (!edge_src || !edge_dst || !edge_filt) return TOPO_ERROR_INVALID_ARGUMENT;

    // Sort edges by filtration value using GPU (CUB) if available, else CPU
    int device_count = 0;
    cudaGetDeviceCount(&device_count);

    // Build edge array
    EdgeSortKey* edges = (EdgeSortKey*)malloc(m * sizeof(EdgeSortKey));
    if (!edges) return TOPO_ERROR_INTERNAL;

    for (int i = 0; i < m; i++) {
        edges[i].filt = edge_filt[i];
        edges[i].src = edge_src[i];
        edges[i].dst = edge_dst[i];
    }

    if (device_count > 0) {
        // GPU sort using CUB
        // Extract keys for sorting
        double* h_keys = (double*)malloc(m * sizeof(double));
        int* h_values = (int*)malloc(m * sizeof(int)); // index permutation
        for (int i = 0; i < m; i++) {
            h_keys[i] = edge_filt[i];
            h_values[i] = i;
        }

        double *d_keys_in = nullptr, *d_keys_out = nullptr;
        int *d_values_in = nullptr, *d_values_out = nullptr;
        size_t key_bytes = m * sizeof(double);
        size_t val_bytes = m * sizeof(int);

        cudaMalloc(&d_keys_in, key_bytes);
        cudaMalloc(&d_keys_out, key_bytes);
        cudaMalloc(&d_values_in, val_bytes);
        cudaMalloc(&d_values_out, val_bytes);

        cudaMemcpy(d_keys_in, h_keys, key_bytes, cudaMemcpyHostToDevice);
        cudaMemcpy(d_values_in, h_values, val_bytes, cudaMemcpyHostToDevice);

        void* d_temp = nullptr;
        size_t temp_bytes = 0;
        cub::DeviceRadixSort::SortPairs(d_temp, temp_bytes,
                                         d_keys_in, d_keys_out,
                                         d_values_in, d_values_out, m);
        cudaMalloc(&d_temp, temp_bytes);
        cub::DeviceRadixSort::SortPairs(d_temp, temp_bytes,
                                         d_keys_in, d_keys_out,
                                         d_values_in, d_values_out, m);

        int* sorted_indices = (int*)malloc(val_bytes);
        cudaMemcpy(sorted_indices, d_values_out, val_bytes, cudaMemcpyDeviceToHost);

        // Reorder edges according to sorted permutation
        EdgeSortKey* sorted_edges = (EdgeSortKey*)malloc(m * sizeof(EdgeSortKey));
        for (int i = 0; i < m; i++) {
            sorted_edges[i] = edges[sorted_indices[i]];
        }
        memcpy(edges, sorted_edges, m * sizeof(EdgeSortKey));

        free(sorted_edges);
        free(sorted_indices);
        free(h_keys);
        free(h_values);
        cudaFree(d_keys_in);
        cudaFree(d_keys_out);
        cudaFree(d_values_in);
        cudaFree(d_values_out);
        cudaFree(d_temp);
    } else {
        // CPU fallback sort
        qsort(edges, m, sizeof(EdgeSortKey), edge_compare);
    }

    // Union-find to compute H0 persistence
    UnionFind uf;
    uf.init(n, vertex_filt);

    int count = 0;
    for (int i = 0; i < m; i++) {
        double dying_birth, death;
        if (uf.unite(edges[i].src, edges[i].dst, edges[i].filt, dying_birth, death)) {
            // Only record finite persistence pairs (where birth != death)
            if (dying_birth != death) {
                out_births[count] = dying_birth;
                out_deaths[count] = death;
                count++;
            }
        }
    }

    *out_count = count;
    uf.destroy();
    free(edges);
    return TOPO_SUCCESS;
}
