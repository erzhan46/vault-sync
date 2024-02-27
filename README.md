# vault-sync
Vault sync operator to automate vault secrets operator AppRole authentication configuration

Experimenting with python and kubernetes.
Operator will watch vault-sync Custom Resource - determine application name, etc.
Then it will generate namespace in Hashicorp Vault, configure AppRole authentication for current K8S namespace to access secrets in that Hashicorp namespace

## Deployment - TBD
- Helm chart?
- Operator?

## Testing
- Install minicube
  https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-minikube-raft
- Install and configure (namespaces, admin AppRole, etc.)  Hashicorp Vault
```
# Connectivity to vault deployed on minicube
$ kubectl port-forward \
    vault-0 \
    8200:8200

$ jq -r ".root_token" cluster-keys.json # Get the token

$ export VAULT_ADDR="http://localhost:8200/"
$ export VAULT_TOKEN='<TOKEN>'


# Configure admin approle
$ vault auth enable approle

$ vault policy write admin - <<EOF
path "*" {
  capabilities = [ "create", "read", "update" , "delete" , "list" , "sudo" ] 
}
EOF

$ vault write auth/approle/role/admin \
 secret_id_ttl=0 \
 token_num_used=0 \
 token_ttl=0 \
 token_max_ttl=0 \
 secret_id_num_uses=0 \
 token_policies="admin"

# Access vault using admin approle credentials
$ vault read auth/approle/role/admin/role-id # Get the role-id
$ vault write -f auth/approle/role/admin/secret-id # Get the secret-id

$ role_id="<ROLE-ID>"
$ secret_id="<SECRET-ID>"
$ vault write auth/approle/login role_id=$role_id secret_id=$secret_id # Get the token
$ export VAULT_TOKEN='<TOKEN_FROM_APPROLE>'

```
- Install and configure Hashicorp Vault Secrets operator
  https://developer.hashicorp.com/vault/tutorials/kubernetes/vault-secrets-operator#install-the-vault-secrets-operator
- Deploy operator with required parameters 
- Test - create namespaces with vault-sync CR - observe Vault namespace created and Vault connectivity/authentication configured by vault-sync operator
- Test - create VaultStaticSecret CR (part of Vault Secrets operator) pointing to Vault kv - observe K8S secret created

## Appendix

### Validating appRole authentication with Vault Secrets Operator
```
# Read only role
$ vault policy write readonly - <<EOF
path "kv-v2/*" {
   capabilities = ["read"]
}
path "kv-v2/data/*" {
capabilities = ["read"]
}
path "kv-v2/metadata/*" {
capabilities = ["read"]
}
EOF

# Read only appRole
$ vault write auth/approle/role/yob-test2 \
secret_id_ttl=0 \
token_num_uses=0 \
token_ttl=0 \
token_max_ttl=0 \
secret_id_num_uses=0 \
token_policies="readonly"

# AppRole credentials
$ vault read auth/approle/role/yob-test2/role-id
$ vault write -f auth/approle/role/yob-test2/secret-id

#Login and use or create k8s secret and use
$ vault write auth/approle/login role_id=$role_id secret_id=$secret_id

# Set VAULT_TOKEN env var

# Test Query:
$ vault kv put secret/yobtest2 username="user" password="password"
$ vault kv get secret/yobtest2

# Test Query 2:
$ vault secrets enable kv-v2
$ vault kv put kv-v2/yobtest3 username="user" password="password"
$ vault kv get kv-v2/yobtest3

# OpenShift:
$ kubectl -n yob-test2 create secret generic approle-secret --from-literal=id="$secret_id"

```
