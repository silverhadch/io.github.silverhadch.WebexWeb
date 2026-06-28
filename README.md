# Webex Web
> *A working Linux client for Webex – because the official app is broken.*

Webex in its own window, not a browser tab. Built with Electron.

> **Not affiliated with, endorsed by, or connected to Cisco in any way.**
> Webex is a trademark of Cisco Systems, Inc.

![Webex Web](data/screenshot.png)

## Install

    flatpak remote-add --if-not-exists webexweb \
      https://silverhadch.github.io/io.github.silverhadch.WebexWeb/index.flatpakrepo
    flatpak install webexweb io.github.silverhadch.WebexWeb

## Build locally

    flatpak install -y flathub org.flatpak.Builder
    flatpak install -y flathub \
      org.freedesktop.Platform//25.08 \
      org.freedesktop.Sdk//25.08 \
      org.electronjs.Electron2.BaseApp//25.08

    flatpak run org.flatpak.Builder --user --install --force-clean \
      build-dir io.github.silverhadch.WebexWeb.yaml

    flatpak run io.github.silverhadch.WebexWeb

## License

MIT. See [LICENSE](LICENSE).
