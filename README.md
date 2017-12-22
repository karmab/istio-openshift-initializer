# istio openshift initializer

# repo to host code to autoinject istio side cars to deployment configs objects

# first, prevent existing dc to be affected by the change 

```
oc annotate dc docker-registry sidecar.istio.io/inject='false' -n default
oc annotate dc router sidecar.istio.io/inject='false' -n default
```

## manual testing

```
oc login
virtualenv openshift
source openshift/bin/activate
pip install openshift
python initializer.py
```

## deploy 

```
oc create -f istio-openshift-initializer.yml
```

## TODO

- switch to initializers on an enable openshift instance as the current deploymentconfigs.py doesnt work because several controllers handle the dc, while we're trying to update it !
