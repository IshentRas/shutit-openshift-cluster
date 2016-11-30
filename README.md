# shutit-openshift-cluster

## Video

[![asciicast](https://asciinema.org/a/91801.png)](https://asciinema.org/a/91801)

## Run

To run (virtualbox flavour):

```
# as root
[install pip]
[sudo] pip install shutit
git clone --recursive https://github.com/ianmiell/shutit-openshift-cluster
cd shutit-openshift-cluster
./run.sh
```

To run (libvirt flavour, eg Centos7):

```
# as root
yum install -y epel-release
yum install -y python-pip git
pip install shutit
git clone --recursive https://github.com/ianmiell/shutit-openshift-cluster
cd shutit-openshift-cluster
./run.sh --echo -s shutit-library.virtualization.virtualization.virtualization virt_method libvirt
```


## More

For more info, see [here](https://medium.com/@zwischenzugs/a-complete-openshift-cluster-on-vagrant-step-by-step-7465e9816d98#.pv26dz7q1)

