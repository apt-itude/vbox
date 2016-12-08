"""Manages VirtualBox VMs"""
# PYTHON_ARGCOMPLETE_OK

from __future__ import print_function

import argparse
import textwrap

import vbox.config
import vbox.error
import vbox.json_file
import vbox.manager


def main():
    args = _parse_args()
    try:
        args.func(args)
    except vbox.json_file.JsonFileNotFoundError as err:
        print(str(err))
        print('Run "vm add" to create a config file with a new VM definition')
    except vbox.error.Error as err:
        print(str(err))


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)

    subparsers = parser.add_subparsers()
    _add_connect_subparser(subparsers)
    _add_start_subparser(subparsers)
    _add_stop_subparser(subparsers)
    _add_add_subparser(subparsers)
    _add_remove_subparser(subparsers)
    _add_select_subparser(subparsers)
    _add_list_subparser(subparsers)
    _add_current_subparser(subparsers)

    _try_enabling_autocomplete(parser)

    return parser.parse_args()


def _try_enabling_autocomplete(parser):
    try:
        import argcomplete
    except ImportError:
        pass
    else:
        argcomplete.autocomplete(parser)


def _add_connect_subparser(subparsers):
    parser = subparsers.add_parser(
        'connect',
        help='Connects to a VM via SSH (starts first if not running)'
    )
    parser.add_argument(
        'name',
        nargs='?',
        help='name of VM'
    )
    parser.add_argument(
        '-a', '--address',
        help='address of VM'
    )
    parser.set_defaults(func=_start_and_connect)


def _start_and_connect(args):
    manager = vbox.manager.VMManager(name=args.name)
    manager.start_and_connect(address=args.address)


def _add_start_subparser(subparsers):
    parser = subparsers.add_parser(
        'start',
        help='Brings up a VM'
    )
    parser.add_argument(
        'name',
        nargs='?',
        help='name of VM'
    )
    parser.set_defaults(func=_start)


def _start(args):
    manager = vbox.manager.VMManager(name=args.name)
    manager.start()


def _add_stop_subparser(subparsers):
    parser = subparsers.add_parser(
        'stop',
        help='Shuts down a VM'
    )
    parser.add_argument(
        'name',
        nargs='?',
        help='name of VM'
    )
    parser.set_defaults(func=_stop)


def _stop(args):
    manager = vbox.manager.VMManager(name=args.name)
    manager.stop()


def _add_add_subparser(subparsers):
    parser = subparsers.add_parser(
        'add',
        help='Adds a new VM definition to the config'
    )
    parser.add_argument(
        'name',
        help='name of VM'
    )
    parser.add_argument(
        'address',
        help='address of VM'
    )
    parser.set_defaults(func=_add)


def _add(args):
    config = vbox.config.Config()
    try:
        config.add_or_update_vm(args.name, args.address)
    except vbox.json_file.JsonFileNotFoundError:
        config.create(args.name, args.address)


def _add_remove_subparser(subparsers):
    parser = subparsers.add_parser(
        'remove',
        help='Removes a VM definition from the config'
    )
    parser.add_argument(
        'name',
        help='name of VM'
    )
    parser.set_defaults(func=_remove)


def _remove(args):
    config = vbox.config.Config()
    config.remove_vm(args.name)


def _add_select_subparser(subparsers):
    parser = subparsers.add_parser(
        'select',
        help='Sets the given VM as current in the config'
    )
    parser.add_argument(
        'name',
        help='name of VM'
    )
    parser.set_defaults(func=_select)


def _select(args):
    config = vbox.config.Config()
    config.set_current_vm(args.name)


def _add_list_subparser(subparsers):
    parser = subparsers.add_parser(
        'list',
        help='Lists all currently configured VMs'
    )
    _add_verbose_flag(parser)
    parser.set_defaults(func=_list)


def _add_verbose_flag(parser):
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='displays VM details'
    )


def _list(args):
    config = vbox.config.Config()
    for vm_config in config.get_vms():
        _print_vm_info(vm_config, verbose=args.verbose)


def _print_vm_info(vm_config, verbose=False):
    name = vm_config['name']
    address = vm_config['address']

    manager = vbox.manager.VMManager(name=name)
    state = manager.get_state()

    if verbose:
        print(textwrap.dedent("""
            {name}:
                Address: {address}
                State:   {state}
        """).lstrip().format(
            name=name,
            address=address,
            state=state)
        )
    else:
        print(name)


def _add_current_subparser(subparsers):
    parser = subparsers.add_parser(
        'current',
        help='Displays the current VM'
    )
    _add_verbose_flag(parser)
    parser.set_defaults(func=_display_current)


def _display_current(args):
    config = vbox.config.Config()
    _print_vm_info(config.get_current_vm(), verbose=args.verbose)


if __name__ == '__main__':
    main()
