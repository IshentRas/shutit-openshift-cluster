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
	master1.vm.hostname = "master1.vagrant.test"
	master1.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "2048"]
	  v.customize ["modifyvm", :id, "--cpus", "2"]
	end
  end
  config.vm.define "master2" do |master2|
	master2.vm.box = ''' + '"' + vagrant_image + '"' + '''
	master2.vm.hostname = "master2.vagrant.test"
	master2.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "2048"]
	  v.customize ["modifyvm", :id, "--cpus", "2"]
	end
  end
  config.vm.define "master3" do |master3|
	master3.vm.box = ''' + '"' + vagrant_image + '"' + '''
	master3.vm.hostname = "master3.vagrant.test"
	master3.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "2048"]
	  v.customize ["modifyvm", :id, "--cpus", "2"]
	end
  end

  config.vm.define "node1" do |node1|
	node1.vm.box = ''' + '"' + vagrant_image + '"' + '''
	node1.vm.hostname = "node1.vagrant.test"
	node1.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "512"]
	  v.customize ["modifyvm", :id, "--cpus", "2"]
	end
  end
end''')
		machine_names = ('master1','master2','master3','node1')
		machines = ('master1.vagrant.test','master2.vagrant.test','master3.vagrant.test','node1.vagrant.test')
		if shutit.whoami() != 'root':
			pw = shutit.get_env_pass()
		else:
			pw = ''
		for machine in machine_names:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + ' ' + machine,{'assword for':pw},timeout=99999)
		###############################################################################
		# SET UP MACHINES AND START CLUSTER
		###############################################################################
		master1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master1.vagrant.test | awk '{print $2}'""")
		master2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master2.vagrant.test | awk '{print $2}'""")
		master3_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master3.vagrant.test | awk '{print $2}'""")
		node1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^node1.vagrant.test | awk '{print $2}'""")
		#shutit.begin_asciinema_session(title='chef shutit multinode setup')
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			shutit.send('''sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf''',note='Switch off fastest mirror - it gives me nothing but grief (looooong waits')
			shutit.send('rm -fr /var/cache/yum/*')
			shutit.send('yum clean all')
			shutit.install('xterm')
			shutit.install('net-tools')
			shutit.install('git')
			# Allow logins via ssh between machines
			shutit.send('''sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config''',note='Allow logins between machines')
			shutit.send('echo root:origin | /usr/sbin/chpasswd',note='set root password')
			shutit.send('systemctl restart sshd',note='restart sshd')
			shutit.install('epel-release')
			shutit.send('rpm -i https://packages.chef.io/files/stable/chef/12.4.1/el/7/chef-12.4.1-1.el7.x86_64.rpm',note='install chef')
			shutit.send('mkdir -p /root/chef-solo-example /root/chef-solo-example/cookbooks /root/chef-solo-example/environments /root/chef-solo-example/logs',note='Create chef folders')
			shutit.send('cd /root/chef-solo-example/cookbooks')
			shutit.send('git clone https://github.com/IshentRas/cookbook-openshift3',note='Clone chef repo')
			# Filthy hack to 'override' the node['ipaddress'] value
			ip_addr = shutit.send_and_get_output("""ip -4 addr show dev eth1 | grep inet | awk '{print $2}' | awk -F/ '{print $1}'""")
			shutit.send('''sed -i 's/#{node..ipaddress..}/''' + ip_addr + '''/g' /root/chef-solo-example/cookbooks/cookbook-openshift3/attributes/default.rb''')
			shutit.send("""sed -i "s/node..ipaddress../'""" + ip_addr + """'/g" /root/chef-solo-example/cookbooks/cookbook-openshift3/attributes/default.rb""")

			shutit.send('curl -L https://supermarket.chef.io/cookbooks/iptables/versions/1.0.0/download | tar -zxvf -',note='Get cookbook dependencies')
			shutit.send('curl -L https://supermarket.chef.io/cookbooks/yum/download | tar -zxvf -')
			shutit.send('curl -L https://supermarket.chef.io/cookbooks/selinux_policy/download | tar -zxvf -')
			shutit.send('curl -L https://supermarket.chef.io/cookbooks/compat_resource/download | tar -zxvf -')
			shutit.send_file('/root/chef-solo-example/solo.rb','''cookbook_path [
			   '/root/chef-solo-example/cookbooks',
			   '/root/chef-solo-example/site-cookbooks'
			  ]
environment_path '/root/chef-solo-example/environments'
file_backup_path '/root/chef-solo-example/backup'
file_cache_path '/root/chef-solo-example/cache'
log_location STDOUT
solo true''',note='Create solo.rb file')

			shutit.send_file('''/root/chef-solo-example/environments/ocp-cluster-environment.json''','''{
  "name": "ocp-cluster-environment",
  "description": "",
  "cookbook_versions": {
									  },
  "json_class": "Chef::Environment",
  "chef_type": "environment",
  "default_attributes": {

  },
  "override_attributes": {
	"cookbook-openshift3": {
	  "openshift_HA": true,
	  "openshift_cluster_name": "master1.vagrant.test",
	  "openshift_master_cluster_vip": "''' + master1_ip + '''",
	  "openshift_deployment_type": "origin",
	  "master_servers": [
		{
		  "fqdn": "master1.vagrant.test",
		  "ipaddress": "''' + master1_ip + '''"
		},
		{
		  "fqdn": "master2.vagrant.test",
		  "ipaddress": "''' + master2_ip + '''"
		},
		{
		  "fqdn": "master3.vagrant.test",
		  "ipaddress": "''' + master3_ip + '''"
		}
	  ],
	  "master_peers": [
		{
		  "fqdn": "master2.vagrant.test",
		  "ipaddress": "''' + master2_ip + '''"
		},
		{
		  "fqdn": "master3.vagrant.test",
		  "ipaddress": "''' + master3_ip + '''"
		}
	  ],
	  "etcd_servers": [
		{
		  "fqdn": "master1.vagrant.test",
		  "ipaddress": "''' + master1_ip + '''"
		},
		{
		  "fqdn": "master2.vagrant.test",
		  "ipaddress": "''' + master2_ip + '''"
		},
		{
		  "fqdn": "master3.vagrant.test",
		  "ipaddress": "''' + master3_ip + '''"
		}
	  ],
	  "node_servers": [
		{
		  "fqdn": "node1.vagrant.test",
		  "ipaddress": "''' + node1_ip + '''"
		},
		{
		  "fqdn": "master1.vagrant.test",
		  "ipaddress": "''' + master1_ip + '''"
		},
		{
		  "fqdn": "master2.vagrant.test",
		  "ipaddress": "''' + master2_ip + '''"
		},
		{
		  "fqdn": "master3.vagrant.test",
		  "ipaddress": "''' + master3_ip + '''"
		}
	  ]
	}
  }
}''',note='Create environment file')
			shutit.logout()
			shutit.logout()

		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			shutit.send('echo "*/5 * * * * chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb >> /root/chef-solo-example/logs/chef.log 2>&1" | crontab',note='set up crontab on ' + machine)
			shutit.logout()
			shutit.logout()
		
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send_until('oc get all','.*kubernetes.*',cadence=60,note='Wait until oc get all returns OK')
		shutit.send_until('oc get nodes','master1.* Ready.*',cadence=60,note='Wait until oc get all returns OK')
		shutit.send_until('oc get nodes','master2.* Ready.*',cadence=60,note='Wait until oc get all returns OK')
		shutit.send_until('oc get nodes','master3.* Ready.*',cadence=60,note='Wait until oc get all returns OK')
		shutit.send_until('oc get nodes','node1.* Ready.*',cadence=60,note='Wait until oc get all returns OK')
		#shutit.end_asciinema_session()
		shutit.pause_point('')
		shutit.logout()
		shutit.logout()
		###############################################################################
		# TODO: set up core services
		#shutit.send('git clone --depth=1 https://github.com/openshift/origin')
		#shutit.send('cd origin/examples')
		## TODO: https://github.com/openshift/origin/tree/master/examples/data-population
		#shutit.send('cd data-population')
		#shutit.send('ln -s /etc/origin openshift.local.config')
		#shutit.send('./populate.sh')
		###############################################################################

		return True


	def get_config(self, shutit):
		#shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/trusty64')
		shutit.get_config(self.module_id,'vagrant_image',default='centos/7')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		#shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'memory',default='512')
		return True


def module():
	return shutit_openshift_cluster(
		'tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster', 857091783.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
