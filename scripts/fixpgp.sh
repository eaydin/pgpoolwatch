#!/usr/bin/env bash
echo "Stopping pgpool service..."
# trying stopping pgpool status gracefully
systemctl stop pgpool

echo "Killing all child processes just in case..."
# incase it failed, kill all child processes
ps aux | grep pgpool | awk {'print $2'} | xargs kill -9

echo "Removing the pgpool_status file (if this doesn't fix it, try: echo -e \"up\nup\" > /tmp/pgpool_status"
rm -f /tmp/pgpool_status
#echo -e "up\nup" > /tmp/pgpool_status

echo "Removing socket files of pgpool"
rm -f /tmp/.s.PGSQL.*

echo "It is a good idea to run this script on the other pgpool server (if you haven't already) before bringing them up"

echo "You may run 'systemctl start pgpool' if you have fixed both servers".