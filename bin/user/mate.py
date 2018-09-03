#!/usr/bin/python
# Copyright 2018 Matthew Wall
#
# Driver for MATE3 solar controller.
#
# Use http GET request to the Dev_status.cgi

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
    ('grid_power',  'REAL'), # Watt - instantaneous
    ('grid_energy', 'REAL'), # kWh - delta since last
]

weewx.units.obs_group_dict['grid_power'] = 'group_power' # watt
weewx.units.obs_group_dict['grid_energy'] = 'group_energy' # watt-hour
try:
    # weewx prior to 3.7.0.  for 3.7.0+ this goes in the weewx config file
    weewx.accum.extract_dict['grid_energy'] = weewx.accum.Accum.sum_extract
except AttributeError:
    pass


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

    DEFAULT_MAP = {
        # global
        'system_battery_voltage': 'Sys_Batt_V.0',
        # Dev=FX
        'inverter_current': 'Inv_I.*',
        'charger_current': 'Chg_I.*',
        'buy_current': 'Buy_I.*',
        'sell_current': 'Sell_I.*',
        'VAC_in': 'voltage_in.*',
        'VAC_out': 'voltage_out.*',
        'battery_voltage': 'Batt_V.*',
        # Dev=CC
        'output_current': 'Out_I.*',
        'input_current': 'In_I.*',
        'battery_voltage': 'Batt_V.*',
        'input_voltage': 'In_V.*',
        'output_energy': 'Out_kWh.*',
        'output_capacity': 'Out_AH.*',
        # Dev=FNDC
        'shunt_a_current': 'Shunt_A_I.*',
        'shunt_a_capacity': 'Shunt_A_AH.*',
        'shunt_a_energy': 'Shunt_A_kWh.*',
        'shunt_b_current': 'Shunt_B_I.*',
        'shunt_b_capacity': 'Shunt_B_AH.*',
        'shunt_b_energy': 'Shunt_B_kWh.*',
        'state_of_charge': 'SOC.*',
        'state_of_charge_min': 'Min_SOC.*',
        'days_since_full': 'Days_since_full.*',
        'input_capacity_today': 'In_AH_today.*',
        'output_capacity_today': 'Out_AH_today.*',
        'input_energy_today': 'In_kWh_today.*',
        'output_energy_today': 'Out_kWh_today.*',
        'net_capacity': 'Net_CFC_AH.*',
        'net_energy': 'Net_CFC_kWh.*',
        'battery_voltage': 'Batt_V.*',
        'battery_temperature': 'Batt_temp.*',
        }

    def __init__(self, **stn_dict):
        loginf('driver version is %s' % DRIVER_VERSION)
        host = None
        try:
            host = stn_dict['host']
        except KeyError, e:
            raise Exception("unspecified parameter %s" % e)
        loginf('host is %s' % host)
        self._model = stn_dict.get('model', 'MATE3')
        self.max_tries = int(stn_dict.get('max_tries', 5))
        self.retry_wait = int(stn_dict.get('retry_wait', 30))
        self._sensor_map = stn_dict.get('sensor_map', MATEDriver.DEFAULT_MAP)
        loginf('sensor map is %s' % self._sensor_map)
        self._poll_interval = int(stn_dict.get('poll_interval', 30))
        if self._poll_interval < 30:
            raise Exception('poll_interval must be 30 seconds or greater')
        loginf('poll interval is %s' % self._poll_interval)
        self.last_total = dict()
        self._mate = Mate(host)

    def closePort(self):
        self._mate = None

    @property
    def hardware_name(self):
        return self._model

    def genLoopPackets(self):
        ntries = 0
        while ntries < self.max_tries:
            ntries += 1
            try:
                data = self._mate.get_data()
                logdbg("raw data: %s" % data)
                sensors = self.raw_to_sensors(data)
                logdbg("sensors: %s" % sensors)
                packet = self.sensors_to_fields(sensors, self._sensor_map)
                logdbg("packet: %s" % packet)
                ntries = 0
                if packet:
                    yield packet
                time.sleep(self._poll_interval)
            except IOError, e:
                logerr("Failed attempt % of %d to get LOOP data: %s" %
                       (ntries, self.max_tries, e))
                logdbg("Waiting %d seconds before retry" % self.retry_wait)
                time.sleep(self.retry_wait)
        else:
            msg = "Max retries (%d) exceeded for LOOP data" % self.max_tries
            logerr(msg)
            raise weewx.RetriesExceeded(msg)

    def raw_to_sensors(self, data):
        # extract the numeric values from raw data
        pkt = dict()
        if 'devstatus' not in data:
            return pkt
        if 'Sys_Time' in data['devstatus']:
            pkt['sys_time'] = data['devstatus']['Sys_Time']
        if 'Sys_Bat_V' in data['devstatus']:
            pkt['sys_battery'] = data['devstatus']['Sys_Batt_V']
        for portdata in data['devstatus']['ports']:
            port = portdata['Port']
            dev = portdata.get('Dev')
            for k in portdata:
                if k not in ['Port', 'Dev']:
                    try:
                        label = '%s.%s' % (port, k)
                        pkt[label] = float(portdata[k])
                    except ValueError, e:
                        logdbg("cannot get float for %s=%s:%s" % (label, k, e))
        return pkt

    @staticmethod
    def sensors_to_fields(pkt, sensor_map):
        # map sensor values to database fields
        if sensor_map is None:
            return pkt
        packet = dict()
        for n in sensor_map:
            label = MATEDriver._find_match(sensor_map[n], pkt.keys())
            if label:
                packet[n] = pkt.get(label)
        if packet:
            packet['dateTime'] = int(time.time() + 0.5)
            packet['usUnits'] = weewx.US        
        return packet

    @staticmethod
    def _find_match(pattern, keylist):
        # find the first key in pkt that matches the specified pattern.
        # the general form of a pattern is:
        #   <observation_name>.<sensor_id>
        # do glob-style matching.
        if pattern in keylist:
            return pattern
        match = None
        pparts = pattern.split('.')
        if len(pparts) == 2:
            for k in keylist:
                kparts = k.split('.')
                if (len(kparts) == 2 and
                    MATEDriver._part_match(pparts[0], kparts[0]) and
                    MATEDriver._part_match(pparts[1], kparts[1])):
                    match = k
                    break
                elif pparts[0] == k:
                    match = k
                    break
        return match

    @staticmethod
    def _part_match(pattern, value):
        # use glob matching for parts of the tuple
        matches = fnmatch.filter([value], pattern)
        return True if matches else False


class MATE:

    def __init__(self, host):
        self.host = host

    def get_data(self):
        url = 'http://%s/Dev_status.cgi?&Port=0' % self.host
        req = urllib2.Request(url=url, data=params, headers=headers)
        resp = urllib2.urlopen(req).read(65535)
        resp_obj = json.loads(resp)
        logdbg("resp_obj: %s" % resp_obj)
        return resp_obj


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
    parser.add_option('--host', dest='host', metavar='HOST',
                      help='hostname or IP address of the device',
                      default='192.168.0.2')

    (options, args) = parser.parse_args()

    if options.version:
        print "vedirect driver version %s" % DRIVER_VERSION
        exit(1)

    if options.debug:
        syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_DEBUG))

    s = MATE(options.host)
    while True:
        data = s.get_data()
        print "data:", data
        time.sleep(1)
