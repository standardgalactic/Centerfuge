FROM rust:1-bookworm AS build
WORKDIR /app
COPY . .
RUN cargo build --release -p rsvpctl

FROM debian:bookworm-slim AS run
WORKDIR /app
COPY --from=build /app/target/release/rsvpctl /usr/local/bin/rsvpctl
ENTRYPOINT ["/usr/local/bin/rsvpctl"]
