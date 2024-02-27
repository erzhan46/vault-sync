from kubernetes import client, config, watch
import os
import logging
import hvac

def crd_watch():
    apiClient = client.ApiClient()
    customObjects = client.CustomObjectsApi(apiClient)
    w = watch.Watch()
    for event in w.stream(customObjects.list_cluster_custom_object, group="stable.example.com", version="v1alpha1", plural="vaultsyncs", 
                          timeout_seconds=(os.environ.get("WATCH_TIMEOUT") if os.environ.get("WATCH_TIMEOUT") else 3600)):
        logging.info("Checking vaultsync resource %s in namespace %s" % (event['object']['metadata']['name'], event['object']['metadata']['namespace']))


def main():
    # Set logging format
    logging.basicConfig(format='%(asctime)s %(message)s', level=(logging.DEBUG if os.environ.get("DEBUG") else logging.INFO))

    # Assuming this script runs as K8S pod or kubeconfig is authenticated to cluster
    config.load_kube_config()

    # Authenticate to Vault using env vars 
    vault_addr = os.environ.get("VAULT_ADDR")
    vault_token = os.environ.get("VAULT_TOKEN")
    vault_role_id = os.environ.get("VAULT_ROLE_ID")
    vault_secret_id = os.environ.get("VAULT_SECRET_ID")
    if not vault_token:
        logging.info("Authenticating to Vault %s using AppRole." %(vault_addr))
        vault_client = hvac.Client(
            url=vault_addr
        )
        vault_client.auth.approle.login(
            role_id=vault_role_id,
            secret_id=vault_secret_id
        )
    else:
        logging.info("Authenticating to Vault %s using Token." %(vault_addr))
        vault_client = hvac.Client(
            url=vault_addr,
            token=vault_token
        )

    # main loop
    while (True):
        logging.info("(Re)Starting watch loop")
        crd_watch()

    logging.info("Exiting.")


if __name__ == '__main__':
    main()
