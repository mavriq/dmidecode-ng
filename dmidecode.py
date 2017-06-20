
import os
import sys


__version__ = "0.8.1"

TYPE = {
    0: 'bios',
    1: 'system',
    2: 'base board',
    3: 'chassis',
    4: 'processor',
    7: 'cache',
    8: 'port connector',
    9: 'system slot',
    10: 'on board device',
    11: 'OEM strings',
    13: 'bios language',
    15: 'system event log',
    16: 'physical memory array',
    17: 'memory_device',
    19: 'memory array mapped address',
    24: 'hardware security',
    25: 'system power controls',
    27: 'cooling device',
    32: 'system boot',
    41: 'onboard device',
}


try:
    next.__doc__
except NameError:
    # need for python-2.4
    def next(iterator):
        return iterator.next()


def parse_dmi(content):
    """
    Parse the whole dmidecode output.
    Returns a list of tuples of (type int, value dict).
    """
    info = []
    lines = iter(content.strip().splitlines())
    while True:
        try:
            line = next(lines)
        except StopIteration:
            break

        if line.startswith('Handle 0x'):
            typ = int(line.split(',', 2)[1].strip()[len('DMI type'):])
            if typ in TYPE:
                info.append((typ, _parse_handle_section(lines)))
    return info


def _parse_handle_section(lines):
    """
    Parse a section of dmidecode output

    * 1st line contains address, type and size
    * 2nd line is title
    * line started with one tab is one option and its value
    * line started with two tabs is a member of list
    """
    data = {
        '_title': next(lines).rstrip(),
    }

    k = None
    for line in lines:
        line = line.rstrip()
        if line.startswith('\t\t'):
            if not isinstance(data.get(k), list):
                data[k] = [data.get(k)]
            data[k].append(line.lstrip())
        elif line.startswith('\t'):
            k, v = [i.strip() for i in line.lstrip().split(':', 1)]
            if v:
                data[k] = v
            else:
                data[k] = []
        else:
            break

    return data


def profile():
    if os.isatty(sys.stdin.fileno()):
        content = _get_output()
    else:
        content = sys.stdin.read()

    info = parse_dmi(content)
    _show(info)


def _get_output():
    from subprocess import Popen, PIPE
    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = open('/dev/null', 'w')
    cmdline = 'sudo dmidecode'
    _env = os.environ.copy()
    _env['LC_ALL'] = 'C'
    _env['LANG'] = 'C'
    _env['PATH'] = ':'.join((
        os.environ.get('PATH', ''),
        '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin',
    ))
    _cmd = Popen(
        cmdline,
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
        env=_env,
    )
    _x = _cmd.communicate()
    if _cmd.returncode != 0:
        raise OSError({
            'command': cmdline,
            'returncode': _cmd.returncode,
            'stdout': _x[0],
            'stderr': _x[1],
        })
    else:
        return _x[0].decode()


def _show(info):
    def _get(i):
        return [v for j, v in info if j == i]

    system = _get(1)[0]
    print('%s %s (SN: %s, UUID: %s)' % (
        system.get('Manufacturer', '-n/a-'),
        system.get('Product Name', '-n/a-'),
        system.get('Serial Number', '-n/a-'),
        system.get('UUID', '-n/a-'),
    ))

    for cpu in _get(4):
        print('%s %s %s (Core: %s, Thead: %s)' % (
            cpu.get('Manufacturer', '-n/a-'),
            cpu.get('Family', '-n/a-'),
            cpu.get('Max Speed', '-n/a-'),
            cpu.get('Core Count', '-n/a-'),
            cpu.get('Thread Count', '-n/a-'),
        ))

    cnt, total, unit = 0, 0, None
    for mem in _get(17):
        if mem['Size'] == 'No Module Installed':
            continue
        i, unit = mem['Size'].split()
        cnt += 1
        total += int(i)
    print('%d memory stick(s), %d %s in total' % (
        cnt,
        total,
        unit,
    ))


if __name__ == '__main__':
    profile()
