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
			shutit.send('rpm -i https://packages.chef.io/stable/el/7/chef-12.16.42-1.el7.x86_64.rpm',note='install chef')
			shutit.send('mkdir -p /root/chef-solo-example /root/chef-solo-example/cookbooks /root/chef-solo-example/environments /root/chef-solo-example/logs',note='Create chef folders')
			shutit.send('cd /root/chef-solo-example/cookbooks')
			shutit.send('git clone https://github.com/IshentRas/cookbook-openshift3',note='Clone chef repo')
			# Filthy hack to 'override' the node['ipaddress'] value
			ip_addr = shutit.send_and_get_output("""ip -4 addr show dev eth1 | grep inet | awk '{print $2}' | awk -F/ '{print $1}'""")
			shutit.send('''sed -i 's/#{node..ipaddress..}/''' + ip_addr + '''/g' /root/chef-solo-example/cookbooks/cookbook-openshift3/attributes/default.rb''')
			shutit.send("""sed -i "s/node..ipaddress../'""" + ip_addr + """'/g" /root/chef-solo-example/cookbooks/cookbook-openshift3/attributes/default.rb""")

			shutit.send('curl -L https://supermarket.chef.io/cookbooks/iptables/download | tar -zxvf -',note='Get cookbook dependencies')
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
		shutit.send('yum install -y https://packages.chef.io/stable/el/7/chefdk-1.0.3-1.el7.x86_64.rpm')
		shutit.send('oc label node master1.vagrant.test region=registry')
		shutit.send("""oadm registry --config=/etc/origin/master/admin.kubeconfig --service-account=registry --images='registry.access.redhat.com/openshift3/ose-${component}:${version}' --selector=region=registry""",note='Create an ephemeral registry.',check_exit=False)
		shutit.send("""oc create route passthrough --service registry-console --port registry-console -n default""",note='Create route for reg console')
		shutit.send("""oc new-app -n default --template=registry-console -p OPENSHIFT_OAUTH_PROVIDER_URL="https://master1.vagrant.test:8443",REGISTRY_HOST=$(oc get route docker-registry -n default --template='{{ .spec.host }}'),COCKPIT_KUBE_URL=$(oc get route registry-console -n default --template='https://{{ .spec.host }}')""")
		shutit.send('cd /root/chef-solo-example/cookbooks')
		shutit.send('chef generate cookbook ose-wrapper')
		shutit.send_file('/root/chef-solo-example/cookbooks/ose-wrapper/recipes/default.rb','''master_servers = node['cookbook-openshift3']['master_servers']
etcd_upgrade_servers = node['ose-wrapper']['etcd_upgrade_servers']
shutdown_servers = node['ose-wrapper']['shutdown_servers']

# - etcd_migration_new_node:               "https://master3.net.thing:2380"
# - etcd_migration_drop_node:              "https://master1.net.thing"
if master_servers.any? && master_servers.first['fqdn'] == node['fqdn'] && node['ose-wrapper']['etcd_migration_endpoint'] && node['ose-wrapper']['etcd_migration_new_node'] && node['ose-wrapper']['etcd_migration_drop_node']
  # Switched off by default - step 6
  execute 'Add node to etcd cluster' do
    command "[[ $(etcdctl --endpoints #{node['ose-wrapper']['etcd_migration_endpoint']} \
             --ca-file #{node['cookbook-openshift3']['etcd_ca_cert']} --cert-file #{node['cookbook-openshift3']['etcd_conf_dir']}/master.etcd-client.key \
             member add #{node['ose-wrapper']['etcd_migration_new_node']}) ]]"
    only_if "[[ $(etcdctl --endpoints #{node['ose-wrapper']['etcd_migration_endpoint']} \
             --ca-file #{node['cookbook-openshift3']['etcd_ca_cert']} --cert-file #{node['cookbook-openshift3']['etcd_conf_dir']}/master.etcd-client.key \
             member list | grep #{node['ose-wrapper']['etcd_migration_new_node']} | wc -l) == '0' ]]"
  end

  execute 'Drop node from etcd cluster' do
    command "[[ $(etcdctl --endpoints #{node['ose-wrapper']['etcd_migration_endpoint']} \
             --ca-file #{node['cookbook-openshift3']['etcd_ca_cert']} --cert-file #{node['cookbook-openshift3']['etcd_conf_dir']}/master.etcd-client.key \
             member remove $(etcdctl --endpoints #{node['ose-wrapper']['etcd_migration_endpoint']} \
             --ca-file #{node['cookbook-openshift3']['etcd_ca_cert']} --cert-file #{node['cookbook-openshift3']['etcd_conf_dir']}/master.etcd-client.key \
             member list | grep #{node['ose-wrapper']['etcd_migration_drop_node']} | awk -F: '{print $1}')) ]]"
    only_if "[[ $(etcdctl --endpoints #{node['ose-wrapper']['etcd_migration_endpoint']} \
             --ca-file #{node['cookbook-openshift3']['etcd_ca_cert']} --cert-file #{node['cookbook-openshift3']['etcd_conf_dir']}/master.etcd-client.key \
             member list | grep #{node['ose-wrapper']['etcd_migration_drop_node']} | wc -l) == '1' ]]"
  end
end

if etcd_upgrade_servers.find { |server_node| server_node['fqdn'] == node['fqdn'] }
  bash 'Install migrated etcd if not done already' do
    code <<-EOF
      systemctl stop etcd
      sed -i 's/ETCD_INITIAL_CLUSTER_STATE=.*/ETCD_INITIAL_CLUSTER_STATE=existing/' /etc/etcd/etcd.conf
      mv /var/lib/etcd/member/wal/*.wal /var/lib/etcd/.deleteme.wal
      systemctl start etcd
      touch /var/lib/etcd/.migrated
    EOF
    not_if '[[ -a /var/lib/etcd/.migrated ]]'
  end
end

# Stop all core OpenShift services
if shutdown_servers.find { |server_node| server_node['fqdn'] == node['fqdn'] }
  service 'atomic_openshift_master_controllers' do
    service_name 'atomic-openshift-master-controllers'
    action [:stop, :disable]
  end
  service 'atomic_openshift_master_api' do
    service_name 'atomic-openshift-master-api'
    action [:stop, :disable]
  end
  service 'atomic_openshift_node' do
    service_name 'atomic-openshift-node'
    action [:stop, :disable]
  end
end''')
		shutit.send('mkdir -p /root/chef-solo-example/cookbooks/ose-wrapper/attributes')
		shutit.send_file('/root/chef-solo-example/cookbooks/ose-wrapper/attributes/default.rb','''default['ose-wrapper']['etcd_upgrade_servers'] = []
default['ose-wrapper']['shutdown_servers'] = []
default['ose-wrapper']['etcd_migration_endpoint'] = nil
default['ose-wrapper']['etcd_migration_new_node'] = nil
default['ose-wrapper']['etcd_migration_drop_node'] = nil''')

		shutit.pause_point('see comments following')
# CHANGE THE CRONTAB WITH new recipes
# CHANGE THE ENV FILE
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
