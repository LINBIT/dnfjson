#!/usr/bin/env python3

import argparse
import json
import sys

import dnf
from dnf.cli.option_parser import OptionParser

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
    def __init__(self, total_pkgs):
        self.done_steps = 0
        self.pkg_done = {}
        self.total_pkgs = total_pkgs

    def progress(self, package, action, ti_done, ti_total, ts_done, ts_total):
        if action not in [dnf.callback.PKG_INSTALL, dnf.callback.PKG_UPGRADED]:
            return

        if package in self.pkg_done:
            return

        self.pkg_done[package] = True

        print(json.dumps({
            'type': 'installing',
            'package': json_package(package) if package not in [None, ''] else None,
            'action': status_strings[action],
            'done_pkgs': len(self.pkg_done),
            'total_pkgs': self.total_pkgs,
        }))


def prepare_dnf(args=None):
    base = dnf.Base()
    base.init_plugins()
    base.configure_plugins()
    base.conf.exclude_pkgs(args.excludepkgs if args else None)
    base.read_all_repos()

    if args and args.repofrompath:
        for label, path in args.repofrompath.items():
            this_repo = base.repos.add_new_repo(label, base.conf, baseurl=[path])
            this_repo._configure_from_options(args)

    if args and args.repos:
        base.repos.all().disable()
        for repo in args.repos:
            base.repos.get_matching(repo).enable()

    base.fill_sack()
    return base


def json_package(pkg):
    return {
        'name': pkg.name,
        'epoch': pkg.epoch,
        'version': pkg.version,
        'release': pkg.release,
        'arch': pkg.arch,
        'repo': pkg.reponame,
    }


def install(packages, args=None):
    with prepare_dnf(args) as base:
        base.install_specs(packages)
        base.resolve()

        if args and args.pretend:
            json_pkgs = []
            for pkg in base.transaction.install_set:
                json_pkgs.append(json_package(pkg))
            print(json.dumps({
                'packages': json_pkgs,
            }))
            return

        base.download_packages(base.transaction.install_set, progress=JsonProgressMeter())
        base.do_transaction(JsonTransactionProgress(len(base.transaction.install_set)))


def upgrade(packages, args=None):
    with prepare_dnf(args) as base:
        if len(packages) == 0:
            base.upgrade_all()
        else:
            base.upgrade(packages)
        base.resolve()

        if args and args.pretend:
            json_pkgs = []
            for pkg in base.transaction.install_set:
                json_pkgs.append(json_package(pkg))
            print(json.dumps({
                'packages': json_pkgs,
            }))
            return

        base.download_packages(base.transaction.install_set, progress=JsonProgressMeter())
        base.do_transaction(JsonTransactionProgress(len(base.transaction.install_set)))


def list_pkgs(packages=None, args=None):
    with prepare_dnf(args) as base:
        # by default (both False), display all packages
        if args and (not args.installed and not args.available):
            args.installed = True
            args.available = True
        j = {}

        def apply_filters(q):
            if packages:
                q = q.filter(name__glob=packages)
            if args and args.latest:
                q = q.latest(args.latest)
            return q

        if args and args.available:
            q_available = base.sack.query().available()
            q_available = apply_filters(q_available)
            available_pkgs = q_available.run()
            j['available'] = [json_package(x) for x in available_pkgs]
        if args and args.installed:
            q_installed = base.sack.query().installed()
            q_installed = apply_filters(q_installed)
            installed_pkgs = q_installed.run()
            j['installed'] = [json_package(x) for x in installed_pkgs]
        print(json.dumps(j))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', '--repoid', default=[],
                        dest='repos', action=OptionParser._SplitCallback)
    parser.add_argument('--repofrompath', default={},
                        action=OptionParser._SplitExtendDictCallback,
                        metavar='[repo,path]',
                        help='label and path to an additional repository to use (same '
                             'path as in a baseurl), can be specified multiple times.')
    parser.add_argument("--setopt", dest="setopts", default=[],
                        action=OptionParser._SetoptsCallback,
                        help="set arbitrary config and repo options")

    subparsers = parser.add_subparsers(dest='command')

    install_group = subparsers.add_parser('install')
    install_group.add_argument('--pretend', action='store_true')
    install_group.add_argument('-x', '--exclude', '--excludepkgs', default=[],
                               dest='excludepkgs', action=OptionParser._SplitCallback)
    install_group.add_argument('package', nargs='+')

    upgrade_group = subparsers.add_parser('upgrade')
    upgrade_group.add_argument('--pretend', action='store_true')
    upgrade_group.add_argument('-x', '--exclude', '--excludepkgs', default=[],
                               dest='excludepkgs', action=OptionParser._SplitCallback)
    upgrade_group.add_argument('package', nargs='*')

    list_group = subparsers.add_parser('list')
    list_group.add_argument('-x', '--exclude', '--excludepkgs', default=[],
                            dest='excludepkgs', action=OptionParser._SplitCallback)
    list_group.add_argument('--installed', action='store_true')
    list_group.add_argument('--available', action='store_true')
    list_group.add_argument('--latest', type=int)
    list_group.add_argument('package', nargs='*')

    args = parser.parse_args()

    if not args.command:
        parser.parse_args(['--help'])
        sys.exit(0)

    if 'excludepkgs' not in args:
        args.excludepkgs = []

    if args.command == 'install':
        install(args.package, args=args)
        return

    if args.command == 'upgrade':
        upgrade(args.package, args=args)
        return

    if args.command == 'list':
        list_pkgs(packages=args.package, args=args)
        return


if __name__ == '__main__':
    main()
