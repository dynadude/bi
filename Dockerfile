ARG ALPINE_VERSION=3.23
ARG DEBIAN_VERSION=13.4
ARG PYWIN_VERSION=3.14

FROM alpine:${ALPINE_VERSION} AS linux-musl-build
RUN --mount=type=cache,sharing=locked,target=/var/cache/apk/ \
    apk add python3 py3-pip binutils
RUN python3 -m venv /tmp/venv
RUN /tmp/venv/bin/pip install pyinstaller

WORKDIR /tmp/workdir
COPY bi.py .

RUN /tmp/venv/bin/pyinstaller --onefile bi.py


FROM debian:${DEBIAN_VERSION} AS linux-gnu-build
RUN --mount=type=cache,sharing=locked,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update

RUN --mount=type=cache,sharing=locked,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt install -y python3 python3-venv python3-pip binutils
RUN python3 -m venv /tmp/venv
RUN /tmp/venv/bin/pip install pyinstaller

WORKDIR /tmp/workdir
COPY bi.py .

RUN /tmp/venv/bin/pyinstaller --onefile bi.py


FROM tobix/pywine:${PYWIN_VERSION} AS windows-build
WORKDIR /tmp/workdir
COPY bi.py .

RUN wine pyinstaller --onefile bi.py


FROM alpine:${ALPINE_VERSION}
WORKDIR /tmp/dist/

COPY --from=linux-musl-build /tmp/workdir/dist/bi bi-linux-musl
COPY --from=linux-gnu-build /tmp/workdir/dist/bi bi-linux-gnu
COPY --from=windows-build /tmp/workdir/dist/bi.exe bi-windows.exe
