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

## deploy 

the following yaml will deploy the controller using my image stored in docker.io (and the corresponding initializerconfiguration object) 

```
oc create -f istio-openshift-initializer.yml
```

## TODO

- use configmaps to indicate image tag and so on
- render basetemplate.yml with jinja with the data from the configmap
- find out why the update of the containers and the initializers doesnt work in a single replace
