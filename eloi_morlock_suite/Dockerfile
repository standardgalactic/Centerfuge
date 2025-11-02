
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
RUN apt-get update && \
    apt-get install -y blender ffmpeg python3-pip zip && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY scripts/ scripts/
COPY run_eloi_morlock_stills.sh run_eloi_morlock_stills.sh
RUN chmod +x run_eloi_morlock_stills.sh
ENTRYPOINT ["/bin/bash"]
