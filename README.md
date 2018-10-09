# Auditing Examples

## Scripts
The following python scripts are found in the `audit` module:

```python
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

```

## Permissions setup
Chose or [create project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
and enable the necessary APIs:
```sh
# set existing project as default
gcloud config set project <PROJECT_NAME>
# OR create new one
gcloud projects create <PROJECT_NAME> --set-as-default
# enable necessary APIs
gcloud services enable\
  admin.googleapis.com\
  cloudresource.googleapis.com\
  stackdriver.googleapis.com\
  logging.googleapis.com
```

Edit the [app engine service account](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount) for the project,
this gives the app permission organizational
```
Google Cloud Console -> IAM -> Service accounts -> edit <PROJECT-ID>@appspot.gserviceaccount.com

Enable GSuite domain-wide delegation:   (checked)
Product name (OAuth consent screen)     ${PRODUCT_NAME}
# Take Note of the clientID, used in Gsuite setup

Switch from the project to the domain context in the console and add the
following roles:
 - Compute Viewer               (instance and firewall info)
 - Compute Network Viewer       (network routes)
 - Organization Role Viewer     (top-down IAM Roles)
 - Organization Policy Viewer   (top-down IAM policies)
 - Folder Editor                (folder IAM policies)
```

setup GSuite [delegating authority](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#delegatingauthority),
this gives the app permission to get data from the Admin (GSuite) SDK
```
Admin Console -> Security -> Advanced Settings ->  Manage API client access

Client Name:  ${OAUTH2CLIENTID} (also referenced as 'cliendID')
API Scopes:   https://www.googleapis.com/auth/admin.directory.group.readonly,
              https://www.googleapis.com/auth/admin.directory.user.readonly,
              https://www.googleapis.com/auth/admin.reports.audit.readonly
```

configure app via ENV variables
```sh
vi app.yaml
...
env_variables:
  ADMIN_EMAIL: ''       # Admin email associated with OAuth permissions
  GCP_DOMAIN: ''        # domain to audit
  GCP_ORG_ID: ''        # 12-digit org-id: use `gcloud organizations list`
  GCP_LOG_PROJECT: ''   # project-id for stackdriver logs: use `gcloud projects list`
...
```

### Deploy to GAE
```sh
# ensure 'lib' dependencies are up-to-date
pip install -r requirements.txt -t lib/

# deploy application
gg app deploy app.yaml cron.yaml

# list newly created logs
gcloud logging logs list
```

### Debugging
```
Google Cloud Console -> App Engine -> Task Queues -> cron jobs (tab)
select `view` for a given cron job to view the request logs
```

### View logs
```
Google Cloud Console -> logging -> advanced filter
  resource.type="global"
  logName="projects/<GCP_LOG_PROJECT./logs/<LOG>" # optional
```

### GAE local development
install dependencies:
```sh
# only required first time run or on-change of 'requirements.txt'
pip install -r requirements.txt -t lib/
```

Start the server inside the container:
```sh
# convert keys
cat secret.p12 | openssl pkcs12 -nodes -nocerts -passin pass:notasecret | openssl rsa > secret.pem

dev_appserver.py app.yaml\
  --appidentity_email_address=gcauditor@<YOUR_PROJECT>.iam.gserviceaccount.com\
  --appidentity_private_key_path=./secret.pem
```

### clear logs
```sh
gcloud logging logs delete projects/stackdriver-1522806312/logs/custom.auth.google.com%2Fadminactivity
gcloud logging logs delete projects/stackdriver-1522806312/logs/custom.auth.google.com%2Flogins
gcloud logging logs delete projects/stackdriver-1522806312/logs/custom.google.com%2fpermissions
gcloud logging logs delete projects/stackdriver-1522806312/logs/custom.google.com%2fnetwork
```
