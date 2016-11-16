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
    master1.vm.hostname = "master1.vagrant.test"
    master1.vm.provider :virtualbox do |v|
      v.customize ["modifyvm", :id, "--memory", "2048"]
      v.customize ["modifyvm", :id, "--cpus", "2"]
    end
  end
  config.vm.define "master2" do |master2|
    master2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master2.vm.hostname = "master2.vagrant.test"
  end
  config.vm.define "master3" do |master3|    
    master3.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master3.vm.hostname = "master3.vagrant.test"
  end

  config.vm.define "openshiftcluster" do |openshiftcluster|
    openshiftcluster.vm.box = ''' + '"' + vagrant_image + '"' + '''
    openshiftcluster.vm.hostname = "openshiftcluster.vagrant.test"
  end

  config.vm.define "etcd1" do |etcd1|
    etcd1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd1.vm.hostname = "etcd1.vagrant.test"
  end
  config.vm.define "etcd2" do |etcd2|
    etcd2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd2.vm.hostname = "etcd2.vagrant.test"
  end
  config.vm.define "etcd3" do |etcd3|
    etcd3.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd3.vm.hostname = "etcd3.vagrant.test"
  end
  config.vm.define "etcd4" do |etcd4|
    etcd4.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd4.vm.hostname = "etcd4.vagrant.test"
  end
  config.vm.define "etcd5" do |etcd5|
    etcd5.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd5.vm.hostname = "etcd5.vagrant.test"
  end
  config.vm.define "etcd6" do |etcd6|
    etcd6.vm.box = ''' + '"' + vagrant_image + '"' + '''
    etcd6.vm.hostname = "etcd6.vagrant.test"
  end

  config.vm.define "node1" do |node1|
    node1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    node1.vm.hostname = "node1.vagrant.test"
  end
end''')
		password = shutit.get_env_pass()
		shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'],{'assword':password},timeout=99999)
		master1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master1.vagrant.test | awk '{print $2}'""")
		master2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master2.vagrant.test | awk '{print $2}'""")
		etcd1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd1.vagrant.test | awk '{print $2}'""")
		etcd2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd2.vagrant.test | awk '{print $2}'""")
		etcd3_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd3.vagrant.test | awk '{print $2}'""")
		etcd4_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd4.vagrant.test | awk '{print $2}'""")
		etcd5_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd5.vagrant.test | awk '{print $2}'""")
		etcd6_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd6.vagrant.test | awk '{print $2}'""")
		node1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^node1.vagrant.test | awk '{print $2}'""")
		openshiftcluster_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^openshiftcluster.vagrant.test' | awk '{print $2}'""")
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			# Switch off fastest mirror - it gives me nothing but grief (looooong waits)
			shutit.send('''sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf''')
			# See: https://access.redhat.com/articles/1320623
			shutit.send('rm -fr /var/cache/yum/*')
			shutit.send('yum clean all')
			shutit.send('yum update -y -q')
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
		shutit.send('etcdctl --endpoints https://' + etcd1_ip + ':2379,https://' + etcd2_ip + ':2379,https://' + etcd3_ip + ':2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list')
		shutit.send('git clone --depth=1 https://github.com/openshift/origin')
		shutit.send('cd origin/examples')
		# TODO: https://github.com/openshift/origin/tree/master/examples/data-population
		shutit.send('cd data-population')
		shutit.send('ln -s /etc/origin openshift.local.config')
		shutit.send("""sed -i 's/10.0.2.15/openshiftcluster/g' common.sh""")
		#shutit.send('./populate.sh')
		shutit.logout()
		shutit.logout()

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
				etcdip = etcd4_ip
			elif newnode == 'etcd5':
				etcdip = etcd5_ip
			elif newnode == 'etcd6':
				etcdip = etcd6_ip
			shutit.send('mkdir -p /etc/etcd/generated_certs/etcd-${ETCDSERVER}')
			shutit.send('cd /etc/etcd/generated_certs/etcd-${ETCDSERVER}')
			shutit.send('cp /etc/etcd/ca.crt .')
			shutit.send('export SAN=IP:' + etcdip)
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
			shutit.send('etcdctl --endpoints https://' + etcd1_ip + ':2379,https://' + etcd2_ip + ':2379,https://' + etcd3_ip + ':2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member add ' + newnode + '.vagrant.test https://' + etcdip + ':2380 | grep ^ETCD > /tmp/out',note='Add node to cluster')
			etcd_config = shutit.send_and_get_output('cat /tmp/out')
			shutit.logout()
			shutit.login(command='ssh ' + newnode)
			shutit.install('etcd')
			shutit.send('cd /etc/etcd/')
			shutit.send('tar -zxf /home/vagrant/etcd-' + newnode + '.vagrant.test.tgz')
			shutit.send('chown etcd:etcd /etc/etcd/ca.crt /etc/etcd/server.key /etc/etcd/server.crt /etc/etcd/peer.key /etc/etcd/peer.crt')
			shutit.send('rm -f /etc/etcd/etcd.conf && cp /home/vagrant/etcd.conf /etc/etcd')
			shutit.send('chown root:root /etc/etcd/etcd.conf')
			shutit.send(r"""sed -i 's/ETCD_LISTEN_PEER_URLS=https:\/\/""" + etcd1_ip + r""":2380/ETCD_LISTEN_PEER_URLS=https:\/\/""" + etcdip + """:2380/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/ETCD_LISTEN_CLIENT_URLS=https:\/\/""" + etcd1_ip + r""":2379/ETCD_LISTEN_CLIENT_URLS=https:\/\/""" + etcdip + """:2379/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/ETCD_INITIAL_ADVERTISE_PEER_URLS=https:\/\/""" + etcd1_ip + r""":2380/ETCD_INITIAL_ADVERTISE_PEER_URLS=https:\/\/""" + etcdip + """:2380/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/ETCD_ADVERTISE_CLIENT_URLS=https:\/\/""" + etcd1_ip r""":2379/ETCD_INITIAL_ADVERTISE_CLIENT_URLS=https:\/\/""" + etcdip + """:2379/g' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/^ETCD_NAME=.*//' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/^ETCD_INITIAL_CLUSTER=.*//' /etc/etcd/etcd.conf""")
			shutit.send(r"""sed -i 's/^ETCD_INITIAL_CLUSTER_STATE=.*//' /etc/etcd/etcd.conf""")
			shutit.send('''cat >> /etc/etcd/etcd.conf << END
