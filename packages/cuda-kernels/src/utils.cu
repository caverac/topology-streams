#include "topostreams/error.h"
#include "topostreams/types.h"

extern "C" const char* topo_error_string(TopoError err) {
    switch (err) {
        case TOPO_SUCCESS:               return "success";
        case TOPO_ERROR_INVALID_ARGUMENT: return "invalid argument";
        case TOPO_ERROR_CUDA_MALLOC:     return "CUDA malloc failed";
        case TOPO_ERROR_CUDA_MEMCPY:     return "CUDA memcpy failed";
        case TOPO_ERROR_CUDA_KERNEL:     return "CUDA kernel launch failed";
        case TOPO_ERROR_CUDA_NOT_AVAILABLE: return "CUDA device not available";
        case TOPO_ERROR_INTERNAL:        return "internal error";
        default:                         return "unknown error";
    }
}
