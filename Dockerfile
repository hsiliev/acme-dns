FROM golang:alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o acme-dns

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/acme-dns .
RUN mkdir -p /etc/acme-dns
RUN mkdir -p /var/lib/acme-dns
RUN rm -rf ./config.cfg
RUN apk --no-cache add ca-certificates && update-ca-certificates

VOLUME ["/etc/acme-dns", "/var/lib/acme-dns"]
ENTRYPOINT ["./acme-dns"]
EXPOSE 53 80 443
EXPOSE 53/udp
