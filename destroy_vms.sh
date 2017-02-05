#!/bin/bash
rm -rf vagrant_run/*
if [[ $(command -v VBoxManage) != '' ]]
then
	while true
	do
		VBoxManage list runningvms | grep shutit_openshift_cluster | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep shutit_openshift_cluster | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep shutit_openshift_cluster | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep shutit_openshift_cluster | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) != '' ]]
then
	if [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
	then
	    virsh list | grep shutit_openshift_cluster | awk '{print $1}' | xargs -n1 virsh destroy
	fi
fi
