#!/usr/bin/env bash
# Install (or uninstall) JadivCalc Template desktop launchers on Linux.
#
#   ./install-launcher.sh            # install for the current user
#   ./install-launcher.sh --uninstall
#
# Installs into the per-user XDG locations (no root required):
#   ~/.local/share/applications/   – .desktop launchers
#   ~/.local/share/icons/hicolor/scalable/apps/ – the icon
set -euo pipefail

# Absolute path to this repository (where the .py scripts live).
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$REPO_DIR/assets"

APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

DESKTOP_FILES=(jadivcalc.desktop jadivcalc-sk.desktop)
ICON_NAME=jadivcalc.svg

do_uninstall() {
    for f in "${DESKTOP_FILES[@]}"; do
        rm -f "$APP_DIR/$f"
    done
    rm -f "$ICON_DIR/$ICON_NAME"
    echo "Removed JadivCalc Template launchers."
    update_caches
}

update_caches() {
    command -v update-desktop-database >/dev/null 2>&1 \
        && update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
    command -v gtk-update-icon-cache >/dev/null 2>&1 \
        && gtk-update-icon-cache -f -i -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" >/dev/null 2>&1 || true
}

do_install() {
    mkdir -p "$APP_DIR" "$ICON_DIR"
    install -m 0644 "$ASSETS_DIR/$ICON_NAME" "$ICON_DIR/$ICON_NAME"
    local icon_path="$ICON_DIR/$ICON_NAME"

    # Escape characters that are special in a sed replacement (\, &, |).
    local escaped_repo_dir escaped_icon
    escaped_repo_dir=$(printf '%s' "$REPO_DIR" | sed 's/[&|\]/\\&/g')
    escaped_icon=$(printf '%s' "$icon_path" | sed 's/[&|\]/\\&/g')

    for f in "${DESKTOP_FILES[@]}"; do
        # Point Exec at the repo and Icon at the absolute installed icon path,
        # so the launcher shows the icon regardless of icon-theme caches.
        sed -e "s|__INSTALL_DIR__|$escaped_repo_dir|g" \
            -e "s|__ICON_PATH__|$escaped_icon|g" \
            "$ASSETS_DIR/$f" > "$APP_DIR/$f"
        chmod 0644 "$APP_DIR/$f"
    done

    update_caches
    echo "Installed JadivCalc Template launchers into $APP_DIR"
    echo "Installed icon to $icon_path"
    echo "Look for 'JadivCalc Template' in your application menu."
}

if [[ "${1:-}" == "--uninstall" || "${1:-}" == "-u" ]]; then
    do_uninstall
elif [[ -z "${1:-}" ]]; then
    do_install
else
    echo "Usage: $0 [options]"
    echo "  -u, --uninstall  Uninstall the launchers and icon"
    echo "  -h, --help       Show this help message"
    exit 1
fi
