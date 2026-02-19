#ifndef TOPOSTREAMS_ERROR_H
#define TOPOSTREAMS_ERROR_H

#include "topostreams/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Return a human-readable string for the given error code.
 */
const char* topo_error_string(TopoError err);

#ifdef __cplusplus
}
#endif

#endif /* TOPOSTREAMS_ERROR_H */
