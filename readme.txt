weewx-mate

This is a driver for weewx that collects data from MATE3 solar controllers.

How to install this extension

0) install weewx

http://weewx.com/docs.html

1) download the driver

wget -O weewx-mate.zip https://github.com/matthewwall/weewx-mate/archive/master.zip

2) install the driver

wee_extension --install weewx-mate.zip

3) configure the driver

wee_config --reconfigure

4) start weewx

sudo /etc/init.d/weewx start
