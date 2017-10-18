#!/bin/sh
failed_node=$1
new_master=$2
(
date
echo "Failed node: $failed_node"
set -x
if [ -z "$new_master" ]
then
    echo "New Master Argument Empty..."
    echo "We should restart Pgpool"
    ping -c1 -s0 bursadb
    ping -c1 -s0 ankaradb
    ping -c1 -s0 8.8.8.8
    # systemctl restart pgpool
    /usr/bin/python /root/vt/sendmail.py @/root/vt/args.txt --failed-node=$failed_node --new-master=EMPTY --subject="PGPWATCH Failure - System Might Need Attention"
else
    echo "New Master: $new_master"
    /usr/bin/ssh -T -l postgres $new_master "ping -c1 -s0 -q 8.8.8.8 > /dev/null && /usr/pgsql-9.6/bin/repmgr -f /etc/repmgr/9.6/repmgr.conf standby promote 2>/dev/null 1>/dev/null <&-"
    /usr/bin/python /root/vt/sendmail.py @/root/vt/args.txt --failed-node=$failed_node --new-master=$new_master --subject='PGPWATCH Failure - failover run'
fi
exit 0;
) 2>&1 | tee -a /var/log/pgpool_failover.log
