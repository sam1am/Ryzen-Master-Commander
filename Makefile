# Configuration
VERSION := $(shell python -c "from src.version import __version__; print(__version__)")
PYTHON := python3
BUILD_DIR := ./builds/ryzen-master-commander
DEV_VENV := .venv
PACKAGE_NAME := ryzen-master-commander
RPM_BUILD_DIR := $(HOME)/rpmbuild

# Default target
all: arch deb rpm flatpak

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) dist build *.egg-info
	rm -rf $(RPM_BUILD_DIR)
	rm -rf flatpak-repo
	rm -rf flatpak-pip-cache
	rm -rf .flatpak-builder

# Development environment
dev-setup:
	$(PYTHON) -m venv $(DEV_VENV)
	$(DEV_VENV)/bin/pip install -e .
	$(DEV_VENV)/bin/pip install pytest flake8 black

# Run the app in development mode
dev-run:
	$(DEV_VENV)/bin/python -m src.main

# Code quality
lint:
	$(DEV_VENV)/bin/flake8 src
	$(DEV_VENV)/bin/black --check src

format:
	$(DEV_VENV)/bin/black src --line-length 79 src

test:
	$(DEV_VENV)/bin/pytest

# ====== ARCH PACKAGE ======
arch: $(BUILD_DIR)
	@echo "Building Arch package (version $(VERSION))..."
	tar -czf $(BUILD_DIR)/$(PACKAGE_NAME)-$(VERSION).tar.gz --exclude='.git' --exclude='builds' --exclude='.venv' .
	mkdir -p $(BUILD_DIR)/temp
	cp ./packaging/arch/PKGBUILD $(BUILD_DIR)/temp/
	cp $(BUILD_DIR)/$(PACKAGE_NAME)-$(VERSION).tar.gz $(BUILD_DIR)/temp/  # <-- Add this line
	cd $(BUILD_DIR)/temp && \
		sed -i "s/pkgver=.*/pkgver=$(VERSION)/" PKGBUILD && \
		makepkg -sf && \
		cp *.pkg.tar.zst ../
	rm -rf $(BUILD_DIR)/temp
	@echo "Arch package created in $(BUILD_DIR)"

install-arch: arch
	@echo "Installing Arch package..."
	sudo pacman -R $(PACKAGE_NAME) || true
	sudo pacman -U $(BUILD_DIR)/$(PACKAGE_NAME)-$(VERSION)-1-any.pkg.tar.zst

# ====== DEBIAN PACKAGE ======
deb: $(BUILD_DIR)
	@echo "Building Debian package (version $(VERSION))..."
	# Create temporary build directory
	$(eval DEB_TEMP := $(shell mktemp -d))
	$(eval DEB_ROOT := $(DEB_TEMP)/$(PACKAGE_NAME)_$(VERSION))
	$(eval DEBIAN_DIR := $(DEB_ROOT)/DEBIAN)
	$(eval INSTALL_ROOT := $(DEB_ROOT)/usr)
	
	# Create directory structure
	mkdir -p $(DEBIAN_DIR)
	mkdir -p $(INSTALL_ROOT)
	
	# Install the package
	$(PYTHON) setup.py install --root=$(DEB_ROOT) --prefix=/usr
	
	# Create control file
	echo "Package: $(PACKAGE_NAME)" > $(DEBIAN_DIR)/control
	echo "Version: $(VERSION)" >> $(DEBIAN_DIR)/control
	echo "Section: utils" >> $(DEBIAN_DIR)/control
	echo "Priority: optional" >> $(DEBIAN_DIR)/control
	echo "Architecture: all" >> $(DEBIAN_DIR)/control
	echo "Depends: python3 (>= 3.8), python3-pyqt6, python3-numpy, python3-pillow, python3-pyqtgraph, policykit-1" >> $(DEBIAN_DIR)/control
	echo "Maintainer: sam1am <noreply@merrythieves.com>" >> $(DEBIAN_DIR)/control
	echo "Description: TDP and fan control for AMD Ryzen processors" >> $(DEBIAN_DIR)/control
	echo " Ryzen Master Commander provides TDP and fan control capabilities" >> $(DEBIAN_DIR)/control
	echo " for AMD Ryzen processors on Linux." >> $(DEBIAN_DIR)/control
	
	# Create postinst script
	echo "#!/bin/sh" > $(DEBIAN_DIR)/postinst
	echo "set -e" >> $(DEBIAN_DIR)/postinst
	echo 'if [ -x /usr/bin/update-desktop-database ]; then' >> $(DEBIAN_DIR)/postinst
	echo '    /usr/bin/update-desktop-database -q' >> $(DEBIAN_DIR)/postinst
	echo 'fi' >> $(DEBIAN_DIR)/postinst
	echo 'if [ -x /usr/bin/gtk-update-icon-cache ]; then' >> $(DEBIAN_DIR)/postinst
	echo '    /usr/bin/gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor' >> $(DEBIAN_DIR)/postinst
	echo 'fi' >> $(DEBIAN_DIR)/postinst
	chmod 755 $(DEBIAN_DIR)/postinst
	
	# Copy polkit file
	mkdir -p $(DEB_ROOT)/usr/share/polkit-1/actions/
	cp -f polkit/com.merrythieves.ryzenadj.policy $(DEB_ROOT)/usr/share/polkit-1/actions/
	
	# Build the package
	fakeroot dpkg-deb --build $(DEB_ROOT)
	
	# Move the package
	mv $(DEB_TEMP)/$(PACKAGE_NAME)_$(VERSION).deb $(BUILD_DIR)/
	
	# Clean up
	rm -rf $(DEB_TEMP)
	
	@echo "Debian package created in $(BUILD_DIR)"

