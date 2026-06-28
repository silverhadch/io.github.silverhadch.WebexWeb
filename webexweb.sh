#!/bin/sh
exec zypak-wrapper /app/electron/electron /app/main \
  --ozone-platform-hint=auto \
  --enable-features=WebRTCPipeWireCapturer \
  --autoplay-policy=no-user-gesture-required \
  "$@"
