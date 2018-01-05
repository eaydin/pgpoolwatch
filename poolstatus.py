#!/usr/bin/python

import cStringIO, operator
import subprocess as sp
from datetime import datetime

# The indent function is used to pretty print tables
# Source of the function: http://code.activestate.com/recipes/267662-table-indentation/

def indent(rows, hasHeader=False, headerChar='-', delim=' | ', justify='left',
           separateRows=False, prefix='', postfix='', wrapfunc=lambda x:x):
    """Indents a table by column.
       - rows: A sequence of sequences of items, one sequence per row.
       - hasHeader: True if the first row consists of the columns' names.
       - headerChar: Character to be used for the row separator line
         (if hasHeader==True or separateRows==True).
       - delim: The column delimiter.
       - justify: Determines how are data justified in their column.
         Valid values are 'left','right' and 'center'.
       - separateRows: True if rows are to be separated by a line
         of 'headerChar's.
       - prefix: A string prepended to each printed row.
       - postfix: A string appended to each printed row.
       - wrapfunc: A function f(text) for wrapping text; each element in
         the table is first wrapped by this function."""
    # closure for breaking logical rows to physical, using wrapfunc
    def rowWrapper(row):
        newRows = [wrapfunc(item).split('\n') for item in row]
        return [[substr or '' for substr in item] for item in map(None,*newRows)]
    # break each logical row into one or more physical ones
    logicalRows = [rowWrapper(row) for row in rows]
    # columns of physical rows
    columns = map(None,*reduce(operator.add,logicalRows))
    # get the maximum of each column by the string length of its items
    maxWidths = [max([len(str(item)) for item in column]) for column in columns]
    rowSeparator = headerChar * (len(prefix) + len(postfix) + sum(maxWidths) + \
                                 len(delim)*(len(maxWidths)-1))
    # select the appropriate justify method
    justify = {'center':str.center, 'right':str.rjust, 'left':str.ljust}[justify.lower()]
    output=cStringIO.StringIO()
    if separateRows: print >> output, rowSeparator
    for physicalRows in logicalRows:
        for row in physicalRows:
            print >> output, \
                prefix \
                + delim.join([justify(str(item),width) for (item,width) in zip(row,maxWidths)]) \
                + postfix
        if separateRows or hasHeader: print >> output, rowSeparator; hasHeader=False
    return output.getvalue()


