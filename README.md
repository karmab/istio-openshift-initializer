# istio openshift initializer

# repo to host code to autoinject istio side cars to deployment configs objects

## requirements

your openshift instance needs initializers deployed . On a 3.7 cluster using *oc cluster up*, that means editing master-config.yml and make sure the following snippet is there (we are adding the Initializers block):

```
admissionConfig:
  pluginConfig:
    GenericAdmissionWebhook:
      configuration:
        apiVersion: v1
        disable: false
        kind: DefaultAdmissionConfig
      location: ""
    Initializers:
      configuration:
        apiVersion: v1
        disable: false
        kind: DefaultAdmissionConfig
      location: ""
```

if testing with oc cluster up, you can use the following snippet:

```
echo 'Initializers:\n      configuration:\n        apiVersion: v1\n        disable: false\n        kind: DefaultAdmissionConfig\n      location: ""' > ini.txt
grep -q Initializers /var/lib/origin/openshift.local.config/master/master-config.yaml || sed  -i "/GenericAdmissionWebhook/i\ \ \ \ `cat ini.txt`" /var/lib/origin/openshift.local.config/master/master-config.yaml
docker restart origin
```

also prevent existing dc to be affected by the change:

```
oc annotate dc docker-registry sidecar.istio.io/inject='false' -n default
oc annotate dc router sidecar.istio.io/inject='false' -n default
```

you will also need to give privileges to the sa running the istio-openshift-initializer pod so that it can watch/edit deploymentconfigs in the cluster.
provided you installed istio, the following line will do the trick:

```
oc adm policy add-cluster-role-to-user cluster-admin -z istio-initializer-service-account -n istio-system
```

## manual testing

create the initializerconfiguration object

```
oc create -f initializerconfiguration.yml
```

then launch manually the controller 

```
virtualenv openshift
source openshift/bin/activate
pip install openshift
oc login
python initializer.py
```

you can also use the docker version (jimmy hendrix would have liked istio)

```
docker run --rm -it -v ~/.kube:/home/jhendrix/.kube karmab/istio-openshift-initializer
```

## deploy 

the following yaml will deploy the controller using my image stored in docker.io (and the corresponding initializerconfiguration object) 

```
oc create -f istio-openshift-initializer.yml
```

## TODO

- handle debug set to False from configmap
- find out why the update of the containers and the initializers doesnt work in a single replace
