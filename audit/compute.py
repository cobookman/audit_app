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

from iptools import IpRangeList
from googleapiclient.errors import HttpError
from utils import get_api, pagingc, paging_batch, last_log_time, log_write,\
    log_timestamp, log_entry_id, get_project_ids, error_info

def log_all_network(resource, log_id):
    for p in get_project_ids():
        log_network(p, resource, log_id)

def log_network(project, resource, log_id):
    try:
        zones = get_zones(project)
    except HttpError as e:
        code, reason = error_info(e)
        # skip projects for which compute API is not enabled
        if reason == 'accessNotConfigured': return
        else: raise
    rules = get_fw_rules(project)
    routes = get_routes(project)
    api = get_api('compute').instances()
    for zone in zones:
        req = api.list(project=project, zone=zone)
        paging_batch(
            lambda batch: log_write(
                map( lambda i: to_network_entry(
                        i,
                        filter(lambda r: rule_applies(i, r), rules),
                        filter(lambda r: instance_ip_in_range(i, IpRangeList(r['destRange'])), routes)
                    ),
                    batch
                ),
                resource, log_id
            ),
            api, req
        )
        break

def to_network_entry(instance, rules, routes):
    time = log_timestamp()
    iid = instance['id']
    return {
        'timestamp': time,
        # TODO: insertId - map to source Etags?
        'insertId': log_entry_id([str(time['seconds']), str(iid)]),
        'jsonPayload': {
            'instance': iid,
            'rules': rules,
            'routes': routes
        },
        'resource': { 'type': 'global' }
    }

def instance_ip_in_range(instance, range):
    for ni in instance['networkInterfaces']:
        if ni['networkIP'] in range : return True
    return False

def rule_applies(instance, rule, source=True):
    if source:
        return \
        rule_tags_apply(instance, rule) or \
        rule_service_accts_apply(instance, rule) or \
        rule_range_apply(instance, rule)
    else:
        return \
        rule_tags_apply(instance, rule, 'targetTags') or \
        rule_service_accts_apply(instance, rule, 'targetServiceAccounts') or \
        rule_range_apply(instance, rule, 'destinationRanges')

def rule_tags_apply(instance, rule, rule_key='targetTags'):
    return set(rule.get(rule_key,[])).intersection(instance['tags'].get('items',[])) > 0

def rule_service_accts_apply(instance, rule, rule_key='sourceServiceAccount'):
    accts = map(lambda sa : sa['email'], instance['serviceAccounts'])
    return set(rule.get(rule_key,[])).intersection(accts) > 0

def rule_range_apply(instance, rule, rule_key='sourceRanges'):
    instance_ip_in_range(instance, IpRangeList(*rule.get(rule_key, [])))

def instance_ip_in_range(instance, range):
    for ni in instance['networkInterfaces']:
        if ni['networkIP'] in range : return True
    return False

def get_fw_rules(project):
    api = get_api('compute').firewalls()
    return pagingc(api, api.list(project=project))

def get_routes(project):
    api = get_api('compute').routes()
    return pagingc(api, api.list(project=project))

def get_zones(project):
    api = get_api('compute').zones()
    return map(
        lambda z: z['name'],
        pagingc(api, api.list(project=project))
    )