install-deb: deb
	@echo "Installing Debian package..."
	sudo dpkg -i $(BUILD_DIR)/$(PACKAGE_NAME)_$(VERSION).deb
	sudo apt-get install -f

# ====== RPM PACKAGE ======
rpm: $(BUILD_DIR)
	@echo "Building RPM package (version $(VERSION))..."
	
	# Check for rpmbuild
	@which rpmbuild >/dev/null || { echo "rpmbuild not found. Installing..."; sudo pacman -S --needed rpm-tools; }
	
	# Create RPM build directories
	mkdir -p $(RPM_BUILD_DIR)/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	
	# Initialize RPM database if needed
	@if [ ! -d "/var/lib/rpm" ]; then \
		echo "Initializing RPM database..."; \
		sudo mkdir -p /var/lib/rpm; \
		sudo rpm --initdb; \
	fi
	
	# Create source directory
	mkdir -p $(RPM_BUILD_DIR)/BUILD/$(PACKAGE_NAME)-$(VERSION)
	
	# Copy files
	rsync -a --exclude='.git' --exclude='builds' --exclude='$(DEV_VENV)' --exclude='rpmbuild' . $(RPM_BUILD_DIR)/BUILD/$(PACKAGE_NAME)-$(VERSION)/
	
	# Create tarball
	cd $(RPM_BUILD_DIR)/BUILD && \
		tar -czf $(RPM_BUILD_DIR)/SOURCES/$(PACKAGE_NAME)-$(VERSION).tar.gz $(PACKAGE_NAME)-$(VERSION)
	
	# Create spec file
	echo "Name:           $(PACKAGE_NAME)" > $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Version:        $(VERSION)" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Release:        1%{?dist}" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Summary:        TDP and fan control for AMD Ryzen processors" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "License:        MIT" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "URL:            https://github.com/sam1am/Ryzen-Master-Commander" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Source0:        %{name}-%{version}.tar.gz" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "BuildArch:      noarch" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Requires:       python >= 3.8" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Requires:       python-pyqt6" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Requires:       python-numpy" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Requires:       python-pillow" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Requires:       python-pyqtgraph" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Requires:       polkit" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%description" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "Ryzen Master Commander provides TDP and fan control capabilities" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "for AMD Ryzen processors on Linux." >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%prep" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%setup -q" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%build" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "python setup.py build" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%install" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "python setup.py install --skip-build --root=%{buildroot} --prefix=/usr" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "mkdir -p %{buildroot}/usr/share/polkit-1/actions/" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "cp -p polkit/com.merrythieves.ryzenadj.policy %{buildroot}/usr/share/polkit-1/actions/" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%files" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%license LICENSE" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/bin/ryzen-master-commander" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/bin/ryzen-master-commander-helper" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/share/applications/ryzen-master-commander.desktop" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/share/icons/hicolor/*/apps/ryzen-master-commander.png" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/share/ryzen-master-commander/" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/share/polkit-1/actions/com.merrythieves.ryzenadj.policy" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/lib/python*/site-packages/src/" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "/usr/lib/python*/site-packages/ryzen_master_commander*.egg-info/" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%post" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo 'if [ -x /usr/bin/update-desktop-database ]; then' >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo '    /usr/bin/update-desktop-database -q' >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo 'fi' >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo 'if [ -x /usr/bin/gtk-update-icon-cache ]; then' >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo '    /usr/bin/gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor' >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo 'fi' >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "%changelog" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "* $(shell date "+%a %b %d %Y") Sam M <noreply@merrythieves.com> - $(VERSION)-1" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	echo "- Updated to version $(VERSION)" >> $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	
	# Build the RPM
	rpmbuild -ba $(RPM_BUILD_DIR)/SPECS/$(PACKAGE_NAME).spec
	
	@echo "Copying RPM package to build directory..."
	@mkdir -p $(BUILD_DIR)
	@bash -c 'RPM_PATH="/home/sam/rpmbuild/RPMS/noarch/$(PACKAGE_NAME)-$(VERSION)-1.noarch.rpm"; \
		echo "Looking for: $$RPM_PATH"; \
		if [ -f "$$RPM_PATH" ]; then \
			echo "Found RPM at: $$RPM_PATH"; \
			cp "$$RPM_PATH" $(BUILD_DIR)/; \
			echo "RPM package copied to $(BUILD_DIR)"; \
		else \
			echo "ERROR: RPM file not found at: $$RPM_PATH"; \
			ls -la /home/sam/rpmbuild/RPMS/noarch/; \
			echo "Trying direct copy..."; \
			cp /home/sam/rpmbuild/RPMS/noarch/$(PACKAGE_NAME)-$(VERSION)-1.noarch.rpm $(BUILD_DIR)/ || echo "Direct copy failed too"; \
		fi'


	@echo "RPM package created in $(BUILD_DIR)"

