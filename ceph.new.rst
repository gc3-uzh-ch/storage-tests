
Bootstrap first monitor (storage5)
----------------------------------

::

    root@storage5:~# ceph-authtool --create-keyring /tmp/ceph.mon.keyring --gen-key -n mon. --cap mon 'allow *'
    creating /tmp/ceph.mon.keyring
    root@storage5:~# ceph-authtool --create-keyring /etc/ceph/ceph.client.admin.keyring --gen-key -n client.admin --set-uid=0 --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow'
    creating /etc/ceph/ceph.client.admin.keyring
    root@storage5:~# ceph-authtool /tmp/ceph.mon.keyring --import-keyring /etc/ceph/ceph.client.admin.keyring
    importing contents of /etc/ceph/ceph.client.admin.keyring into /tmp/ceph.mon.keyring

Create the mon map::

    root@storage5:~# monmaptool --create --generate -c /etc/ceph/ceph.conf /tmp/monmap
    monmaptool: monmap file /tmp/monmap
    monmaptool: set fsid to 7705608d-cbef-477a-865d-f5ae4c03370a
    monmaptool: writing epoch 0 to /tmp/monmap (4 monitors)
    root@storage5:~# monmaptool --print /tmp/monmap
    monmaptool: monmap file /tmp/monmap
    epoch 0
    fsid 7705608d-cbef-477a-865d-f5ae4c03370a
    last_changed 2014-06-16 12:29:19.990247
    created 2014-06-16 12:29:19.990247
    0: 192.168.160.65:6789/0 mon.storage5
    1: 192.168.160.66:6789/0 mon.storage6
    2: 192.168.160.67:6789/0 mon.storage7
    3: 192.168.160.68:6789/0 mon.storage8

    root@storage5:~# ceph-mon --mkfs -i storage5 --monmap /tmp/monmap --keyring /tmp/ceph.mon.keyring
    2014-06-16 11:45:07.169957 7fe23504a800 -1 did not load config file, using default settings.
    ceph-mon: created monfs at /var/lib/ceph/mon/ceph-storage5 for mon.storage5
    root@storage5:~# ls /var/lib/ceph/mon/ceph-0
    keyring  store.db

Copy the important files on all the other servers::

    root@storage5:~# for i in storage{6..8}; do scp /tmp/monmap $i:/tmp; scp /tmp/ceph.mon.keyring $i:/tmp; scp /etc/ceph/ceph.client.admin.keyring $i:/etc/ceph;done

Start the monitor::

    root@storage5:~# start ceph-mon id=storage5
    ceph-mon (ceph/storage5) start/running, process 24559
    root@storage5:~# ceph -s
    2014-06-16 11:46:00.189453 7fea06015700 -1 Errors while parsing config file!
    2014-06-16 11:46:00.189465 7fea06015700 -1 end of key=val line 18 reached, no "=val" found...missing =?
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_ERR 192 pgs stuck inactive; 192 pgs stuck unclean; no osds
         monmap e1: 1 mons at {storage5=192.168.160.65:6789/0}, election epoch 2, quorum 0 storage5
         osdmap e1: 0 osds: 0 up, 0 in
          pgmap v2: 192 pgs, 3 pools, 0 bytes data, 0 objects
                0 kB used, 0 kB / 0 kB avail
                     192 creating

The same on all the other servers::

    root@storage5:~# for host in storage{6..8}; do ssh $host ceph-mon --mkfs -i $host --monmap /tmp/monmap --keyring /tmp/ceph.mon.keyring; ssh $host start ceph-mon id=$host; done
    ceph-mon: set fsid to 7705608d-cbef-477a-865d-f5ae4c03370a
    ceph-mon: created monfs at /var/lib/ceph/mon/ceph-storage6 for mon.storage6
    ceph-mon (ceph/storage6) start/running, process 4144
    ceph-mon: set fsid to 7705608d-cbef-477a-865d-f5ae4c03370a
    ceph-mon: created monfs at /var/lib/ceph/mon/ceph-storage7 for mon.storage7
    ceph-mon (ceph/storage7) start/running, process 2947
    ceph-mon: set fsid to 7705608d-cbef-477a-865d-f5ae4c03370a
    ceph-mon: created monfs at /var/lib/ceph/mon/ceph-storage8 for mon.storage8
    ceph-mon (ceph/storage8) start/running, process 2579

