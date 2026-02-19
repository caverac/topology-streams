#include <cuda_runtime.h>

#include "topostreams/density.h"

#define CHECK_CUDA(call) do { \
    cudaError_t err = (call); \
    if (err != cudaSuccess) return TOPO_ERROR_CUDA_MALLOC; \
} while(0)

#define CHECK_CUDA_MEMCPY(call) do { \
    cudaError_t err = (call); \
    if (err != cudaSuccess) return TOPO_ERROR_CUDA_MEMCPY; \
} while(0)

/**
 * Trivial 1-thread-per-point kernel: filtration[i] = -1.0 / max(kth_dist[i], 1e-10)
 */
__global__ void density_filtration_kernel(const double* __restrict__ kth_distances,
                                          int n,
                                          double* __restrict__ out_filtration) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;

    double d = kth_distances[i];
    if (d < 1e-10) d = 1e-10;
    out_filtration[i] = -1.0 / d;
}

extern "C" TopoError topo_gpu_density_filtration(const double* kth_distances, int n,
                                                  double* out_filtration) {
    if (!kth_distances || !out_filtration) return TOPO_ERROR_INVALID_ARGUMENT;
    if (n <= 0) return TOPO_ERROR_INVALID_ARGUMENT;

    int device_count = 0;
    cudaGetDeviceCount(&device_count);
    if (device_count == 0) return TOPO_ERROR_CUDA_NOT_AVAILABLE;

    double* d_kth = nullptr;
    double* d_out = nullptr;
    size_t bytes = (size_t)n * sizeof(double);

    CHECK_CUDA(cudaMalloc(&d_kth, bytes));
    CHECK_CUDA(cudaMalloc(&d_out, bytes));
    CHECK_CUDA_MEMCPY(cudaMemcpy(d_kth, kth_distances, bytes, cudaMemcpyHostToDevice));

    int threads = 256;
    int blocks = (n + threads - 1) / threads;
    density_filtration_kernel<<<blocks, threads>>>(d_kth, n, d_out);

    cudaError_t kerr = cudaGetLastError();
    if (kerr != cudaSuccess) {
        cudaFree(d_kth);
        cudaFree(d_out);
        return TOPO_ERROR_CUDA_KERNEL;
    }

    CHECK_CUDA_MEMCPY(cudaMemcpy(out_filtration, d_out, bytes, cudaMemcpyDeviceToHost));

    cudaFree(d_kth);
    cudaFree(d_out);
    return TOPO_SUCCESS;
}
