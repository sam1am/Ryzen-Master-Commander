from setuptools import setup, find_packages
import os

# Get the absolute path to the directory where setup.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define proper paths based on setup.py location
fan_profiles_path = os.path.join(BASE_DIR, 'share/ryzen-master-commander/fan_profiles')
tdp_profiles_path = os.path.join(BASE_DIR, 'share/ryzen-master-commander/tdp_profiles')

# Create data files structure properly
# Add this to your data_files list in setup.py
data_files = [
    ('share/applications', [os.path.join(BASE_DIR, 'share/applications/ryzen-master-commander.desktop')]),
    ('share/ryzen-master-commander/fan_profiles', 
     [os.path.join(fan_profiles_path, file) for file in os.listdir(fan_profiles_path) if os.path.isfile(os.path.join(fan_profiles_path, file))]),
    ('share/ryzen-master-commander/tdp_profiles', 
     [os.path.join(tdp_profiles_path, file) for file in os.listdir(tdp_profiles_path) if os.path.isfile(os.path.join(tdp_profiles_path, file))]),
    ('bin', [os.path.join(BASE_DIR, 'bin/ryzen-master-commander'), 
             os.path.join(BASE_DIR, 'bin/ryzen-master-commander-helper')]),
    # Add this line for the polkit policy
    ('share/polkit-1/actions', [os.path.join(BASE_DIR, 'polkit/com.merrythieves.ryzenadj.policy')]),
]

# Add icon files
for size in ['16x16', '32x32', '64x64', '128x128']:
    icon_dir = os.path.join(BASE_DIR, f'share/icons/hicolor/{size}/apps')
    if os.path.exists(icon_dir):
        data_files.append((f'share/icons/hicolor/{size}/apps', 
                          [os.path.join(icon_dir, 'ryzen-master-commander.png')]))

setup(
    name="ryzen-master-commander",
    version="1.0.1",
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
    install_requires=[
        "PyQt5",
        "pyqtgraph",
        "numpy",
        "Pillow",
        "pystray",
    ],
    python_requires=">=3.6",
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'ryzen-master-commander=ryzen_master_commander.main:main',
        ],
    },
)