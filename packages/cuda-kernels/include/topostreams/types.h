#ifndef TOPOSTREAMS_TYPES_H
#define TOPOSTREAMS_TYPES_H

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    TOPO_SUCCESS = 0,
    TOPO_ERROR_INVALID_ARGUMENT = 1,
    TOPO_ERROR_CUDA_MALLOC = 2,
    TOPO_ERROR_CUDA_MEMCPY = 3,
    TOPO_ERROR_CUDA_KERNEL = 4,
    TOPO_ERROR_CUDA_NOT_AVAILABLE = 5,
    TOPO_ERROR_INTERNAL = 99
} TopoError;

#ifdef __cplusplus
}
#endif

#endif /* TOPOSTREAMS_TYPES_H */
