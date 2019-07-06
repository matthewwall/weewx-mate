#!/usr/bin/python
# Copyright 2018 Matthew Wall
#
# Driver for MATE3 solar controller.
#
# Use http GET request to the Dev_status.cgi
#
# The MATE3 is a hub for one or more devices.  If you query it with Port=0 you
# will see the output from all attached devices.  A typical configuration will
# have one weewx instance for each device, and thus one database for each
# device.
#
# The following devices are recognized:
#  GS - ?
#  FX - inverter
#  CC - charge controller
#  FNDC - DC battery monitor
#
# From the 'Application Note' for OutBack FX/FXR inverter data stream:
#  http://www.outbackpower.com/downloads/documents/appnotes/m3_datalog_app_note.pdf
#
# Inverter (FX/FXR)
#
# Port Number:  Indicates the designation of the OutBack HUB port used by the
# inverter.  The addresses will be 01 to 10 and will correspond to the
# appropriate numbered port.  If the system display is connected directly to
# the inverter without a HUB, this item will read 00.
#
# Device Type:  Indicates the presence of an FX-class or FXR-class inverter.
# For the FX class, the device type is 2.  For the FXR class, the device type
# is 5.
#
# Inverter Current:  Measures the AC current the inverter is delivering to
# loads from the batteries.  The range is 00 to 99 in increments of 1 ampere.
#
# Charger Current:  Measures the AC current the inverter is taking from the AC
# input and delivering to the batteries.  The range is 00 to 99 in 1-ampere
# increments.
#
# Buy Current:  Measures AC current the inverter is taking from the AC input
# and delivering to both the batteries and output loads.  The range is 00 to
# 99 in 1-ampere increments.
#
# AC Input Voltage:  Measures the voltage at the inverter's AC input terminals.
# The range is 000 to 256 in 1-volt increments.  If value 1 of Misc is set,
# this number must be doubled.  See the definition of Miscon page 4.
#
# AC Output Voltage:  Measures the voltage at the inverter's AC output
# terminals.  The range is 000 to 256 in 1-volt increments.  If value 1 of
# Misc is set, then this number must be doubled.  See the definition of Misc
# on page 4.
#
# Sell Current:  Measures the AC current the inverter is taking from the
# batteries and delivering to the AC input.  The range is 00 to 99 in 1-ampere
# increments.
#
# Inverter Operating Modes:  Reports any of a variety of functions that can be
# performed by the inverter.  The range is 00 to 99, although not all items are
# in use.
#
# Charge controller (CC)
#
# Port Number:  Indicates the designation of the OutBack HUB port used by the
# charge controller.   The addresses will be 01 to 10 and will correspond to
# the appropriate numbered port.  If the system display is connected directly
# to the charge controller without a HUB, this item will read 00.
#
# Device Type:  Indicates the presence of an OutBack charge controller of any
# model.  This device type is always 3.
#
# Charger Current:  Measures the DC current delivered from the controller
# output to the batteries.  The range is 00 to 99 in increments of 1 ampere.
# (A separate item measures tenths of an amp.  The MX60 controller does not
# use this item.)
#
# PV Current:  Measures the DC current delivered from the PV array to the
# charge controller's input.  The range is 00 to 99 in increments of 1 ampere.
#
# PV Input Voltage:  The DC voltage as measured at the charge controller's
# input (PV) terminals.  The range is 000 to 255 in increments of 1 volt.
#
# Daily Kilowatt-Hours:  The kilowatt-hours harvested by the controller that
# day.  The range is 000 to 999, incorporating one decimal place.  For example,
# a harvest of 55.5 kilowatt-hours will be sent as '555'.  This number is reset
# to zero any time the controller undergoes its wakeup procedure, or every 24
# hours.
#
# AUX Modes:  The current operating mode for the charge controller's (example
# FM80/60) auxiliary terminals.  (See Table 14.)  The range is 00 to 99.  (The
# MX60 controller only uses the first six modes on the list.)  When the AUX
# output becomes active, add 64 to the disabled value.  Hence, values below 63
# indicate the selected AUX mode, while values above 63 also show that it is
# active. For example, a disabled vent fan would have a value 04 and an enabled
# vent fan would result in a value of 68.
#
# Fault Codes:  There are 8 individual values displayed in values ranging from
# 000 to 255.  Each value represents a different fault as shown in Table 15.
# For example, a shorted battery sensor would return a value of 32. Only
# certain values are used.
#   On MX60 controllers, this is only valid with firmware aboverevision 5.11.
#   On FLEXmax 100 and FLEXmax Extreme controllers, bit 4 and 5(values 8-16)
#     are in use.  Bit 4 represents the Fault Input Active error.  Bit 5 is
#     the Over Temperature error.)
#
# Charger Mode:  Reports the charge controller's present status in a three-
# stage charge cycle.  The range is 00 to 99, although not all items are in
# use.  Items and their corresponding modes are shown in Table 16.
#  Silent:  The controller has entered the quiescent period following a
#    charging cycle.
#  Float:  The controller is in a low constant-voltage charge, the laststage
#    of a charging cycle.
#  Bulk:  The controller is in a constant-current charge, the beginning
#    stage of a charging cycle.
#  Absorb:  The controller is in a high constant-voltage charge, the middle
#    stage of a charging cycle.
#  Equalize:  The controller is running equalization, a controlled overcharge
#    for battery maintenance.
#
# Battery Voltage:  The DC voltage as measured at the charge controller's
# battery terminals.  The range is 000 to 999, incorporating one decimal place.
# For example, a 24.8 Vdc battery voltage will be sent as '248'.
#
# Daily AH:  The daily total of amp-hours delivered to the batteries by the
# charge controller.  Range is 0000 to 2000.  The number is reset to zero at
# midnight.  This item is not valid for the MX60 controller; '9999' will be
# returned.
#
# Battery monitor (FNDC)
#
# Port Number:  Indicates the designation of the OutBack HUB port used by the
# FLEXnet DC.   The addresses will be 01 to 10 and will correspond to the
# appropriate numbered port.
#
# Device Type:  Indicates the presence of a FLEXnet DC monitor.  This device
# type is always 4.
#
# Shunt Current:  Measures the DC current delivered across
# a specified shunt.  The range is 0009 to 9999, incorporating one decimal
# place.  For example, a current of 112.3 amps will be sent as '1123'.
# Separate character strings report the status of up to three shunts (A, B,
# and C), if present).
#
# Extra Data Identifier:  This data stream reflects data that typically changes
# very slowly.  This column provides an identifier for the type of data
# appearing in the next column (Extra Data).  A total additive value from 0 to
# 63 can be determined from the Type section of Table 18.

