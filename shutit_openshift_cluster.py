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
		machines = ('master1','master2','master3','etcd1','etcd2','etcd3','node1','node2','lb')
		module_name = 'shutit_openshift_cluster_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		# TODO: needs vagrant 1.8.6+
		shutit.send('rm -rf ' + home_dir + '/' + module_name + ' && mkdir -p ' + home_dir + '/' + module_name + ' && cd ~/' + module_name)
		shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(home_dir + '/' + module_name + '/Vagrantfile','''

Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "master1" do |master1|    
    master1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master1.vm.hostname = "master1.vagrant.test"
    #master1.vm.network "private_network", ip: "192.168.2.2"
  end
  config.vm.define "master2" do |master2|    
    master2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master2.vm.hostname = "master2.vagrant.test"
    #master2.vm.network "private_network", ip: "192.168.2.3"
  end
  config.vm.define "master3" do |master3|    
    master3.vm.box = ''' + '"' + vagrant_image + '"' + '''
    master3.vm.hostname = "master3.vagrant.test"
    #master3.vm.network "private_network", ip: "192.168.2.4"
  end

  config.vm.define "lb" do |lb|
    lb.vm.box = ''' + '"' + vagrant_image + '"' + '''
    #lb.vm.network :private_network, ip: "192.168.2.13"
    lb.vm.hostname = "lb.vagrant.test"
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

  config.vm.define "node1" do |node1|
    node1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    #node1.vm.network :private_network, ip: "192.168.2.24"
    node1.vm.hostname = "node1.vagrant.test"
  end
  config.vm.define "node2" do |node2|
    node2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    #node2.vm.network :private_network, ip: "192.168.2.25"
    node2.vm.hostname = "node2.vagrant.test"
  end
end''')
		password = shutit.get_env_pass()
		shutit.multisend('vagrant up --provider virtualbox',{'assword':password},timeout=99999)
		for machine in machines:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
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
		shutit.send('git clone https://github.com/openshift/openshift-ansible -b release-1.3')
		shutit.multisend('ssh-keygen',{'Enter file':'','Enter passphrase':'','Enter same pass':''})
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
openshift_master_cluster_hostname=openshift-cluster.vagrant.test
openshift_master_cluster_public_hostname=openshift-cluster.vagrant.test

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
master3.vagrant.test

# host group for etcd
[etcd]
etcd1.vagrant.test
etcd2.vagrant.test
etcd3.vagrant.test

# Specify load balancer host
[lb]
lb.vagrant.test

# host group for nodes, includes region info
[nodes]
master[1:3].vagrant.test openshift_node_labels="{'region': 'infra', 'zone': 'default'}"
node1.vagrant.test openshift_node_labels="{'region': 'primary', 'zone': 'east'}"
node2.vagrant.test openshift_node_labels="{'region': 'primary', 'zone': 'west'}"''')
		for machine in machines:
			# Set up ansible.
			shutit.multisend('ssh-copy-id root@' + machine,{'ontinue connecting':'yes','assword':'origin'})
			shutit.multisend('ssh-copy-id root@' + machine + '.vagrant.test',{'ontinue connecting':'yes','assword':'origin'})
		shutit.pause_point('ansible-playbook ~/openshift-ansible/playbooks/byo/config.yml')
		shutit.multisend('ansible-playbook ~/openshift-ansible/playbooks/byo/config.yml',{'ontinue connecting':'yes'})
		shutit.logout()
		shutit.logout()
		shutit.pause_point('')

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
		'git.shutit_openshift_cluster.shutit_openshift_cluster', 857091783.0001,   
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
	)
