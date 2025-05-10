cd ~/github/Ryzen-Master-Commander
tar -czf builds/ryzen-master-commander/ryzen-master-commander-1.0.3.tar.gz --exclude='.git' --exclude='builds' .

cd builds/ryzen-master-commander
rm -rf pkg src
makepkg -sf
sudo pacman -R ryzen-master-commander
# sudo pacman -U ryzen-master-commander-1.0.0-1-any.pkg.tar.zst