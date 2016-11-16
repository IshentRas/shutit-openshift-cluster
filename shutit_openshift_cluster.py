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
		machine_names = ('master1','master2','etcd1','etcd2','etcd3','node1','openshiftcluster','etcd4','etcd5','etcd6')
		machines = ('master1.vagrant.test','master2.vagrant.test','etcd1.vagrant.test','etcd2.vagrant.test','etcd3.vagrant.test','node1.vagrant.test','openshiftcluster.vagrant.test','etcd4.vagrant.test','etcd5.vagrant.test','etcd6.vagrant.test')
		password = shutit.get_env_pass()
		shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'],{'assword':password},timeout=99999)
		master1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master1.vagrant.test | awk '{print $2}'""")
		master2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master2.vagrant.test | awk '{print $2}'""")
		master3_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^master3.vagrant.test | awk '{print $2}'""")
		etcd1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd1.vagrant.test | awk '{print $2}'""")
		etcd2_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd2.vagrant.test | awk '{print $2}'""")
		etcd3_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd3.vagrant.test | awk '{print $2}'""")
		etcd4_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd4.vagrant.test | awk '{print $2}'""")
		etcd5_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd5.vagrant.test | awk '{print $2}'""")
		etcd6_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^etcd6.vagrant.test | awk '{print $2}'""")
		node1_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^node1.vagrant.test | awk '{print $2}'""")
		openshiftcluster_ip = shutit.send_and_get_output("""vagrant landrush ls | grep -w ^openshiftcluster.vagrant.test | awk '{print $2}'""")
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
			# This is to prevent ansible from getting the 'wrong' ip address for the host from eth0.
			# See: http://stackoverflow.com/questions/29495704/how-do-you-change-ansible-default-ipv4
			shutit.send('route add -net 8.8.8.8 netmask 255.255.255.255 eth1')
			ip_addr = shutit.send_and_get_output("""ip -4 route get 8.8.8.8 | head -1 | awk '{print $NF}'""")
			shutit.send(r"""sed -i 's/127.0.0.1\t\(.*\).vagrant.test.*/""" + ip_addr + r"""\t\1.vagrant.test\t\1/' /etc/hosts""")
			shutit.install('epel-release')
			shutit.send('rpm -i https://packages.chef.io/stable/el/7/chef-12.16.42-1.el7.x86_64.rpm')
			shutit.send('mkdir -p /root/chef-solo-example')
			shutit.send('mkdir -p /root/chef-solo-example/cookbooks')
			shutit.send('mkdir -p /root/chef-solo-example/environments')
			shutit.send('mkdir -p /root/chef-solo-example/logs')
			shutit.send('cd /root/chef-solo-example/cookbooks')
			shutit.send('git clone https://github.com/IshentRas/cookbook-openshift3')
			# Filthy hack to 'override' the node['ipaddress'] value
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
			shutit.logout()
			shutit.logout()
		for machine in machine_names:
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su - ')
			if machine not in ('etcd4','etcd5','etcd6'):
				shutit.send('echo "*/5 * * * * chef-solo --environment ocp-cluster-environment -o recipe[cookbook-openshift3],recipe[cookbook-openshift3::common],recipe[cookbook-openshift3::master],recipe[cookbook-openshift3::node] -c ~/chef-solo-example/solo.rb >> /root/chef-solo-example/logs/chef.log 2>&1" | crontab')
			shutit.logout()
			shutit.logout()
		
		# Wait 15 minutes for everything to be ready
		shutit.send('date && sleep $[60 * 15]',timeout=9999)
		shutit.login(command='vagrant ssh master1')
		shutit.login(command='sudo su - ')
		shutit.send('oc get all')
		shutit.logout()
		shutit.logout()

		# TODO: set up core services

		#shutit.send('git clone --depth=1 https://github.com/openshift/origin')
		#shutit.send('cd origin/examples')
		## TODO: https://github.com/openshift/origin/tree/master/examples/data-population
		#shutit.send('cd data-population')
		#shutit.send('ln -s /etc/origin openshift.local.config')
		#shutit.send("""sed -i 's/10.0.2.15/openshiftcluster/g' common.sh""")
		#shutit.send('./populate.sh')
		shutit.logout()
		shutit.logout()

		##shutit.pause_point('Migrate etcd....')
		## Get backup
		## https://docs.openshift.com/enterprise/3.2/install_config/upgrading/manual_upgrades.html#preparing-for-a-manual-upgrade
		#for machine in ('etcd1','etcd2','etcd3'):
		#	shutit.login(command='vagrant ssh ' + machine)
		#	shutit.login(command='sudo su - ')
		#	shutit.send('ETCD_DATA_DIR=/var/lib/etcd')
		#	shutit.send('etcdctl backup --data-dir $ETCD_DATA_DIR --backup-dir $ETCD_DATA_DIR.backup')
		#	shutit.send('cp /etc/etcd/etcd.conf /etc/etcd/etcd.conf.bak')
		#	shutit.logout()
		#	shutit.logout()
		## https://docs.openshift.com/enterprise/3.2/install_config/downgrade.html
		#for machine in ('master1','master2'):
		#	shutit.login(command='vagrant ssh ' + machine)
		#	shutit.login(command='sudo su - ')
		#	#shutit.send('systemctl stop atomic-openshift-master-api')
		#	#shutit.send('systemctl stop atomic-openshift-master-controllers')
		#	#shutit.send('systemctl stop atomic-openshift-node')
		#	shutit.send('systemctl stop origin-master-api')
		#	shutit.send('systemctl stop origin-master-controllers')
		#	shutit.send('systemctl stop origin-node')
		#	shutit.logout()
		#	shutit.logout()
		#for machine in ('node1'):
		#	shutit.login(command='vagrant ssh ' + machine)
		#	shutit.login(command='sudo su - ')
		#	#shutit.send('systemctl stop atomic-openshift-node')
		#	shutit.send('systemctl stop origin-node')
		#	shutit.logout()
		#	shutit.logout()
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
