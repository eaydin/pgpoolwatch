# pgpoolwatch

Services and scripts to monitor PGPOOL + repmgr cluster. Compatible with repmgr 3.2, pgpool + postgresql 9.6. Best to use with Global Server Load Balancing scenarios.

### Introduction

This project started off with a simple script (which is now *poolstatus.py*) to simply monitor the state of the cluster with a single command.
Now it has multiple servers that run alongside pgpool and repmgr to notify external services.

The basic idea is to detect wether one of the pgpool instances is correctly running (using *pgpwatch*). If it does, than a specific port on the server is open.
Also the same principle follows for repmgr instances. Yet, the repmgr watching services (i.e. *repmgrwatch*) can check on their corresponding pgpool servers and open their TCP ports according to the status of the pgpool status. Also only the **master** repmgr port is opened, so it is easy to distinguish with host to use for writing.

The services are capable of sending mails using SMTP.

You can have either 1 or 2 pgpools in your cluster. Works with both ways.

The scripts are tested in Python 2.7. Services (which reside in the *services* directory) are compatible with *systemd* and are tested on CentOS 7.

### Sample poolstatus Output

A Simple Script to Get Reports on a pgpool + repmgr cluster

Designed for a cluster of (either 1 or 2) pgpool server(s), and multiple repmgr servers. 

When you run the *poolstatus.py* script alone, you should get the following output in a healthy cluster:

```
-bash-4.2$ python pgpwatch.py
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
- Number of Events (all) | 68                         
- Number of Events (24h) | 12 
- MASTER                 | dbser2                     | Disk | 5%
- SLAVE                  | dbser1                     | Disk | 5%
```

The script should be run on the pgpool server, which usually would have passwordless ssh access to the repmgr servers.

For now, the script assumes that it has access to the pgpool database on `localhost` with the user `pgpool` and the database `postgres`. So you should get a successful result from the following command.

`psql -h localhost -U pgpool -d postgres`

Also, for now it assumes it has access to the repmgr postgresql databases with username `repmgr` and database `repmgr`. It also assumes the repmgr binary is located at `/usr/pgsql-9.6/bin/repmgr`

These assumptions are hard coded in the script right now, will make them parametric sometime in the future.

The script will auto detect which one is the master and which one is the slave.

When calling this script from within the pgpwatch service, you can specify its path and from which user to call it. So it may be a good idea to create a hardlink of this file into the relevant users home directory according to your system structure.

Tested with Python 2.7