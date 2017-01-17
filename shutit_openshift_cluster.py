import random
import string
import os
import inspect

from shutit_module import ShutItModule

class shutit_openshift_cluster(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.cfg[self.module_id]['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		run_dir = shutit.cfg[self.module_id]['vagrant_run_dir']
		module_name = 'shutit_openshift_cluster_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.send('command rm -rf ' + run_dir + '/' + module_name + ' && command mkdir -p ' + run_dir + '/' + module_name + ' && command cd ' + run_dir + '/' + module_name)
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(run_dir + '/' + module_name + '/Vagrantfile','''

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
  config.vm.define "node2" do |node2|
	node2.vm.box = ''' + '"' + vagrant_image + '"' + '''
	node2.vm.hostname = "node2.vagrant.test"
	node2.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "512"]
	  v.customize ["modifyvm", :id, "--cpus", "2"]
	end
  end
end''')
		machine_names = ('master1','master2','master3','node1','node2',)
		machines = ('master1.vagrant.test','master2.vagrant.test','master3.vagrant.test','node1.vagrant.test','node2.vagrant.test',)
		pw = shutit.get_env_pass()
		for machine in machine_names:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + ' ' + machine,{'assword for':pw},timeout=99999)
		###############################################################################
		# SET UP MACHINES AND START CLUSTER
		###############################################################################
		master1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master1.vagrant.test | awk '{print $2}'""")
		master2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master2.vagrant.test | awk '{print $2}'""")
		master3_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master3.vagrant.test | awk '{print $2}'""")
		node1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^node1.vagrant.test | awk '{print $2}'""")
		node2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^node2.vagrant.test | awk '{print $2}'""")
		
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')

			# Switch off fastest mirror - it gives me nothing but grief (looooong waits)
			shutit.send('''sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/fastestmirror.conf''')
			# See: https://access.redhat.com/articles/1320623
			shutit.send('rm -fr /var/cache/yum/*')
			shutit.send('yum clean all')
			shutit.install('xterm')
			shutit.install('net-tools')
			shutit.install('git')
			# Allow logins via ssh between machines
			shutit.send('''sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config''')
			shutit.send('echo root:origin | /usr/sbin/chpasswd')
			shutit.send('systemctl restart sshd')
			shutit.install('epel-release')
			shutit.send('rpm -i https://packages.chef.io/stable/el/7/chef-12.16.42-1.el7.x86_64.rpm')
			shutit.send('mkdir -p /root/chef-solo-example')
			shutit.send('mkdir -p /root/chef-solo-example/cookbooks')
			shutit.send('mkdir -p /root/chef-solo-example/environments')
			shutit.send('mkdir -p /root/chef-solo-example/logs')
			shutit.send('cd /root/chef-solo-example/cookbooks')
			shutit.send('git clone -b cert_retrieval_bugfix https://github.com/IshentRas/cookbook-openshift3')
			# Filthy hack to 'override' the node['ipaddress'] value
			ip_addr = shutit.send_and_get_output("""ip -4 addr show dev eth1 | grep inet | awk '{print $2}' | awk -F/ '{print $1}'""")
			shutit.send('''sed -i 's/#{node..ipaddress..}/''' + ip_addr + '''/g' /root/chef-solo-example/cookbooks/cookbook-openshift3/attributes/default.rb''')
			shutit.send("""sed -i "s/node..ipaddress../'""" + ip_addr + """'/g" /root/chef-solo-example/cookbooks/cookbook-openshift3/attributes/default.rb""")

			shutit.send('curl -L https://supermarket.chef.io/cookbooks/iptables/download | tar -zxvf -')
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
solo true''')

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
		  "fqdn": "node2.vagrant.test",
		  "ipaddress": "''' + node2_ip + '''"
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
}''')
			shutit.logout()
			shutit.logout()
		
		wait = 0
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			shutit.send('echo "*/5 * * * * sleep ' + str(wait) + ' && chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb >> /root/chef-solo-example/logs/chef.log 2>&1" | crontab')
			shutit.logout()
			shutit.logout()
			wait += 60
		
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		if not shutit.send_until('oc get all','.*kubernetes.*',cadence=60,retries=120):
			shutit.pause_point('not installed?')
		shutit.logout()
		shutit.logout()

		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			# Workaround required for dns/landrush/docker issues: https://github.com/docker/docker/issues/18842
			shutit.insert_text('Environment=GODEBUG=netdns=cgo','/lib/systemd/system/docker.service',pattern='.Service.')
			shutit.send('systemctl daemon-reload')
			shutit.send('systemctl restart docker')
			shutit.logout()
			shutit.logout()

		# TODO: set up core services

		#shutit.send('git clone --depth=1 https://github.com/openshift/origin')
		#shutit.send('cd origin/examples')
		## TODO: https://github.com/openshift/origin/tree/master/examples/data-population
		#shutit.send('cd data-population')
		#shutit.send('ln -s /etc/origin openshift.local.config')
		#shutit.send('./populate.sh')
		###############################################################################

		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send('oadm manage-node master1.vagrant.test --schedulable=true')
		shutit.send('oadm manage-node master2.vagrant.test --schedulable=true')
		shutit.send('oadm manage-node master3.vagrant.test --schedulable=true')
		shutit.send('oc label node master1.vagrant.test region=infra')
		shutit.send('oc label node master2.vagrant.test region=infra')
		shutit.send('oc label node master3.vagrant.test region=infra')
		shutit.send('oc label node node1.vagrant.test region=user')
		shutit.send('oc label node node2.vagrant.test region=user')
		shutit.logout()
		shutit.logout()

		shutit.send('sleep 500') # Wait for all to settle

		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			# Use IPTables to block node1 from master2,3, node2, and node2 from master1, and node1
			if machine == 'node1':
				shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
				shutit.send('''(nohup /bin/bash -c 'while true; do iptables -A OUTPUT -d ''' + master2_ip + ''' -j DROP && iptables -A OUTPUT -d ''' + master3_ip + ''' -j DROP && iptables -A OUTPUT -d ''' + node2_ip + ''' -j DROP && sleep 60; done') &''')
			elif machine == 'node2':
				shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
				shutit.send('''(nohup /bin/bash -c 'while true; do iptables -A OUTPUT -d ''' + master1_ip + ''' -j DROP && iptables -A OUTPUT -d ''' + node1_ip + ''' -j DROP && sleep 60; done') &''')
			else:
				shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
			shutit.logout()
			shutit.logout()

		shutit.pause_point('OK?')
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
