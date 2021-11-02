openpilot tools
============

SSH
============

Connect to your comma device using [SSH](ssh/README.md)


System requirements
============

openpilot is developed and tested on **Ubuntu 20.04**, which is the primary development target aside from the [supported embdedded hardware](https://github.com/commaai/openpilot#running-on-pc). We also have a CI test to verify that openpilot builds on macOS, but the tools are untested. For the best experience, stick to Ubuntu 20.04, otherwise openpilot and the tools should work with minimal to no modifications on macOS and other Linux systems.

Setup your PC
============
1. Clone openpilot into your home directory:
``` bash
cd ~
git clone --recurse-submodules https://github.com/commaai/openpilot.git
```

2. Run the setup script:

Ubuntu 20.04 LTS:
``` bash
openpilot/tools/ubuntu_setup.sh
```
MacOS:
``` bash
openpilot/tools/mac_setup.sh
```

3. Build openpilot by running SCons in the root of the openpilot directory
``` bash
cd openpilot && scons -j$(nproc)
```

4. Try out some tools!

NOTE: you can always run `update_requirements.sh` to pull in new python dependencies.

Windows
------------

Neither openpilot nor any of the tools are developed or tested on Windows, but the [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/about) should get Windows users a similiar experience to Ubuntu. [WSL 2](https://docs.microsoft.com/en-us/windows/wsl/compare-versions) specifically has been reported by several users to be a seamless experience.

Follow [these instructions](https://docs.microsoft.com/en-us/windows/wsl/install) to setup the WSL and install the `Ubuntu-20.04` distribution. Once your Ubuntu WSL environment is setup, follow the Linux setup instructions to finish setting up your environment.

Tools
============

[Plot logs](plotjuggler)
-------------

Easily plot openpilot logs with [PlotJuggler](https://github.com/facontidavide/PlotJuggler), an open source tool for visualizing time series data.


[Run openpilot in a simulator](sim)
-------------

Test openpilots performance in a simulated environment. The [CARLA simulator](https://github.com/carla-simulator/carla) allows you to set a variety of features like:
* Weather
* Environment physics
* Cars
* Traffic and pedestrians


[Replay a drive](replay)
-------------

Review video and log data from routes and stream CAN messages to your device.


[Debug car controls](joystick)
-------------

Use a joystick to control your car.


Welcomed contributions
=============

* Documentation: code comments, better tutorials, etc
* Support for platforms other than Ubuntu 20.04
* Performance improvements
* More tools: anything that you think might be helpful to others.

![Imgur](https://i.imgur.com/IdfBgwK.jpg)
