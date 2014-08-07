#!/usr/bin/env python
# -*- coding: utf-8 -*-# 
# @(#)genfioconf.py
# 
# 
# Copyright (C) 2014, GC3, University of Zurich. All rights reserved.
# 
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

__docformat__ = 'reStructuredText'
__author__ = 'Antonio Messina <antonio.s.messina@gmail.com>'

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import argparse
import os
import re
import subprocess
import sys
import tempfile

ALL_TESTS = ['write', 'read', 'randwrite', 'randread']
DEFAULT_BLOCKSIZES = ['4k', '8k', '16k', '32k', '64k', '1m']
DEFAULT_SIZES = ['1g', '10g', '100g']
DEFAULT_THREADS = 1

UZH_EXPECTED_PERF = {
 
    'OSD Very High Capacity': {
        'write': {
            'minsize': 10*2**30,
            'mindisks': 16,
            'minbw': 1.5 * 2**30,
        },
    },

    'OSD High Capacity': {
        'write': {
            'minsize': 10*2**30,
            'mindisks': 16,
            'minbw': 1.5 * 2**30,
        },
    },

    'OSD High Performance (SATA/SAS)': {
        'write': {
            'minsize': 10*2**30,
            'mindisks': 16,
            'minbw': 2 * 2**30,
        },
    },

    'OSD High Performance (SSD)': {
        'randwrite': {
            'minsize': 1*2**30,
            'mindisks': 16,
            'minbw': 1 * 2**30,
            'bs': 4*2**10,
        },
    },
    'OSD Very High Performance': {
        'write': {
            'minsize': 1*2**30,
            'mindisks': 16,
            'minbw': 3 * 2**30,
        },
        'randwrite': {
            'minsize': 1*2**30,
            'mindisks': 16,
            'minbw': 1 * 2**30,
            'bs': 4*2**10,
        },
    },

}

def create_config_file(conf, size, bs, rw):
    cfg = ['[global]']

    # size = conf.get('size', '1m')
    # bs = conf.get('bs', '1m')
    # rw = conf.get('rw', 'write')
    # direct = conf.get('direct', 1)

    cfg.append('size=%s' % size)
    cfg.append('bs=%s' % bs)
    cfg.append('rw=%s' % rw)
    cfg.append('direct=%d' % conf.direct)
    cfg.append('numjobs=%d' % conf.numjobs)

    cfgfile = "UZH_bs:%s_size:%s_direct:%d_th:%d.%s.fio" % (
        bs, size, conf.direct, conf.numjobs, rw)
    # for log in ['bw', 'iops', 'lat']:
    # for log in ['bw', 'iops']:
    #     cfg.append('write_%s_log=%s' % (log, rw))

    cfg.append('') # empty line

    ndir = 0
    for directory in conf.devices:
        ndir += 1
        section = 'file%03d' % ndir
        cfg.append("[%s]" % section)
        cfg.append("filename=%s" % directory)
        # statistic files generated by FIO
        if conf.stats:
            for log in ['bw', 'iops', 'lat']:
                cfg.append('write_%s_log=%s.%s.%s.%dth.%03d' % (log, size,bs , rw,  conf.numjobs, ndir))


        cfg.append("")

    with open(cfgfile, 'w') as fd:
        fd.write(str.join('\n', cfg))

    return cfgfile


