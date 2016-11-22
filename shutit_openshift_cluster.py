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

  config.vm.define "etcd1" do |etcd1|
	etcd1.vm.box = ''' + '"' + vagrant_image + '"' + '''
	etcd1.vm.hostname = "etcd1.vagrant.test"
	etcd1.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "512"]
	  v.customize ["modifyvm", :id, "--cpus", "2"]
	end
  end
  config.vm.define "etcd2" do |etcd2|
	etcd2.vm.box = ''' + '"' + vagrant_image + '"' + '''
	etcd2.vm.hostname = "etcd2.vagrant.test"
	etcd2.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "512"]
	  v.customize ["modifyvm", :id, "--cpus", "2"]
	end
  end
  config.vm.define "etcd3" do |etcd3|
	etcd3.vm.box = ''' + '"' + vagrant_image + '"' + '''
	etcd3.vm.hostname = "etcd3.vagrant.test"
	etcd3.vm.provider :virtualbox do |v|
	  v.customize ["modifyvm", :id, "--memory", "512"]
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
		machine_names = ('master1','master2','master3','etcd1','etcd2','etcd3','node1')
		machines = ('master1.vagrant.test','master2.vagrant.test','master3.vagrant.test','etcd1.vagrant.test','etcd2.vagrant.test','etcd3.vagrant.test','node1.vagrant.test')
		pw = shutit.get_env_pass()
		for machine in machine_names:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + ' ' + machine,{'assword for':pw},timeout=99999)
		###############################################################################
		# SET UP MACHINES AND START CLUSTER
		###############################################################################
		master1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master1.vagrant.test | awk '{print $2}'""")
		master2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master2.vagrant.test | awk '{print $2}'""")
		master3_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master3.vagrant.test | awk '{print $2}'""")
		etcd1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd1.vagrant.test | awk '{print $2}'""")
		etcd2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd2.vagrant.test | awk '{print $2}'""")
		etcd3_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd3.vagrant.test | awk '{print $2}'""")
		node1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^node1.vagrant.test | awk '{print $2}'""")
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
			shutit.send('curl -L https://supermarket.chef.io/cookbooks/yum/versions/3.9.0/download | tar -zxvf -')
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

		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			if machine not in ('etcd1','etcd2','etcd3'):
				shutit.send('echo "*/5 * * * * chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb >> /root/chef-solo-example/logs/chef.log 2>&1" | crontab')
			shutit.logout()
			shutit.logout()
		
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send_until('oc get all','.*kubernetes.*',cadence=60)
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

		###############################################################################
		# GET BACKUP, STOP SERVICE
		###############################################################################
		# https://docs.openshift.com/enterprise/3.2/install_config/upgrading/manual_upgrades.html#preparing-for-a-manual-upgrade
		for machine in ('master1','master2','master3'):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			shutit.send('ETCD_DATA_DIR=/var/lib/etcd')
			shutit.send('etcdctl backup --data-dir $ETCD_DATA_DIR --backup-dir $ETCD_DATA_DIR.backup')
			shutit.send('cp /etc/etcd/etcd.conf /etc/etcd/etcd.conf.bak')
			shutit.logout()
			shutit.logout()
		# Switch off chef crons
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			if machine not in ('etcd1','etcd2','etcd3'):
				shutit.send('echo "#*/5 * * * * chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb >> /root/chef-solo-example/logs/chef.log 2>&1" | crontab')
			shutit.logout()
			shutit.logout()
		# https://docs.openshift.com/enterprise/3.2/install_config/downgrade.html
		for machine in ('master1','master2','master3'):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			#shutit.send('systemctl stop atomic-openshift-master-api')
			#shutit.send('systemctl stop atomic-openshift-master-controllers')
			#shutit.send('systemctl stop atomic-openshift-node')
			shutit.send_until('systemctl stop origin-master-api','')
			shutit.send_until('systemctl stop origin-master-controllers','')
			shutit.logout()
			shutit.logout()
		for machine in ('node1',):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			#shutit.send('systemctl stop atomic-openshift-node')
			shutit.send_until('systemctl stop origin-node','')
			shutit.logout()
			shutit.logout()
		###############################################################################
		
		###############################################################################
		# GET CERTS
		###############################################################################
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		# Extend cluster to 5 in chef on master1 just to get the certs
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
		  "ipaddress": "''' + master2_ip + '''"
		},
		{
		  "fqdn": "master2.vagrant.test",
		  "ipaddress": "''' + master2_ip + '''"
		},
		{
		  "fqdn": "etcd1.vagrant.test",
		  "ipaddress": "''' + etcd1_ip + '''"
		},
		{
		  "fqdn": "etcd2.vagrant.test",
		  "ipaddress": "''' + etcd2_ip + '''"
		},
		{
		  "fqdn": "etcd3.vagrant.test",
		  "ipaddress": "''' + etcd3_ip + '''"
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
}''')
		# Re-run chef to generate certs for etcd1,2,3
		shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
		# Revert master1 to previous state now certs have been generated.
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
}''')

		shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
		shutit.logout()
		shutit.logout()

		# Shut down openshift again, as chef runs will have started it up.
		for machine in ('master1','master2','master3'):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			#shutit.send('systemctl stop atomic-openshift-master-api')
			#shutit.send('systemctl stop atomic-openshift-master-controllers')
			#shutit.send('systemctl stop atomic-openshift-node')
			shutit.send_until('systemctl stop origin-master-api','')
			shutit.send_until('systemctl stop origin-master-controllers','')
			shutit.send_until('systemctl stop origin-node','')
			shutit.logout()
			shutit.logout()
		###############################################################################

		###############################################################################
		# ETCD1
		###############################################################################
		# Add etcd1 to cluster and drop master1 - TODO: do this in chef?
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send('etcdctl --endpoints https://' + master3_ip + ':2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member add etcd1.vagrant.test https://' + etcd1_ip + ':2380',note='Add node to cluster')
		shutit.send("""etcdctl https://""" + master3_ip + """:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member remove $(etcdctl --endpoints https://""" + master3_ip + """:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list | grep master1.vagrant.test | awk -F: '{print $1}')""",note='Drop node from cluster')
		shutit.logout()
		shutit.logout()
		###############################################################################

		###############################################################################
		# go to etcd1 and set up etcd
		shutit.login(command='vagrant ssh etcd1')
		shutit.login(command='sudo su - ')
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
		  "fqdn": "master2.vagrant.test",
		  "ipaddress": "''' + master2_ip + '''"
		},
		{
		  "fqdn": "master3.vagrant.test",
		  "ipaddress": "''' + master3_ip + '''"
		},
		{
		  "fqdn": "etcd1.vagrant.test",
		  "ipaddress": "''' + etcd1_ip + '''"
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
}''')
		# Can we do this with chef?
		shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
		# Shut down etcd
		shutit.send('systemctl stop etcd')
		# Replace new with existing
		shutit.send("""sed -i 's/ETCD_INITIAL_CLUSTER_STATE=.*/ETCD_INITIAL_CLUSTER_STATE=existing/' /etc/etcd/etcd.conf""")
		# Remove existing db
		shutit.send('rm -f rm /var/lib/etcd/member/wal/0000000000000000-0000000000000000.wal',{'remove regular':'y'})
		# Start up etcd
		shutit.send('systemctl start etcd')
		shutit.logout()
		shutit.logout()
		################################################################################

		###############################################################################
		# ETCD2		
		###############################################################################
		# Add etcd2 to cluster and drop master2 - TODO: do this in chef?
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send('etcdctl --endpoints https://' + master3_ip + ':2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member add etcd1.vagrant.test https://' + etcd2_ip + ':2380',note='Add node to cluster')
		shutit.send("""etcdctl --endpoints https://""" + master3_ip + """:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member remove $(etcdctl --endpoints https://""" + master3_ip + """:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list | grep master2.vagrant.test | awk -F: '{print $1}')""",note='Drop node from cluster')
		shutit.logout()
		shutit.logout()
		###############################################################################


		###############################################################################
		# go to etcd2 and set up etcd
		shutit.login(command='vagrant ssh etcd2')
		shutit.login(command='sudo su - ')
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
		  "fqdn": "master3.vagrant.test",
		  "ipaddress": "''' + master3_ip + '''"
		},
		{
		  "fqdn": "etcd1.vagrant.test",
		  "ipaddress": "''' + etcd1_ip + '''"
		},
		{
		  "fqdn": "etcd2.vagrant.test",
		  "ipaddress": "''' + etcd2_ip + '''"
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
}''')
		# Can we do this with chef?
		shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
		# Shut down etcd
		shutit.send('systemctl stop etcd')
		# Replace new with existing
		shutit.send("""sed -i 's/ETCD_INITIAL_CLUSTER_STATE=.*/ETCD_INITIAL_CLUSTER_STATE=existing/' /etc/etcd/etcd.conf""")
		# Remove existing db
		shutit.send('rm -f rm /var/lib/etcd/member/wal/0000000000000000-0000000000000000.wal',{'remove regular':'y'})
		# Start up etcd
		shutit.send('systemctl start etcd')
		shutit.logout()
		shutit.logout()
		################################################################################


		###############################################################################
		# ETCD3
		###############################################################################
		# Add etcd3 to cluster and drop master3 - TODO: do this in chef?
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send('etcdctl --endpoints https://' + master3_ip + ':2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member add etcd1.vagrant.test https://' + etcd3_ip + ':2380',note='Add node to cluster')
		shutit.send("""etcdctl --endpoints https://""" + master3_ip + """:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member remove $(etcdctl --endpoints https://""" + master3_ip + """:2379 --ca-file /etc/origin/master/master.etcd-ca.crt --cert-file /etc/origin/master/master.etcd-client.crt --key-file /etc/origin/master/master.etcd-client.key member list | grep master3.vagrant.test | awk -F: '{print $1}')""",note='Drop node from cluster')
		shutit.logout()
		shutit.logout()
		###############################################################################

		###############################################################################
		# go to etcd3 and set up etcd
		shutit.login(command='vagrant ssh etcd3')
		shutit.login(command='sudo su - ')
		final_chef_config = '''{
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
		  "fqdn": "etcd1.vagrant.test",
		  "ipaddress": "''' + etcd1_ip + '''"
		},
		{
		  "fqdn": "etcd2.vagrant.test",
		  "ipaddress": "''' + etcd2_ip + '''"
		},
		{
		  "fqdn": "etcd3.vagrant.test",
		  "ipaddress": "''' + etcd3_ip + '''"
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
}'''
		shutit.send_file('''/root/chef-solo-example/environments/ocp-cluster-environment.json''',final_chef_config)
		# Can we do this with chef?
		shutit.send_until('chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb','.*Report handlers complete.*')
		# Shut down etcd
		shutit.send('systemctl stop etcd')
		# Replace new with existing
		shutit.send("""sed -i 's/ETCD_INITIAL_CLUSTER_STATE=.*/ETCD_INITIAL_CLUSTER_STATE=existing/' /etc/etcd/etcd.conf""")
		# Remove existing db
		shutit.send('rm -f rm /var/lib/etcd/member/wal/0000000000000000-0000000000000000.wal',{'remove regular':'y'})
		# Start up etcd
		shutit.send('systemctl start etcd')
		shutit.logout()
		shutit.logout()
		################################################################################

		################################################################################
		# Update the chef config to reflect the new reality, and then run chef everywhere
		################################################################################
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			shutit.send_file('''/root/chef-solo-example/environments/ocp-cluster-environment.json''',final_chef_config)
			shutit.send('echo "*/5 * * * * chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb >> /root/chef-solo-example/logs/chef.log 2>&1" | crontab')
			shutit.logout()
			shutit.logout()

		shutit.pause_point('etcd should be migrated and all ok. Wait for chef to re-run everywhere')

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
