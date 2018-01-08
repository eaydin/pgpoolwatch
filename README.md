# pgpoolwatch

Services and scripts to monitor PGPOOL + repmgr cluster. Compatible with repmgr 3.2, pgpool + postgresql 9.6. Best to use with Global Server Load Balancing scenarios.

### Introduction

This project started off with a simple script (which is now *poolstatus.py*) to simply monitor the state of the cluster with a single command.
Now it has multiple servers that run alongside pgpool and repmgr to notify external services.

The basic idea is to detect wether one of the pgpool instances is correctly running (using *pgpwatch*). If it does, than a specific port on the server is open.
Also the same principle follows for repmgr instances. Yet, the repmgr watching services (i.e. *repmgrwatch*) can check on their corresponding pgpool servers and open their TCP ports according to the status of the pgpool status. Also only the **master** repmgr port is opened, so it is easy to distinguish with host to use for writing.

The services are capable of sending mails using SMTP.

You can have either 1 or 2 pgpools in your cluster. Works with both ways.
Also note that you don't need to have any pgpools at all. You can use the *repmgrwatch* service only if you only want to monitor your repmgr cluster and detect the master server using TCP Port checks.

The scripts are tested in Python 2.7. Services (which reside in the *services* directory) are compatible with *systemd* and are tested on CentOS 7.

### Topology in Action

Below is a scenario with 2 GSLB's checking on 2 pgpools and 3 repmgr servers.

* We want pgp.mydomain.com to return

    * One of the pgpool servers if it is active.
    * If both pgpool servers are down, return the master repmgr server.
* We want db.mydomain.com to return the master repmgr server *only if pgpools are down*.

The crucial point is *only if pgpools are down*. If we wanted db.mydomain.com to return the master repmgr *even if one of the pgpools were up*, then we'd set the `force_open` setting to `yes` in the `config.ini` file for the repmgr settings.

```
               +----------------------------------------------+
               |                                              |
          +----+                  GSLB 1&2                    +------+
          |    |                                              |      |
          |    +---+-----------------+-----------------+------+      |
          |        |                 |                 |             |
          |        |                 |                 |             |
          |        | OK              |                 | OK          |
          |        |                 |                 |             |
          |        |                 |                 |             |
          |    +---v----------+      |        +--------v-----+       |
          |    |              |      |        |              |       |
          |    |     PGP1     +---------------+     PGP2     |       |
   DEAD   |    |   TCP 5559   |      |        |   TCP 5559   |       | DEAD
(OR ALIVE)|    |              |      |        |              |       |
          |    +--------------+      |        +--------------+       |
          |                          |                               |
          |                          |                               |
          |                          | DEAD                          |
          |                          |                               |
          |                          |                               |
          |   +------------+     +---v--------+     +------------+   |
          |   |   REPMGR   |     |   REPMGR   |     |   REPMGR   |   |
          +--->  (master)  +-----+  (slave1)  +-----+  (slave2)  <---+
              |  TCP 5560  |     |  TCP 5560  |     |  TCP 5560  |
              +------------+     +------------+     +------------+

```

The above scenario uses 5559 to open on PGP servers, and 5560 on REPMGR servers. We could have used the same ports, doesn't really matter.

The GSLB will check on port 5559 on PGP1 and PGP2, if both are alive, pgpwatch will keep those ports open, so the GSLB will return single or both A records depending on the GSLB configuration.

Also the GSLB will check on port 5560 all of the REPMGR servers. None of them will have their port open if they detect that PGP's have 5559 open. When both of the PGP's close their 5559 (i.e. failure) then the master REPMGR will open its 5560. Therefore the GSLB will detect it.

It is possible to configure the GSLB to check the PGP's first, and when both fail, it can check the REPMGR ports, that way on a failure of PGP's, the pgp.mydomain.com can return the master repmgr even though none of the PGP's are running.

If we'd set the `force_open=yes` configuration in the `config.ini` for the `repmgr` section, then the `DEAD (OR ALIVE)`  connection in the diagram would have been `ALIVE/OK`.


### Installation

Assuming you have setup all of your pgpool and repmgr servers, all you need is Python 2.7 and git in your system.

#### repmgr

Clone this repository in a path (i.e. `/root/`).
```bash
git clone https://github.com/eaydin/pgpoolwatch
```

Enter the directory, copy and edit the setting files.

```bash
cd pgpoolwatch
cp config.ini.sample config.ini
cp args.txt.sample args.txt
```

Edit `config.ini` and if you enable `sendmail` in it, then you better edit `args.txt` too.

You can check if the script is running correctly by running the `repmgrwatch.py` script.

If everything seems normal, install the repmgrwatch service to systemd path and enable.

