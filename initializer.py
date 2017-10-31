import json
from kubernetes import config
# from openshift import client, watch
from kubernetes import client, watch
import os
import yaml


INITIALIZER = 'sidecar.initializer.istio.io'


def inject(obj):
    metadata = obj.metadata
    if not metadata:
        print("No metadata in object, skipping: %s" % json.dumps(obj, indent=1))
        return
    name = metadata.name
    namespace = metadata.namespace
    annotations = metadata.annotations
    if 'sidecar.istio.io/inject' in annotations and annotations['sidecar.istio.io/inject'] == 'false':
        return
    if 'sidecar.istio.io/status' in annotations and 'injected' in annotations['sidecar.istio.io/status']:
        return
    print("Updating deployment config %s" % name)
    # print(obj.spec.template.spec)
    metadata.annotations['sidecar.istio.io/status'] == 'injected-version-karim@111111111'
    obj.spec.template.metadata.annotations['sidecar.istio.io/status'] == 'injected-version-karim@111111111'
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
    api.replace_namespaced_deployment_config(name, namespace, obj)
    # initializers = metadata.initializers
    # if initializers is None:
    #     return
    # for entry in initializers.pending:
    #     if entry.name == INITIALIZER:
    #         print("Updating deployment config %s" % name)
    #         initializers.pending.remove(entry)
    #         if not initializers.pending:
    #             initializers = None
    #         obj.metadata.initializers = initializers
    #         if annotation is None or (annotations and annotation in annotations and annotations[annotation] == 'true'):
    #             print("Injecting istio stuff to deployment config %s" % name)
    #             newcontainer = {'image': 'xxx', 'name': 'injected'}
    #             obj.spec.template.spec.containers.append(newcontainer)
    #         api.replace_namespaced_deployment_config(name, namespace, obj)
    #         break


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
    # api = client.OapiApi()
    api = client.AppsV1beta1Api()
    resource_version = ''
    while True:
        # stream = watch.Watch().stream(api.list_deployment_config_for_all_namespaces, include_uninitialized=True, resource_version=resource_version)
        stream = watch.Watch().stream(api.list_deployment_for_all_namespaces, include_uninitialized=True, resource_version=resource_version)
        for event in stream:
                obj = event["object"]
                operation = event['type']
                spec = obj.spec
                if not spec:
                    continue
                metadata = obj.metadata
                resource_version = metadata._resource_version
                name = metadata.name
                print("Handling %s on %s" % (operation, name))
                inject(obj)