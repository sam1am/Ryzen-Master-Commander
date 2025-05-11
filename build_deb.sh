#!/bin/bash
set -e

# Read version
VERSION=$(cat version.txt)
PKG_NAME="ryzen-master-commander"
ARCH="all"  # Python packages are typically architecture-independent

# Create temporary build directory
BUILD_DIR=$(mktemp -d)
DEB_ROOT="${BUILD_DIR}/${PKG_NAME}_${VERSION}"
DEBIAN_DIR="${DEB_ROOT}/DEBIAN"
INSTALL_ROOT="${DEB_ROOT}/usr"

echo "Building ${PKG_NAME} version ${VERSION}"
echo "Using build directory: ${BUILD_DIR}"

# Create directory structure
mkdir -p "${DEBIAN_DIR}"
mkdir -p "${INSTALL_ROOT}"

# Install the package to the temporary directory
python setup.py install --root="${DEB_ROOT}" --prefix=/usr

# Create DEBIAN/control file
cat > "${DEBIAN_DIR}/control" << EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.8), python3-pyqt5, python3-numpy, python3-pillow, python3-pyqtgraph, policykit-1
Maintainer: sam1am <noreply@merrythieves.com>
Description: TDP and fan control for AMD Ryzen processors
 Ryzen Master Commander provides TDP and fan control capabilities 
 for AMD Ryzen processors on Linux.
EOF

# Create postinst script to update icon cache and desktop database
cat > "${DEBIAN_DIR}/postinst" << EOF
#!/bin/sh
set -e
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database -q
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor
fi
EOF
chmod 755 "${DEBIAN_DIR}/postinst"

# Copy polkit file to correct Debian location if needed
mkdir -p "${DEB_ROOT}/usr/share/polkit-1/actions/"
cp -f polkit/com.merrythieves.ryzenadj.policy "${DEB_ROOT}/usr/share/polkit-1/actions/"

# Build the package
fakeroot dpkg-deb --build "${DEB_ROOT}"

# Move the resulting .deb file to current directory
mv "${BUILD_DIR}/${PKG_NAME}_${VERSION}.deb" "./builds/${PKG_NAME}/${PKG_NAME}_${VERSION}.deb"

# Clean up
rm -rf "${BUILD_DIR}"

echo "Package created: ./builds/${PKG_NAME}/${PKG_NAME}_${VERSION}.deb"