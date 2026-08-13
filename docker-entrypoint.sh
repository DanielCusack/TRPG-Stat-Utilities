#!/bin/sh
# Refresh static files into the shared volume on start, so nginx serves the
# assets belonging to the image that is actually running. Then hand over to
# the CMD (uvicorn) as PID 1 so signals are delivered correctly.
set -e

# The dev compose stack bind-mounts the source tree and serves static via
# WhiteNoise, so collecting on every start is just noise.
if [ "$SKIP_COLLECTSTATIC" != "1" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
