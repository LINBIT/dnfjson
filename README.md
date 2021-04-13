# dnfjson

`dnfjson` is a helper script which uses [libdnf](https://github.com/rpm-software-management/libdnf),
the core library of [dnf](https://github.com/rpm-software-management/dnf), to
perform certain package management tasks while providing machine readable output
in the JSON format.

## Installing

```
$ pip3 install https://github.com/LINBIT/dnfjson/archive/refs/heads/master.zip
```

## Example

```
$ dnfjson.py install acpid
{"type": "downloading", "package": "acpid-2.0.30-2.el8.x86_64.rpm", "done_files": 1, "total_files": 1, "done_size": 82288, "total_size": 82288}
{"type": "installing", "package": {"name": "acpid", "epoch": 0, "version": "2.0.30", "release": "2.el8", "arch": "x86_64"}, "action": "PKG_INSTALL", "done_pkgs": 1, "total_pkgs": 1}

$ dnfjson.py upgrade --pretend
{"packages": [{"name": "file", "epoch": 0, "version": "5.33", "release": "16.el8_3.1", "arch": "x86_64"}, {"name": "file-libs", "epoch": 0, "version": "5.33", "release": "16.el8_3.1", "arch": "x86_64"}, {"name": "systemd", "epoch": 0, "version": "239", "release": "41.el8_3.2", "arch": "x86_64"}, {"name": "zlib", "epoch": 0, "version": "1.2.11", "release": "16.2.el8_3", "arch": "x86_64"}, {"name": "crypto-policies", "epoch": 0, "version": "20210209", "release": "1.gitbfb6bed.el8_3", "arch": "noarch"}, {"name": "crypto-policies-scripts", "epoch": 0, "version": "20210209", "release": "1.gitbfb6bed.el8_3", "arch": "noarch"}, {"name": "dbus", "epoch": 1, "version": "1.12.8", "release": "12.el8_3", "arch": "x86_64"}, {"name": "dbus-common", "epoch": 1, "version": "1.12.8", "release": "12.el8_3", "arch": "noarch"}, {"name": "dbus-daemon", "epoch": 1, "version": "1.12.8", "release": "12.el8_3", "arch": "x86_64"}, {"name": "systemd-libs", "epoch": 0, "version": "239", "release": "41.el8_3.2", "arch": "x86_64"}, {"name": "systemd-pam", "epoch": 0, "version": "239", "release": "41.el8_3.2", "arch": "x86_64"}, {"name": "systemd-udev", "epoch": 0, "version": "239", "release": "41.el8_3.2", "arch": "x86_64"}, {"name": "dbus-libs", "epoch": 1, "version": "1.12.8", "release": "12.el8_3", "arch": "x86_64"}, {"name": "dbus-tools", "epoch": 1, "version": "1.12.8", "release": "12.el8_3", "arch": "x86_64"}]}
```
