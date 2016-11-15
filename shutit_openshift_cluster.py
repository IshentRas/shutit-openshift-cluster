import random
import string
import os

from shutit_module import ShutItModule

class shutit_openshift_cluster(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		home_dir = os.path.expanduser('~')
		machine_names = ('master1','master2','etcd1','etcd2','etcd3','node1','openshiftcluster','etcd4','etcd5','etcd6')
		machines = ('master1.vagrant.test','master2.vagrant.test','etcd1.vagrant.test','etcd2.vagrant.test','etcd3.vagrant.test','node1.vagrant.test','openshiftcluster.vagrant.test','etcd4.vagrant.test','etcd5.vagrant.test','etcd6.vagrant.test')
		module_name = 'shutit_openshift_cluster_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		# TODO: needs vagrant 1.8.6+
		shutit.send('rm -rf ' + home_dir + '/' + module_name + ' && mkdir -p ' + home_dir + '/' + module_name + ' && cd ~/' + module_name)
		shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(home_dir + '/' + module_name + '/Vagrantfile','''

Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "''' + memory + '''"
  end
  config.vm.provider "libvirt" do |vb|
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "master1" do |master1|
    master1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master1.vm.network "private_network", ip: "192.168.2.2"
    master1.vm.hostname = "master1.vagrant.test"
    master1.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", "2048"]
      v.customize ["modifyvm", :id, "--cpus", "2"]
    end
  end
  config.vm.define "master2" do |master2|
    master2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master2.vm.network "private_network", ip: "192.168.2.3"
    master2.vm.hostname = "master2.vagrant.test"
  end

  config.vm.define "openshiftcluster" do |openshiftcluster|
    openshiftcluster.vm.box = ''' + '"' + vagrant_image + '"' + '''
    openshiftcluster.vm.network :private_network, ip: "192.168.2.13"
    openshiftcluster.vm.hostname = "openshiftcluster.vagrant.test"
  end

  config.vm.define "etcd1" do |etcd1|
    etcd1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd1.vm.network :private_network, ip: "192.168.2.14"
    etcd1.vm.hostname = "etcd1.vagrant.test"
  end
  config.vm.define "etcd2" do |etcd2|
    etcd2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd2.vm.network :private_network, ip: "192.168.2.15"
    etcd2.vm.hostname = "etcd2.vagrant.test"
  end
  config.vm.define "etcd3" do |etcd3|
    etcd3.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd3.vm.network :private_network, ip: "192.168.2.16"
    etcd3.vm.hostname = "etcd3.vagrant.test"
  end
  config.vm.define "etcd4" do |etcd4|
    etcd4.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd4.vm.network :private_network, ip: "192.168.2.17"
    etcd4.vm.hostname = "etcd4.vagrant.test"
  end
  config.vm.define "etcd5" do |etcd5|
    etcd5.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd5.vm.network :private_network, ip: "192.168.2.18"
    etcd5.vm.hostname = "etcd5.vagrant.test"
  end
  config.vm.define "etcd6" do |etcd6|
    etcd6.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd6.vm.network :private_network, ip: "192.168.2.19"
    etcd6.vm.hostname = "etcd6.vagrant.test"
  end

  config.vm.define "node1" do |node1|
    node1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    node1.vm.network :private_network, ip: "192.168.2.24"
    node1.vm.hostname = "node1.vagrant.test"
  end
end''')
		password = shutit.get_env_pass()
		# TODO: provider
		shutit.multisend('vagrant up --provider virtualbox',{'assword':password},timeout=99999)
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			# Switch off fastest mirror - it gives me nothing but grief (looooong waits)
			shutit.send('''sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf''')
			# See: https://access.redhat.com/articles/1320623
			shutit.send('rm -fr /var/cache/yum/*')
			shutit.send('yum clean all')
			shutit.send('yum update -y')
			shutit.install('xterm')
			shutit.install('net-tools')
			shutit.send('''sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config''')
			shutit.send('echo root:origin | /usr/sbin/chpasswd')
			shutit.send('systemctl restart sshd')
			# This is to prevent ansible from getting the 'wrong' ip address for the host from eth0.
			# See: http://stackoverflow.com/questions/29495704/how-do-you-change-ansible-default-ipv4
			shutit.send('route add -net 8.8.8.8 netmask 255.255.255.255 eth1')
			ip_addr = shutit.send_and_get_output("""ip -4 route get 8.8.8.8 | head -1 | awk '{print $NF}'""")
			shutit.send(r"""sed -i 's/127.0.0.1\t\(.*\).vagrant.test.*/""" + ip_addr + r"""\t\1.vagrant.test\t\1/' /etc/hosts""")
			shutit.logout()
			shutit.logout()
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.install('epel-release')
		shutit.install('git')
		shutit.install('ansible')
		shutit.install('pyOpenSSL')
		shutit.install('etcd') # For the client
		shutit.send('git clone --depth=1 https://github.com/openshift/openshift-ansible -b release-1.3')
		shutit.send_file('/etc/ansible/hosts','''# Create an OSEv3 group that contains the master, nodes, etcd, and lb groups.
# The lb group lets Ansible configure HAProxy as the load balancing solution.
# Comment lb out if your load balancer is pre-configured.
[OSEv3:children]
masters
nodes
etcd
lb

# Set variables common for all OSEv3 hosts
[OSEv3:vars]
ansible_ssh_user=root
deployment_type=origin

# Uncomment the following to enable htpasswd authentication; defaults to
# DenyAllPasswordIdentityProvider.
#openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider', 'filename': '/etc/origin/master/htpasswd'}]

# Native high availbility cluster method with optional load balancer.
# If no lb group is defined installer assumes that a load balancer has
# been preconfigured. For installation the value of
# openshift_master_cluster_hostname must resolve to the load balancer
# or to one or all of the masters defined in the inventory if no load
# balancer is present.
openshift_master_cluster_method=native
openshift_master_cluster_hostname=openshiftcluster.vagrant.test
openshift_master_cluster_public_hostname=openshiftcluster.vagrant.test

# apply updated node defaults
openshift_node_kubelet_args={'pods-per-core': ['10'], 'max-pods': ['250'], 'image-gc-high-threshold': ['90'], 'image-gc-low-threshold': ['80']}

# override the default controller lease ttl
#osm_controller_lease_ttl=30

# enable ntp on masters to ensure proper failover
openshift_clock_enabled=true

# host group for masters
[masters]
master1.vagrant.test
master2.vagrant.test

# host group for etcd
[etcd]
etcd1.vagrant.test
etcd2.vagrant.test
etcd3.vagrant.test

# Specify load balancer host
[lb]
openshiftcluster.vagrant.test

# host group for nodes, includes region info
[nodes]
master[1:2].vagrant.test openshift_node_labels="{'region': 'infra', 'zone': 'default'}"
node1.vagrant.test openshift_node_labels="{'region': 'primary', 'zone': 'east'}"''')
		shutit.logout()
		shutit.logout()
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			shutit.multisend('ssh-keygen',{'Enter file':'','Enter passphrase':'','Enter same pass':''})
			# Set up ansible.
			for othermachine in machine_names:
				shutit.multisend('ssh-copy-id root@' + othermachine,{'ontinue connecting':'yes','assword':'origin'})
				shutit.multisend('ssh-copy-id root@' + othermachine + '.vagrant.test',{'ontinue connecting':'yes','assword':'origin'})
			shutit.logout()
			shutit.logout()
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		while True:
			shutit.multisend('ansible-playbook -vvv ~/openshift-ansible/playbooks/byo/config.yml 2>&1 | tee -a ansible.log',{'ontinue connecting':'yes'})
			if shutit.send_and_match_output('oc get nodes','.*node1.vagrant.test     Ready.*'):
				break
		# Need to set masters as schedulable (why? - ansible seems to un-schedule them)
		shutit.send('oadm manage-node master1.vagrant.test --schedulable')
		shutit.send('oadm manage-node master2.vagrant.test --schedulable')
		# List the etcd members
		shutit.send('etcdctl --endpoints https://192.168.2.14:2379,https://192.168.2.15:2379,https://192.168.2.16:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list')
		shutit.send('git clone --depth=1 https://github.com/openshift/origin')
		shutit.send('cd origin/examples')
		# TODO: https://github.com/openshift/origin/tree/master/examples/data-population
		shutit.send('cd data-population')
		shutit.send('ln -s /etc/origin openshift.local.config')
		shutit.send("""sed -i 's/10.0.2.15/openshiftcluster/g' common.sh""")
		#shutit.send('./populate.sh')
		shutit.logout()
		shutit.logout()

		#shutit.pause_point('Migrate etcd....')
		# Get backup
		# https://docs.openshift.com/enterprise/3.2/install_config/upgrading/manual_upgrades.html#preparing-for-a-manual-upgrade
		for machine in ('etcd1','etcd2','etcd3'):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			shutit.send('ETCD_DATA_DIR=/var/lib/etcd')
			shutit.send('etcdctl backup --data-dir $ETCD_DATA_DIR --backup-dir $ETCD_DATA_DIR.backup')
			shutit.send('cp /etc/etcd/etcd.conf /etc/etcd/etcd.conf.bak')
			shutit.logout()
			shutit.logout()
		# https://docs.openshift.com/enterprise/3.2/install_config/downgrade.html
		for machine in ('master1','master2'):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			#shutit.send('systemctl stop atomic-openshift-master-api')
			#shutit.send('systemctl stop atomic-openshift-master-controllers')
			#shutit.send('systemctl stop atomic-openshift-node')
			shutit.send('systemctl stop origin-master-api')
			shutit.send('systemctl stop origin-master-controllers')
			shutit.send('systemctl stop origin-node')
			shutit.logout()
			shutit.logout()
		for machine in ('master1','master2','node1'):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			#shutit.send('systemctl stop atomic-openshift-node')
			shutit.send('systemctl stop origin-node')
			shutit.logout()
			shutit.logout()

		# Generate certs for new nodes
		shutit.login(command='vagrant ssh etcd1')
		shutit.login(command='sudo su - ')
		etcd_openssl_conf = '/etc/etcd/openssl.conf'
		for newnode in ('etcd4','etcd5','etcd6'):
			shutit.send('ETCDSERVER=' + newnode + '.vagrant.test')
			if newnode == 'etcd4':
				shutit.send('ETCDIP=192.168.2.17')
				etcdip = '192.168.2.17'
			elif newnode == 'etcd5':
				shutit.send('ETCDIP=192.168.2.18')
				etcdip = '192.168.2.18'
			elif newnode == 'etcd6':
				shutit.send('ETCDIP=192.168.2.19')
				etcdip = '192.168.2.19'
			shutit.send('mkdir -p /etc/etcd/generated_certs/etcd-${ETCDSERVER}')
			shutit.send('cd /etc/etcd/generated_certs/etcd-${ETCDSERVER}')
			shutit.send('cp /etc/etcd/ca.crt .')
			shutit.send('export SAN=IP:${ETCDIP}')
			shutit.send('openssl req -new -keyout peer.key -config /etc/etcd/ca/openssl.cnf -out peer.csr -reqexts etcd_v3_req -batch -nodes -subj /CN=${ETCDSERVER}')
			shutit.send('openssl ca -name etcd_ca -config /etc/etcd/ca/openssl.cnf -out peer.crt -in peer.csr -extensions etcd_v3_ca_peer -batch')
			shutit.send('openssl req -new -keyout server.key -config /etc/etcd/ca/openssl.cnf -out server.csr -reqexts etcd_v3_req -batch -nodes -subj /CN=${ETCDSERVER}')
			shutit.send('openssl ca -name etcd_ca -config /etc/etcd/ca/openssl.cnf -out server.crt -in server.csr -extensions etcd_v3_ca_server -batch')
			shutit.send('tar -czvf /etc/etcd/generated_certs/etcd-${ETCDSERVER}.tgz -C /etc/etcd/generated_certs/etcd-${ETCDSERVER} .')
			shutit.send('cd ..')
			shutit.multisend('scp etcd-' + newnode + '.vagrant.test.tgz vagrant@' + newnode + ':',{'onnecting':'yes','assword':'vagrant'})
			shutit.multisend('scp /etc/etcd/etcd.conf vagrant@' + newnode + ':',{'onnecting':'yes','assword':'vagrant'})
			# Add node and get the output
			shutit.login(command='ssh master1')
			shutit.send('etcdctl --endpoints https://192.168.2.14:2379,https://192.168.2.15:2379,https://192.168.2.16:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member add ' + newnode + '.vagrant.test https://' + etcdip + ':2380 | grep ^ETCD > /tmp/out',note='Add node to cluster')
			etcd_config = shutit.send_and_get_output('cat /tmp/out')
			shutit.logout()
			shutit.login(command='ssh ' + newnode)
			shutit.install('etcd')
			shutit.send('cd /etc/etcd/')
			shutit.send('tar -zxf /home/vagrant/etcd-' + newnode + '.vagrant.test.tgz')
			shutit.send('chown etcd:etcd /etc/etcd/ca.crt /etc/etcd/server.key /etc/etcd/server.crt /etc/etcd/peer.key /etc/etcd/peer.crt')
			shutit.send('rm -f /etc/etcd/etcd.conf && cp /home/vagrant/etcd.conf /etc/etcd')
			shutit.send('chown root:root /etc/etcd/etcd.conf')
			shutit.send(r"""sed -i 's/ETCD_LISTEN_PEER_URLS=https:\/\/192.168.2.14:2380/ETCD_LISTEN_PEER_URLS=https:\/\/""" + etcdip + """:2380/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/ETCD_LISTEN_CLIENT_URLS=https:\/\/192.168.2.14:2379/ETCD_LISTEN_CLIENT_URLS=https:\/\/""" + etcdip + """:2379/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/ETCD_INITIAL_ADVERTISE_PEER_URLS=https:\/\/192.168.2.14:2380/ETCD_INITIAL_ADVERTISE_PEER_URLS=https:\/\/""" + etcdip + """:2380/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/ETCD_INITIAL_ADVERTISE_CLIENT_URLS=https:\/\/192.168.2.14:2379/ETCD_INITIAL_ADVERTISE_CLIENT_URLS=https:\/\/""" + etcdip + """:2379/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/^ETCD_NAME=.*//' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/^ETCD_INITIAL_CLUSTER=.*//' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/^ETCD_INITIAL_CLUSTER_STATE=.*//' /etc/etcd/etcd.conf""")
			shutit.send('''cat >> /etc/etcd/etcd.conf << END
''' + etcd_config + '''
END''')
			shutit.logout()
			shutit.pause_point('Try starting up etcd on ' + newnode)
		shutit.logout()
		shutit.logout()
		# TODO: update chef scritps?
		# TODO: update master config
		# TODO: bring cluster back up

# OLD
		# Chef variables
		#master_generate_certs_dir = '/var/www/html/master/generated_certs'
		#master_etcd_cert_prefix = 'master.etcd-'
		#master_server_fqdn = 'master1.vagrant.test'
		#master_server_ip = '192.168.2.2'
		#master_etcd_cert_prefix = 'etcd_v3_req'
#		# etcd_master == master1 in this chef script
#		for j
#        %w(server peer).each do |etcd_certificates|
#            command "openssl req -new -keyout #{etcd_certificates}.key -config #{node['cookbook-openshift3']['etcd_openssl_conf']} -out #{etcd_certificates}.csr -reqexts #{node['cookbook-openshift3']['etcd_req_ext']} -batch -nodes -subj /CN=#{etcd_master['fqdn']}"
#            environment 'SAN' => "IP:#{etcd_master['ipaddress']}"
#            cwd "#{node['cookbook-openshift3']['etcd_generated_certs_dir']}/etcd-#{etcd_master['fqdn']}"
#            creates "#{node['cookbook-openshift3']['etcd_generated_certs_dir']}/etcd-#{etcd_master['fqdn']}/#{etcd_certificates}.csr"
#
#            command "openssl ca -name #{node['cookbook-openshift3']['etcd_ca_name']} -config #{node['cookbook-openshift3']['etcd_openssl_conf']} -out #{etcd_certificates}.crt -in #{etcd_certificates}.csr -extensions #{node['cookbook-openshift3']["etcd_ca_exts_#{etcd_certificates}"]} -batch"
#            environment 'SAN' => ''
#            cwd "#{node['cookbook-openshift3']['etcd_generated_certs_dir']}/etcd-#{etcd_master['fqdn']}"
#            creates "#{node['cookbook-openshift3']['etcd_generated_certs_dir']}/etcd-#{etcd_master['fqdn']}/#{etcd_certificates}.crt"
#
#        link "#{node['cookbook-openshift3']['etcd_generated_certs_dir']}/etcd-#{etcd_master['fqdn']}/ca.crt" do
#          to "#{node['cookbook-openshift3']['etcd_ca_dir']}/ca.crt"
#          link_type :hard
#        end

#        #cwd "#{node['cookbook-openshift3']['master_generated_certs_dir']}/openshift_master-#{master_server['fqdn']}"
#		shutit.send('cd ' + master_generated_certs_dir + '/openshift_master-' + master_server_fqdn)
#        #environment 'SAN' => "IP:#{master_server['ipaddress']}"
#		shutit.send('export SAN=' + master_server_ip)
#		#command "openssl req -new -keyout #{node['cookbook-openshift3']['master_etcd_cert_prefix']}client.key -config #{node['cookbook-openshift3']['etcd_openssl_conf']} -out #{node['cookbook-openshift3']['master_etcd_cert_prefix']}client.csr -reqexts #{node['cookbook-openshift3']['etcd_req_ext']} -batch -nodes -subj /CN=#{master_server['fqdn']}"
#		shutit.send('openssl req -new -keyout ' + master_etcd_cert_prefix + 'client.key -config ' + etcd_openssl_conf + ' -out ' + master_etcd_cert_prefix + 'client.csr -reqexts ' + master_etcd_cert_prefix + ' -batch -nodes -subj /CN=' + master_server_fqdn)
#
#		#cwd "#{node['cookbook-openshift3']['master_generated_certs_dir']}/openshift_master-#{master_server['fqdn']}"
#		shutit.send('cd ' + master_generated_certs_dir + '/openshift_master-' + master_server_fqdn)
#		#environment 'SAN' => ''
#		shutit.send('export SAN=""')
#		#command "openssl ca -name #{node['cookbook-openshift3']['etcd_ca_name']} -config #{node['cookbook-openshift3']['etcd_openssl_conf']} -out #{node['cookbook-openshift3']['master_etcd_cert_prefix']}client.crt -in #{node['cookbook-openshift3']['master_etcd_cert_prefix']}client.csr -batch"
#		shutit.send('openssl ca -name ' + etcd_ca_name + ' -config ' + etcd_openssl_conf + ' -out ' + master_etcd_cert_prefix + 'client.crt -in ' + master_etcd_cert_prefix + 'client.csr -batch')
#
#		#link "#{node['cookbook-openshift3']['master_generated_certs_dir']}/openshift_master-#{master_server['fqdn']}/#{node['cookbook-openshift3']['master_etcd_cert_prefix']}ca.crt" do
#		#to "#{node['cookbook-openshift3']['etcd_ca_dir']}/ca.crt"
#		#link_type :hard
#		shutit.send('ln ' + master_generated_certs_dir + '/openshift_master-' + master_server_fqdn + '/' + master_etcd_cert_prefix + 'ca.crt ' + etcd_ca_dir + '/ca/crt')
#
#    execute "Create a tarball of the etcd master certs for #{master_server['fqdn']}" do
#      command "tar czvf #{node['cookbook-openshift3']['master_generated_certs_dir']}/openshift_master-#{master_server['fqdn']}.tgz -C #{node['cookbook-openshift3']['master_generated_certs_dir']}/openshift_master-#{master_server['fqdn']} . "
#      creates "#{node['cookbook-openshift3']['master_generated_certs_dir']}/openshift_master-#{master_server['fqdn']}.tgz"
#    end
#		shutit.pause_point('add items on the fly: https://coreos.com/etcd/docs/latest/v2/admin_guide.html#member-migration')
#		shutit.logout()
#		shutit.logout()

		# OLD METHOD
		## Stop etcd
		#for machine in ('etcd1','etcd2','etcd3'):
		#	shutit.login(command='vagrant ssh ' + machine)
		#	shutit.login(command='sudo su - ')
		#	shutit.send('systemctl stop etcd')
		#	shutit.logout()
		#	shutit.logout()
		## Uninstall etcd
		#for machine in ('etcd1','etcd2','etcd3'):
		#	shutit.login(command='vagrant ssh ' + machine)
		#	shutit.login(command='sudo su - ')
		#	shutit.remove('etcd')
		#	shutit.logout()
		#	shutit.logout()
		## Reinstall etcd
		#for machine in ('etcd1','etcd2','etcd3'):
		#	shutit.login(command='vagrant ssh ' + machine)
		#	shutit.login(command='sudo su - ')
		#	shutit.install('etcd')
		#	shutit.logout()
		#	shutit.logout()
		#shutit.pause_point('https://docs.openshift.com/enterprise/3.2/install_config/downgrade.html#downgrading-restoring-external-etcd')
		#shutit.login(command='vagrant ssh etcd1')
		#shutit.login(command='sudo su - ')
		## Run the following on the etcd host:
		#shutit.send('ETCD_DIR=/var/lib/etcd')
		#shutit.send('mv $ETCD_DIR /var/lib/etcd.orig')
		#shutit.send('cp -Rp ${ETCD_DIR}.backup $ETCD_DIR')
		#shutit.send('chcon -R --reference /var/lib/etcd.orig/ $ETCD_DIR')
		#shutit.send('chown -R etcd:etcd $ETCD_DIR')
		## Restore your /etc/etcd/etcd.conf file from backup or .rpmsave.
		#shutit.send('cp /etc/etcd/etcd.conf.bak /etc/etcd/etcd.conf')
		#shutit.send("""sed -i '/ExecStart/s/"$/  --force-new-cluster"/' /usr/lib/systemd/system/etcd.service""")
		#shutit.send('systemctl daemon-reload')
		#shutit.send('systemctl start etcd')
		#shutit.send('systemctl status etcd')

		## Verify the etcd service started correctly, then re-edit the /usr/lib/systemd/system/etcd.service file and remove the --force-new-cluster option:
		#shutit.send("""sed -i '/ExecStart/s/ --force-new-cluster//' /usr/lib/systemd/system/etcd.service""")
		#shutit.send('systemctl daemon-reload')
		#shutit.send('systemctl start etcd')
		#shutit.send('systemctl status etcd')
		#shutit.send('etcdctl --cert-file=/etc/etcd/peer.crt --key-file=/etc/etcd/peer.key --ca-file=/etc/etcd/ca.crt --peers="https://192.168.2.14:2379" ls')
		#shutit.send('etcdctl --cert-file=/etc/etcd/peer.crt --key-file=/etc/etcd/peer.key --ca-file=/etc/etcd/ca.crt --peers="https://192.168.2.14:2379" member list')

		## Adding a new node
		#etcd_first_member_id = shutit.send_and_get_output("""etcdctl --cert-file=/etc/etcd/peer.crt --key-file=/etc/etcd/peer.key --ca-file=/etc/etcd/ca.crt --peers="https://192.168.2.14:2379" member list | awk -F: '{print $1}'""")
		## Replace the initial with a single node
		#shutit.send("""sed -i 's/^ETCD.*/ETCD_INITIAL_ADVERTISE_PEER_URLS=https:\/\/192.168.2.14:2380/'""")
		#shutit.send('''etcdctl --cert-file=/etc/etcd/peer.crt --key-file=/etc/etcd/peer.key --ca-file=/etc/etcd/ca.crt --peers="https://192.168.2.14:2379" member update ''' + etcd_first_member_id + ''' https://192.168.2.14:2380''')
		#shutit.pause_point('Re-run the member list command and ensure the peer URLs no longer include localhost.')

		## TODO: add nodes
		#shutit.logout()
		#shutit.logout()
		return True

	def get_config(self, shutit):
		#shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/trusty64')
		shutit.get_config(self.module_id,'vagrant_image',default='centos/7')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		#shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'memory',default='512')
		return True

	def test(self, shutit):

		return True

	def finalize(self, shutit):

		return True

	def isinstalled(self, shutit):

		return False

	def start(self, shutit):

		return True

	def stop(self, shutit):

		return True

def module():
	return shutit_openshift_cluster(
		'tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster', 857091783.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
