# KnotDNS Zabbix Monitoring

Template KnotDNS - Zabbix

## Usage

Enable stats module in knot

```txt
mod-stats:
  - id: dnsstats
    server-operation: on
    query-type: on
    response-code: on
```

Add UserParams to Zabbix Agent

```txt
UserParameter=knotstat.status,sudo /opt/knotstats.py status
UserParameter=knotstat.zones,sudo /opt/knotstats.py zones
UserParameter=knotstat.zone[*],sudo /opt/knotstats.py zone "$1"
```

Add permissions to zabbix user via sudo

```txt
# /etc/sudoers.d/zabbix
zabbix ALL=(ALL) NOPASSWD:/opt/knotstats.py
```
