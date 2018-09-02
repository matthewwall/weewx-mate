#!/usr/bin/python
# Copyright 2018 Matthew Wall
#
# Driver for MATE3 solar controller.

import os
import syslog
import time

import weewx.drivers
import weewx.engine
import weewx.units

DRIVER_NAME = "MATE"
DRIVER_VERSION = "0.1"


def loader(config_dict, engine):
    return MATEDriver(**config_dict[DRIVER_NAME])

def confeditor_loader():
    return MATEConfigurationEditor()


def logmsg(dst, msg):
    syslog.syslog(dst, 'mate: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)


# schema specifically for MATE devices
schema = [
    ('dateTime',  'INTEGER NOT NULL UNIQUE PRIMARY KEY'),
    ('usUnits',   'INTEGER NOT NULL'),
    ('interval',  'INTEGER NOT NULL'),
    ('LOAD',      'REAL'), # LOAD: OFF (0) or ON (1)
    ('ERR',     'REAL'), # ERR: 0 or 1
    ('VPV',  'REAL'), # VPV (mV) module voltage
    ('PPV',    'REAL'), # PPV (W) module power
    ('I',         'REAL'), # I (mA) current
    ('IL',    'REAL'), # IL (mA) load current?
    ('V', 'REAL'), # V (mV) battery voltage
    ('CS',   'REAL'), # CS: 0=off, 2=fault, 3=bulk, 4=abs, 5=float
    ('T',         'REAL'), # T (degree_C)
    ('P',         'REAL'), # P (W)
    ('CE',        'REAL'), # CE (mAh)
    ('SOC',       'REAL'), # SOC (%)
    ('TTG',       'REAL'), # TTG (minute)
    ('alarm',     'REAL'), # Alarm
    ('relay',     'REAL'), # Relay
    ('AR',        'REAL'), # AR
    ('H1',        'REAL'), # H1 (mAh)
    ('H2',        'REAL'), # H2 (mAh)
    ('H3',        'REAL'), # H3 (mAh)
    ('H4',        'REAL'), # H4
    ('H5',        'REAL'), # H5
    ('H6',        'REAL'), # H6 (mAh)
    ('H7',        'REAL'), # H7 (mV)
    ('H8',        'REAL'), # H8 (mV)
    ('H9',        'REAL'), # H9 (s)
    ('H10',       'REAL'), # H10
    ('H11',       'REAL'), # H11
    ('H12',       'REAL'), # H12
    ('H15',       'REAL'), # H15 (mV)
    ('H16',       'REAL'), # H16 (mV)
    ('H17',       'REAL'), # H17 (0.01 kWh): accumulated daily production
    ('H18',       'REAL'), # H18 (0.01 kWh): accumulated daily production
    ('H19',       'REAL'), # H19 (0.01 kWh): accumulated daily production
    ('H20',       'REAL'), # H20 (0.01 kWh): accumulated daily production
    ('H21',       'REAL'), # H21 (W)
    ('H22',       'REAL'), # H22 (0.01 kWh)
    ('H23',       'REAL'), # H23 (W)
]

weewx.units.obs_group_dict['range'] = 'group_range'
weewx.units.obs_group_dict['range2'] = 'group_range'
weewx.units.obs_group_dict['range3'] = 'group_range'
weewx.units.USUnits['group_range'] = 'inch'
weewx.units.MetricUnits['group_range'] = 'cm'
weewx.units.MetricWXUnits['group_range'] = 'cm'


class MATEConfigurationEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[MATE]
    # This section is for the MATE driver.

    # The hostname or IP address of the MATE
    host = 0.0.0.0

    # The driver to use
    driver = user.mate
"""
    def prompt_for_settings(self):
        print "Specify the hostname or IP address of the MATE, for example:"
        print "mate.example.com or 192.168.0.5"
        host = self._prompt('host', '192.168.0.2')
        return {'host': host}


class MATEDriver(weewx.drivers.AbstractDevice):

    def __init__(self, **stn_dict):
        loginf('driver version is %s' % DRIVER_VERSION)
        self._model = stn_dict.get('model', 'MATE3')
        self._poll_interval = int(stn_dict.get('poll_interval', 1))
        loginf('poll interval is %s' % self._poll_interval)
        host = stn_dict['host']
        loginf('host is %s' % host)
        self._mate = VEDirect(host)
        self._mate.open()

    def closePort(self):
        self._mate.close()

    @property
    def hardware_name(self):
        return self._model

    def genLoopPackets(self):
        while True:
            data = self._mate.get_data()
            if data:
                logdbg("raw data: %s" % data)
                packet = self._data_to_packet(data)
                logdbg("packet: %s" % packet)
                if packet:
                    yield packet
            time.sleep(self._poll_interval)
                

    def _data_to_packet(self, data):
        # convert raw data to database fields
        pkt = dict()
        # if we actually ended up with something, then make it a weewx packet
        if pkt:
            pkt['dateTime'] = int(time.time() + 0.5)
            pkt['usUnits'] = weewx.US
        return pkt


class MATE:

    def __init__(self, host):
        self.host = host

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, _, value, traceback):
        self.close()

    def open(self):
        pass

    def close(self):
        pass


# define a main entry point for basic testing of the device.  invoke this as
# follows from the weewx root dir:
#
# PYTHONPATH=bin python bin/weewx/drivers/mate.py

if __name__ == '__main__':
    import optparse

    usage = """%prog [options] [--debug] [--help]"""
    
    syslog.openlog('vedirect', syslog.LOG_PID | syslog.LOG_CONS)
    syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_INFO))
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display driver version')
    parser.add_option('--debug', dest='debug', action='store_true',
                      help='display diagnostic information while running')
    parser.add_option('--port', dest='host', metavar='HOST',
                      help='hostname or IP address of the device',
                      default='192.168.0.2')

    (options, args) = parser.parse_args()

    if options.version:
        print "vedirect driver version %s" % DRIVER_VERSION
        exit(1)

    if options.debug:
        syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_DEBUG))

    with MATE(options.host) as s:
        while True:
            data = s.get_data()
            print "data:", data
            time.sleep(1)
