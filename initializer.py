import json
from jinja2 import Environment, FileSystemLoader
from kubernetes import config
from kubernetes import client as kclient
from openshift import client as oclient
from openshift import watch
import os
import yaml


INITIALIZER = 'sidecar-dc.initializer.istio.io'
VERSION = "injected-version-root@111111111"
CONFIGMAP = "istio-inject-dc"
CONFIGMAPNAMESPACE = "istio-system"
ISTIO_VERSION = '0.4.0'
TEMPLATE = 'basetemplate.j2'
NAMESPACES = ['']
IMAGEPULLPOLICY = 'IfNotPresent'
VERBOSITY = 2
DEBUG = True


def inject(obj):
    metadata = obj.metadata
    if not metadata:
        print("No metadata in object, skipping: %s" % json.dumps(obj, indent=1))
        return
    name = metadata.name
    namespace = metadata.namespace
    annotations = metadata.annotations
    initializers = metadata.initializers
    if initializers is None:
        return
    for entry in initializers.pending:
        if entry.name == initializername:
            print("Updating deployment config %s" % name)
            obj.metadata.initializers.pending.remove(entry)
            if not initializers.pending:
                obj.metadata.initializers = None
            if annotations is not None and '%s/inject' % initializername in annotations and annotations['%s/inject' % initializername] == 'false':
                api.replace_namespaced_deployment_config(name, namespace, obj)
                break
            if annotations is not None and '%s/status' % initializername in annotations and 'injected' in annotations['%s/status' % initializername]:
                api.replace_namespaced_deployment_config(name, namespace, obj)
                break
            print("Updating %s" % name)
            if metadata.annotations is None:
                obj.metadata.annotations = {}
            obj.metadata.annotations['%s/status' % initializername] = VERSION
            if obj.spec.template.metadata.annotations is None:
                obj.spec.template.metadata.annotations = {}
            obj.spec.template.metadata.annotations['%s/status' % initializername] = VERSION
            containers[0]['args'][9] = name
            for container in containers:
                obj.spec.template.spec.containers.append(container)
            if obj.spec.template.spec.init_containers is None:
                obj.spec.template.spec.init_containers = []
            for initcontainer in initcontainers:
                obj.spec.template.spec.init_containers.append(initcontainer)
            if obj.spec.template.spec.volumes is None:
                obj.spec.template.spec.volumes = []
            for volume in volumes:
                obj.spec.template.spec.volumes.append(volume)
            # api.patch_namespaced_deployment_config(name, namespace, obj)
            api.replace_namespaced_deployment_config(name, namespace, obj)
            alldc = api.list_deployment_config_for_all_namespaces(include_uninitialized=True)
            updateddc = [d for d in alldc.items if d.metadata.name == name and d.metadata.namespace == namespace][0]
            try:
                api.replace_namespaced_deployment_config(name, namespace, updateddc)
            except:
                continue
            break


if __name__ == "__main__":
    global api
    global containers
    global initcontainers
    global volumes
    global initializername
    if 'KUBERNETES_PORT' in os.environ:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    kv1 = kclient.CoreV1Api()
    configmaps = kv1.list_namespaced_config_map(CONFIGMAPNAMESPACE)
    policy = 'enabled'
    initializername = INITIALIZER
    initimage = 'docker.io/istio/proxy_init:%s' % ISTIO_VERSION
    proxyimage = 'docker.io/istio/proxy_debug:%s' % ISTIO_VERSION
    imagepullpolicy = IMAGEPULLPOLICY
    debug = DEBUG
    verbosity = VERBOSITY
    namespaces = NAMESPACES
    configmap = None
    if configmaps.items:
        found = [c for c in configmaps.items if c.metadata.name == CONFIGMAP]
        if found:
            configmap = found[0]
    if configmap is not None:
        print("Applying settings from configmap")
        config = yaml.load(configmap.data['config'])
        policy = config.get('policy', 'enabled')
        initializername = config.get('initializerName', INITIALIZER)
        namespaces = config.get('namespaces', NAMESPACES)
        params = config.get('params')
        if params is not None:
            initimage = params.get('initImage', initimage)
            proxyimage = params.get('proxyImage', proxyimage)
            imagepullpolicy = params.get('imagePullPolicy', imagepullpolicy)
            debug = params.get('debugMode', debug)
            verbosity = params.get('verbosity', verbosity)
    print("Current settings :")
    print("namespaces : %s" % namespaces)
    print("initimage : %s" % initimage)
    print("proxyimage : %s" % proxyimage)
    print("imagepullpolicy : %s" % imagepullpolicy)
    print("verbosity : %s" % verbosity)
    env = Environment(loader=FileSystemLoader('.'))
    templ = env.get_template(os.path.basename(TEMPLATE))
    render = templ.render(initimage=initimage, proxyimage=proxyimage, imagepullpolicy=imagepullpolicy, verbosity=verbosity)
    base = yaml.load(render)
    containers = base['containers']
    initcontainers = base['initContainers']
    volumes = base['volumes']
    api = oclient.OapiApi()
    resource_version = ''
    while True:
        stream = watch.Watch().stream(api.list_deployment_config_for_all_namespaces, include_uninitialized=True, resource_version=resource_version)
        for event in stream:
                obj = event["object"]
                operation = event['type']
                spec = obj.spec
                if not spec:
                    continue
                metadata = obj.metadata
                resource_version = metadata._resource_version
                name = metadata.name
                namespace = metadata.namespace
                if operation == 'ADDED':
                    if policy != 'enabled':
                        print("Skipping %s on %s as per current policy" % (operation, name))
                    elif namespace not in namespaces and namespaces != ['']:
                        print("Skipping %s on %s as of the namespace of this deployment config" % (operation, name))
                    else:
                        print("Handling %s on %s" % (operation, name))
                        inject(obj)
