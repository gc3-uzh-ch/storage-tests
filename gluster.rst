Basic info
----------

Get information about the peers::

    gluster peer status
    root@storage1:~# gluster peer status
    Number of Peers: 3

    Hostname: storage2
    Uuid: dab93f65-2586-47e1-8c0d-a18300413d9d
    State: Peer in Cluster (Connected)

    Hostname: storage3
    Uuid: 217426a8-d9a2-4304-96f8-70be8c5061a7
    State: Peer in Cluster (Connected)

    Hostname: storage4
    Uuid: ad57f4d3-5f98-42af-a866-40d664b71792
    State: Peer in Cluster (Connected)



Gluster volume creation
-----------------------

Create a volume

Create a directory on all the bricks, and then create the volume::

    # pdsh -w storage[1-4] mkdir  /srv/gluster/bricks/devgroup0/glance
    root@storage1:~# gluster volume create glance replica 2 storage{1..4}:/srv/gluster/bricks/devgroup0/glance
    root@storage1:~# gluster volume info
     
    Volume Name: glance
    Type: Distributed-Replicate
    Volume ID: 2fa125fc-f5b3-4d46-80ac-eb5681112bc1
    Status: Created
    Number of Bricks: 2 x 2 = 4
    Transport-type: tcp
    Bricks:
    Brick1: storage1:/srv/gluster/bricks/devgroup0/glance
    Brick2: storage2:/srv/gluster/bricks/devgroup0/glance
    Brick3: storage3:/srv/gluster/bricks/devgroup0/glance
    Brick4: storage4:/srv/gluster/bricks/devgroup0/glance

Start the volume::

    root@storage1:~# gluster volume start glance
    volume start: glance: success
    root@storage1:~# gluster volume info
     
    Volume Name: glance
    Type: Distributed-Replicate
    Volume ID: 2fa125fc-f5b3-4d46-80ac-eb5681112bc1
    Status: Started
    Number of Bricks: 2 x 2 = 4
    Transport-type: tcp
    Bricks:
    Brick1: storage1:/srv/gluster/bricks/devgroup0/glance
    Brick2: storage2:/srv/gluster/bricks/devgroup0/glance
    Brick3: storage3:/srv/gluster/bricks/devgroup0/glance
    Brick4: storage4:/srv/gluster/bricks/devgroup0/glance

Create a volume for nova-instances, spanning *all* the nodes/bricks::

    # pdsh -w storage[1-4] mkdir  /srv/gluster/bricks/devgroup{0..5}/nova-instances
    root@storage1:~# gluster volume create nova-instances replica 2 $(for i in {0..5}; do echo storage{1..4}:/srv/gluster/bricks/devgroup$i/nova-instances; done)
    root@storage1:~# gluster volume start  nova-instances
    volume start: nova-instances: success

The same for cinder::

    # pdsh -w storage[1-4] mkdir  /srv/gluster/bricks/devgroup{0..5}/cinder
    root@storage1:~# gluster volume create cinder replica 2 $(for i in {0..5}; do echo storage{1..4}:/srv/gluster/bricks/devgroup$i/cinder; done)
    root@storage1:~# gluster volume start cinder
    volume start: cinder: success


Needed for qemu::


    volume set server.allow-insecure on

Also::

    root@node-08-01-06:~# id libvirt-qemu
    uid=112(libvirt-qemu) gid=115(kvm) groups=115(kvm)

    root@storage1:~# gluster vol set cinder storage.owner-uid 112
    volume set: success
    root@storage1:~# gluster vol set cinder storage.owner-gid 115
    volume set: success

With current gluster 3.5.0, you also have to stop and start the
volume::

    root@storage1:~# gluster volume stop cinder
    root@storage1:~# gluster volume start cinder

Also you should change the permissions on /var/lib/nova/instances::

    root@node-08-01-06:~# chown nova.nova /var/lib/nova/instances

Note: the kernel on the storage and clients must be at least 3.3


Still not working. Why?

