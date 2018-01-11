import json
from kubernetes import config
from openshift import client, watch
import os
import yaml


INITIALIZER = 'istio-sidecar-dc.initializer.istio.io'
VERSION = "injected-version-root@111111111"


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
        if entry.name == INITIALIZER:
            print("Updating deployment config %s" % name)
            obj.metadata.initializers.pending.remove(entry)
            if not initializers.pending:
                obj.metadata.initializers = None
            if annotations is not None and '%s/inject' % INITIALIZER in annotations and annotations['%s/inject' % INITIALIZER] == 'false':
                api.replace_namespaced_deployment_config(name, namespace, obj)
                break
            if annotations is not None and '%s/status' % INITIALIZER in annotations and 'injected' in annotations['%s/status' % INITIALIZER]:
                api.replace_namespaced_deployment_config(name, namespace, obj)
                break
            print("Updating %s" % name)
            if metadata.annotations is None:
                obj.metadata.annotations = {}
            obj.metadata.annotations['%s/status' % INITIALIZER] = VERSION
            if obj.spec.template.metadata.annotations is None:
                obj.spec.template.metadata.annotations = {}
            obj.spec.template.metadata.annotations['%s/status' % INITIALIZER] = VERSION
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
    with open('basetemplate.yml') as data:
        base = yaml.load(data)
        containers = base['containers']
        initcontainers = base['initContainers']
        volumes = base['volumes']
    if 'KUBERNETES_PORT' in os.environ:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    api = client.OapiApi()
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
                if operation == 'ADDED':
                    print("Handling %s on %s" % (operation, name))
                    inject(obj)
