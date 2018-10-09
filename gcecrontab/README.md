# GCE Startup Script for CRON Jobs

Use the following as a
[GCE startup script](https://cloud.google.com/compute/docs/startupscript)
to inject cron jobs into a VM instance at boot time

```sh
#/bin/bash
CRON_PATH='/usr/local/bin'
CRON_SCRIPT="${CRON_PATH}/cron.sh"
CRON_JOBS="${CRON_PATH}/jobs.txt"
LOGS_PATH="/var/log/cron"
CRON_LOGS="${LOGS_PATH}/cron.log"
# CRON_LOGS="/dev/null"

# setup logging
mkdir -p ${LOGS_PATH}
touch ${CRON_LOGS}

# write script(s) for cron triggers - edit this script as required
script="
  #!/bin/bash
  python gce_main.py
"
# NOTE: ${script} is wrapped in "" to preserve newlines on write
echo "${script}"  > ${CRON_SCRIPT}
chmod +x ${CRON_SCRIPT}

# write cron triggers - edit CRON schedule as required
echo "* * * * * /bin/bash ${CRON_SCRIPT} >> ${CRON_LOGS} 2>&1" > ${CRON_JOBS}

# schedule and validate
whoami
crontab ${CRON_JOBS}
crontab -l
```