```bash
cp services/repmgrwatch.service /etc/systemd/system
systemctl daemon-reload
systemctl enable repmgrwatch
```

Start the service
```bash
systemctl start repmgrwatch

```

#### pgpool

Clone this repository in a path (i.e. `/root`/).
```bash
git clone https://github.com/eaydin/pgpoolwatch
```

Enter the directory, copy and edit the setting files.

```bash
cd pgpoolwatch
cp config.ini.sample config.ini
cp args.txt.sample args.txt
```

Edit `config.ini` and if you enable `sendmail` in it, then you better edit `args.txt` too.

It is best to run the `poolstatus.py` script as the `postgres` user. So you better create a hardlink of it to the users home directory.

Assuming the home directory of user `postgres` is `/var/lib/pgsql` you can

```bash
ln /root/pgpoolwatch/poolstatus.py /var/lib/pgsql/poolstatus.py
chown postgres: /root/pgpoolwatch/poolstatus.py
chmod +x /root/pgpoolwatch/poolstatus.py
```

This way the *postgres* user can run the script.
Note that it is a good idea to have both *postgres* user and *root* user to have access to the repmgr servers. In order to do that, create an SSH RSA public/private key pair and add it to the postgres user in the repmgr server. Also copy the private key to the root users `.ssh` folder so that it can also access. It is a good idea to disable `StrictHostKeyChecking` in `ssh_config`, yet it is a better idea to keep it asking but creating first SSH connections from both root and postgres users.

Test the poolstatus script as postgres user.
```bash
runuser -l postgres -c '/var/lib/pgsql/poolstatus.py'
```

Also test the pgpwatch script (as root user).
```bash
cd /root/pgpoolwatch
./pgpwatch.py
```

If you are happy with the results, install, enable and start the pgpwatch systemd service.

```bash
cp services/pgpwatch.service /etc/systemd/system
systemctl daemon-reload
systemctl enable pgpwatch
systemctl start pgpwatch
```

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

### Configuration Files

#### config.ini

This is the main configuration file for both pgpwatch and repmgr watch services. The default path is `/root/pgpwatch/config.ini` yet while running both scripts, it can be specified as following arguments:

```bash
./pgpwatch.py --config=/path/to/config.ini
./repmgrwatch.py --config=/path/to/config.ini
```

It consists of three sections.

#####[pgp]
These settings only apply to pgpwatch
* **check_period**: The period (in seconds) to run check.
* **success_period**: The number of checks (not seconds!) should be elapsed to send a "System is Successfully running" mail. So if `check_period=5` and `success_period=500` than the system will be checked every 5 seconds, and a "success" mail will be sent every 2500 seconds.
* **mail_on_success**: Either `yes` or `no`. Should we send a mail even when the system is running smoothly?
* **open_port**: Port to open when pgpool is running. Default `5559`.

#####[repmgr]
These settings only apply to repmgrwatch
* **check_period**: The period (in seconds) to run check.
* **pgp_server_1**: IP or hostname of the first pgpool server.
* **pgp_server_2**: IP or hostname of the second pgpool server. If you only have one pgpool server, keep it the same with `pgp_server_1`.
* **check_port**: Port number to check on pgpool servers. Default `5559`.
* **open_port**: Port to open when repmgr is running. Default `5559`.
* **force_open**: Either `yes` or `no`. Should we open the port on repmgr even though pgpool instances are running correctly? Default is `no`.

#####[general]
These settings apply both to pgpwatch and repmgrwatch
* **sendmail**: Either `yes` or `no`. Should we send mails?
* **sendmail_path**: Path to the sendmail script. Default is `/root/pgpoolwatch/sendmail.py`
* **sendmail_settings_path**: Path of arguments to pass to the sendmail script. Default is `/root/pgpoolwatch/args.txt`
* **poolstatus_path**: Path of the poolstatus script. Default is `/root/pgpoolwatch/poolstatus.py`
* **poolstatus_user**: Username to run the poolstatus script. Default is `postgres`

#### args.txt

This is the arguments file for the sendmail script. This is a seperate file from the config.ini only for historical reasons. They should be merged in the future.
Default values are as following (self explaining):
```
--user=sender@email.com
--password=SuperSecr3tPassw0rd
--sender=sender@email.com
--server=mail.emailcom
--port=587
--subject=PGPOOL Status Script - Failure
--receivers=bill@microsoft.com page@google.com
```

Other optional arguments are:
```
--failed-node=Name of the failed node
--new-master=Name of the new repmgr master
--body=The message body. <br>Better to write it in <b>HTML</b>
```

Passing the args.txt to the sendmail script:

```bash
python /path/to/sendmail.py @/other/path/to/args.txt
```