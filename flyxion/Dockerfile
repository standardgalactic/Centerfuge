FROM node:20-alpine AS elm-builder
WORKDIR /app
RUN npm install -g elm@0.19.1
COPY elm/ ./elm/
WORKDIR /app/elm
RUN elm make src/Main.elm --optimize --output=../static/main.js

FROM golang:1.22-alpine AS go-builder
WORKDIR /app
COPY go/ ./go/
COPY static/ ./static/
COPY --from=elm-builder /app/static/main.js ./static/main.js
WORKDIR /app/go/server
RUN go mod init flyxion || true && go mod tidy
RUN go build -o /flyxiond

FROM alpine:3.20
WORKDIR /app
COPY --from=go-builder /flyxiond .
COPY --from=go-builder /app/static ./static
EXPOSE 8080
ENV RSVP_W=64 RSVP_H=64
ENTRYPOINT ["./flyxiond"]
