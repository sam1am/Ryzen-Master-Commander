# Set up development environment
make dev-setup

# Run development version of the app
make dev-run

# Check code quality
make lint

# Build all packages
make all

# Build and install just the Arch package 
make install-arch

# Clean all build artifacts
make clean

# Prepare a new release
make bump-version
make release