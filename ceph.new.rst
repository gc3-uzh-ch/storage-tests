
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

Configure radosgw on a VM
-------------------------

Network configuration
+++++++++++++++++++++

First of all, the VM must be able to contact the nodes.

In order to do that, since we are using the same L2 network for both
L3 network (10.8.0.0/24 and 192.168.160.0/22), we configure routing on
the VM::

    root@rados:~# route add -net 192.168.160.0/22 dev eth0
    root@rados:~# route -n
    Kernel IP routing table
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
    0.0.0.0         10.8.0.1        0.0.0.0         UG    0      0        0 eth0
    10.8.0.0        0.0.0.0         255.255.255.0   U     0      0        0 eth0
    192.168.160.0   0.0.0.0         255.255.252.0   U     0      0        0 eth0

and on the storage nodes (this after moving eth0 to eth4, 10gbe)::

    antonio@kenny:~$ pdsh -w storage[5-8] -l root route add -net 10.8.0.0/24 dev eth4
    antonio@kenny:~$ pdsh -w storage[5-8] -l root route -n | dshbak -c
    ----------------
    storage[5-8]
    ----------------
    Kernel IP routing table
    Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
    0.0.0.0         192.168.160.1   0.0.0.0         UG    0      0        0 eth4
    10.8.0.0        0.0.0.0         255.255.255.0   U     0      0        0 eth4
    192.168.160.0   0.0.0.0         255.255.252.0   U     0      0        0 eth4

and check that the VM can ping the storage nodes::

    root@rados:~# ping -c 1 192.168.160.65
    PING 192.168.160.65 (192.168.160.65) 56(84) bytes of data.
    64 bytes from 192.168.160.65: icmp_seq=1 ttl=64 time=0.489 ms

    --- 192.168.160.65 ping statistics ---
    1 packets transmitted, 1 received, 0% packet loss, time 0ms
    rtt min/avg/max/mdev = 0.489/0.489/0.489/0.000 ms


Keys configuration
++++++++++++++++++

Also check: http://ceph.com/docs/master/radosgw/config/

Create a keyring::

    root@storage5:~# ceph-authtool --create-keyring /etc/ceph/ceph.client.radosgw.keyring
    creating /etc/ceph/ceph.client.radosgw.keyring

Create a new key::

    root@storage5:~# ceph-authtool /etc/ceph/ceph.client.radosgw.keyring -n client.radosgw.gateway --gen-key

Add capabilities to that key::

    root@storage5:~# ceph-authtool -n client.radosgw.gateway --cap osd 'allow rwx' --cap mon 'allow rw' /etc/ceph/ceph.client.radosgw.keyring

Add the key in the keyring to the ceph keyring::

    root@storage5:~# ceph -k /etc/ceph/ceph.client.admin.keyring auth add client.radosgw.gateway -i /etc/ceph/ceph.client.radosgw.keyring
    added key for client.radosgw.gateway