Check the status::

    root@storage5:~# ceph -s
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_ERR 192 pgs stuck inactive; 192 pgs stuck unclean; no osds
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 8, quorum 0,1,2,3 storage5,storage6,storage7,storage8
         osdmap e1: 0 osds: 0 up, 0 in
          pgmap v2: 192 pgs, 3 pools, 0 bytes data, 0 objects
                0 kB used, 0 kB / 0 kB avail
                     192 creating


Create OSDs (`--zap-disk` is needed because I used the device for
testing before)::


    for host in storage{5..8}; do \
        for dev in /dev/sda[a-z]; do \
            ssh $host grep ^$dev /proc/mount || ssh $host ceph-disk prepare --zap-disk \
            --cluster ceph \
            --cluster-uuid 7705608d-cbef-477a-865d-f5ae4c03370a \
            --fs-type xfs $dev; done; done


Note: the bootstrap key is used by ceph-disk activate. ceph auth list
will show you the current bootstrap key, and the same key must be in
/var/lib/ceph/bootstrap-osd/ceph.keyring. If you have problems, you can get
the key for bootstrap-osd, or if it deosn't exist::

    root@storage5:~# ceph auth get-or-create-key client.bootstrap-osd mon "allow profile bootstrap-osd"
    AQDLHJ9TwAeFCBAAgnT30pTxpK+lhx/orwidjA==

Copy the key in /var/lib/ceph/bootstrap-osd/ceph.keyring::

    root@storage5:~# ceph-authtool /var/lib/ceph/bootstrap-osd/ceph.keyring -C --name=client.bootstrap-osd -a AQDLHJ9TwAeFCBAAgnT30pTxpK+lhx/orwidjA==

Copy it on all the other clients::

    root@storage5:~# for host in storage{6..8}; do scp /var/lib/ceph/bootstrap-osd/ceph.keyring $host:/var/lib/ceph/bootstrap-osd/; done
    ceph.keyring                                                                                                                                                                      100%   71     0.1KB/s   00:00    
    ceph.keyring                                                                                                                                                                      100%   71     0.1KB/s   00:00    
    ceph.keyring                                                                                                                                                                      100%   71     0.1KB/s   00:00    



Note: osd indexing is not following the configuration file, but the
order of creation!

After a while, you will see::

    root@storage5:~# ceph -s
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_WARN too few pgs per osd (2 < min 20)
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 8, quorum 0,1,2,3 storage5,storage6,storage7,storage8
         osdmap e1006: 192 osds: 192 up, 192 in
          pgmap v2361: 384 pgs, 3 pools, 0 bytes data, 0 objects
                20058 MB used, 174 TB / 174 TB avail
                     384 active+clean


Increase the pg and pgp number, if you want. Please note ethat this
will take a lot of time::

    ceph osd pool set rbd pg_num $[4*1024]

wait a bit...

::
    ceph osd pool set rbd pgp_num $[4*1024]

wait a bit longer (load on storage5 ~= 60!)...

Still had a problem::

   root@storage5:~# ceph -s
       cluster 7705608d-cbef-477a-865d-f5ae4c03370a
        health HEALTH_WARN 8 pgs peering; 8 pgs stuck inactive; 8 pgs stuck unclean
        monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 38, quorum 0,1,2,3 storage5,storage6,storage7,storage8
        osdmap e1046: 192 osds: 192 up, 192 in
         pgmap v2440: 4224 pgs, 3 pools, 0 bytes data, 0 objects
               21431 MB used, 174 TB / 174 TB avail
                   4216 active+clean
                      6 peering
                      2 remapped+peering


