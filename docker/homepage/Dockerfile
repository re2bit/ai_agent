FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY src/homepage/main.go .
COPY src/homepage/templates ./templates

RUN go build -o homepage main.go

FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/homepage .

EXPOSE 8080

CMD ["./homepage"]