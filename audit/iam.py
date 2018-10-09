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

from utils import get_api, pagingc, paging_batch, last_log_time, log_write, log_print,\
log_timestamp, log_entry_id, dump, flatmap, to_dict, get_folder_ids, get_project_ids

USER_SCOPES=[
    'https://www.googleapis.com/auth/admin.directory.group.readonly',
    'https://www.googleapis.com/auth/admin.directory.user.readonly'
]

def log_permissions(domain, org, resource, log_id):
    log_write(
        map(lambda (u, p): to_perm_entry(u, p), audit_report_policy(domain, org).iteritems()),
        resource, log_id
    )

def to_perm_entry(user, permissions):
    time = log_timestamp()
    return {
        'timestamp': time,
        # TODO: insertId - map to source Etags?
        'insertId': log_entry_id([str(time['seconds']), user]),
        'jsonPayload': {
            'user': user,
            'permissions': permissions
        },
        'resource': { 'type': 'global' }
    }

def audit_report_policy(domain, org):
    groups = to_dict(user_group_mapping(domain))
    return policy_by_user(
        filter(lambda p: substitute_members(p, groups), get_all_policies(org))
    )

def policy_by_user(policies):
    ret = {}
    for p in policies:
        for m in p['members']:
            if m not in ret: ret[m] = []
            ret[m].append({'resource':p['resource'], 'role':p['role']})
    return ret

def substitute_members(policy, groups):
    found = []
    def record(member):
        if member.startswith('serviceAccount:'): return False
        if member.startswith('group:'):
            found.append(member)
            return False
        return True
    ret = filter(lambda m: record(m), policy['members'])
    for g in found: ret + groups[g]
    policy['members'] = ret
    return not not ret # for filter function

def get_all_policies(org):
    return get_org_policies(org)\
        + flatmap(lambda f: get_folder_policies(f), get_folder_ids(org))\
        + flatmap(lambda p: get_project_policies(p), get_project_ids() )

def get_org_policies(resource, body={}):
    api = get_api('cloudresourcemanager').organizations()
    return policy_wrap(
        # api.getIamPolicy doesn't apper to have paging
        api.getIamPolicy(resource=resource, body=body).execute()['bindings'],
        resource, 'organization'
    )

def get_folder_policies(resource, body={}):
    api = get_api('cloudresourcemanager', 'v2').folders()
    return policy_wrap(
        pagingc(api, api.getIamPolicy(resource=resource, body=body), item_key='bindings'),
        resource, 'folder'
    )

def get_project_policies(resource, body={}):
    api = get_api('cloudresourcemanager').projects()
    return policy_wrap(
        pagingc(api, api.getIamPolicy(resource=resource, body=body), item_key='bindings'),
        resource, 'project'
    )

def policy_wrap(policies, resource, type):
    for p in policies: p['resource'] = {'name':resource, 'type':type}
    return policies

def get_members(group):
    api = get_api('admin', 'directory_v1', USER_SCOPES).members()
    return pagingc(api, api.list(groupKey=group), item_key='members')

def get_member_emails(group):
    return filter(lambda e: e is not None,
        map(lambda m : m.get('email'), get_members(group)))

def user_group_mapping(domain):
    return map(lambda g:
        ('group:{}'.format(g), get_member_emails(g)),
        get_group_ids(domain)
    )

def get_groups(domain):
    api = get_api('admin', 'directory_v1', USER_SCOPES).groups()
    return pagingc(api, api.list(domain=domain), item_key='groups')

def get_group_ids(domain):
    return map(lambda g: g['email'], get_groups(domain))

def get_users(domain):
    api = get_api('admin', 'directory_v1', USER_SCOPES).users()
    return pagingc(api, api.list(domain=domain), item_key='users')
