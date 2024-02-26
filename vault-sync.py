from kubernetes import client, config, watch
from pprint import pprint


def main():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    config.load_kube_config()

    apiClient = client.ApiClient()
    customObjects = client.CustomObjectsApi(apiClient)
#    count = 10
    for i in (1,2):
        w = watch.Watch()
        for event in w.stream(customObjects.list_cluster_custom_object, group="stable.example.com", version="v1alpha1", plural="vaultsyncs", timeout_seconds=1000):
            print("Event: %s %s: %s" % (event['type'], event['object']['metadata']['namespace'], event['object']['metadata']['name']))
#            pprint(event['object']['metadata']['name'])
#        count -= 1
#        if not count:
#            w.stop()
    print("Finished configmaps stream.")


if __name__ == '__main__':
    main()
