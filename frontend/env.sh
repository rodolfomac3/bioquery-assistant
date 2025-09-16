#!/bin/sh
# Replace placeholder in built JS with runtime REACT_APP_API_URL
: "${REACT_APP_API_URL:?REACT_APP_API_URL not set}"
find /usr/share/nginx/html -type f -name '*.js' -exec \
  sed -i "s|__API_URL__|$REACT_APP_API_URL|g" {} +
exec "$@"
