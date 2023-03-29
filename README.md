# install-omnetpp-inet-and-veins-on-ubuntu
Install all folder above, include: omnetpp-6.0.1, inet4.4, veins-veins-5.2.
# Installing OMNeT++ *
## Installing the prerequisite packets
> $ sudo apt install -f

> $ sudo apt update

> $ sudo apt-get install build-essential gcc g++ bison flex perl python python3 qt5-default libqt5opengl5-dev tcl-dev tk-dev libxml2-dev zlib1g-dev default-jre doxygen graphviz libwebkitgtk-1.0

> $ sudo apt-get install openscenegraph-plugin-osgearth libosgearth-dev

## Add environment variable
> $cd omnetpp-6.0.1

> $ . setenv 

> $ gedit ~/.bashrc

### Add the path: export PATH=$PATH:/home/user/Downloads/omnetpp-5.4.1/bin

> $ sudo -s

> $ ./configure

> $ make
# Add INET and Veins into OMNeT++