2014-06-10 16:35:11.346 12009 DEBUG nova.virt.libvirt.config [req-4776c718-6a92-4923-8413-dff5affa61e0 9150e4f4542843bb8a39872e484483e0 3244794c89194872b688e4e892d497ba] Generated XML ('<disk type="network" device="disk">\n  <driver name="qemu" type="raw" cache="none"/>\n  <source protocol="gluster" name="cinder/volume-da96369a-c7fb-491a-a835-c90e2c0a8591">\n    <host name="storage2" port="24007"/>\n  </source>\n  <target bus="virtio" dev="vdb"/>\n  <serial>da96369a-c7fb-491a-a835-c90e2c0a8591</serial>\n</disk>\n',)  to_xml /usr/lib/python2.7/dist-packages/nova/virt/libvirt/config.py:71

and https://bugzilla.redhat.com/show_bug.cgi?id=1017289

Problem: qemu does not support gluster.
Solution: install qemu from ppa:semiosis/ubuntu-qemu-glusterfs
(or recompile with gluster support)

problem: libvirt does not support gluster
solution: recompile libvirt

On a machine with gluster-common intalled::

    apt-get install pbuilder
    apt-get build-dep libvirt-bin
    apt-get source -b libvirt


NOTE: I DON'T THINK I'VE UPDATED libvirtd, but now it works!

Testing
-------

Create volume, attach it to the instance, run iozone -a on it.

Run iozone -a on the root disk. Results may be modified by the fact
that I was also trying to start a new instance, and I've detached a
volume that didn't complete very fast because it was trying to unmount
the glusterfs cinder volume but it took some time (load 6, at least
one thread using 100% waiting time)

Mounting a new volume, writing 10 files each 1GB big::

    mount /dev/vdb1 /mnt
    for i in {1..20}; do dd if=/dev/zero bs=1M count=1024 of=/mnt/zero.$i; done

1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 12.8066 s, 83.8 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 19.4014 s, 55.3 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 18.3923 s, 58.4 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 18.8105 s, 57.1 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 13.1885 s, 81.4 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 18.9627 s, 56.6 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 18.7395 s, 57.3 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 18.4782 s, 58.1 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 18.9517 s, 56.7 MB/s
1024+0 records in
1024+0 records out
1073741824 bytes (1.1 GB) copied, 18.5625 s, 57.8 MB/s
...

Creating a snapshot (very fast)
Creating a volume from snapshot (taking a lot of time), the following
command is issued: /usr/bin/qemu-img convert -O raw
/var/lib/cinder/volumes/03ddfcad54c41027eaa2322e11499670/volume-307c1274-f179-42e7-a1d8-3e593587b02e
/var/lib/cinder/volumes/03ddfcad54c41027eaa2322e11499670/volume-6f557cab-6d08-4a54-8ce4-e6ed1e9495be

Volume seems to be created correctly. However, the originating volume
become unreadable after a while::

    root@test2:~# mount /dev/vdb1 /mnt/
    mount: /dev/vdb1: can't read superblock

Trying to detach and re-attach the volume using the same device name
(vdb) didn't work, as mount is stuck. Detaching is hunging, no log on
nova-compute.log or /var/log/glusterfs/\*log (maybe I had a shell on
/var/lib/cinder/volumes/03\*?)
A cpu is at 100% waiting, no process seem to use cpu, although there
is a qemu-img in D mode::

    nova     28725  0.0  0.0 154448  5992 ?        D    16:18   0:00 qemu-img info /var/lib/nova/mnt/03ddfcad54c41027eaa2322e11499670/volume-307c1274-f179-42e7-a1d8-3e593587b02e.e495778c-6cc0-4081-86d2-308ad3fe1d19