solved with::

    root@storage5:~# ceph health detail
    HEALTH_WARN 8 pgs peering; 8 pgs stuck inactive; 8 pgs stuck unclean
    pg 2.656 is stuck inactive since forever, current state peering, last acting [88,70]
    pg 2.ae0 is stuck inactive since forever, current state remapped+peering, last acting [79,148]
    pg 2.20d is stuck inactive since forever, current state peering, last acting [28,159]
    pg 2.4bb is stuck inactive since forever, current state peering, last acting [129,114]
    pg 2.fcf is stuck inactive since forever, current state peering, last acting [43,79]
    pg 2.425 is stuck inactive since forever, current state remapped+peering, last acting [170,29]
    pg 2.85e is stuck inactive since forever, current state peering, last acting [129,28]
    pg 2.8dd is stuck inactive since forever, current state peering, last acting [115,169]
    pg 2.656 is stuck unclean since forever, current state peering, last acting [88,70]
    pg 2.ae0 is stuck unclean since forever, current state remapped+peering, last acting [79,148]
    pg 2.20d is stuck unclean since forever, current state peering, last acting [28,159]
    pg 2.4bb is stuck unclean since forever, current state peering, last acting [129,114]
    pg 2.fcf is stuck unclean since forever, current state peering, last acting [43,79]
    pg 2.425 is stuck unclean since forever, current state remapped+peering, last acting [170,29]
    pg 2.85e is stuck unclean since forever, current state peering, last acting [129,28]
    pg 2.8dd is stuck unclean since forever, current state peering, last acting [115,169]
    pg 2.4bb is peering, acting [129,114]
    pg 2.425 is remapped+peering, acting [170,29]
    pg 2.20d is peering, acting [28,159]
    pg 2.fcf is peering, acting [43,79]
    pg 2.ae0 is remapped+peering, acting [79,148]
    pg 2.8dd is peering, acting [115,169]
    pg 2.85e is peering, acting [129,28]
    pg 2.656 is peering, acting [88,70]
    root@storage5:~# ceph pg force_create_pg 2.656
    pg 2.656 now creating, ok
    root@storage5:~# ceph health detail
    HEALTH_OK


Trying to reboot a node::

    root@storage6:~# exec reboot 
    root@storage5:~# ceph -s
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_WARN 1953 pgs degraded; 12 pgs peering; 38 pgs stale; 8 pgs stuck inactive; 2009 pgs stuck unclean; 48/192 in osds are down; 1 mons down, quorum 0,2,3 storage5,storage7,storage8
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 40, quorum 0,2,3 storage5,storage7,storage8
         osdmap e1059: 192 osds: 144 up, 192 in
          pgmap v2510: 4224 pgs, 3 pools, 0 bytes data, 0 objects
                21494 MB used, 174 TB / 174 TB avail
                    2155 active+clean
                       8 peering
                       3 stale+remapped+peering
                      69 active+remapped
                       1 remapped+peering
                    1953 active+degraded
                      35 stale+active+clean
    root@storage5:~# ceph -s
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_WARN 2020 pgs degraded; 2052 pgs stuck unclean; 48/192 in osds are down; 1 mons down, quorum 0,2,3 storage5,storage7,storage8
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 40, quorum 0,2,3 storage5,storage7,storage8
         osdmap e1059: 192 osds: 144 up, 192 in
          pgmap v2512: 4224 pgs, 3 pools, 0 bytes data, 0 objects
                21582 MB used, 174 TB / 174 TB avail
                    2127 active+clean
                      77 active+remapped
                    2020 active+degraded

Problem: /var/log too short in the sdcard, we probably need to use one
of the disks for /var/log and /var/lib/ceph/mon/ceph-*

Probably, too many OSDs on the same machine, which only has 8 cores
and 32GB of ram!

Placement
---------

Create two racks::

    ceph osd crush add-bucket rack-es-4 rack
    ceph osd crush add-bucket rack-es-5 rack

Move storage nodes to the correct rack::

    ceph osd crush move storage5 rack=rack-es-4
    ceph osd crush move storage6 rack=rack-es-4
    ceph osd crush move storage7 rack=rack-es-4
    ceph osd crush move storage8 rack=rack-es-4

Then, move the racks under the root::

    root@storage5:~# ceph osd crush move rack-es-4 root=default
    moved item id -6 name 'rack-es-4' to location {root=default} in crush map
    root@storage5:~# ceph osd crush move rack-es-5 root=default
    moved item id -7 name 'rack-es-5' to location {root=default} in crush map

Note that this will cause a rebalancing of the cluster.


Clients
-------

First of all, let's create pools for various services::

    ceph osd pool create cinder 8192
    ceph osd pool create glance 8192
    ceph osd pool create instances 8192