import fnmatch
import json
import os
import syslog
import time
import urllib2

import weewx.drivers
import weewx.engine
import weewx.units

DRIVER_NAME = "MATE"
DRIVER_VERSION = "0.3"


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


# schema specifically for MATE devices.  this schema is a superset of all the
# fields that are found for each type of device that might be connected to a
# MATE hub.
schema = [
    ('dateTime',  'INTEGER NOT NULL UNIQUE PRIMARY KEY'),
    ('usUnits',   'INTEGER NOT NULL'),
    ('interval',  'INTEGER NOT NULL'),
    ('system_battery_voltage', 'REAL'),
    ('battery_voltage', 'REAL'),
    ('charger_current', 'REAL'),
    ('charger_L1_current', 'REAL'),
    ('charger_L2_current', 'REAL'),
    ('inverter_current', 'REAL'),
    ('inverter_L1_current', 'REAL'),
    ('inverter_L2_current', 'REAL'),
    ('buy_current', 'REAL'),
    ('buy_L1_current', 'REAL'),
    ('buy_L2_current', 'REAL'),
    ('sell_current', 'REAL'),
    ('sell_L1_current', 'REAL'),
    ('sell_L2_current', 'REAL'),
    ('VAC1_in', 'REAL'),
    ('VAC1_L1_in', 'REAL'),
    ('VAC1_L2_in', 'REAL'),
    ('VAC2_in', 'REAL'),
    ('VAC2_L1_in', 'REAL'),
    ('VAC2_L2_in', 'REAL'),
    ('VAC_out', 'REAL'),
    ('VAC_L1_out', 'REAL'),
    ('VAC_L2_out', 'REAL'),
    ('state_of_charge', 'REAL'),
    ('state_of_charge_min', 'REAL'),
    ('net_energy', 'REAL'),
    ('net_capacity', 'REAL'),
    ('battery_temperature', 'REAL'),
    ('days_since_full', 'REAL'),
    ('input_current', 'REAL'),
    ('input_voltage', 'REAL'),
    ('input_capacity', 'REAL'),
    ('input_capacity_today', 'REAL'),
    ('output_energy', 'REAL'),
    ('output_current', 'REAL'),
    ('output_capacity', 'REAL'),
    ('output_capacity_today', 'REAL'),
    ('shunt_a_current', 'REAL'),
    ('shunt_a_capacity', 'REAL'),
    ('shunt_a_energy', 'REAL'),
    ('shunt_b_current', 'REAL'),
    ('shunt_b_capacity', 'REAL'),
    ('shunt_b_energy', 'REAL'),
    ('shunt_c_current', 'REAL'),
    ('shunt_c_capacity', 'REAL'),
    ('shunt_c_energy', 'REAL'),
]

