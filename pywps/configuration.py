##################################################################
# Copyright 2018 Open Source Geospatial Foundation and others    #
# licensed under MIT, Please consult LICENSE.txt for details     #
##################################################################

"""
Reads the PyWPS configuration file
"""

import logging
import sys
import os
import tempfile
import pywps
import configparser

__author__ = "Calin Ciociu"

RAW_OPTIONS = [('logging', 'format'), ]

CONFIG = None
LOGGER = logging.getLogger("PYWPS")


def get_config_value(section, option):
    """Get desired value from  configuration files

    :param section: section in configuration files
    :type section: string
    :param option: option in the section
    :type option: string
    :returns: value found in the configuration file
    """

    if not CONFIG:
        load_configuration()

    value = ''

    if CONFIG.has_section(section):
        if CONFIG.has_option(section, option):
            raw = (section, option) in RAW_OPTIONS
            value = CONFIG.get(section, option, raw=raw)

            # Convert Boolean string to real Boolean values
            if value.lower() == "false":
                value = False
            elif value.lower() == "true":
                value = True

    return value


def load_configuration(cfgfiles=None):
    """Load PyWPS configuration from configuration files.
    The later configuration file in the array overwrites configuration
    from the first.

    :param cfgfiles: list of configuration files
    """

    global CONFIG

    LOGGER.info('loading configuration')
    CONFIG = configparser.ConfigParser(os.environ)

    LOGGER.debug('setting default values')
    CONFIG.add_section('server')
    CONFIG.set('server', 'encoding', 'utf-8')
    CONFIG.set('server', 'language', 'en-US')
    CONFIG.set('server', 'url', 'http://localhost/wps')
    CONFIG.set('server', 'maxprocesses', '30')
    CONFIG.set('server', 'maxsingleinputsize', '1mb')
    CONFIG.set('server', 'maxrequestsize', '3mb')
    CONFIG.set('server', 'temp_path', tempfile.gettempdir())
    CONFIG.set('server', 'processes', '')
    outputpath = tempfile.gettempdir()
    CONFIG.set('server', 'outputurl', 'file://{}'.format(outputpath))
    CONFIG.set('server', 'outputpath', outputpath)
    # list of allowed input paths (file url input) seperated by ':'
    CONFIG.set('server', 'allowedinputpaths', '')
    CONFIG.set('server', 'workdir', tempfile.gettempdir())
    CONFIG.set('server', 'parallelprocesses', '2')
    # If this flag is enabled it will set the HOME environment
    # for each process to its current workdir (a temp folder).
    CONFIG.set('server', 'sethomedir', 'false')
    # If this flag is enabled PyWPS will remove the process temporary workdir
    # after process has finished.
    CONFIG.set('server', 'cleantempdir', 'true')
    CONFIG.set('server', 'storagetype', 'file')

    CONFIG.add_section('processing')
    CONFIG.set('processing', 'mode', 'default')
    CONFIG.set('processing', 'path', os.path.dirname(os.path.realpath(sys.argv[0])))

    CONFIG.add_section('logging')
    CONFIG.set('logging', 'file', '')
    CONFIG.set('logging', 'level', 'WARNING')
    CONFIG.set('logging', 'database', 'sqlite:///pywps-logs.sqlite')
    CONFIG.set('logging', 'db_echo', 'false')
    # CONFIG.set('logging', 'prefix', 'pywps_')
    CONFIG.set('logging', 'format', '%(asctime)s] [%(levelname)s] file=%(pathname)s line=%(lineno)s module=%(module)s function=%(funcName)s %(message)s')  # noqa

    CONFIG.add_section('metadata:main')
    CONFIG.set('metadata:main', 'identification_title', 'PyWPS Processing Service')
    CONFIG.set('metadata:main', 'identification_abstract', 'PyWPS is an implementation of the Web Processing Service standard from the Open Geospatial Consortium. PyWPS is written in Python.')  # noqa
    CONFIG.set('metadata:main', 'identification_keywords', 'PyWPS,WPS,OGC,processing')
    CONFIG.set('metadata:main', 'identification_keywords_type', 'theme')
    CONFIG.set('metadata:main', 'identification_fees', 'NONE')
    CONFIG.set('metadata:main', 'identification_accessconstraints', 'NONE')
    CONFIG.set('metadata:main', 'provider_name', 'Organization Name')
    CONFIG.set('metadata:main', 'provider_url', 'https://pywps.org/')
    CONFIG.set('metadata:main', 'contact_name', 'Lastname, Firstname')
    CONFIG.set('metadata:main', 'contact_position', 'Position Title')
    CONFIG.set('metadata:main', 'contact_address', 'Mailing Address')
    CONFIG.set('metadata:main', 'contact_city', 'City')
    CONFIG.set('metadata:main', 'contact_stateorprovince', 'Administrative Area')
    CONFIG.set('metadata:main', 'contact_postalcode', 'Zip or Postal Code')
    CONFIG.set('metadata:main', 'contact_country', 'Country')
    CONFIG.set('metadata:main', 'contact_phone', '+xx-xxx-xxx-xxxx')
    CONFIG.set('metadata:main', 'contact_fax', '+xx-xxx-xxx-xxxx')
    CONFIG.set('metadata:main', 'contact_email', 'Email Address')
    CONFIG.set('metadata:main', 'contact_url', 'Contact URL')
    CONFIG.set('metadata:main', 'contact_hours', 'Hours of Service')
    CONFIG.set('metadata:main', 'contact_instructions', 'During hours of service.  Off on weekends.')
    CONFIG.set('metadata:main', 'contact_role', 'pointOfContact')

    CONFIG.add_section('grass')
    CONFIG.set('grass', 'gisbase', '')

    CONFIG.add_section("jobqueue")
    CONFIG.set("jobqueue", "pause", "30")

    CONFIG.add_section('s3')
    CONFIG.set('s3', 'bucket', '')
    CONFIG.set('s3', 'prefix', '')
    CONFIG.set('s3', 'public', 'false')
    CONFIG.set('s3', 'encrypt', 'false')
    CONFIG.set('s3', 'region', '')

    config_files = _get_default_config_files_location()

    if cfgfiles:
        config_files.extend(cfgfiles)

    if 'PYWPS_CFG' in os.environ:
        config_files.append(os.environ['PYWPS_CFG'])

    loaded_files = CONFIG.read(config_files, encoding='utf-8')
    if loaded_files:
        LOGGER.info('Configuration file(s) {} loaded'.format(loaded_files))
    else:
        LOGGER.info('No configuration files loaded. Using default values')

    _check_config()


