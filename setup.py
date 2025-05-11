from setuptools import setup, find_packages
import os

# All paths for data_files must be relative to this setup.py file.

fan_profiles_source_dir = 'share/ryzen-master-commander/fan_profiles'
tdp_profiles_source_dir = 'share/ryzen-master-commander/tdp_profiles'

data_files = [
    # Target installation directory, [list of source files relative to setup.py]
    ('share/applications', ['share/applications/ryzen-master-commander.desktop']),
    (fan_profiles_source_dir, # Target dir is same as source for these
     [os.path.join(fan_profiles_source_dir, f) for f in os.listdir(fan_profiles_source_dir) if os.path.isfile(os.path.join(fan_profiles_source_dir, f))]),
    (tdp_profiles_source_dir, # Target dir is same as source for these
     [os.path.join(tdp_profiles_source_dir, f) for f in os.listdir(tdp_profiles_source_dir) if os.path.isfile(os.path.join(tdp_profiles_source_dir, f))]),
    # REMOVED 'bin/ryzen-master-commander' from here.
    # Keep ryzen-master-commander-helper if it's a separate script not managed by entry_points
    ('bin', ['bin/ryzen-master-commander-helper']), # Assuming helper is still needed as a separate file
    ('share/polkit-1/actions', ['polkit/com.merrythieves.ryzenadj.policy']),
]

# Add icon files using relative paths
for size in ['16x16', '32x32', '64x64', '128x128']:
    icon_source_file_rel = os.path.join('share/icons/hicolor', size, 'apps', 'ryzen-master-commander.png')
    icon_target_dir = os.path.join('share/icons/hicolor', size, 'apps')
    if os.path.isfile(icon_source_file_rel):
        data_files.append((icon_target_dir, [icon_source_file_rel]))

setup(
    #get version from ./ver.txt
    version = open('version.txt').read().strip(),
    name="ryzen-master-commander",
    author="sam1am",
    author_email="noreply@merrythieves.com",
    description="TDP and fan control for AMD Ryzen processors",
    url="https://github.com/sam1am/Ryzen-Master-Commander",
    packages=['ryzen_master_commander', 'ryzen_master_commander.app'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    license_files=('LICENSE',),
    install_requires=[
        "PyQt5",
        "pyqtgraph",
        "numpy",
        "Pillow",
        "pystray",
    ],
    python_requires=">=3.8",
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'ryzen-master-commander=ryzen_master_commander.main:main', # This will create /usr/bin/ryzen-master-commander
        ],
    },
)