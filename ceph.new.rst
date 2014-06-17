
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
