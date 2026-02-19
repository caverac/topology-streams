cmake_minimum_required(VERSION 3.24)
project(topostreams LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CUDA_STANDARD 17)

# Target T4 GPU (sm_75) by default, allow override
set(CMAKE_CUDA_ARCHITECTURES "75" CACHE STRING "CUDA architectures to target")

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

add_library(topostreams SHARED
    src/utils.cu
    src/knn.cu
    src/density.cu
    src/persistence_h0.cu
    src/persistence_h1.cu
    src/radius_query.cu
)

target_include_directories(topostreams PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Link CUDA runtime
target_link_libraries(topostreams PRIVATE CUDA::cudart)

# Set library output name
set_target_properties(topostreams PROPERTIES
    OUTPUT_NAME "topostreams"
    CUDA_SEPARABLE_COMPILATION ON
    POSITION_INDEPENDENT_CODE ON
)

# Install targets
install(TARGETS topostreams
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/topostreams
    DESTINATION include
)