Note: creating all these pgs basically put down the cluster, which was
unresponsive for a lot of time (1-2h). Also, /var/log was filled, and
this was one more reason why the cluster was unresponsive.

Create accounts::

    ceph auth get-or-create client.cinder mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=cinder, allow rx pool=glance'
    ceph auth get-or-create client.glance mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=glance'

Copy the keyring on the remote machine::

    root@storage5:~# ceph auth get-or-create client.glance | ssh cloud3 sudo tee /etc/ceph/ceph.client.glance.keyring
    [client.glance]
    	key = AQDBUZ9TUD2BChAAc0PsLKQ9GWsoBiKBCglc9Q==
    root@storage5:~# ceph auth get-or-create client.cinder | ssh cloud3 sudo tee /etc/ceph/ceph.client.cinder.keyring
    [client.cinder]
    	key = AQC6UZ9TCBioMhAAFBvv0WiYy80EJyuRumOwng==

Ensure glance and cinder can access the files::

    root@storage5:~# ssh cloud3 chown glance.glance /etc/ceph/ceph.client.glance.keyring
    root@storage5:~# ssh cloud3 chown cinder.cinder /etc/ceph/ceph.client.cinder.keyring

Ensure ceph.conf is copied to all the nodes (actually, only the mon
part is interesting)::

    root@storage5:~# scp /etc/ceph/ceph.conf cloud3:/etc/ceph

At this point, after updating glance configuration file you should be
able to upload an image to glance, and this is seen (as a list of
chunk) on ceph using the `rados` command::

    rados -p glance ls

However, with rbd you can actually see the image::

    root@storage5:~# rbd  ls glance
    f90a196e-82a4-4a9f-a990-867274da34a0

The same from the controller, but with id `glance`::

    root@cloud3:~# rbd --id glance ls glance
    f90a196e-82a4-4a9f-a990-867274da34a0

and get more detailed information on the image file::

    root@cloud3:~# rbd --id glance -p glance  info f90a196e-82a4-4a9f-a990-867274da34a0
    rbd image 'f90a196e-82a4-4a9f-a990-867274da34a0':
    	size 1287 MB in 161 objects
    	order 23 (8192 kB objects)
    	block_name_prefix: rbd_data.1a7c727761da
    	format: 2
    	features: layering


http://ceph.com/docs/master/install/manual-deployment/
http://ceph.com/docs/master/rados/configuration/pool-pg-config-ref/
http://ceph.com/docs/next/rbd/rbd-openstack/
http://ceph.com/docs/master/rados/troubleshooting/troubleshooting-pg/
http://ceph.com/docs/master/start/hardware-recommendations/

to boot nova images directly from ceph:
https://blueprints.launchpad.net/nova/+spec/rbd-clone-image-handler

HA and ceph:
http://behindtheracks.com/tag/icehouse/

