# pgpoolwatch
A Simple Script to Get Reports on a pgpool + repmgr cluster

Designed for a cluster of (either 1 or 2) pgpool server(s), 2 repmgr servers. The script should be run on the pgpool server, which usually would have passwordless ssh access to the repmgr servers.

Tested with Python 2.7

For now, the script assumes that it has access to the pgpool database on localhost with the user pgpool and the database postgres. So you should get a successful result from the following command.

`psql -h localhost -U pgpool -d postgres`

Also, for now it assumes it has access to the repmgr postgresql databases with username repmgr and database repmgr. It also assumes the repmgr binary is located at `/usr/pgsql-9.6/bin/repmgr`

These assumptions are hard coded in the script right now, will make them parametric sometime in the future.

The script will auto detect which one is the master and which one is the slave.

# Sample Output

An example output would look like:

```
-bash-4.2$ python watch.py
Output of: show pool_nodes
 node_id | hostname | port | status | lb_weight |  role   | select_cnt | load_balance_node | replication_delay
---------+----------+------+--------+-----------+---------+------------+-------------------+-------------------
 0       |  dbser1  | 5432 | down   | 0.500000  | standby | 0          | false             | 0
 1       |  dbser2  | 5432 | up     | 0.500000  | primary | 0          | true              | 0
(2 rows)


Output of: repmgr cluster show
Role      | Name     | Upstream | Connection String
----------+----------|----------|----------------------------------------
* master  |  dbser2  |          | host=dbser2 dbname=repmgr user=repmgr
  standby |  dbser1  |  dbser2  | host=dbser1 dbname=repmgr user=repmgr

Output of: pg_stat_replication
- Parameter        | Value
--------------------------------------------------
- pid              | 4468
- usesysid         | 16384
- usename          | repmgr
- application_name | dbser1
- client_addr      | 192.168.45.3
- client_hostname  |
- client_port      | 55632
- backend_start    | 2017-07-28 16:06:17.006554+03
- backend_xmin     |
- state            | 16384
- sent_location    | 16384
- write_location   | 16384
- flush_location   | 16384
- replay_location  | 16384
- sync_priority    | 16384
- sync_state       | 16384

- Parameter              | Value
-------------------------------------------------------------------
- Current Datetime       | 2017-07-29 17:33:54.419750
- xlog_location (master) | 0/801FBC8
- xlog_location (slave)  | 0/801FBC8
- WAL Process (master)   | 0/801FBC8                  | UP
- WAL Process (slave)    | 0/801FBC8                  | UP
- MASTER                 | dbser2                     | Disk | 5%
- SLAVE                  | dbser1                     | Disk | 5%
```


