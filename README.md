Python3 Bluetooth device implementation
=======================================

This is totally incomplete and experimental work!

*Python 3* and *Linux* only.

I'm testing mostly with Python 3.5.2 on Ubuntu Xenial on an ARM Chromebook,
and less often on a Raspberry Pi 3.

Please do not expect:
* Accurate documentation
* Support for other platforms
* Any particular function working
* A proper user-facing API
* Any technical support from me


Current state 2017/09/17
------------------------

`gatt.py` is the main GATT server implementation.

Running `gatt.py` itself runs a unit test: it will create a `GattServer`
with a few test services, then issue GATT commands to them, read from
file `gatt-cmds.hex`. Expected responses packets are checked.

Running `device.py` makes a simple device which will advertise and 
accept connections. The main interesting bit is the `start()` method
which sets the advertising data and adds a `GattServer` instance.

Note there isn't yet a proper API for making your own device, you'll
have to hack `device.py`. Lots of stuff (notifications, security, ...)
isn't implemented yet.

File `central.py` has a prototype Central implementation as a pure 
Python stack talking to the HCI interface. It currently does basic
scanning.

