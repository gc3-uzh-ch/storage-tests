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


Needed for qemu: 
volume set server.allow-insecure on

Also:

root@node-08-01-06:~# id nova
uid=499(nova) gid=499(nova) groups=116(libvirtd),499(nova)

root@storage1:~# gluster vol set cinder storage.owner-uid 499
volume set: success
root@storage1:~# gluster vol set cinder storage.owner-gid 116
volume set: success

This was not enough, however, I had to change the permission on the
filesystem

Also, update to kernel 3.13 also on the storage nodes


Still not working. Why?

2014-06-10 16:35:11.346 12009 DEBUG nova.virt.libvirt.config [req-4776c718-6a92-4923-8413-dff5affa61e0 9150e4f4542843bb8a39872e484483e0 3244794c89194872b688e4e892d497ba] Generated XML ('<disk type="network" device="disk">\n  <driver name="qemu" type="raw" cache="none"/>\n  <source protocol="gluster" name="cinder/volume-da96369a-c7fb-491a-a835-c90e2c0a8591">\n    <host name="storage2" port="24007"/>\n  </source>\n  <target bus="virtio" dev="vdb"/>\n  <serial>da96369a-c7fb-491a-a835-c90e2c0a8591</serial>\n</disk>\n',)  to_xml /usr/lib/python2.7/dist-packages/nova/virt/libvirt/config.py:71

and https://bugzilla.redhat.com/show_bug.cgi?id=1017289

Problem: qemu does not support gluster.
Solution: install qemu from ppa:semiosis/ubuntu-qemu-glusterfs
(or recompile with gluster support)

problem: libvirt does not support gluster
solution: recompile libvirt

On a machine with gluster-common intalled,
apt-get install pbuilder
apt-get build-dep libvirt-bin
apt-get source -b libvirt