erasure (cold storage, uses less space but it's slower, sort of raid5)
http://ceph.com/docs/firefly/dev/erasure-coded-pool/

on different types of osd
http://ceph.com/docs/master/rados/operations/crush-map/

http://www.sebastien-han.fr/blog/2014/01/13/ceph-managing-crush-with-the-cli/



Problem:

Uploading an image using glance, interrupting the upload. In glance,
there is no image, however, in rados I see::

    root@storage5:~# rbd ls -p glance
    71b6f92a-6512-4919-b12d-d65b6dd9a2ab
    861bd4c7-0965-4133-a094-5d0fb3ec2cb7
    f90a196e-82a4-4a9f-a990-867274da34a0

I *know* for a fact that images `a47bf8bb-25ad-4f3c-88ab-e43962a1b140`
and `71b6f92a-6512-4919-b12d-d65b6dd9a2ab` are invalid, but how can I
tell otherwise::

    root@storage5:~# rbd info -p glance f90a196e-82a4-4a9f-a990-867274da34a0
    rbd image 'f90a196e-82a4-4a9f-a990-867274da34a0':
    	size 1287 MB in 161 objects
    	order 23 (8192 kB objects)
    	block_name_prefix: rbd_data.1a7c727761da
    	format: 2
    	features: layering
    root@storage5:~# rbd info -p glance a47bf8bb-25ad-4f3c-88ab-e43962a1b140
    rbd image 'a47bf8bb-25ad-4f3c-88ab-e43962a1b140':
    	size 1287 MB in 161 objects
    	order 23 (8192 kB objects)
    	block_name_prefix: rbd_data.1d0c302cc484
    	format: 2
    	features: layering


Test:

4 VM started from volume (or volume snapshots).
iozone running on all instances
shutdown one node

::
    (ansible)antonio@kenny:~/github/storage-test(master*)$ pdsh -w storage[6-8] free -m|dshbak -c
    ----------------
    storage6
    ----------------
                 total       used       free     shared    buffers     cached
    Mem:         32240      32015        224          0         45      23712
    -/+ buffers/cache:       8258      23982
    Swap:         4983          0       4983
    ----------------
    storage7
    ----------------
                 total       used       free     shared    buffers     cached
    Mem:         32240      32053        186          0         44      23927
    -/+ buffers/cache:       8082      24158
    Swap:         4983          0       4983
    ----------------
    storage8
    ----------------
                 total       used       free     shared    buffers     cached
    Mem:         32240      32032        208          0         42      23703
    -/+ buffers/cache:       8285      23954
    Swap:         4983          0       4983
    (ansible)antonio@kenny:~/github/storage-test(master*)$ pdsh -w storage[6-8] uptime|sort
    storage6:  14:17:17 up 20:05,  1 user,  load average: 4.88, 5.57, 5.00
    storage7:  14:17:18 up 20:04,  0 users,  load average: 5.68, 7.86, 6.96
    storage8:  14:17:17 up 20:04,  0 users,  load average: 7.20, 6.86, 6.44

ceph -w on storage6::

    2014-06-17 14:18:11.079939 mon.1 [INF] pgmap v7633: 24896 pgs: 12446 active+degraded, 12450 active+clean; 49368 MB data, 104 GB used, 85462 GB / 85567 GB avail; 28154 kB/s rd, 121 MB/s wr, 528 op/s; 5816/23664 objects degraded (24.577%)
    [...]
    (ansible)antonio@kenny:~/github/storage-test(master*)$ pdsh -w storage[6-8] uptime|sort
    storage6:  14:21:10 up 20:09,  1 user,  load average: 28.80, 11.77, 7.26
    storage7:  14:21:10 up 20:08,  0 users,  load average: 31.76, 12.46, 8.51
    storage8:  14:21:11 up 20:08,  0 users,  load average: 43.04, 15.51, 9.40

ceph -s::

    root@storage6:~# ceph -s
    2014-06-17 14:21:42.349319 7f6ddc185700  0 -- :/1003732 >> 192.168.160.65:6789/0 pipe(0x7f6dd80371f0 sd=3 :0 s=1 pgs=0 cs=0 l=1 c=0x7f6dd8037460).fault
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_WARN 10 pgs peering; 86 pgs recovering; 17 pgs recovery_wait; 115 pgs stuck inactive; 2786 pgs stuck unclean; 28 requests are blocked > 32 sec; recovery 12678/24188 objects degraded (52.414%); 1 mons down, quorum 1,2,3 storage6,storage7,storage8
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 16, quorum 1,2,3 storage6,storage7,storage8
         osdmap e568: 92 osds: 69 up, 69 in
          pgmap v7750: 24896 pgs, 6 pools, 50416 MB data, 12094 objects
                86832 MB used, 64090 GB / 64175 GB avail
                12678/24188 objects degraded (52.414%)
                     136 inactive
                    2537 active
                      10 peering
                      17 active+recovery_wait
                   22110 active+clean
                      86 active+recovering
    recovery io 247 MB/s, 0 keys/s, 59 objects/s
      client io 569 MB/s rd, 2469 MB/s wr, 9479 op/s


Restarting storage5::

    root@storage6:~# ceph -s
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_WARN 110 pgs recovering; 614 pgs recovery_wait; 571 pgs stuck unclean; 5 requests are blocked > 32 sec; recovery 3417/25862 objects degraded (13.212%)
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 18, quorum 0,1,2,3 storage5,storage6,storage7,storage8
         osdmap e580: 92 osds: 92 up, 92 in
          pgmap v8213: 24896 pgs, 6 pools, 53764 MB data, 12931 objects
                127 GB used, 85440 GB / 85567 GB avail
                3417/25862 objects degraded (13.212%)
                      38 active
                     614 active+recovery_wait
                   24134 active+clean
                     110 active+recovering
    recovery io 160 MB/s, 38 objects/s
      client io 1557 kB/s rd, 14667 kB/s wr, 199 op/s


load::

    (ansible)antonio@kenny:~/github/storage-test(master*)$ pdsh -w storage[6-8] uptime|sort
    storage6:  14:31:32 up 20:19,  2 users,  load average: 17.16, 12.30, 8.85
    storage7:  14:31:32 up 20:18,  0 users,  load average: 15.30, 11.69, 9.45
    storage8:  14:31:32 up 20:18,  0 users,  load average: 11.93, 12.60, 10.85


Boot from image: need to copy the /etc/ceph/ceph.client.cinder.keyring
on the compute node, because of a missing feature. Also, in this case,
nova-compute will download from glance, and then use rbd to import the
image to ceph.

Volume creation: check

Volume snapshot: check

Boot from volume: check

Boot from volume snapshot (creates new volume): check

Boot from image (create a new volume): almost working: the image went
into timeout because volume creation took too much, I used 20GB disk


Live migration: need very simple patch for nova:
https://bugs.launchpad.net/nova/+bug/1303536 patch is
https://launchpadlibrarian.net/173194970/ensure_added_feature_is_unique.patch



Boot from snapshot
-------------------

Create a volume snapshot::

    root@cloud3:~# cinder list
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+-------------+
    |                  ID                  |   Status  |         Display Name         | Size | Volume Type | Bootable | Attached to |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+-------------+
    | fd0dffdc-4cd3-4432-b57d-d44bc590d124 | available | Ubuntu 14.04 x86_64 from rbd |  20  |     None    |   true   |             |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+-------------+
    root@cloud3:~# cinder snapshot-create --display-name ubuntu_14.04 fd0dffdc-4cd3-4432-b57d-d44bc590d124
    +---------------------+--------------------------------------+
    |       Property      |                Value                 |
    +---------------------+--------------------------------------+
    |      created_at     |      2014-06-17T14:51:03.988370      |
    | display_description |                 None                 |
    |     display_name    |             ubuntu_14.04             |
    |          id         | ea6d42de-3a67-4a51-a03a-b7fe528f484a |
    |       metadata      |                  {}                  |
    |         size        |                  20                  |
    |        status       |               creating               |
    |      volume_id      | fd0dffdc-4cd3-4432-b57d-d44bc590d124 |
    +---------------------+--------------------------------------+
    root@cloud3:~# cinder snapshot-list
    +--------------------------------------+--------------------------------------+-----------+--------------+------+
    |                  ID                  |              Volume ID               |   Status  | Display Name | Size |
    +--------------------------------------+--------------------------------------+-----------+--------------+------+
    | ea6d42de-3a67-4a51-a03a-b7fe528f484a | fd0dffdc-4cd3-4432-b57d-d44bc590d124 | available | ubuntu_14.04 |  20  |
    +--------------------------------------+--------------------------------------+-----------+--------------+------+

Boot from this snapshot::

    root@cloud3:~# nova boot --flavor m1.small --key-name antonio --snapshot ea6d42de-3a67-4a51-a03a-b7fe528f484a test
    +--------------------------------------+-------------------------------------------------+
    | Property                             | Value                                           |
    +--------------------------------------+-------------------------------------------------+
    | OS-DCF:diskConfig                    | MANUAL                                          |
    | OS-EXT-AZ:availability_zone          | nova                                            |
    | OS-EXT-SRV-ATTR:host                 | -                                               |
    | OS-EXT-SRV-ATTR:hypervisor_hostname  | -                                               |
    | OS-EXT-SRV-ATTR:instance_name        | instance-0000001b                               |
    | OS-EXT-STS:power_state               | 0                                               |
    | OS-EXT-STS:task_state                | scheduling                                      |
    | OS-EXT-STS:vm_state                  | building                                        |
    | OS-SRV-USG:launched_at               | -                                               |
    | OS-SRV-USG:terminated_at             | -                                               |
    | accessIPv4                           |                                                 |
    | accessIPv6                           |                                                 |
    | adminPass                            | fidnq25XYQkD                                    |
    | config_drive                         |                                                 |
    | created                              | 2014-06-17T14:51:48Z                            |
    | flavor                               | m1.small (2)                                    |
    | hostId                               |                                                 |
    | id                                   | 103d201c-db05-4d9e-aee4-5d9b27cbef1d            |
    | image                                | Attempt to boot from volume - no image supplied |
    | key_name                             | antonio                                         |
    | metadata                             | {}                                              |
    | name                                 | test                                            |
    | os-extended-volumes:volumes_attached | []                                              |
    | progress                             | 0                                               |
    | security_groups                      | default                                         |
    | status                               | BUILD                                           |
    | tenant_id                            | a040593d8bd44e8982c46f96d5d5d04e                |
    | updated                              | 2014-06-17T14:51:49Z                            |
    | user_id                              | 3ab7addf37e14fe6bbe23f17a7a3b3b4                |
    +--------------------------------------+-------------------------------------------------+
    root@cloud3:~# nova list
    +--------------------------------------+-----------------+--------+----------------------+-------------+------------------+
    | ID                                   | Name            | Status | Task State           | Power State | Networks         |
    +--------------------------------------+-----------------+--------+----------------------+-------------+------------------+
    | 103d201c-db05-4d9e-aee4-5d9b27cbef1d | test            | BUILD  | block_device_mapping | NOSTATE     | private=10.8.0.2 |
    | fc17ef33-5be7-42b3-a3c9-76135d54f243 | test from image | ACTIVE | deleting             | Running     | private=10.8.0.4 |
    +--------------------------------------+-----------------+--------+----------------------+-------------+------------------+
    root@cloud3:~# nova list
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    | ID                                   | Name            | Status | Task State | Power State | Networks         |
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    | 103d201c-db05-4d9e-aee4-5d9b27cbef1d | test            | ACTIVE | -          | Running     | private=10.8.0.2 |
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+

A new volume is created for the machine::

    root@cloud3:~# cinder list
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+--------------------------------------+
    |                  ID                  |   Status  |         Display Name         | Size | Volume Type | Bootable |             Attached to              |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+--------------------------------------+
    | 1fafcf0b-be35-46b0-9df1-5109882cbec2 |   in-use  |                              |  20  |     None    |   true   | 103d201c-db05-4d9e-aee4-5d9b27cbef1d |
    | fd0dffdc-4cd3-4432-b57d-d44bc590d124 | available | Ubuntu 14.04 x86_64 from rbd |  20  |     None    |   true   |                                      |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+--------------------------------------+


Boot from volume snapshot, but deleting the volume after vm
termination::

    root@cloud3:~# nova boot --block-device shutdown=remove,source=snapshot,id=ea6d42de-3a67-4a51-a03a-b7fe528f484a,dest=volume,bootindex=0 --flavor m1.small --key-name antonio   test 
    root@cloud3:~# nova list
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    | ID                                   | Name            | Status | Task State | Power State | Networks         |
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    | 09295b96-5c64-491d-aa71-5507c5d07d53 | test            | ACTIVE | -          | Running     | private=10.8.0.2 |
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    root@cloud3:~# cinder list
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+--------------------------------------+
    |                  ID                  |   Status  |         Display Name         | Size | Volume Type | Bootable |             Attached to              |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+--------------------------------------+
    | 4665c620-18ba-443b-82e6-aba98d326879 |   in-use  |                              |  20  |     None    |   true   | 09295b96-5c64-491d-aa71-5507c5d07d53 |
    | fd0dffdc-4cd3-4432-b57d-d44bc590d124 | available | Ubuntu 14.04 x86_64 from rbd |  20  |     None    |   true   |                                      |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+--------------------------------------+
    root@cloud3:~# nova delete test
    root@cloud3:~# nova list
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    | ID                                   | Name            | Status | Task State | Power State | Networks         |
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    +--------------------------------------+-----------------+--------+------------+-------------+------------------+
    root@cloud3:~# cinder list
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+-------------+
    |                  ID                  |   Status  |         Display Name         | Size | Volume Type | Bootable | Attached to |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+-------------+
    | fd0dffdc-4cd3-4432-b57d-d44bc590d124 | available | Ubuntu 14.04 x86_64 from rbd |  20  |     None    |   true   |             |
    +--------------------------------------+-----------+------------------------------+------+-------------+----------+-------------+
