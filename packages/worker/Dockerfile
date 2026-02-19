# Stage 1: Build CUDA kernels
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY ../cuda-kernels/ /build/cuda-kernels/

RUN cd /build/cuda-kernels \
    && mkdir build && cd build \
    && cmake .. -DCMAKE_CUDA_ARCHITECTURES=75 \
    && make -j$(nproc)

# Stage 2: Python runtime
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

# Copy built CUDA library
COPY --from=builder /build/cuda-kernels/build/libtopostreams.so /usr/local/lib/
RUN ldconfig

ENV TOPOSTREAMS_LIB_PATH=/usr/local/lib/libtopostreams.so

WORKDIR /app

# Install Python packages
COPY ../cuda-kernels/python/ /app/cuda-kernels-python/
RUN pip3 install /app/cuda-kernels-python/

COPY ../stream-finder/ /app/stream-finder/
RUN pip3 install "/app/stream-finder/[gpu]"

COPY . /app/worker/
RUN pip3 install /app/worker/

# Run the worker
CMD ["python3", "-m", "worker.main"]
