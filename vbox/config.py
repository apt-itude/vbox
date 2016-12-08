"""An interface to the configuration file"""

from __future__ import print_function

import os

import vbox.json_file
import vbox.error


class Error(vbox.error.Error):

    """Base class for errors in config module"""


_HOME_DIR = os.path.expanduser('~')
CONFIG_FILE_PATH = os.path.join(_HOME_DIR, '.vbox', 'config.json')


class Config(object):

    """Gets and sets configuration data"""

    def __init__(self, path=CONFIG_FILE_PATH):
        """
        *path* is an optional path to the config file (defaults to CONFIG_FILE_PATH)
        """
        self.json_file = vbox.json_file.JsonFile(path, validate=_validate, indent=2)

    def create(self, name, address):
        """
        Creates the config file, adds a single VM definition with the given *name* and *address*,
        and sets the given *name* as the current VM
        """
        self.json_file.write({
            'vms': [
                {
                    'name': name,
                    'address': address
                }
            ],
            'current': name
        })
        print('Created config file')

    def add_or_update_vm(self, name, address):
        """
        If a VM exists in the config with the given *name*, updates it with the given *address*.
        Otherwise, creates a new entry with the given *name* and *address*.

        Raises json_file.JsonFileNotFoundError and json_file.InvalidDataError
        """
        with self.json_file.modify() as config:
            try:
                vm_config = _find_vm_config(config, name)
            except VMNotFoundError:
                vm_config = {
                    'name': name
                }
                config['vms'].append(vm_config)

                print('Added VM {} to the config'.format(name))

            vm_config['address'] = address

            print('Set address of VM {} to {}'.format(name, address))

    def remove_vm(self, name):
        """
        Removes the VM with the given *name* from the config

        Raises json_file.JsonFileNotFoundError and json_file.InvalidDataError
        """
        with self.json_file.modify() as config:
            config['vms'] = [vm_config for vm_config in config['vms'] if vm_config['name'] != name]

        print('Removed VM {} from the config'.format(name))

    def get_vm(self, name):
        """
        Returns a dictionary with the config for the VM with the given *name*

        Raises json_file.JsonFileNotFoundError, json_file.InvalidDataError, and VMNotFoundError
        """
        config = self.json_file.read()
        return _find_vm_config(config, name)

    def get_vms(self):
        """
        Returns a list of the VM configurations

        Raises json_file.JsonFileNotFoundError and json_file.InvalidDataError
        """
        return self.json_file.read()['vms']

    def set_current_vm(self, name):
        """
        Sets the current VM in the config to the given *name*

        Raises json_file.JsonFileNotFoundError and json_file.InvalidDataError
        """
        with self.json_file.modify() as config:
            config['current'] = name

        print('Selected VM {} as current'.format(name))

    def get_current_vm(self):
        """
        Returns a dictionary with the config for the current VM

        Raises json_file.JsonFileNotFoundError, json_file.InvalidDataError, and VMNotFoundError
        """
        config = self.json_file.read()
        current_vm_name = config['current']
        return _find_vm_config(config, current_vm_name)


def _validate(config):
    if 'vms' not in config:
        raise vbox.json_file.InvalidDataError('Missing list of VMs')

    try:
        current_vm_name = config['current']
    except KeyError:
        raise vbox.json_file.InvalidDataError('Missing current VM')

    try:
        _find_vm_config(config, current_vm_name)
    except VMNotFoundError:
        raise vbox.json_file.InvalidDataError(
            'Current VM {} does not exist in config'.format(current_vm_name)
        )


def _find_vm_config(config, name):
    for vm_config in config['vms']:
        if vm_config['name'] == name:
            return vm_config

    raise VMNotFoundError(name)


class VMNotFoundError(Error):

    """VM does not exist in config"""

    def __init__(self, name):
        super(VMNotFoundError, self).__init__('VM {} does not exist in config'.format(name))
