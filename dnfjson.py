#! /usr/bin/env python

import argparse
import json
import dnf

status_strings = {
    dnf.callback.PKG_DOWNGRADE: 'PKG_DOWNGRADE',
    dnf.callback.PKG_DOWNGRADED: 'PKG_DOWNGRADED',
    dnf.callback.PKG_INSTALL: 'PKG_INSTALL',
    dnf.callback.PKG_OBSOLETE: 'PKG_OBSOLETE',
    dnf.callback.PKG_OBSOLETED: 'PKG_OBSOLETED',
    dnf.callback.PKG_REINSTALL: 'PKG_REINSTALL',
    dnf.callback.PKG_REINSTALLED: 'PKG_REINSTALLED',
    dnf.callback.PKG_REMOVE: 'PKG_REMOVE',
    dnf.callback.PKG_UPGRADE: 'PKG_UPGRADE',
    dnf.callback.PKG_UPGRADED: 'PKG_UPGRADED',
    dnf.callback.PKG_CLEANUP: 'PKG_CLEANUP',
    dnf.callback.PKG_VERIFY: 'PKG_VERIFY',
    dnf.callback.PKG_SCRIPTLET: 'PKG_SCRIPTLET',
    dnf.callback.TRANS_PREPARATION: 'TRANS_PREPARATION',
    dnf.callback.TRANS_POST: 'TRANS_POST',
}

class JsonProgressMeter(dnf.callback.DownloadProgress):
    def __init__(self):
        self.done_files = 0
        self.done_size = 0

    def start(self, total_files, total_size, total_drpms=0):
        self.total_files = total_files
        self.total_size = total_size
        self.done_files = 0
        self.done_size = 0

    def progress(self, payload, done):
        pass

    def end(self, payload, status, err_msg):
        self.done_files += 1
        self.done_size += int(payload.download_size)
        print(json.dumps({
            'type': 'downloading',
            'package': str(payload),
            'done_files': self.done_files,
            'total_files': self.total_files,
            'done_size': self.done_size,
            'total_size': self.total_size,
        }))

class JsonTransactionProgress(dnf.callback.TransactionProgress):
    def __init__(self):
        self.done_steps = 0

    def progress(self, package, action, ti_done, ti_total, ts_done, ts_total):
        if action not in [dnf.callback.PKG_INSTALL, dnf.callback.PKG_UPGRADED]:
            return

        if ts_done > self.done_steps:
            print(json.dumps({
                'type': 'installing',
                'package': json_package(package) if package not in [None, ''] else None,
                'action': status_strings[action],
                'done_steps': ts_done,
                'total_steps': ts_total,
                'done_size': ti_done,
                'total_size': ti_total,
            }))
            self.done_steps = ts_done

def prepare_dnf():
    base = dnf.Base()
    base.read_all_repos()
    base.fill_sack()
    return base

def json_package(pkg):
    return {
        'name': pkg.name,
        'epoch': pkg.epoch,
        'version': pkg.version,
        'release': pkg.release,
        'arch': pkg.arch,
    }

def install(packages, pretend=False):
    base = prepare_dnf()
    base.install_specs(packages)
    base.resolve()

    if pretend:
        json_pkgs = []
        for pkg in base.transaction.install_set:
            json_pkgs.append(json_package(pkg))
        print(json.dumps({
            'packages': json_pkgs,
        }))
        return

    base.download_packages(base.transaction.install_set, progress=JsonProgressMeter())
    base.do_transaction(JsonTransactionProgress())

def upgrade(packages, pretend=False):
    base = prepare_dnf()

    if len(packages) == 0:
        base.upgrade_all()
    else:
        base.upgrade(packages)
    base.resolve()

    if pretend:
        json_pkgs = []
        for pkg in base.transaction.install_set:
            json_pkgs.append(json_package(pkg))
        print(json.dumps({
            'packages': json_pkgs,
        }))
        return

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    install_group = subparsers.add_parser('install')
    install_group.add_argument('--pretend', action='store_true')
    install_group.add_argument('package', nargs='+')

    install_group = subparsers.add_parser('upgrade')
    install_group.add_argument('--pretend', action='store_true')
    install_group.add_argument('package', nargs='*')

    args = parser.parse_args()

    if not args.command:
        parser.parse_args(['--help'])
        sys.exit(0)

    if args.command == 'install':
        install(args.package, pretend=args.pretend)
        return

    if args.command == 'upgrade':
        upgrade(args.package, pretend=args.pretend)
        return

if __name__ == '__main__':
    main()