Unable to terminate instance::

    ==> /var/log/libvirt/libvirtd.log <==
    2014-06-11 11:29:18.514+0000: 1261: info : libvirt version: 1.2.2
    2014-06-11 11:29:18.514+0000: 1261: error : virNetSocketReadWire:1454 : End of file while reading data: Input/output error
    2014-06-11 11:31:39.680+0000: 1261: error : virNetSocketReadWire:1454 : End of file while reading data: Input/output error
    2014-06-11 11:53:30.776+0000: 1267: error : qemuMonitorTextAddDrive:2611 : operation failed: open disk image file failed
    2014-06-11 11:56:17.966+0000: 1261: error : virNetSocketReadWire:1454 : End of file while reading data: Input/output error
    2014-06-11 12:06:04.030+0000: 1261: error : virNetSocketReadWire:1454 : End of file while reading data: Input/output error
    2014-06-11 13:02:29.475+0000: 1261: warning : qemuMonitorJSONHandleDeviceDeleted:931 : missing device in device deleted event
    2014-06-11 13:29:27.726+0000: 1263: error : qemuProcessPrepareChardevDevice:2620 : Unable to pre-create chardev file '/var/lib/nova/instances/31e6265b-83eb-4777-9a30-d6e312ad3482/console.log': No such file or directory
    2014-06-11 13:33:31.706+0000: 1261: warning : qemuMonitorJSONHandleDeviceDeleted:931 : missing device in device deleted event
    2014-06-11 14:17:58.627+0000: 1261: warning : qemuMonitorJSONHandleDeviceDeleted:931 : missing device in device deleted event
    2014-06-11 14:44:02.655+0000: 1262: error : virProcessKillPainfully:320 : Failed to terminate process 22402 with SIGKILL: Device or resource busy

    ==> /var/log/nova/nova-compute.log <==
    2014-06-11 16:44:02.656 18063 ERROR nova.virt.libvirt.driver [req-c2093adc-bd8a-4ab6-a78e-dc351c8fab88 9150e4f4542843bb8a39872e484483e0 3244794c89194872b688e4e892d497ba] [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9] Error from libvirt during destroy. Code=38 Error=Failed to terminate process 22402 with SIGKILL: Device or resource busy
    2014-06-11 16:44:03.169 18063 ERROR nova.compute.manager [req-c2093adc-bd8a-4ab6-a78e-dc351c8fab88 9150e4f4542843bb8a39872e484483e0 3244794c89194872b688e4e892d497ba] [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9] Setting instance vm_state to ERROR
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9] Traceback (most recent call last):
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/compute/manager.py", line 2250, in do_terminate_instance
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     reservations=reservations)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/hooks.py", line 103, in inner
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     rv = f(*args, **kwargs)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/compute/manager.py", line 2220, in _delete_instance
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     user_id=user_id)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/openstack/common/excutils.py", line 68, in __exit__
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     six.reraise(self.type_, self.value, self.tb)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/compute/manager.py", line 2190, in _delete_instance
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     self._shutdown_instance(context, db_inst, bdms)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/compute/manager.py", line 2125, in _shutdown_instance
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     requested_networks)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/openstack/common/excutils.py", line 68, in __exit__
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     six.reraise(self.type_, self.value, self.tb)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/compute/manager.py", line 2115, in _shutdown_instance
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     block_device_info)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/virt/libvirt/driver.py", line 951, in destroy
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     self._destroy(instance)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/virt/libvirt/driver.py", line 908, in _destroy
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     instance=instance)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/openstack/common/excutils.py", line 68, in __exit__
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     six.reraise(self.type_, self.value, self.tb)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/nova/virt/libvirt/driver.py", line 880, in _destroy
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     virt_dom.destroy()
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/eventlet/tpool.py", line 179, in doit
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     result = proxy_call(self._autowrap, f, *args, **kwargs)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/eventlet/tpool.py", line 139, in proxy_call
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     rv = execute(f,*args,**kwargs)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/eventlet/tpool.py", line 77, in tworker
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     rv = meth(*args,**kwargs)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]   File "/usr/lib/python2.7/dist-packages/libvirt.py", line 918, in destroy
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9]     if ret == -1: raise libvirtError ('virDomainDestroy() failed', dom=self)
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9] libvirtError: Failed to terminate process 22402 with SIGKILL: Device or resource busy
    2014-06-11 16:44:03.169 18063 TRACE nova.compute.manager [instance: c0c5822b-fd4c-45dc-af6d-74a1763952f9] 

