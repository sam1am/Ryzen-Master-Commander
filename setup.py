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
    ('bin', ['bin/ryzen-master-commander',
             'bin/ryzen-master-commander-helper']),
    ('share/polkit-1/actions', ['polkit/com.merrythieves.ryzenadj.policy']),
]

# Add icon files using relative paths
for size in ['16x16', '32x32', '64x64', '128x128']:
    # Source path relative to setup.py
    icon_source_file_rel = os.path.join('share/icons/hicolor', size, 'apps', 'ryzen-master-commander.png')
    # Target installation directory
    icon_target_dir = os.path.join('share/icons/hicolor', size, 'apps')

    # Check existence of the *source* file using its relative path
    if os.path.isfile(icon_source_file_rel):
        data_files.append((icon_target_dir, [icon_source_file_rel]))
    # else:
    #     print(f"Warning: Icon file not found at {icon_source_file_rel}")


setup(
    name="ryzen-master-commander",
    version="1.0.3", # <-- INCREMENT VERSION AGAIN!
    author="sam1am",
    author_email="noreply@merrythieves.com",
    description="TDP and fan control for AMD Ryzen processors",
    url="https://github.com/sam1am/Ryzen-Master-Commander",
    packages=['ryzen_master_commander', 'ryzen_master_commander.app'],
    include_package_data=True, # If you have a MANIFEST.in, this is useful. Otherwise, data_files is explicit.
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Consider SPDX format later
        "Operating System :: POSIX :: Linux",
    ],
    license_files=('LICENSE',), # Add this to specify the license file
    install_requires=[
        "PyQt5",
        "pyqtgraph",
        "numpy",
        "Pillow",
        "pystray",
    ],
    python_requires=">=3.8", # Python 3.6 is EOL. Consider a more recent minimum.
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'ryzen-master-commander=ryzen_master_commander.main:main',
        ],
    },
)