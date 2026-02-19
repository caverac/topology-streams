#include <cfloat>
#include <cstdio>
#include <cuda_runtime.h>

#include "topostreams/knn.h"

#define CHECK_CUDA(call) do { \
    cudaError_t err = (call); \
    if (err != cudaSuccess) return TOPO_ERROR_CUDA_MALLOC; \
} while(0)

#define CHECK_CUDA_MEMCPY(call) do { \
    cudaError_t err = (call); \
    if (err != cudaSuccess) return TOPO_ERROR_CUDA_MEMCPY; \
} while(0)

/**
 * Brute-force kNN kernel.
 * One block per query point. 256 threads compute distances to all data points
 * in strided fashion, then maintain a thread-local top-k via insertion sort.
 * Final merge across threads uses shared memory.
 */

static __device__ void insert_if_closer(double* dists, int* idxs, int k,
                                        double d, int idx) {
    if (d >= dists[k - 1]) return;
    // Find insertion position
    int pos = k - 1;
    while (pos > 0 && dists[pos - 1] > d) {
        dists[pos] = dists[pos - 1];
        idxs[pos] = idxs[pos - 1];
        pos--;
    }
    dists[pos] = d;
    idxs[pos] = idx;
}

__global__ void knn_kernel(const double* __restrict__ points,
                           int n, int d, int k,
                           double* __restrict__ out_dist,
                           int* __restrict__ out_idx) {
    int query_id = blockIdx.x;
    if (query_id >= n) return;

    const int tid = threadIdx.x;
    const int nthreads = blockDim.x;

    // Thread-local top-k storage (on stack, limited to k <= 256)
    // For larger k, this would need shared memory or global memory
    double local_dist[256];
    int local_idx[256];
    int local_k = min(k, 256);

    for (int i = 0; i < local_k; i++) {
        local_dist[i] = DBL_MAX;
        local_idx[i] = -1;
    }

    const double* query = points + (long long)query_id * d;

    // Each thread processes a strided subset of data points
    for (int i = tid; i < n; i += nthreads) {
        if (i == query_id) continue; // skip self

        const double* p = points + (long long)i * d;
        double dist_sq = 0.0;
        for (int dim = 0; dim < d; dim++) {
            double diff = query[dim] - p[dim];
            dist_sq += diff * diff;
        }
        double dist = sqrt(dist_sq);
        insert_if_closer(local_dist, local_idx, local_k, dist, i);
    }

    // Use shared memory to merge results across threads
    // Simple approach: thread 0 collects all thread-local results
    extern __shared__ char smem[];
    double* s_dist = (double*)smem;
    int* s_idx = (int*)(s_dist + nthreads * local_k);

    // Each thread writes its local results to shared memory
    for (int i = 0; i < local_k; i++) {
        s_dist[tid * local_k + i] = local_dist[i];
        s_idx[tid * local_k + i] = local_idx[i];
    }
    __syncthreads();

    // Thread 0 merges all results
    if (tid == 0) {
        double merged_dist[256];
        int merged_idx[256];
        for (int i = 0; i < local_k; i++) {
            merged_dist[i] = DBL_MAX;
            merged_idx[i] = -1;
        }

        for (int t = 0; t < nthreads; t++) {
            for (int i = 0; i < local_k; i++) {
                double d_val = s_dist[t * local_k + i];
                int i_val = s_idx[t * local_k + i];
                if (i_val >= 0) {
                    insert_if_closer(merged_dist, merged_idx, local_k, d_val, i_val);
                }
            }
        }

        // Write output (k neighbors, skipping self)
        double* out_d = out_dist + (long long)query_id * k;
        int* out_i = out_idx + (long long)query_id * k;
        for (int i = 0; i < k; i++) {
            out_d[i] = merged_dist[i];
            out_i[i] = merged_idx[i];
        }
    }
}

extern "C" TopoError topo_gpu_knn(const double* points, int n, int d, int k,
                                  double* out_dist, int* out_idx) {
    if (!points || !out_dist || !out_idx) return TOPO_ERROR_INVALID_ARGUMENT;
    if (n <= 0 || d <= 0 || k <= 0 || k >= n) return TOPO_ERROR_INVALID_ARGUMENT;
    if (k > 256) return TOPO_ERROR_INVALID_ARGUMENT; // stack limitation

    int device_count = 0;
    cudaGetDeviceCount(&device_count);
    if (device_count == 0) return TOPO_ERROR_CUDA_NOT_AVAILABLE;

    double* d_points = nullptr;
    double* d_out_dist = nullptr;
    int* d_out_idx = nullptr;

    size_t points_bytes = (size_t)n * d * sizeof(double);
    size_t dist_bytes = (size_t)n * k * sizeof(double);
    size_t idx_bytes = (size_t)n * k * sizeof(int);

    CHECK_CUDA(cudaMalloc(&d_points, points_bytes));
    CHECK_CUDA(cudaMalloc(&d_out_dist, dist_bytes));
    CHECK_CUDA(cudaMalloc(&d_out_idx, idx_bytes));

    CHECK_CUDA_MEMCPY(cudaMemcpy(d_points, points, points_bytes, cudaMemcpyHostToDevice));

    int threads = 256;
    int blocks = n;
    size_t smem_size = threads * k * (sizeof(double) + sizeof(int));

    knn_kernel<<<blocks, threads, smem_size>>>(d_points, n, d, k, d_out_dist, d_out_idx);

    cudaError_t kerr = cudaGetLastError();
    if (kerr != cudaSuccess) {
        cudaFree(d_points);
        cudaFree(d_out_dist);
        cudaFree(d_out_idx);
        return TOPO_ERROR_CUDA_KERNEL;
    }

    CHECK_CUDA_MEMCPY(cudaMemcpy(out_dist, d_out_dist, dist_bytes, cudaMemcpyDeviceToHost));
    CHECK_CUDA_MEMCPY(cudaMemcpy(out_idx, d_out_idx, idx_bytes, cudaMemcpyDeviceToHost));

    cudaFree(d_points);
    cudaFree(d_out_dist);
    cudaFree(d_out_idx);

    return TOPO_SUCCESS;
}