Trying to debug, following
https://github.com/gluster/glusterfs/blob/master/doc/admin-guide/en-US/markdown/admin_troubleshooting.md#troubleshooting-file-locks

::
    root@storage4:~# gluster volume statedump cinder

Nothing is written anywhere, so I cannot run clear-locks



After creation of the snapshot, a QCOW2 image is created::

    qemu-img info volume-307c1274-f179-42e7-a1d8-3e593587b02e.e495778c-6cc0-4081-86d2-308ad3fe1d19
    image: volume-307c1274-f179-42e7-a1d8-3e593587b02e.e495778c-6cc0-4081-86d2-308ad3fe1d19
    file format: qcow2
    virtual size: 100G (107374182400 bytes)
    disk size: 6.8G
    cluster_size: 65536
    backing file: volume-307c1274-f179-42e7-a1d8-3e593587b02e
    backing file format: raw
    Format specific information:
        compat: 1.1
        lazy refcounts: false

where `307c1274-f179-42e7-a1d8-3e593587b02e` is the id of the original
volume, and `e495778c-6cc0-4081-86d2-308ad3fe1d19` is the ID of the
snapshot



During heavy tests, the root volume of the machine went
offline. Rebooting the machine, it doesn't seem to boot cleanly::

    [    2.541282] EXT4-fs (vda1): mounting ext3 file system using the ext4 subsystem
    [    2.556061] EXT4-fs (vda1): INFO: recovery required on readonly filesystem
    [    2.566711] EXT4-fs (vda1): write access will be enabled during recovery
    [    3.953667] Buffer I/O error on device vda1, logical block 0
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 1
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 65536
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 65537
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 65538
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 65740
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 66050
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 197209
    [    3.957652] lost page write due to I/O error on vda1
    [    3.957652] Buffer I/O error on device vda1, logical block 197210
    [    3.957652] lost page write due to I/O error on vda1
    [    4.114897] JBD2: recovery failed
    [    4.119188] EXT4-fs (vda1): error loading journal
    mount: mounting /dev/disk/by-uuid/9fff4eb9-c5cd-414f-b119-7e517416e751 on /root failed: Invalid argument
    Begin: Running /scripts/local-bottom ... done.
    done.
    Begin: Running /scripts/init-bottom ... mount: mounting /dev on /root/dev failed: No such file or directory
    done.
    mount: mounting /sys on /root/sys failed: No such file or directory
    mount: mounting /proc on /root/proc failed: No such file or directory
    Target filesystem doesn't have requested /sbin/init.
    No init found. Try passing init= bootarg.


    BusyBox v1.21.1 (Ubuntu 1:1.21.0-1ubuntu1) built-in shell (ash)
    Enter 'help' for a list of built-in commands.



Final notes
-----------

* nova will not use libgfapi for VM started from images downloaded
  from glance, it will only use it for volumes, either:
  - VM starting from a volume
  - Volumes attached to the VM.
  This has an impact on the performance, as mounting
  /var/lib/nova/instances via gluster will use the FUSE implementation
  of the filesystem.

Test replace a brick
--------------------

http://www.gluster.org/pipermail/gluster-users/2013-August/036989.html

* Shutdown glusterd on one storage4 (holding cinder and
  nova-instances)
* rebalance gluster
* remove vg devgroup0 (contains some data)
* re-create vg devgroup0
* replace brick
* rebalance gluster


References
----------

http://www.gluster.org/community/documentation/index.php/Libgfapi_with_qemu_libvirt
https://blueprints.launchpad.net/nova/+spec/glusterfs-native-support
http://www.gluster.org/2012/11/integration-with-kvmqemu/
https://github.com/gluster/glusterfs/tree/master/doc/admin-guide/en-US/markdown