def run_test(fname):
    print("Running command: 'fio %s'" % fname)
    pipe = subprocess.Popen(['fio', fname], stdout=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = pipe.communicate()
    with open(fname + '.out', 'w') as fd:
        fd.write(stdout)        
    return stdout


def bytes_to_human(num):
    for x in ['bytes','KB','MB','GB']:
        if abs(num) < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def human_to_bytes(s):
    """convert string s in the form [0-9]+KB/s or similar into bytes (or bytes per seconds"""
    is_speed = False
    if s.endswith('/s'):
        s = s[:-2]
        is_speed = True

    units = {'k': 2**10,
             'kb': 2**10,
             'm': 2**20,
             'mb': 2**20,
             'g': 2**30,
             'gb': 2**30,
             't': 2**40,
             'tb': 2**40,
             'p': 2**50,
             'pb' : 2**50,}

    s = s.lower()
    m = re.match(r'(?P<val>[0-9.]+)(?P<unit>[a-zA-Z]*)', s)
    
    try:
        return float(m.group('val')) * units.get(m.group('unit'), 1)
    except Exception as ex:
        import pdb; pdb.set_trace()


def parse_results(results, cfg):
    # This is the typical output of fio:
    #
    # file001: (g=0): rw=write, bs=4K-4K/4K-4K/4K-4K, ioengine=sync, iodepth=1
    # file002: (g=0): rw=write, bs=4K-4K/4K-4K/4K-4K, ioengine=sync, iodepth=1
    # ...
    # file048: (g=0): rw=write, bs=4K-4K/4K-4K/4K-4K, ioengine=sync, iodepth=1
    # fio-2.1.3
    # Starting 48 processes
    #
    # file001: (groupid=0, jobs=1): err= 0: pid=420: Tue Aug  5 20:50:52 2014
    #   write: io=1024.0MB, bw=24052KB/s, iops=6012, runt= 43597msec
    #     clat (usec): min=70, max=17432, avg=161.64, stdev=99.88
    #      lat (usec): min=71, max=17432, avg=162.50, stdev=100.41
    #     clat percentiles (usec):
    #      |  1.00th=[   96],  5.00th=[  105], 10.00th=[  110], 20.00th=[  118],
    #      | 30.00th=[  125], 40.00th=[  133], 50.00th=[  139], 60.00th=[  149],
    #      | 70.00th=[  161], 80.00th=[  181], 90.00th=[  229], 95.00th=[  286],
    #      | 99.00th=[  502], 99.50th=[  660], 99.90th=[ 1144], 99.95th=[ 1272],
    #      | 99.99th=[ 1480]
    #     bw (KB  /s): min=20576, max=33016, per=3.26%, avg=24036.97, stdev=2313.78
    #     lat (usec) : 100=2.10%, 250=90.26%, 500=6.63%, 750=0.61%, 1000=0.20%
    #     lat (msec) : 2=0.19%, 4=0.01%, 10=0.01%, 20=0.01%
    #   cpu          : usr=2.36%, sys=13.69%, ctx=315800, majf=0, minf=103
    #   IO depths    : 1=100.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=0.0%
    #      submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
    #      complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
    #      issued    : total=r=0/w=262144/d=0, short=r=0/w=0/d=0
    # file002: (groupid=0, jobs=1): err= 0: pid=424: Tue Aug  5 20:50:52 2014
    # ...
    # Run status group 0 (all jobs):
    #   WRITE: io=49152MB, aggrb=736909KB/s, minb=15352KB/s, maxb=26150KB/s, mint=40098msec, maxt=68301msec
    #
    # Disk stats (read/write):
    #   sdaa: ios=0/261017, merge=0/0, ticks=0/30660, in_queue=30536, util=68.63%
    #   sdab: ios=0/261798, merge=0/0, ticks=0/36700, in_queue=36560, util=80.82%

    data = {}
    msg = []
    size = 0
    bs = 0
    rw = None

    data = {'aggr': {}, 'disks_iops': [], 'disks_bw': []}

    files_re = re.compile(
        r'.* rw=(?P<rw>[^,]*), bs=(?P<read>[0-9.]+[a-zA-Z]+)-[^/]*/'
        r'(?P<write>[0-9.]+[a-zA-Z]+)-[^,]*,.*'
    )
    disk_re = re.compile(
        r'\s*(?P<rw>write|read|randwrite|randread)\s*: io=(?P<io>[^,]+), '
        r'bw=(?P<bw>[^,]+), iops=(?P<iops>[^,]+), runt=(?P<runt>[^,]+)'
    )
    aggr_re = re.compile(
        r'\s*(?P<RW>WRITE|READ|RANDWRITE|RANDREAD): io=(?P<iops>[^,]+), '
        r'aggrb=(?P<aggrb>[^,]+), minb=(?P<minb>[^,]+), maxb=(?P<maxb>[^,]+).*'
    )

    for line in results.split('\n'):
        if disk_re.match(line):
            m = disk_re.match(line)
            bw = human_to_bytes(m.group('bw'))
            iops = int(m.group('iops'))

            data['disks_bw'].append(bw)
            data['disks_iops'].append(iops)

            if not size:
                # size = human_to_bytes(m.group('io'))
                size = m.group('io')
        elif aggr_re.match(line):
            m = aggr_re.match(line)
            # Maybe it's the last lines. 
            m = aggr_re.match(line)
            if not m:
                continue
            data['aggr'] = {
                'bw': m.group('aggrb'),
                'minb': m.group('minb'),
                'maxb': m.group('maxb'),
                }                        
        elif files_re.match(line) and not bs:
            m = files_re.match(line)
            # we assume all blocksizes are the same
            # bs = human_to_bytes(m.group('read'))
            bs = m.group('read')
            rw = m.group('rw')

    totiops = sum(data['disks_iops'])
    numdisks = len(data['disks_iops'])
    if not numdisks:
        if cfg.verbose:
            return "Unable to parse file\n"
        else:
            return ''
    avgiops = totiops / numdisks

    totbw = sum(data['disks_bw'])
    numdisksbw = len(data['disks_bw'])
    avgbw = totbw / numdisksbw

    if numdisks != numdisksbw and cfg.verbose:
        print("WARNING: Device count mismatch: %d (iops) != %d (bw)" % (numdisks, numdisksbw))

    if cfg.verbose:
        msg.append("%s: aggr iops=%d, bw: %s/s" % (rw, totiops, bytes_to_human(totbw)))
        msg.append("%s: avg iops=%d, bw: %s/s" % (rw, avgiops, bytes_to_human(avgbw)))
        msg.append("%s: min iops=%d, bw: %s/s" % (rw,
                                                      min(data['disks_iops']),
                                                      bytes_to_human(min(data['disks_bw']))))
        msg.append("%s: max iops=%d, bw: %s/s" % (rw,
                                                      max(data['disks_iops']),
                                                      bytes_to_human(max(data['disks_bw']))))

    sizeb = human_to_bytes(size)
    bsb = human_to_bytes(bs)
    for osd, tests in UZH_EXPECTED_PERF.items():
        if rw in tests:
            values = tests[rw]
            compliant = True
            if 'mindisks' in values and numdisks < values['mindisks']:
                continue
            if 'minsize' in values and sizeb < values['minsize']:
                continue
            if 'bs' in values and bsb < values['bs']:
                continue

            if 'numrun' not in UZH_EXPECTED_PERF[osd][rw]:
                UZH_EXPECTED_PERF[osd][rw]['numrun'] = 1
            else:
                UZH_EXPECTED_PERF[osd][rw]['numrun'] += 1
            # Test is to be used to check compliance with RFP
            if data['aggr']['bw'] < values.get('minbw', 0):
                msg.append("%s: NOT COMPLIANT: %s/s < %s/s" % (
                    osd, bytes_to_human(data['aggr']['bw']),
                    bytes_to_human(values.get('minbw', 0))))
                compliant = False
            if avgiops < values.get('miniops', 0):
                msg.append("%s: NOT COMPLIANT: %d iops < %d iops" % (
                    osd, avgiops, values.get('miniops', 0)))
                compliant = False
            if compliant:
                msg.append("%s: COMPLIANT" % osd)

    if msg:
        msg.insert(0, "%s: size=%s, bs=%s, nthreads=%d" % (rw, size, bs, numdisks))
        msg.append('')
        return str.join('\n', msg)
    else:
        return ''


if __name__ == "__main__":
        
    parser = argparse.ArgumentParser(description='Script to run FIO and parse outputs')
    subparser = parser.add_subparsers(dest='cmd')
    run_parser = subparser.add_parser('run', help='Run FIO')
    run_parser.add_argument('-b', help='blocksize',
                            nargs='*',
                            default=DEFAULT_BLOCKSIZES,
                            dest='bs')

    run_parser.add_argument('-s', help='size',
                            nargs='*',
                            default=DEFAULT_SIZES,
                            dest='size')

    run_parser.add_argument('-t', help='tests to run',
                            nargs='*',
                            default=ALL_TESTS,
                            choices=ALL_TESTS,
                            dest='tests')

    run_parser.add_argument('--numjobs', help="Threads per file",
                            type=int, default=DEFAULT_THREADS)

    run_parser.add_argument('-i', help='Do not run with direct-IO',
                            default=True, action='store_false', dest='direct')
    run_parser.add_argument('-d', help='Devices to test',
                            nargs='+', dest='devices')

    run_parser.add_argument('-n', help='Do not run tests, just create configuration files',
                            default=True, action='store_false', dest='run_tests')

    run_parser.add_argument('-l', help='also generate statistic files',
                            default=False, action='store_true', dest='stats')
    run_parser.add_argument('-v', dest='verbose', action='count')

    print_parser = subparser.add_parser('print', help='Parse data from output files')
    print_parser.add_argument('-v', dest='verbose', action='count')
    print_parser.add_argument('FILE', nargs='*', 
                              default=[fname for fname in os.listdir('.') if fname.endswith('.out')], 
                              help='output file names. Default: *.out')

    cfg = parser.parse_args(sys.argv[1:])

    if cfg.cmd == 'run':
        for size in cfg.size:
            for bs in cfg.bs:
                for rw in cfg.tests:
                    conf_file = create_config_file(cfg, size, bs, rw)
                    if not cfg.run_tests: 
                        print("Config file %s written" % conf_file)
                        continue
                    results = run_test(conf_file)
                    out = parse_results(results, cfg)
                    if out: print(out)

    elif cfg.cmd == 'print':
        for fname in cfg.FILE:
            if cfg.verbose:
                print("Reading file %s" % fname)
            with open(fname) as fd:
                out = parse_results(fd.read(), cfg)
                if out: print(out)

    for osd, tests in UZH_EXPECTED_PERF.items():
        for rw in tests:
            if 'numrun' not in tests[rw]:
                print("%s: NOT COMPLIANT: test `%s` not performed." % (osd, rw))
