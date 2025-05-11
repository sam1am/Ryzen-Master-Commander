# Read in the version from the version file
VERSION=$(cat version.txt)
echo "Building Ryzen Master Commander version $VERSION"
rm ./builds/ryzen-master-commander/ryzen-master-commander-$VERSION.tar.gz
rm ./builds/ryzen-master-commander/ryzen-master-commander-$VERSION-1-any.pkg.tar.zst

cd ~/github/Ryzen-Master-Commander
tar -czf builds/ryzen-master-commander/ryzen-master-commander-$VERSION.tar.gz --exclude='.git' --exclude='builds' .



cd builds/ryzen-master-commander
# modify the PKGBUILD pkgver=1.0.6 line to the version variable
sed -i "s/pkgver=.*/pkgver=$VERSION/" PKGBUILD
# wait for the user to press enter
read -p "Press enter to continue"
rm -rf pkg src
makepkg -sf
sudo pacman -R ryzen-master-commander
sudo pacman -U ryzen-master-commander-$VERSION-1-any.pkg.tar.zst
# sudo pacman -U ryzen-master-commander-1.0.6.tar.gz