FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
ARG DEBIAN_FRONTEND=noninteractive
ARG BLENDER_VERSION=4.2.2
ARG BLENDER_MAJOR=4.2
RUN apt-get update && apt-get install -y --no-install-recommends \
  wget ca-certificates python3 python3-pip git ffmpeg parallel \
  libgl1 libx11-6 libxi6 libxxf86vm1 libxcursor1 libxrender1 libxrandr2 \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN wget -q https://download.blender.org/release/Blender${BLENDER_MAJOR}/blender-${BLENDER_VERSION}-linux-x64.tar.xz && \
  tar -xf blender-${BLENDER_VERSION}-linux-x64.tar.xz && \
  ln -s /opt/blender-${BLENDER_VERSION}-linux-x64/blender /usr/local/bin/blender && \
  rm blender-${BLENDER_VERSION}-linux-x64.tar.xz
COPY tools/requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /workspace
COPY . .
RUN chmod +x run_field_pipeline.sh
ENTRYPOINT ["/bin/bash"]