''' + etcd_config + '''
END''')
			shutit.send('systemctl start etcd')
			shutit.logout()
		shutit.logout()
		shutit.logout()

		# Now drop members
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		# Note new list of endpoints
		shutit.send("""etcdctl --endpoints https://""" + etcd4_ip + """:2379,https://""" + etcd5_ip + r""":2379,https://""" + etcd6_ip + r""":2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list | grep name.etcd1 | awk -F: '{print $1}' > /tmp/out""")
		etcd1_id = shutit.send_and_get_output('cat /tmp/out')
		shutit.send('etcdctl --endpoints https://' + etcd4_ip + ':2379,https://' + etcd5_ip + r':2379,https://' + etcd6_ip + r':2379  --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member remove ' + etcd1_id,note='Add node to cluster')

		shutit.send("""etcdctl --endpoints https://""" + etcd4_ip + """:2379,https://""" + etcd5_ip + r""":2379,https://""" + etcd6_ip + r""":2379  --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list | grep name.etcd2 | awk -F: '{print $1}' > /tmp/out""")
		etcd2_id = shutit.send_and_get_output('cat /tmp/out')
		shutit.send('etcdctl --endpoints ' + etcd4_ip + ':2379,https://' + etcd5_ip + r':2379,https://' + etcd6_ip + r':2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member remove ' + etcd2_id,note='Add node to cluster')

		shutit.send("""etcdctl --endpoints https://""" + etcd4_ip + """:2379,https://""" + etcd5_ip + r""":2379,https://""" + etcd6_ip + r""":2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list | grep name.etcd3 | awk -F: '{print $1}' > /tmp/out""")
		etcd3_id = shutit.send_and_get_output('cat /tmp/out')
		shutit.send('etcdctl --endpoints ' + etcd4_ip + ':2379,https://' + etcd5_ip + r':2379,https://' + etcd6_ip + r':2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member remove ' + etcd3_id,note='Add node to cluster')
		shutit.logout()
		shutit.logout()

		# clean out the etcd1-3 servers
		for server in ('etcd1','etcd2','etcd3'):
			shutit.login(command='vagrant ssh ' + server)
			shutit.login(command='sudo su - ')
			shutit.send('yum remove -y etcd')
			shutit.logout()
			shutit.logout()

		# update master config and bring cluster up
		for server in ('master1','master2'):
			shutit.login(command='vagrant ssh ' + server)
			shutit.login(command='sudo su - ')
			shutit.send("""sed -i 's/etcd1/etcd4/g' /etc/origin/master/master-config.yaml""")
			shutit.send("""sed -i 's/etcd2/etcd5/g' /etc/origin/master/master-config.yaml""")
			shutit.send("""sed -i 's/etcd3/etcd6/g' /etc/origin/master/master-config.yaml""")
			shutit.send('systemctl restart origin-master-controllers')
			shutit.send('systemctl restart origin-master-api')
			shutit.logout()
			shutit.logout()

		for server in ('master1','master2','node1'):
			shutit.login(command='vagrant ssh ' + server)
			shutit.login(command='sudo su - ')
			shutit.send('systemctl restart origin-node')
			shutit.logout()
			shutit.logout()

		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send("""sed -i 's/etcd1/etcd4/g' /etc/ansible/hosts""")
		shutit.send("""sed -i 's/etcd2/etcd5/g' /etc/ansible/hosts""")
		shutit.send("""sed -i 's/etcd3/etcd6/g' /etc/ansible/hosts""")
		while True:
			shutit.multisend('ansible-playbook ~/openshift-ansible/playbooks/byo/config.yml 2>&1 | tee -a ansible.log',{'ontinue connecting':'yes'})
			if shutit.send_and_match_output('oc get nodes','.*node1.vagrant.test     Ready.*'):
				break
		# Need to set masters as schedulable (why? - ansible seems to un-schedule them)
		shutit.send('oadm manage-node master1.vagrant.test --schedulable')
		shutit.send('oadm manage-node master2.vagrant.test --schedulable')
		shutit.logout()
		shutit.logout()
		shutit.pause_point('etcd cluster moved and ansible re-run. all should be a-ok now.')
		return True

	def get_config(self, shutit):
		#shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/trusty64')
		shutit.get_config(self.module_id,'vagrant_image',default='centos/7')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		#shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'memory',default='512')
		shutit.get_config('shutit-library.virtualization.virtualization.virtualization','virt_method',default='virtualbox')
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
