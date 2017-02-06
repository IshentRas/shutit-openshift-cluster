#!/bin/bash
set -x
set -e
./destroy_vms.sh
[[ -z "$SHUTIT" ]] && SHUTIT="$1/shutit"
[[ ! -a "$SHUTIT" ]] || [[ -z "$SHUTIT" ]] && SHUTIT="$(which shutit)"
echo using SHUTIT: $SHUTIT
if [[ ! -a "$SHUTIT" ]]
then
	echo "Must have shutit on path, eg export PATH=$PATH:/path/to/shutit_dir"
	exit 1
fi
for ose_major_version in 3.3 3.2
do
	for test_dir in $(cd tests && find * -type d && cd - > /dev/null)
	do
		$SHUTIT build \
			--echo -d bash \
			-m shutit-library/vagrant:shutit-library/virtualbox \
			-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster test_config_dir ${test_dir} \
			-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster ose_major_version ${ose_major_version} \
			-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_yum_cookbook_version latest \
			-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_iptables_cookbook_version latest \
			-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_selinux_policy_cookbook_version latest \
			-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_compat_resource_cookbook_version latest \
			-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_version 12.16.42-1 \
            "$@"
		./destroy_vms.sh
	done
done

# $WORK-specific

$SHUTIT build \
	--echo -d bash \
	-m shutit-library/vagrant:shutit-library/virtualbox \
	-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster test_config_dir                       ${test_dir} \
	-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster ose_major_version                     3.2 \
	-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_yum_cookbook_version             3.6.1 \
	-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_iptables_cookbook_version        1.0.0 \
	-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_selinux_policy_cookbook_version  0.7.2 \
	-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_compat_resource_cookbook_version latest \
	-s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster chef_version                          12.4.1-1 \
    "$@"
./destroy_vms.sh

