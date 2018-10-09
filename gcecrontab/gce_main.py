# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import audit.compute as compute
import audit.reports as reports
import audit.iam as iam

DOMAIN = os.environ['GCP_DOMAIN']
ORG = "organizations/{}".format(os.environ['GCP_ORG_ID'])
LOG_PROJECT = "projects/{}".format(os.environ['GCP_LOG_PROJECT'])

# Syncs GSuite login-activity report to Stackdriver
reports.sync_admin_logs('login', LOG_PROJECT, 'custom.auth.google.com%2flogins')
# Syncs GSuite Admins-activity report to Stackdriver
reports.sync_admin_logs('admin', LOG_PROJECT, 'custom.auth.google.com%2fadminactivity')
# produces report of all GCP users with their  associated IAM policies
iam.log_permissions(DOMAIN, ORG, LOG_PROJECT, 'custom.google.com%2fpermissions')
# produces report of all GCP with their associated routes & firewall rules
compute.log_all_network(LOG_PROJECT, 'custom.google.com%2fnetwork')