def _check_config():
    """Check some configuration values
    """
    global CONFIG

    def checkdir(confid):

        confvalue = get_config_value('server', confid)

        if not os.path.isdir(confvalue):
            LOGGER.warning('server->{} configuration value {} is not directory'.format(confid, confvalue))

        if not os.path.isabs(confvalue):
            LOGGER.warning('server->{} configuration value {} is not absolute path, making it absolute to {}'.format(
                           confid, confvalue, os.path.abspath(confvalue)))
            CONFIG.set('server', confid, os.path.abspath(confvalue))

    [checkdir(n) for n in ['workdir', 'outputpath']]


def _get_default_config_files_location():
    """Get the locations of the standard configuration files. These are
        1. `PYWPS_INSTALLATION/etc/pywps.cfg`
        2. `/etc/pywps.cfg`
        3. `$HOME/.pywps.cfg`
    :returns: configuration files
    :rtype: list of strings
    """
    LOGGER.debug('trying to estimate the default location')
    cfgfiles = [os.path.join(pywps.__path__[0], "etc", "pywps.cfg"), "/etc/pywps.cfg"]
    if 'HOME' in os.environ:
        cfgfiles.append(os.path.join(os.environ['HOME'], ".pywps.cfg"))
    return cfgfiles


def get_size_mb(mbsize):
    """Get real size of given object in Mb.

    """

    size = mbsize.lower()

    import re

    units = re.compile("[gmkb].*")
    newsize = float(re.sub(units, '', size))

    if size.find("g") > -1:
        newsize *= 1024
    elif size.find("m") > -1:
        newsize *= 1
    elif size.find("k") > -1:
        newsize /= 1024
    else:
        newsize *= 1
    LOGGER.debug('Calculated real size of {} is {}'.format(mbsize, newsize))
    return newsize
