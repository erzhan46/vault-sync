from kubernetes import client, config, watch
from kubernetes.dynamic import DynamicClient
import os
import logging
import hvac
import time
from vault_sync_module import vault_sync

# Dict to store vault_sync objects
vault_sync_dict = {}

# Global Vault client
vault_client = hvac.Client()

# Process vaultsync CR
def process_cr(event):
    current_time = time.time()
    renewal_time = current_time - (float(os.environ.get("SECRET_ID_RENEWAL")) if os.environ.get("SECRET_ID_RENEWAL") else global_secret_id_renewal)
    logging.debug("Current time %10.0f" % (current_time))
    logging.debug("Renewal time %10.0f" % (renewal_time))
    name = event['object']['metadata']['name']
    namespace = event['object']['metadata']['namespace']
    vault_namespace = ""
    dict_key = namespace + ":" + name
    if dict_key not in vault_sync_dict:
        vault_sync_dict[dict_key] = vault_sync(name, namespace, vault_namespace, client, vault_client)
    current_vault_sync = vault_sync_dict[dict_key]
    logging.debug(vault_sync_dict[dict_key])
    if current_vault_sync.current_expiration <= renewal_time:
        logging.info("Secret ID renewal expired %10.0f seconds ago. Renewing" % (renewal_time - current_vault_sync.current_expiration))
        current_vault_sync.configure_vault_integration()
        current_vault_sync.current_expiration = current_time
        logging.debug("Set expiration to %10.0f" % (current_vault_sync.current_expiration))



# Watch vaultsync CR's for WATCH_TIMEOUT seconds
def crd_watch():
    api_client = client.ApiClient()
    crd_api = client.CustomObjectsApi(api_client)
    w = watch.Watch()
    for event in w.stream(crd_api.list_cluster_custom_object, group="stable.example.com", version="v1alpha1", plural="vaultsyncs", 
                          timeout_seconds=(os.environ.get("WATCH_TIMEOUT") if os.environ.get("WATCH_TIMEOUT") else global_watch_timeout)):
        logging.info("Checking vaultsync resource %s in namespace %s" % (event['object']['metadata']['name'], event['object']['metadata']['namespace']))
        process_cr(event)


def main():
    # Set logging format
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=(logging.DEBUG if os.environ.get("DEBUG") else logging.INFO))

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
