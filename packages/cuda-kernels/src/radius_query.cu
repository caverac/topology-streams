#include <cuda_runtime.h>

#include "topostreams/radius_query.h"

#define CHECK_CUDA(call) do { \
    cudaError_t err = (call); \
    if (err != cudaSuccess) return TOPO_ERROR_CUDA_MALLOC; \
} while(0)

#define CHECK_CUDA_MEMCPY(call) do { \
    cudaError_t err = (call); \
    if (err != cudaSuccess) return TOPO_ERROR_CUDA_MEMCPY; \
} while(0)

/**
 * 1 thread per data point: check distance to query, atomic counter for output compaction.
 */
__global__ void radius_query_kernel(const double* __restrict__ points,
                                    const double* __restrict__ query,
                                    int n, int d, double radius_sq,
                                    int* __restrict__ out_indices,
                                    int* __restrict__ out_count) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;

    const double* p = points + (long long)i * d;
    double dist_sq = 0.0;
    for (int dim = 0; dim < d; dim++) {
        double diff = p[dim] - query[dim];
        dist_sq += diff * diff;
    }

    if (dist_sq <= radius_sq) {
        int pos = atomicAdd(out_count, 1);
        out_indices[pos] = i;
    }
}

extern "C" TopoError topo_gpu_radius_query(const double* points, const double* query,
                                           int n, int d, double radius,
                                           int* out_indices, int* out_count) {
    if (!points || !query || !out_indices || !out_count) return TOPO_ERROR_INVALID_ARGUMENT;
    if (n <= 0 || d <= 0 || radius < 0.0) return TOPO_ERROR_INVALID_ARGUMENT;

    int device_count = 0;
    cudaGetDeviceCount(&device_count);
    if (device_count == 0) return TOPO_ERROR_CUDA_NOT_AVAILABLE;

    double* d_points = nullptr;
    double* d_query = nullptr;
    int* d_out_indices = nullptr;
    int* d_out_count = nullptr;

    size_t points_bytes = (size_t)n * d * sizeof(double);
    size_t query_bytes = (size_t)d * sizeof(double);
    size_t idx_bytes = (size_t)n * sizeof(int);

    CHECK_CUDA(cudaMalloc(&d_points, points_bytes));
    CHECK_CUDA(cudaMalloc(&d_query, query_bytes));
    CHECK_CUDA(cudaMalloc(&d_out_indices, idx_bytes));
    CHECK_CUDA(cudaMalloc(&d_out_count, sizeof(int)));

    CHECK_CUDA_MEMCPY(cudaMemcpy(d_points, points, points_bytes, cudaMemcpyHostToDevice));
    CHECK_CUDA_MEMCPY(cudaMemcpy(d_query, query, query_bytes, cudaMemcpyHostToDevice));
    CHECK_CUDA_MEMCPY(cudaMemset(d_out_count, 0, sizeof(int)));

    double radius_sq = radius * radius;
    int threads = 256;
    int blocks = (n + threads - 1) / threads;

    radius_query_kernel<<<blocks, threads>>>(d_points, d_query, n, d, radius_sq,
                                              d_out_indices, d_out_count);

    cudaError_t kerr = cudaGetLastError();
    if (kerr != cudaSuccess) {
        cudaFree(d_points);
        cudaFree(d_query);
        cudaFree(d_out_indices);
        cudaFree(d_out_count);
        return TOPO_ERROR_CUDA_KERNEL;
    }

    int h_count = 0;
    CHECK_CUDA_MEMCPY(cudaMemcpy(&h_count, d_out_count, sizeof(int), cudaMemcpyDeviceToHost));
    CHECK_CUDA_MEMCPY(cudaMemcpy(out_indices, d_out_indices, h_count * sizeof(int), cudaMemcpyDeviceToHost));
    *out_count = h_count;

    cudaFree(d_points);
    cudaFree(d_query);
    cudaFree(d_out_indices);
    cudaFree(d_out_count);

    return TOPO_SUCCESS;
}
