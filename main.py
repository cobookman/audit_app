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

import os, webapp2
import audit.compute as compute
import audit.reports as reports
import audit.iam as iam
import audit.utils as ut

# app-engine-standard specific
import google.auth.app_engine
import google.auth.iam
import google.auth.transport.requests
import requests_toolbelt.adapters.appengine
requests_toolbelt.adapters.appengine.monkeypatch()

DOMAIN = os.environ['GCP_DOMAIN']
ORG = "organizations/{}".format(os.environ['GCP_ORG_ID'])
LOG_PROJECT = "projects/{}".format(os.environ['GCP_LOG_PROJECT'])

class logins_report(webapp2.RequestHandler):
    def get(self): self.post()
    def post(self):
        reports.sync_admin_logs('login', LOG_PROJECT, 'custom.auth.google.com%2flogins')

class admins_report(webapp2.RequestHandler):
    def get(self): self.post()
    def post(self):
        reports.sync_admin_logs('admin', LOG_PROJECT, 'custom.auth.google.com%2fadminactivity')

class policy_report(webapp2.RequestHandler):
    def get(self): self.post()
    def post(self):
        iam.log_permissions(DOMAIN, ORG, LOG_PROJECT, 'custom.google.com%2fpermissions')

class network_report(webapp2.RequestHandler):
    def get(self): self.post()
    def post(self):
        compute.log_all_network(LOG_PROJECT, 'custom.google.com%2fnetwork')

class main_route(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('gcauditor routes: logins, admins, policy, network')

app = webapp2.WSGIApplication([
    ('/', main_route),
    ('/logins', logins_report),
    ('/admins', admins_report),
    ('/policy', policy_report),
    ('/network', network_report),
], debug=True)
