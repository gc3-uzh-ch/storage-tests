
Reboot a node
-------------

**IMPORTANT**: if you reboot a node, its OSDs will likely go *out*, so
the CRUSH map will change and the data will be replicated. If you want
to just reboot a node, run::

    # ceph osd set noout

This will give you a warning whenever you run ``ceph -s`` but its'
fine. Then you can safetly reboot the node. Its OSDs will be marked
**down** but not **out**. If multiple nodes will be rebooted, the
cluster may be unavailable. After the node comes back, the OSDs will
be **up** again.

Inconsistent PGs, scrub errors
------------------------------

Checking for the status of the cluster::

    root@storage5:~# ceph -s
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_ERR 538 pgs degraded; 1 pgs inconsistent; 262 pgs stuck unclean; recovery 124/11436 objects degraded (1.084%); 1 scrub errors; 1/92 in osds are down
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 42, quorum 0,1,2,3 storage5,storage6,storage7,storage8
         osdmap e890: 92 osds: 91 up, 92 in
          pgmap v333398: 24896 pgs, 6 pools, 25408 MB data, 5718 objects
                58640 MB used, 85510 GB / 85567 GB avail
                124/11436 objects degraded (1.084%)
                     537 active+degraded
                       1 active+degraded+inconsistent
                   24358 active+clean

Get more details::

    root@storage5:~# ceph health detail
    HEALTH_ERR 1 pgs inconsistent; 1 scrub errors; noout flag(s) set
    pg 3.15ad is active+clean+inconsistent, acting [75,45]
    1 scrub errors

Repair the PGs that need to be repaired::

    root@storage5:~# ceph pg repair 3.15ad
    instructing pg 3.15ad on osd.75 to repair


Replace a failed disk
---------------------

http://karan-mj.blogspot.ch/2014/03/admin-guide-replacing-failed-disk-in.html

How to know where an osd is?
----------------------------

::
    root@storage6:~# ceph osd metadata 45
    { "arch": "x86_64",
      "back_addr": "192.168.160.66:6866\/28732",
      "ceph_version": "ceph version 0.80.4 (7c241cfaa6c8c068bc9da8578ca00b9f4fc7567f)",
      "cpu": "Quad-Core AMD Opteron(tm) Processor 2384",
      "distro": "Ubuntu",
      "distro_codename": "trusty",
      "distro_description": "Ubuntu 14.04.1 LTS",
      "distro_version": "14.04",
      "front_addr": "192.168.160.66:6865\/28732",
      "hb_back_addr": "192.168.160.66:6868\/28732",
      "hb_front_addr": "192.168.160.66:6869\/28732",
      "hostname": "storage6.gc3",
      "kernel_description": "#57-Ubuntu SMP Tue Jul 15 03:51:08 UTC 2014",
      "kernel_version": "3.13.0-32-generic",
      "mem_swap_kb": "5103612",
      "mem_total_kb": "33014048",
      "os": "Linux",
      "osd_data": "\/var\/lib\/ceph\/osd\/ceph-45",
      "osd_journal": "\/var\/lib\/ceph\/osd\/ceph-45\/journal"}



Links
-----

http://ceph.com/docs/master/rados/troubleshooting/troubleshooting-osd/