# associate units with each database field
for x in schema:
    if x[0] in ['dateTime', 'usUnits', 'interval']:
        continue
    elif x[0].startswith('VAC') or x[0].endswith('voltage'):
        weewx.units.obs_group_dict[x[0]] = 'group_volt'
    elif x[0].endswith('current'):
        weewx.units.obs_group_dict[x[0]] = 'group_amp'
    elif x[0].endswith('energy'):
        weewx.units.obs_group_dict[x[0]] = 'group_energy'
    elif x[0].endswith('capacity'):
        weewx.units.obs_group_dict[x[0]] = 'group_count'
    elif x[0].endswith('temperature'):
        weewx.units.obs_group_dict[x[0]] = 'group_temperature'
    else:
        weewx.units.obs_group_dict[x[0]] = 'group_count'

# distinguish deltas versus counters
#try:
    # weewx prior to 3.7.0.  for 3.7.0+ this goes in the weewx config file
#    weewx.accum.extract_dict['grid_energy'] = weewx.accum.Accum.sum_extract
#except AttributeError:
#    pass


class MATEConfigurationEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[MATE]
    # This section is for the MATE driver.

    # The hostname or IP address of the MATE
    host = 0.0.0.0

    # The port number of the device from which to capture data
    port = 1

    # The driver to use
    driver = user.mate
