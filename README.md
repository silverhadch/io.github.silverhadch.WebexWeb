# Webex Web

Runs web.webex.com in its own window instead of a browser tab. Built with
PyQt6 and QtWebEngine.

Independent project, not affiliated with Cisco. Webex is a trademark of Cisco.

## Install

Add the repository and install:

```bash
flatpak remote-add --if-not-exists webexweb \
  https://silverhadch.github.io/io.github.silverhadch.WebexWeb/index.flatpakrepo
flatpak install webexweb io.github.silverhadch.WebexWeb
```

## Build locally

Install the toolchain and runtimes once:

    flatpak install -y flathub org.flatpak.Builder
    flatpak install -y flathub \
      org.kde.Platform//6.10 \
      org.kde.Sdk//6.10 \
      com.riverbankcomputing.PyQt.BaseApp//6.10

Build and install for the current user:

    flatpak run org.flatpak.Builder --user --install --force-clean \
      build-dir io.github.silverhadch.WebexWeb.yaml

Run:

    flatpak run io.github.silverhadch.WebexWeb

## License

MIT.
