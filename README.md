# Ryzen Master Commander

Ryzen Master Commander is a Python-based GUI application for monitoring and controlling Ryzen-based systems, with a focus on the GPD Win Mini. It provides features such as temperature and fan speed monitoring, fan control, and TDP (Thermal Design Power) settings management.

## Features

- Real-time temperature and fan speed monitoring with graphs
- Manual and automatic fan speed control
- TDP settings management with customizable profiles
- User-friendly GUI built with ttkbootstrap

## Installation

### Prerequisites

Before installing Ryzen Master Commander, ensure that you have the following dependencies installed on your system:

- Python 3.6 or higher
- TCL and Tk libraries
- `nbfc` and `ryzenadj` command-line tools

#### Installing Dependencies on Arch Linux

To install the required dependencies on Arch Linux, run the following command:

```
sudo pacman -S python tcl tk nbfc ryzenadj
```

#### Installing Dependencies on Debian-based Systems (Ubuntu, Debian, etc.)

To install the required dependencies on Debian-based systems, run the following commands:

```
sudo apt update
sudo apt install python3 python3-pip tcl tk nbfc ryzenadj
```

### Installing via pip

To install Ryzen Master Commander using pip, run the following command:

```
pip install ryzen-master-commander
```

### Installing from Source

If you want to contribute to the development of Ryzen Master Commander or prefer to install from source, follow these steps:

1. Clone the repository:

```
git clone https://github.com/yourusername/Ryzen-Master-Commander.git
```

2. Navigate to the project directory:

```
cd Ryzen-Master-Commander
```

3. Install the required Python packages:

```
pip install -r requirements.txt
```

4. Run the application:

```
python main.py
```

## Usage

To launch Ryzen Master Commander, run the following command:

```
ryzen-master-commander
```

The application will prompt you for your sudo password, which is required for controlling the fan speed and applying TDP settings.

## Contributing

Contributions to Ryzen Master Commander are welcome! If you find a bug, have a feature request, or want to contribute code, please open an issue or submit a pull request on the [GitHub repository](https://github.com/yourusername/Ryzen-Master-Commander).

## License

This project is licensed under the [Apache License 2.0](LICENSE).

## Acknowledgements

Ryzen Master Commander was developed on Arch Linux for the GPD Win Mini, but it should work on other Ryzen-based devices as well. Special thanks to the developers of the `nbfc` and `ryzenadj` tools, which make this application possible.