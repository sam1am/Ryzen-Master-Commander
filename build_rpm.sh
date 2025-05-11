#!/bin/bash
set -e

# Check if necessary tools are installed
if ! command -v rpmbuild &> /dev/null; then
    echo "rpmbuild command not found. Installing rpm-tools..."
    sudo pacman -S --needed rpm-tools
fi

# Read version
VERSION=$(cat version.txt)
PKG_NAME="ryzen-master-commander"

echo "Building ${PKG_NAME} version ${VERSION} RPM package"

# Create directories for RPM build
RPM_BUILD_DIR="$HOME/rpmbuild"
mkdir -p ${RPM_BUILD_DIR}/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Initialize RPM database if it doesn't exist
if [ ! -d "/var/lib/rpm" ]; then
    echo "Initializing RPM database..."
    sudo mkdir -p /var/lib/rpm
    sudo rpm --initdb
fi

# Create source directory with proper structure
TEMP_SRC_DIR="${RPM_BUILD_DIR}/BUILD/${PKG_NAME}-${VERSION}"
mkdir -p "${TEMP_SRC_DIR}"

# Copy all project files to the source directory
echo "Preparing source files..."
rsync -a --exclude='.git' --exclude='builds' --exclude='rpmbuild' . "${TEMP_SRC_DIR}/"

# Create tarball with proper structure
echo "Creating source tarball..."
pushd "${RPM_BUILD_DIR}/BUILD" > /dev/null
tar -czf "${RPM_BUILD_DIR}/SOURCES/${PKG_NAME}-${VERSION}.tar.gz" "${PKG_NAME}-${VERSION}"
popd > /dev/null

# Create the spec file
echo "Creating RPM spec file..."
cat > "${RPM_BUILD_DIR}/SPECS/${PKG_NAME}.spec" << EOF
Name:           ${PKG_NAME}
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        TDP and fan control for AMD Ryzen processors

License:        MIT
URL:            https://github.com/sam1am/Ryzen-Master-Commander
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python >= 3.8
Requires:       python-pyqt5
Requires:       python-numpy
Requires:       python-pillow
Requires:       python-pyqtgraph
Requires:       polkit

%description
Ryzen Master Commander provides TDP and fan control capabilities
for AMD Ryzen processors on Linux.

%prep
%setup -q

%build
python setup.py build

%install
python setup.py install --skip-build --root=%{buildroot} --prefix=/usr
mkdir -p %{buildroot}/usr/share/polkit-1/actions/
cp -p polkit/com.merrythieves.ryzenadj.policy %{buildroot}/usr/share/polkit-1/actions/

%files
%license LICENSE
/usr/bin/ryzen-master-commander
/usr/bin/ryzen-master-commander-helper
/usr/share/applications/ryzen-master-commander.desktop
/usr/share/icons/hicolor/*/apps/ryzen-master-commander.png
/usr/share/ryzen-master-commander/
/usr/share/polkit-1/actions/com.merrythieves.ryzenadj.policy
/usr/lib/python*/site-packages/ryzen_master_commander/
/usr/lib/python*/site-packages/ryzen_master_commander-*.egg-info/

%post
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database -q
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor
fi

%changelog
* $(date "+%a %b %d %Y") Sam M <noreply@merrythieves.com> - ${VERSION}-1
- Updated to version ${VERSION}
EOF

# Build the RPM package
echo "Building RPM package..."
rpmbuild -ba "${RPM_BUILD_DIR}/SPECS/${PKG_NAME}.spec"

# Copy the resulting RPM to builds directory
mkdir -p "./builds/${PKG_NAME}"
FOUND_RPM=$(find "${RPM_BUILD_DIR}/RPMS/" -name "${PKG_NAME}-${VERSION}*.rpm" 2>/dev/null)
if [ -n "$FOUND_RPM" ]; then
    cp "$FOUND_RPM" "./builds/${PKG_NAME}/"
    echo "Package created: ./builds/${PKG_NAME}/$(basename "$FOUND_RPM")"
else
    echo "Error: Could not find built RPM package"
    exit 1
fi