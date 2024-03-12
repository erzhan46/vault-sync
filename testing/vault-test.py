# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

import hvac
import sys

# Authentication
client = hvac.Client(
    url='http://127.0.0.1:8200',
    token='hvs.CAESIBRcnxxildgwKCWlpRTl3LlY-s3Uwh3_x8TU_NoTOL-TGh4KHGh2cy5YUkFPbVVrU3Z4WFhwaGg4YWRkSjF1aFc'
)

#client.auth.approle.login(
#    role_id='e4bf3f07-343e-1118-d2b0-11bc4311baec',
#    secret_id='4c089e4e-573f-0ef0-bd24-9f42f9d1ae52'
#)

# Writing a secret
#create_response = client.secrets.kv.v2.create_or_update_secret(
#    path='my-secret-password',
#    secret=dict(password='Hashi123'),
#)

#print('Secret written successfully.')

# List secrets
#list_response = client.secrets.kv.v2.list_secrets(
#    path='kv-v2',
#)

#print('The following paths are available under "hvac" prefix: {keys}'.format(
#    keys=','.join(list_response['data']['keys']),
#))

# Reading a secret
read_response = client.secrets.kv.v2.read_secret_version(path='yobtest3')

password = read_response['data']['data']['password']

print("Response: %s", password)