"""
    def prompt_for_settings(self):
        print("Specify the hostname or IP address of the MATE, for example:")
        print("mate.example.com or 192.168.0.5")
        host = self._prompt('host', '192.168.0.2')
        print("Specify the port number of the device that should be monitored")
        port = self._prompt('port', 1)
        return {'host': host, 'port': port}


class MATEDriver(weewx.drivers.AbstractDevice):

    # the map associates an observation with a database field.  each
    # observation is of the form:
    #
    #  <observation_name>.<port>
    #
    # where the port is an integer value such as 1 or 2
    # each port has a type, distinguished by Dev.  the Dev determines which
    # observations may be found.  known Dev include:
    #
    # GS, FX, CC, FNDC
    #
    # the default map matches any port.  if your installation has multiple
    # ports of the same type, and you intend to put all data into a single
    # database, then define a sensor map that distinguishes between ports.
    # you will also probably have to extend the schema, otherwise you will
    # get overlapping data from different devices.

    DEFAULT_MAP = {
        # global
        'system_battery_voltage': 'Sys_Batt_V',
        # Dev=GS
        'battery_voltage': 'Batt_V.*',
        'buy_L1_current': 'Buy_I_L1.*',
        'buy_L2_current': 'Buy_I_L2.*',
        'charger_L1_current': 'Chg_I_L1.*',
        'charger_L2_current': 'Chg_I_L2.*',
        'inverter_L1_current': 'Inv_I_L1.*',
        'inverter_L2_current': 'Inv_I_L2.*',
        'sell_L1_current': 'Sell_I_L1.*',
        'sell_L2_current': 'Sell_I_L2.*',
        'VAC1_L1_in': 'VAC1_in_L1.*',
        'VAC1_L2_in': 'VAC1_in_L2.*',
        'VAC2_L1_in': 'VAC2_in_L1.*',
        'VAC2_L2_in': 'VAC2_in_L2.*',
        'VAC_L1_out': 'VAC_out_L1.*',
        'VAC_L2_out': 'VAC_out_L2.*',
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
        'shunt_c_current': 'Shunt_C_I.*',
        'shunt_c_capacity': 'Shunt_C_AH.*',
        'shunt_c_energy': 'Shunt_C_kWh.*',
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
        except KeyError as e:
            raise Exception("unspecified parameter %s" % e)
        loginf('host is %s' % host)
        port = int(stn_dict.get('port', 1))
        loginf('port is %s' % port)
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
        self._mate = MATE(host, port)

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
            except IOError as e:
                logerr("Failed attempt %s of %s to get LOOP data: %s" %
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
        if 'Sys_Batt_V' in data['devstatus']:
            pkt['sys_battery'] = data['devstatus']['Sys_Batt_V']
        for portdata in data['devstatus']['ports']:
            port = int(portdata['Port'])
            dev = portdata.get('Dev')
            for k in portdata:
                if k in ['Port', 'Dev']:
                    continue
                try:
                    label = '%s.%s' % (k, port)
                    pkt[label] = float(portdata[k])
                except (ValueError, TypeError) as e:
                    logdbg("cannot get float for %s=%s: %s" % (label, k, e))
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

    def __init__(self, host, port=0):
        self.host = host
        self.port = port

    def get_data(self):
        url = 'http://%s/Dev_status.cgi?Port=%s' % (self.host, self.port)
        req = urllib2.Request(url=url)
        resp = urllib2.urlopen(req).read(65535)
        try:
            resp_obj = json.loads(resp)
            logdbg("resp_obj: %s" % resp_obj)
            return resp_obj
        except ValueError as e:
            logerr("cannot parse data: %s (%s)" % (e, resp))
        return dict()

# define a main entry point for basic testing of the device.  invoke this as
# follows from the weewx root dir:
#
# PYTHONPATH=bin python bin/weewx/drivers/mate.py

if __name__ == '__main__':
    import optparse
    import pprint

    usage = """%prog [options] [--debug] [--help]"""
    
    syslog.openlog('mate', syslog.LOG_PID | syslog.LOG_CONS)
    syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_INFO))
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display driver version')
    parser.add_option('--debug', dest='debug', action='store_true',
                      help='display diagnostic information while running')
    parser.add_option('--host',
                      help='hostname or IP address of the device',
                      default='192.168.0.2')
    parser.add_option('--port', type=int,
                      help='port number of the device, 0 for all devices',
                      default=0)

    (options, args) = parser.parse_args()

    if options.version:
        print("mate driver version %s" % DRIVER_VERSION)
        exit(1)

    if options.debug:
        syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_DEBUG))

    s = MATE(options.host, options.port)
    while True:
        data = s.get_data()
#        print("data: %s" % data)
        pprint.pprint(data)
        time.sleep(1)
