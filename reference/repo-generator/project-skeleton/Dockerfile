# syntax=docker/dockerfile:1.7
FROM --platform=$BUILDPLATFORM golang:1.25-alpine AS build

ARG TARGETOS
ARG TARGETARCH
ARG GIT_COMMIT

RUN apk add --no-cache git ca-certificates

WORKDIR /src

COPY go.mod go.sum ./

# Secret-mount keeps credentials out of image layers and history.
# Build with:
#   docker build \
#     --secret id=git_username,env=GIT_USERNAME \
#     --secret id=git_password,env=GIT_PASSWORD \
#     ...
RUN --mount=type=secret,id=git_username \
  --mount=type=secret,id=git_password \
  --mount=type=cache,target=/go/pkg/mod \
  git config --global url."https://$(cat /run/secrets/git_username):$(cat /run/secrets/git_password)@gitlab.com/example-org/platform/backend/".insteadOf "https://gitlab.com/example-org/platform/backend/" \
  && go mod download \
  && rm -f /root/.gitconfig

COPY . .

RUN --mount=type=cache,target=/root/.cache/go-build \
  CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
  go build -trimpath -a -installsuffix cgo \
  -ldflags "-s -w -extldflags -static -X main.commit=${GIT_COMMIT}" \
  -o /out/api .

FROM alpine:3.23

RUN addgroup -S app && adduser -S -G app -u 10001 app \
  && apk upgrade --no-cache \
  && apk add --no-cache tini ca-certificates tzdata \
  && cp /usr/share/zoneinfo/Asia/Bangkok /etc/localtime \
  && echo "Asia/Bangkok" > /etc/timezone \
  && update-ca-certificates

WORKDIR /home/app

COPY --from=build --chown=app:app /out/api /home/app/api

USER app

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/home/app/api"]