On the vm, add the repository (you may need to disable ipv6 and
configure masquerading on the compute node, if it's not done already)::

    root@rados:~# apt-add-repository 'deb http://ceph.com/debian/ trusty main'
    root@rados:~# apt-get update
    [...]
    root@rados:~# apt-get install ceph radosgw

Copy the keyring in the VM::

    root@storage5:/etc/ceph# scp ceph.client.radosgw.keyring 10.8.0.2:/etc/ceph/


Also copy the ceph.conf file::

    root@storage5:/etc/ceph# scp ceph.conf 10.8.0.2:/etc/ceph/
    ceph.conf                    100%   14KB  14.1KB/s   00:00    


In the ceph.conf file, let's try to remove everything but sections
`[global]` and `[mon.*]` (`mon initial members` is useless here, and
so also `[osd.*]`).

Add a section for radosgw::

    [client.radosgw.gateway]
    host = 10.8.0.2
    keyring = /etc/ceph/ceph.client.radosgw.keyring
    rgw socket path = /var/run/ceph/ceph.radosgw.gateway.fastcgi.sock
    log file = /var/log/ceph/client.radosgw.gateway.log


You should be able to run::

    root@rados:/etc/ceph# ceph -n client.radosgw.gateway -s 
        cluster 7705608d-cbef-477a-865d-f5ae4c03370a
         health HEALTH_OK
         monmap e4: 4 mons at {storage5=192.168.160.65:6789/0,storage6=192.168.160.66:6789/0,storage7=192.168.160.67:6789/0,storage8=192.168.160.68:6789/0}, election epoch 46, quorum 0,1,2,3 storage5,storage6,storage7,storage8
         osdmap e922: 92 osds: 92 up, 92 in
          pgmap v351377: 24896 pgs, 6 pools, 78192 MB data, 18914 objects
                160 GB used, 85406 GB / 85567 GB avail
                   24896 active+clean

and::

    root@rados:/etc/ceph# rados -n client.radosgw.gateway lspools
    data
    metadata
    rbd
    cinder
    glance
    instances

Install apache and its fcgi module (multiverse repo)::

    root@rados:~# apt-get install apache2 libapache2-mod-fastcgi

Enable rewrite and fastcgi modules::

a2enmod rewrite fastcgi
service apache2 restart


keystone

http://ceph.com/docs/master/radosgw/keystone/

Erasure
-------

http://karan-mj.blogspot.ch/2014/04/erasure-coding-in-ceph.html

Create a new ruleset::

    root@storage5:~# ceph osd erasure-code-profile set ecruleset
    root@storage5:~# ceph osd erasure-code-profile get ecruleset
    directory=/usr/lib/ceph/erasure-code
    k=2
    m=1
    plugin=jerasure
    technique=reed_sol_van

Set `k` and `m` values (`k`: number of chunks, `m`: chunks of
parity). Also set failure domain to `osd` (optional)::

    root@storage5:~# ceph osd erasure-code-profile set ecruleset k=5 m=2 --force
    root@storage5:~# ceph osd erasure-code-profile set ecruleset ruleset-failure-domain=osd --force
    root@storage5:~# ceph osd erasure-code-profile get ecruleset
    directory=/usr/lib/ceph/erasure-code
    k=2
    m=1
    plugin=jerasure
    ruleset-failure-domain=osd
    technique=reed_sol_van

Create an `ecpool` pool using the `ecruleset` ruleset::

    root@storage5:~# ceph osd pool create ecpool 128 128 erasure ecruleset
    pool 'ecpool' created

Check::

    root@storage5:~# rados lspools
    data
    metadata
    rbd
    [...]
    ecpool
    root@storage5:~# ceph osd dump | grep -i erasure
    pool 14 'ecpool' erasure size 3 min_size 1 crush_ruleset 2 object_hash rjenkins pg_num 128 pgp_num 128 last_change 970 owner 0 flags hashpspool stripe_width 4096


Benchmarking
------------

Rados test: run for 60 seconds, use pool `rbd`, use 32 threads, object
size of 4194304 bytes (4MB, which is the default btw)

(sequential?) write::

    root@storage5:~# rados -p rbd bench -b 4194304 60 write -t 32
    [...]
     Total time run:         60.518910
    Total writes made:      5987
    Write size:             4194304
    Bandwidth (MB/sec):     395.711 

    Stddev Bandwidth:       67.7728
    Max bandwidth (MB/sec): 500
    Min bandwidth (MB/sec): 0
    Average Latency:        0.323123
    Stddev Latency:         0.201529
    Max latency:            1.65925
    Min latency:            0.113003

sequential read (must run a `write --no-cleanup` before)::

    root@storage5:~# rados bench -p rbd 60  seq -t 32 --no-cleanup
     Total time run:        30.924898
    Total reads made:     5988
    Read size:            4194304
    Bandwidth (MB/sec):    774.522 

    Average Latency:       0.16499
    Max latency:           0.367119
    Min latency:           0.051919

and random read::

    root@storage5:~# rados bench -p rbd 60  rand -t 32 --no-cleanup
     Total time run:        60.108433
    Total reads made:     11373
    Read size:            4194304
    Bandwidth (MB/sec):    756.832 

    Average Latency:       0.168952
    Max latency:           0.421654
    Min latency:           0.024715

(note, I couldn't find a better way to cleanup than running ``rados
ls -p rbd | grep ^benchmark_data_storage5 | xargs rados rm -p rbd``)

Write, but with 16MB objects::

    root@storage5:~# rados -p rbd bench -b $[1024*1024*16] 60 write -t 32
     Total time run:         60.324225
    Total writes made:      860
    Write size:             16777216
    Bandwidth (MB/sec):     228.101 

    Stddev Bandwidth:       57.1235
    Max bandwidth (MB/sec): 384
    Min bandwidth (MB/sec): 0
    Average Latency:        2.20626
    Stddev Latency:         0.263532
    Max latency:            2.99246
    Min latency:            0.347751

Interesting: bigger chunks do not lead to better bandwidth.

4kB objects::

    root@storage5:~# rados -p rbd bench -b $[1024*4] 60 write -t 32
     Total time run:         60.136300
    Total writes made:      60242
    Write size:             4096
    Bandwidth (MB/sec):     3.913 

    Stddev Bandwidth:       0.951053
    Max bandwidth (MB/sec): 5.88672
    Min bandwidth (MB/sec): 0
    Average Latency:        0.0319333
    Stddev Latency:         0.0456733
    Max latency:            0.718472
    Min latency:            0.005983

Bandwidth is clearly low, because the object size is very low. Average
latency is interesting (0.03)


Let's also benchmark the erasure encoded pool::

    root@storage5:~# rados bench -p ecpool 60  write -t 32
     Total time run:         60.651051
    Total writes made:      5363
    Write size:             4194304
    Bandwidth (MB/sec):     353.695 

    Stddev Bandwidth:       70.0677
    Max bandwidth (MB/sec): 468
    Min bandwidth (MB/sec): 0
    Average Latency:        0.360607
    Stddev Latency:         0.294105
    Max latency:            3.67487
    Min latency:            0.119527

Not bad at all.


However, rados bench can generate a lot of work, and being the
bottleneck. Let's try running 4 instances, one for each node::

    antonio@kenny:~$ pdsh -l root -g cephtest 'rados bench -p rbd 60 write -t 32 | grep andwidth' |dshbak -c
    ----------------
    storage5
    ----------------
    Bandwidth (MB/sec):     146.071 
    Stddev Bandwidth:       45.8362
    Max bandwidth (MB/sec): 220
    Min bandwidth (MB/sec): 0
    ----------------
    storage6
    ----------------
    Bandwidth (MB/sec):     136.288 
    Stddev Bandwidth:       44.5226
    Max bandwidth (MB/sec): 216
    Min bandwidth (MB/sec): 0
    ----------------
    storage7
    ----------------
    Bandwidth (MB/sec):     136.554 
    Stddev Bandwidth:       43.3056
    Max bandwidth (MB/sec): 212
    Min bandwidth (MB/sec): 0
    ----------------
    storage8
    ----------------
    Bandwidth (MB/sec):     144.096 
    Stddev Bandwidth:       49.6484
    Max bandwidth (MB/sec): 244
    Min bandwidth (MB/sec): 0


Summing up all the values, we get a bandwidth of 562 MB/s!

I don't think we can have a value bigger than this, as the 10gbe is
probably the bottleneck here: the rbd volume has `size=2` (one object
and one replica) so for each write, the osd must write another replica
to another object.

For the erasure coded pool we have instead::

    antonio@kenny:~$ pdsh -l root -g cephtest 'rados bench -p ecpool 60 write -t 32 | grep andwidth' |dshbak -c
    storage5
    ----------------
    Bandwidth (MB/sec):     157.683 
    Stddev Bandwidth:       32.8958
    Max bandwidth (MB/sec): 220
    Min bandwidth (MB/sec): 0
    ----------------
    storage6
    ----------------
    Bandwidth (MB/sec):     159.924 
    Stddev Bandwidth:       32.1713
    Max bandwidth (MB/sec): 208
    Min bandwidth (MB/sec): 0
    ----------------
    storage7
    ----------------
    Bandwidth (MB/sec):     158.980 
    Stddev Bandwidth:       28.425
    Max bandwidth (MB/sec): 208
    Min bandwidth (MB/sec): 0
    ----------------
    storage8
    ----------------
    Bandwidth (MB/sec):     164.479 
    Stddev Bandwidth:       33.3917
    Max bandwidth (MB/sec): 220
    Min bandwidth (MB/sec): 0

638MB/s!! (it should be slower IMHO)

Benchmark the osd::

    root@storage5:~# ceph tell osd.0 bench $[1024*1024*1024] 4096
    Error EINVAL: 'count' values greater than 12288000 for a block size of
    4096 bytes, assuming 100 IOPS, for 30 seconds, can cause ill effects
    on osd.  Please adjust 'osd_bench_small_size_max_iops' with a higher
    value if you wish to use a higher 'count'.

Uhmm... where is it this configuration?::

    root@storage5:~# ceph --admin-daemon /var/run/ceph/ceph-osd.0.asok config show|grep osd_bench
      "osd_bench_small_size_max_iops": "100",
      "osd_bench_large_size_max_throughput": "104857600",
      "osd_bench_max_block_size": "67108864",
      "osd_bench_duration": "30",

Can we inject new configuration? Yes (`osd.*` can be used for *all*
the OSDs)::

    root@storage5:~# ceph tell osd.0 injectargs '--osd_bench_small_size_max_iops 10000'
    osd_bench_small_size_max_iops = '10000' 

Now we can do the benchmark again: writing 1GB in 4MB chunks to
`osd.0`::

    root@storage5:~# ceph tell osd.0 bench $[1024*1024*1024] 4096

=> osd down :(

Trying with 100MB::

    root@storage5:~# ceph tell osd.0 bench $[1024*1024*100] 4096
    { "bytes_written": 104857600,
      "blocksize": 4096,
      "bytes_per_sec": "2115816.000000"}

2MB/s ... veeery slow... (although it's 4kB chunks...)

increasing the blocksize causes the error::

    Error EINVAL: 'count' values greater than 750 for a block size of
    4096 kB, assuming 102400 kB/s, for 30 seconds, can cause ill
    effects on osd.  Please adjust
    'osd_bench_large_size_max_throughput' with a higher value if you
    wish to use a higher 'count'.

which I don't know how to fix :(

Increasing a few more values::

    root@storage5:~# ceph --admin-daemon /var/run/ceph/ceph-osd.0.asok config show|grep osd_bench
      "osd_bench_small_size_max_iops": "10000",
      "osd_bench_large_size_max_throughput": "10485760000000",
      "osd_bench_max_block_size": "67108864",
      "osd_bench_duration": "3000",
    
    root@storage6:~# ceph tell osd.0 bench $[1024*1024*1024] $[1024*1024*4]
    { "bytes_written": 1073741824,
      "blocksize": 4194304,
      "bytes_per_sec": "42741605.000000"}

~40MB/s per OSD, not that much.

Same test, using dd on the device::

    root@storage5:~# dd if=/dev/zero of=/dev/sdz bs=4M count=$[1024/4] oflag=direct
    256+0 records in
    256+0 records out
    1073741824 bytes (1.1 GB) copied, 7.91085 s, 136 MB/s

and on the filesystem::

    root@storage5:~# dd if=/dev/zero of=/var/lib/ceph/osd/ceph-0/deleteme bs=4M count=$[1024/4] oflag=direct
    256+0 records in
    256+0 records out
    1073741824 bytes (1.1 GB) copied, 9.55396 s, 112 MB/s



Misc notes
----------

Add an OSD

I use my own scripted method based on the documentation:
http://ceph.com/docs/master/rados/operations/add-or-rm-osds/

Just remember to run "ceph osd create" _without_ a UUID, then get the OSD number from the output. Here's a quick and dirty version:

OSD=`ceph osd create`
[update ceph.conf if necessary]
mkdir -p /var/lib/ceph/osd/ceph-${OSD}
mkfs_opts=`ceph-conf -c /etc/ceph/ceph.conf -s osd --lookup osd_mkfs_options_xfs`
mount_opts=`ceph-conf -c /etc/ceph/ceph.conf -s osd --lookup osd_mount_options_xfs`
dev=`ceph-conf -c /etc/ceph/ceph.conf -s osd.${OSD} --lookup devs`
mkfs.xfs ${mkfs_opts} ${dev}
mount -t xfs -o ${mount_opts} ${dev} /var/lib/ceph/osd/ceph-${OSD}
ceph-osd -c /etc/ceph/ceph.conf -i ${OSD} --mkfs --mkkey
ceph auth del osd.${OSD} # only if a prior OSD had this number
ceph auth add osd.${OSD} osd 'allow *' mon 'allow rwx' -i /var/lib/ceph/osd/ceph-${o}/keyring

Then set up your CRUSH map and start the OSDs.
