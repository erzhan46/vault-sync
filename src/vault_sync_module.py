from kubernetes import client, config, watch
import os
import logging
import hvac
import time

# Some globals
global_watch_timeout = 3600
global_secret_id_renewal = 3600 * 18
global_secret_id_expiration = 3600 * 24
acl_policy_name = "vault_sync_readonly"

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

    # Configure approle for application
    def configure_vault_approle(self):
        logging.info("Configuring Vault approle for %s application in namespace %s" % (self.name, self.namespace))

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
        print(policy)
 
        # Configure approle
        try:
            app_role = self.vault_client.auth.approle.read_role(
                role_name=self.name,
            )
        except hvac.exceptions.InvalidPath:
            logging.info("Creating Vault approle %s" % (self.name + "_approle"))
            self.vault_client.auth.approle.create_or_update_approle(
                role_name = self.name,
                token_policies = [acl_policy_name],
                secret_id_ttl = (int(os.environ.get("SECRET_ID_TTL")) if os.environ.get("SECRET_ID_TTL") else global_secret_id_expiration),
                token_ttl = (int(os.environ.get("SECRET_ID_TTL")) if os.environ.get("SECRET_ID_TTL") else global_secret_id_expiration)
            )
            app_role = self.vault_client.auth.approle.read_role(
                role_name=self.name,
            )
        print(app_role)
#        logging.debug("AppRole role ID for some-role: %s" % (resp["data"]["role_id"]))

        # Get role_id and secret_id

        # Configure K8S CR's for vault secrets operator


    # Configure Vault integration for application
    def configure_vault_integration(self):
        logging.info("Configuring Vault integration for %s application in namespace %s" % (self.name, self.namespace))
        self.configure_vault_namespace()
        self.configure_vault_approle()