install-rpm: rpm
	@echo "Installing RPM package..."
	sudo rpm -Uvh --force $(BUILD_DIR)/$(PACKAGE_NAME)-$(VERSION)-*.rpm

# ====== FLATPAK PACKAGE ======
flatpak: $(BUILD_DIR)
	@echo "Building Flatpak package (version $(VERSION))..."
	@echo "FORCE CLEANING and preparing pip cache for Flatpak..."
	rm -rf flatpak-pip-cache # Ensure it's clean
	mkdir -p flatpak-pip-cache

	# --- Dependencies for Python 3.12 (Flatpak SDK) ---
	echo "Downloading numpy for Flatpak SDK (Python 3.12)..."
	pip download --no-deps -d flatpak-pip-cache \
		--only-binary=:all: \
		--platform manylinux2014_x86_64 \
		--python-version 3.12 --implementation cp --abi cp312 \
		numpy

	echo "Downloading Pillow for Flatpak SDK (Python 3.12)..."
	pip download --no-deps -d flatpak-pip-cache \
		--only-binary=:all: \
		--platform manylinux_2_28_x86_64 \
		--python-version 3.12 --implementation cp --abi cp312 \
		Pillow

	# --- PyQt6 Components - Multi-step Download for Python 3.12 ---
	echo "Downloading PyQt6-sip==13.6.0 for Python 3.12..."
	pip download --no-deps -d flatpak-pip-cache \
		--only-binary=:all: \
		--platform manylinux_2_5_x86_64 \
		--python-version 3.12 --implementation cp --abi cp312 \
		"PyQt6-sip==13.6.0" # PyQt6 6.7.0 often uses sip 13.6.0

	echo "Downloading PyQt6_Qt6==6.7.0 for Python 3.12 (any compatible platform)..."
	pip download --no-deps -d flatpak-pip-cache \
		--only-binary=:all: \
		--python-version 3.12 --implementation cp --abi cp312 \
		"PyQt6-Qt6==6.7.0" # Get the Qt6 libs for 6.7.0, platform any for this one

	echo "Downloading PyQt6==6.7.0 (main package) for Python 3.12..."
	pip download --no-deps -d flatpak-pip-cache \
		--only-binary=:all: \
		--platform manylinux_2_28_x86_64 \
		--python-version 3.12 --implementation cp --abi cp312 \
		"PyQt6==6.7.0"
	# --- End PyQt6 Components ---

	echo "Downloading pyqtgraph, pystray, and other general dependencies..."
	pip download -d flatpak-pip-cache \
		pyqtgraph pystray # These will also pick up their own deps like six, python-xlib

	echo "Contents of flatpak-pip-cache after download:"
	ls -1 flatpak-pip-cache
	# --- End Dependencies Download ---

	flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo
	flatpak install --user -y flathub org.kde.Platform//6.9 org.kde.Sdk//6.9 || true
	flatpak-builder --user --force-clean --repo=flatpak-repo \
		builds/flatpak-build packaging/flatpak/com.merrythieves.RyzenMasterCommander.yaml
	flatpak build-bundle flatpak-repo $(BUILD_DIR)/ryzen-master-commander-$(VERSION).flatpak \
		com.merrythieves.RyzenMasterCommander

install-flatpak: flatpak
	@echo "Installing Flatpak package..."
	flatpak-builder --user --install --force-clean \
		builds/flatpak-build packaging/flatpak/com.merrythieves.RyzenMasterCommander.yaml

# Bump the version
bump-version:
	@read -p "New version: " new_version; \
	echo "$$new_version" > version.txt; \
	git add version.txt; \
	git commit -m "Bump version to $$new_version"; \
	git tag "v$$new_version"

# Release a new version
release: clean all
	@echo "Creating release for version $(VERSION)..."
	@echo "Packages are ready in $(BUILD_DIR)"
	@echo "Don't forget to push the tag: git push origin v$(VERSION)"

.PHONY: all clean dev-setup dev-run lint format test arch deb rpm install-arch install-deb install-rpm bump-version release