class PoolNodes(object):
    def __init__(self):
        self.node1 = {}
        self.node2 = {}
        self.stat_replication = {}
        self.master = ''
        self.slave = ''
        self.xlog_location = ''
        self.xlog_slave_location = ''
        self.pool_nodes = ''
        self.row_num_all = ''
        self.row_num_24 = ''
        self.master_status = 0
        self.master_stream = ''
        self.slave_status = 0
        self.slave_stream = ''
        self.master_disk = ''
        self.slave_disk = ''
        self.cluster_show = ''
        self.pg_stat_replication = ''

        self._run_pool_nodes()
        self._find_master()
        self._find_slave()
        self._run_cluster_show()
        self._run_stat_replication()

        self._run_repl_events()
        self._run_xlog_location()
        self._run_xlog_slave_location()
        self._wal_process()
        self.master_disk = self._get_disk_usage(self.master)
        self.slave_disk = self._get_disk_usage(self.slave)
        self._pretty_print()

    def _run_pool_nodes(self):
        try:
            output_original = sp.check_output(["psql", "-h", "localhost", "-U", "pgpool", "-d", "postgres", "-c", "show pool_nodes"])

            output = output_original.split('\n')

            self.node1['node_id'] = self._strip_element(output[2], 0)
            self.node1['hostname'] = self._strip_element(output[2], 1)
            self.node1['port'] = self._strip_element(output[2], 2)
            self.node1['status'] = self._strip_element(output[2], 3)
            self.node1['lb_weight'] = self._strip_element(output[2], 4)
            self.node1['role'] = self._strip_element(output[2], 5)
            self.node1['select_cnt'] = self._strip_element(output[2], 6)
            self.node1['load_balance_node'] = self._strip_element(output[2], 7)
            self.node1['replication_delay'] = self._strip_element(output[2], 8)


            self.node2['node_id'] = self._strip_element(output[3], 0)
            self.node2['hostname'] = self._strip_element(output[3], 1)
            self.node2['port'] = self._strip_element(output[3], 2)
            self.node2['status'] = self._strip_element(output[3], 3)
            self.node2['lb_weight'] = self._strip_element(output[3], 4)
            self.node2['role'] = self._strip_element(output[3], 5)
            self.node2['select_cnt'] = self._strip_element(output[3], 6)
            self.node2['load_balance_node'] = self._strip_element(output[3], 7)
            self.node2['replication_delay'] = self._strip_element(output[3], 8)

            self.pool_nodes = output_original
        except:
            self.pool_nodes = "An Error has occurred!"

    def _run_stat_replication(self):
        try:
            if self.master == '':
                self._find_master()
            if self.master != '':
                output = sp.check_output(["psql", "-h", self.master, "-U", "repmgr", "-d", "repmgr",
                                          "-c", "select * from pg_stat_replication"])

                output = output.split('\n')

                self.stat_replication['pid'] = self._strip_element(output[2], 0)
                self.stat_replication['usesysid'] = self._strip_element(output[2], 1)
                self.stat_replication['usename'] = self._strip_element(output[2], 2)
                self.stat_replication['application_name'] = self._strip_element(output[2], 3)
                self.stat_replication['client_addr'] = self._strip_element(output[2], 4)
                self.stat_replication['client_hostname'] = self._strip_element(output[2], 5)
                self.stat_replication['client_port'] = self._strip_element(output[2], 6)
                self.stat_replication['backend_start'] = self._strip_element(output[2], 7)
                self.stat_replication['backend_xmin'] = self._strip_element(output[2], 8)
                self.stat_replication['state'] = self._strip_element(output[2], 1)
                self.stat_replication['sent_location'] = self._strip_element(output[2], 1)
                self.stat_replication['write_location'] = self._strip_element(output[2], 1)
                self.stat_replication['flush_location'] = self._strip_element(output[2], 1)
                self.stat_replication['replay_location'] = self._strip_element(output[2], 1)
                self.stat_replication['sync_priority'] = self._strip_element(output[2], 1)
                self.stat_replication['sync_state'] = self._strip_element(output[2], 1)

                labels = ('Parameter', 'Value')
                data = [["pid",self.stat_replication['pid']], ['usesysid', self.stat_replication['usesysid']],
                        ["usename", self.stat_replication['usename']], ["application_name", self.stat_replication['application_name']],
                        ["client_addr", self.stat_replication['client_addr']],
                        ["client_hostname", self.stat_replication['client_hostname']],
                        ['client_port', self.stat_replication['client_port']],
                        ['backend_start', self.stat_replication['backend_start']],
                        ['backend_xmin', self.stat_replication['backend_xmin']],
                        ['state', self.stat_replication['state']],
                        ['sent_location', self.stat_replication['sent_location']],
                        ['write_location', self.stat_replication['write_location']],
                        ['flush_location', self.stat_replication['flush_location']],
                        ['replay_location', self.stat_replication['replay_location']],
                        ['sync_priority', self.stat_replication['sync_priority']],
                        ['sync_state', self.stat_replication['sync_state']]
                        ]

                self.pg_stat_replication = indent([labels]+data, hasHeader=True, prefix='- ')
        except:
            self.pg_stat_replication = "An error occurred while getting stat_replication"

    def _run_repl_events(self):
        try:
            if self.master == '':
                self._find_master()
            if self.master != '':
                output_all = sp.check_output(["psql", "-h", self.master, "-U", "repmgr", "-d", "repmgr",
                                          "-c", "select * from repl_events"])
                output_24 = sp.check_output(["psql", "-h", self.master, "-U", "repmgr", "-d", "repmgr",
                                          "-c", "select * from repl_events where event_timestamp > now() - interval '24 hours'"])


                self.row_num_all = str(output_all.split('\n')[-3].strip().split()[0][1:])
                self.row_num_24 = str(output_24.split('\n')[-3].strip().split()[0][1:])
        except:
            self.row_num_24 = "?"
            self.row_num_all = "?"

    def _run_xlog_location(self):
        try:
            if self.master == '':
                self._find_master()
            if self.master != '':
                output = sp.check_output(["psql", "-h", self.master, "-U", "repmgr", "-d", "repmgr",
                                          "-c", "select pg_current_xlog_location()"])
                output = output.split('\n')
                self.xlog_location = self._strip_element(output[2],0)
        except Exception as err:
            print("An error has occurred while getting XLOG Location: {0}".format(str(err)))

    def _run_xlog_slave_location(self):
        try:
            if self.slave == '':
                self._find_slave()
            if self.slave != '':
                output = sp.check_output(["psql", "-h", self.slave, "-U", "repmgr", "-d", "repmgr",
                                          "-c", "select pg_last_xlog_receive_location()"])
                output = output.split('\n')
                self.xlog_slave_location = self._strip_element(output[2],0)
        except Exception as err:
            print("An error has occurred while getting XLOG Receive Location: {0}".format(str(err)))

    def _get_disk_usage(self, host):
        try:
            output = sp.check_output(["ssh", "-o", "ConnectTimeout=5", host, "df / -h"])
            output = output.split('\n')[1]
            output = output.split()[4]
        except Exception as err:
            print("Error: {0}".format(str(err)))
            output = '?'
        return output

    def _strip_element(self, input, num):
        return input.split('|')[num].strip()

    def _find_master(self):
        if len(self.node1) == 0 and len(self.node2) == 0:
            self._run_pool_nodes()
        else:
            if self.node1['role'] == 'primary':
                self.master = self.node1['hostname']
            elif self.node2['role'] == 'primary':
                self.master = self.node2['hostname']
            elif self.node1['role'] == 'master':
                self.master = self.node1['hostname']
            elif self.node2['role'] == 'master':
                self.master = self.node2['hostname']
            else:
                print("WARNING: No Master Detected?")
                self.master = ''

    def _find_slave(self):
        if len(self.node1) == 0 and len(self.node2) == 0:
            self._run_pool_nodes()
        else:
            if self.node1['role'] == 'standby':
                self.slave = self.node1['hostname']
            elif self.node2['role'] == 'standby':
                self.slave = self.node2['hostname']
            elif self.node1['role'] == 'slave':
                self.slave = self.node1['hostname']
            elif self.node2['role'] == 'slave':
                self.slave = self.node2['hostname']
            else:
                print("WARNING: No Slave Detected?")
                self.slave = ''

    def _wal_process(self):
        if self.master == '':
            self._find_master()
        if self.slave == '':
            self._find_slave()

        self.master_status = 0
        if self.master != '':
            try:
                output_master = sp.check_output(["ssh", "-o", "ConnectTimeout=5", self.master, "ps aux | egrep 'wal\ssender'"])
                output_master = output_master.strip()
                if len(output_master) != 0:
                    self.master_stream = output_master.split()[-1]
                    self.master_status = 1
            except:
                self.master_stream = ''
                self.master_status = 0

        self.slave_status = 0
        if self.slave != '':
            try:
                output_slave = sp.check_output(["ssh", "-o", "ConnectTimeout=5", self.slave, "ps aux | egrep 'wal\sreceiver'"])
                output_slave = output_slave.strip()
                if len(output_slave) != 0:
                    self.slave_stream = output_slave.split()[-1]
                    self.slave_status = 1
            except:
                self.slave_stream = ''
                self.slave_stream = 0

    def _run_cluster_show(self):
        try:
            if self.master == '':
                self._find_master()
            if self.master != '':
                output = sp.check_output(["ssh", "-o", "ConnectTimeout=5", self.master, "/usr/pgsql-9.6/bin/repmgr cluster show"])
                if len(output) > 0:
                    self.cluster_show = output
        except:
            self.cluster_show = "An Error occurred while getting cluster show."

    def _pretty_print(self):

        print("Output of: show pool_nodes")
        print(self.pool_nodes)

        print("Output of: repmgr cluster show")
        print(self.cluster_show)

        print("Output of: pg_stat_replication")
        print(self.pg_stat_replication)

        if self.master_status:
            master_s = "UP"
            master_s2 = self.master_stream
        else:
            master_s = "DOWN"
            master_s2 = ''
        if self.slave_status:
            slave_s = "UP"
            slave_s2 = self.slave_stream
        else:
            slave_s = "DOWN"
            slave_s2 = ''
        data = [
                ['Current Datetime', str(datetime.now())],
                ['xlog_location (master)', self.xlog_location],
                ['xlog_location (slave)', self.xlog_slave_location],
                ['WAL Process (master)', master_s2, master_s],
                ['WAL Process (slave)', slave_s2, slave_s],
                ['Number of Events (all)', self.row_num_all],
                ['Number of Events (24h)', self.row_num_24],
                ['MASTER', self.master, 'Disk', self.master_disk],
                ['SLAVE', self.slave, 'Disk', self.slave_disk]
        ]
        labels = ('Parameter', 'Value')
        print(indent([labels] + data, hasHeader=True, prefix='- '))

if __name__ == '__main__':
    p = PoolNodes()
