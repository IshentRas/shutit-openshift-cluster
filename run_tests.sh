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
for test_dir in $(cd tests && find * -type d && cd - > /dev/null)
do
	$SHUTIT build --echo -d bash -m shutit-library/vagrant:shutit-library/virtualbox -s tk.shutit.shutit_openshift_cluster.shutit_openshift_cluster test_config_dir $test_dir "$@"
	./destroy_vms.sh
done


