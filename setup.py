from setuptools import setup, find_namespace_packages
from src.version import __version__
import os

# All paths for data_files must be relative to this setup.py file.
fan_profiles_source_dir = 'share/ryzen-master-commander/fan_profiles'
tdp_profiles_source_dir = 'share/ryzen-master-commander/tdp_profiles'

data_files = [
    ('share/applications', ['share/applications/ryzen-master-commander.desktop']),
    (fan_profiles_source_dir, 
     [os.path.join(fan_profiles_source_dir, f) for f in os.listdir(fan_profiles_source_dir) if os.path.isfile(os.path.join(fan_profiles_source_dir, f))]),
    (tdp_profiles_source_dir, 
     [os.path.join(tdp_profiles_source_dir, f) for f in os.listdir(tdp_profiles_source_dir) if os.path.isfile(os.path.join(tdp_profiles_source_dir, f))]),
    ('bin', ['bin/ryzen-master-commander-helper']),
    ('share/polkit-1/actions', ['polkit/com.merrythieves.ryzenadj.policy']),
]

# Add icon files using relative paths
for size in ['16x16', '32x32', '64x64', '128x128']:
    icon_source_file_rel = os.path.join('share/icons/hicolor', size, 'apps', 'ryzen-master-commander.png')
    icon_target_dir = os.path.join('share/icons/hicolor', size, 'apps')
    if os.path.isfile(icon_source_file_rel):
        data_files.append((icon_target_dir, [icon_source_file_rel]))

setup(
    version=__version__,
    name="ryzen-master-commander",
    author="sam1am",
    author_email="noreply@merrythieves.com",
    description="TDP and fan control for AMD Ryzen processors",
    url="https://github.com/sam1am/Ryzen-Master-Commander",
    # package_dir={"": "src"},  # Tell setuptools packages are under src
    # packages=find_namespace_packages(where="src"),  # Find all packages under src
    packages=["src", "src.app"],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    license_files=('LICENSE',),
    install_requires=[
        "PyQt6",
        "pyqtgraph",
        "numpy",
        "Pillow",
        "pystray",
    ],
    python_requires=">=3.8",
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'ryzen-master-commander=src.main:main',
        ],
    },
)