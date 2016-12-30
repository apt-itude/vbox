"""An interface for managing the state of, and connecting to, VMs"""

from __future__ import print_function

import re
import subprocess
import time

import vbox.config
import vbox.error


class Error(vbox.error.Error):

    """Base class for errors in manager module"""


class VMManager(object):

    """Starts, stops, and connects to a VM"""

    def __init__(self, name=None):
        """
        *name* is the name of the VM to manage. If omitted, the current VM set
        in the config will be used.
        """
        self._config = vbox.config.Config()
        self.name = (
            name if name is not None else self._config.get_current_vm()['name']
        )

    def start_and_connect(
            self,
            address=None,
            user=None,
            tries=10,
            retry_interval=5):
        """
        Powers on the VM if it is not already and then connects via SSH

        *address* is the IP address or hostname of the VM to which to connect.
        If omitted, the address associated with the VM's name in the config
        will be used.

        *user* is the username with which to connect. If omitted, the current
        user will be used.

        *tries* is the number of times to try connecting to the VM before
        timing out (default: 10)

        *retry_interval* is the number of seconds to wait before each retry
        (default: 5)
        """
        self.start()
        self.connect(
            address=address,
            user=user,
            tries=tries,
            retry_interval=retry_interval
        )

    def start(self):
        """Powers on the VM if it is not already running"""
        if self.is_running():
            print('VM "{}" is already running'.format(self.name))
        else:
            subprocess.check_call(
                ['VBoxManage', 'startvm', self.name, '--type', 'headless']
            )

    def is_running(self):
        """Returns True if the VM is currently running"""
        try:
            return self.get_state() == 'running'
        except (StateUnavailableError, VBoxManageOutputParseError):
            return False

    def get_state(self):
        """
        Returns the VM state as a string

        Raises StateUnavailableError and VBoxManageOutputParseError
        """
        try:
            vm_info = subprocess.check_output(
                ['VBoxManage', 'showvminfo', '--machinereadable', self.name]
            )
        except subprocess.CalledProcessError:
            raise StateUnavailableError(self.name)

        vm_state_match = re.search(
            r'^VMState="(.*)"$',
            vm_info,
            flags=re.MULTILINE
        )

        if vm_state_match is None:
            raise VBoxManageOutputParseError(
                'Could not state of VM {}'.format(self.name)
            )

        return vm_state_match.group(1)

    def connect(self, address=None, user=None, tries=10, retry_interval=5):
        """
        Connects to the VM via SSH

        *address* is the IP address or hostname of the VM to which to connect.
        If omitted, the address associated with the VM's name in the config
        will be used.

        *user* is the username with which to connect. If omitted, the current
        user will be used.

        *tries* is the number of times to try connecting to the VM before
        timing out (default: 10)

        *retry_interval* is the number of seconds to wait before each retry
        (default: 5)
        """
        address = (
            address if address is not None else
            self._config.get_vm(self.name)['address']
        )

        if user is not None:
            address = '{}@{}'.format(user, address)

        print('Connecting to {}'.format(address))

        success = False
        remaining_tries = tries
        while (not success) and (remaining_tries > 0):
            try:
                subprocess.check_call(['ssh', address])
            except subprocess.CalledProcessError:
                print('Failed to connect to {}; waiting...'.format(address))
                remaining_tries -= 1
                time.sleep(retry_interval)
                print('Retrying...')
            else:
                success = True

        if not success:
            raise ConnectionFailure(address, tries)

    def stop(self):
        """Shuts down the VM if it is currently running"""
        if self.is_running():
            print('Shutting down VM "{}"...'.format(self.name))
            subprocess.check_call(
                ['VBoxManage', 'controlvm', self.name, 'acpipowerbutton']
            )
        else:
            print('VM "{}" is not running'.format(self.name))

        self._wait_for_shutdown()

    def _wait_for_shutdown(self, tries=20, retry_interval=0.5):
        try:
            state = self.get_state()
        except (StateUnavailableError, VBoxManageOutputParseError):
            state = None

        remaining_tries = tries
        while (state != 'poweroff') and (remaining_tries > 0):
            time.sleep(retry_interval)

            try:
                state = self.get_state()
            except (StateUnavailableError, VBoxManageOutputParseError):
                state = None

            remaining_tries -= 1

        if state != 'poweroff':
            raise ShutdownFailure(self.name)

        print('VM "{}" has been successfully shut down'.format(self.name))

    def reboot(self):
        """Reboots the VM if it is currently running"""
        self.stop()
        self.start()


class StateUnavailableError(Error):

    """Error getting the state of a VM"""

    def __init__(self, name):
        super(StateUnavailableError, self).__init__(
            'Failed to get state for VM {}'.format(name)
        )


class VBoxManageOutputParseError(Error):

    """Error parsing output from a VBoxManage command"""


class ConnectionFailure(Error):

    """Failed to connect to VM"""

    def __init__(self, address, tries):
        super(ConnectionFailure, self).__init__(
            'Failed to connect to {} after {} tries'.format(address, tries)
        )


class ShutdownFailure(Error):

    """Failed to shut down the VM"""

    def __init__(self, name):
        super(ShutdownFailure, self).__init__(
            'Failed to shut down VM {}'.format(name)
        )
