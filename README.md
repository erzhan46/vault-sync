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
- Install and configure Hashicorp Vault Secrets operator
- Deploy operator with required parameters 
- Test - create namespaces with vault-sync CR - observe Vault namespace created and Vault connectivity/authentication configured by vault-sync operator
- Test - create VaultStaticSecret CR (part of Vault Secrets operator) pointing to Vault kv - observe K8S secret created
