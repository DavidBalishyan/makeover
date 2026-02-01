# Buildfile for Makeover
py = python3
src = main.py
bin = makeover

[group: General]
# Default target runs all checks
all:
    ${py} ${src} --list

[group: Installation]
# Install binary to ~/.local/bin
install:
    echo "Installing ${bin} to ~/.local/bin..."
    mkdir -p ~/.local/bin
    cp ${src} ~/.local/bin/${bin}
    chmod +x ~/.local/bin/${bin}
    echo "Installation complete."

uninstall:
    echo "Uninstalling ${bin} from ~/.local/bin..."
    rm -f ~/.local/bin/${bin}
    echo "Uninstallation complete."

reinstall: uninstall install

[group: Utility]
# Clean up temporary files
clean:
    echo "Cleaning temporary files..."
    rm -rf __pycache__

lint:
    pylint ${src}

create-env:
    python3 -m venv .venv

install-deps:
    .venv/bin/pip3 install -r requirements.txt

setup: create-env install-deps
