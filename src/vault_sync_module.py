from kubernetes import client, config, watch
from kubernetes.dynamic import DynamicClient
import os
import logging
import hvac
import time

# Some globals
global_watch_timeout = 3600
global_secret_id_renewal = 3600 * 18
global_secret_id_expiration = 3600 * 24
acl_policy_name = "vault_sync_readonly"
k8s_approle_secret = "vault-approle-secret"
k8s_approle_auth = "vault-approle-auth"

# Vault sync class
class vault_sync:
    # Init function - constructor
    def __init__(self, name, namespace, vault_namespace, k8s_client, vault_client):
        self.id = namespace + ":" + name
        self.name = name
        self.namespace = namespace
        self.vault_namespace = vault_namespace
        self.k8s_client = k8s_client
        self.vault_client = vault_client
        self.current_expiration = time.time() - (float(os.environ.get("SECRET_ID_RENEWAL")) if os.environ.get("SECRET_ID_RENEWAL") else global_secret_id_renewal) - 10

    # To print object
    def __str__(self):
        return "ID: %s\nName: %s\nNamespace: %s\nVault Namespace: %s\nCurrent expiration: %10.0f" % (self.id, self.name, self.namespace, self.vault_namespace, self.current_expiration)

    # Configure Vault namespace for application
    def configure_vault_namespace(self):
        if self.vault_namespace == "":
            logging.info("Vault namespace is not defined - skipping")
            return
        logging.info("Configuring Vault namespace %s" % (self.vault_namespace))
        # Create namespace or require one to be already present?
        # RBAC for namespace - from K8S namespace RBAC? (read, edit CRB's on namespace)
        # If creating namespace - create authorization token secret - require it from new apps connecting to existing namespace

    # Configure approle for application
    def configure_vault_approle(self):
        logging.info("Configuring Vault approle for %s application in namespace %s" % (self.name, self.namespace))

        approle_ttl = (int(os.environ.get("SECRET_ID_TTL")) if os.environ.get("SECRET_ID_TTL") else global_secret_id_expiration)
        # Configure policy
        try:
            policy=self.vault_client.sys.read_acl_policy(
                name=acl_policy_name
            )
        except hvac.exceptions.InvalidPath:
            logging.info("Creating Vault policy %s" % (acl_policy_name))
            self.vault_client.sys.create_or_update_acl_policy(
                name = acl_policy_name,
                policy='path "*" { capabilities = ["read"]}'
            )
            policy=self.vault_client.sys.read_acl_policy(
                name=acl_policy_name
            )
        logging.debug("Policy: %s" % (policy))
 
        # Configure approle
        approle_name = self.name + "-approle"
        try:
            app_role = self.vault_client.auth.approle.read_role(
                role_name = approle_name,
            )
        except hvac.exceptions.InvalidPath:
            logging.info("Creating Vault approle %s" % (approle_name))
            self.vault_client.auth.approle.create_or_update_approle(
                role_name = approle_name,
                token_policies = [acl_policy_name],
                secret_id_ttl = approle_ttl,
                token_ttl = approle_ttl
            )
            app_role = self.vault_client.auth.approle.read_role(
                role_name = approle_name,
            )
        logging.debug("AppRole: %s" % (app_role))

        # Get role_id and secret_id
        role_id = self.vault_client.auth.approle.read_role_id(
            role_name = approle_name
        )
        logging.debug("Role_id: %s" % (role_id))
        secret_id = self.vault_client.auth.approle.generate_secret_id(
            role_name = approle_name
        )
        logging.debug("Secret_id: %s" % (secret_id))

        # Configure K8S CR's for vault secrets operator
        # Do not create vaultConnection - it will 'default' to default vaultConnection in vault operator namespace
        # Create AppRole Secret
        client_api = self.k8s_client.CoreV1Api()
        approle_secret_name = k8s_approle_secret + "-" + self.name
        secret_string_data = {
            "id": secret_id['data']['secret_id']
        }
        secret_body = self.k8s_client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=self.k8s_client.V1ObjectMeta(name=approle_secret_name),
            string_data=secret_string_data
        )
        try:
            #secret = client_api.read_namespaced_secret(k8s_approle_secret, self.namespace)
            client_api.patch_namespaced_secret(name=approle_secret_name, namespace=self.namespace, body=secret_body)
            logging.info("Patched secret %s" % (approle_secret_name))
        except self.k8s_client.exceptions.ApiException as e:
            if e.status == 404:
                client_api.create_namespaced_secret(namespace=self.namespace, body=secret_body)
                logging.info("Created secret %s" % (approle_secret_name))

        # Create vaultAuth (using default vaultConnection)
        api_client = self.k8s_client.ApiClient()
        crd_api = self.k8s_client.CustomObjectsApi(api_client)
        approle_auth_name = k8s_approle_auth + "-" + self.name
        try:
            vault_auth = crd_api.get_namespaced_custom_object(group="secrets.hashicorp.com", version="v1beta1", plural="vaultauths", namespace=self.namespace, name=approle_auth_name)
        except self.k8s_client.exceptions.ApiException as e:
            if e.status == 404:
                vault_auth_spec = {
                    'apiVersion': 'secrets.hashicorp.com/v1beta1',
                    'kind': 'VaultAuth',
                    'metadata': {
                        'name': approle_auth_name,
                        'namespace': self.namespace
                    },
                    'spec': {
                        'appRole': {
                            'roleId': role_id['data']['role_id'],
                            'secretRef': approle_secret_name
                        },
                        'method': 'appRole',
                        'mount': 'approle'
                    }
                }
                dyn_client = DynamicClient(api_client)
                vault_auth_resource = dyn_client.resources.get(api_version='secrets.hashicorp.com/v1beta1', kind='VaultAuth')
                vault_auth = vault_auth_resource.create(body=vault_auth_spec, namespace=self.namespace)
                logging.info("Created VaultAuth %s" % (approle_auth_name))
        logging.info("VaultAuth: %s" % (vault_auth))


    # Configure Vault integration for application
    def configure_vault_integration(self):
        logging.info("Configuring Vault integration for %s application in namespace %s" % (self.name, self.namespace))
        self.configure_vault_namespace()
        self.configure_vault_approle()



