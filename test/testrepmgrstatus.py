#!/usr/bin/python

import subprocess
import argparse
import time
import ConfigParser
import SocketServer
import socket


def check_port(address='localhost', port=5559):
    s = socket.socket()
    try:
        s.connect((address, port))
        print "Socket is open"
        del s
        return True
    except socket.error as err:
        print "Socket is closed?: %s" % str(err)
        del s
        return False

class DBWRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        pass

class DBWServer(SocketServer.TCPServer):
    def __init__(self, host='0.0.0.0', port=5559, handler_class=DBWRequestHandler):
        self.host = host
        self.port = port
        self.handler_class = handler_class
        self.start()

    def start(self):
        print "Initiating server..."
        SocketServer.TCPServer.__init__(self, (self.host, self.port), self.handler_class)
        return

    def activate(self):
        print "Activating server..."
        SocketServer.TCPServer.server_activate(self)
        return

    def close(self):
        print "Closing server..."
        return SocketServer.TCPServer.server_close(self)


def send_mail(path='/root/vt/sendmail.py', arguments='@/root/vt/args.txt', subject="PGPWATCH", failed_node='none', new_master='none', body=None):
    p = subprocess.Popen(["/usr/bin/python", path, arguments, "--subject={0}".format(subject), "--failed-node={0}".format(failed_node),
                          "--new-master={0}".format(new_master), "--body={0}".format(body)])
    p.communicate()[0]


def get_masters():
    try:
        output = subprocess.check_output(["/usr/sbin/runuser", "-l", "postgres", "-c", "/usr/pgsql-9.6/bin/repmgr cluster show"])
        nodes = {}
        nodes['masters'] = []
        nodes['slaves'] = []
        if len(output) > 0:
            rows = output.split('\n')[2:-1]
            for row in rows:
                if '|' in row:
                    if 'master' in row.split('|')[0]:
                        nodes['masters'].append(row.split('|')[1].strip())
                    elif 'standby' in row.split('|')[0]:
                        nodes['slaves'].append(row.split('|')[1].strip())
        return True, nodes['masters']
    except Exception as err:
        print("An Error occurred while getting repmgr cluster show ")
        return False, []


def main():

    pgpa = '192.168.168.90'
    pgpb = '192.168.255.90'

    pgpa_s = check_port(pgpa)
    pgpb_s = check_port(pgpb)

    server = DBWServer('0.0.0.0', 5559)
    server.close()

    while True:

        mstat, masters = get_masters()
        if mstat and len(masters) > 0:
            if len(masters) > 1:
                print("Multiple Masters!")
                send_mail(subject='PGPWATCH - Repmgr - Multiple Masters',
                          body='This is the {0}.<br>There are multiple masters in the cluster.<br>This situation should be fixed!'.format(socket.gethostname()))
                if check_port():
                    server.close()
                    print("Server Closed")
            else:
                if masters[0] == socket.gethostname():
                    print("I AM THE MASTER!")
                    if not check_port(pgpa) and not check_port(pgpb) and not check_port():
                        print("Everybody is down, and we are not up? Bringing the 5559 up.")
                        server.start()
                        body_text = """This is the {0}.<br> I am the current master, and all pgpool instances are down,
                        so the GSLB is probably routing traffic through me. It is best that you fix the pgpools as soon
                        as possible.<br>Also double check the the GSLB
                        is really routing traffic through me.""".format(socket.gethostname())
                        send_mail(subject='PGPWATCH - Repmgr - UP (This is bad)', body=body_text)

                    elif check_port() and (check_port(pgpa) or check_port(pgpb)):
                        print("One of the pgpools is up, so we are bringing ourself down.")
                        server.close()
                        body_text="""This is the {0}.<br>I am the current master, and I used to serve as the DB
                        instance. Yet one of the pgpools are back online. That's why I am closing port so that the GSLB
                        won't route traffic through me. It is still best that
                        you check on the system manually""".format(socket.gethostname())
                        send_mail(subject='PGPWATCH - Repmgr - Down (This is good)', body=body_text)


                else:
                    print("I am a slave :(")
                    if check_port():
                        print("I am serving yet I am a slave, this is wrong.")
                        server.close()
                        body_text="""This is the {0}.<br>I am a slave, yet somehow I was serving on port,
                        don't know how this happened (probably a master/slave switch occurred). I am closing port so
                        that the GSLB won't route traffic through my incase both pgpools are down.
                        Nothing to worry about, just a notice.""".format(socket.gethostname())
                        send_mail(subject='PGPWATCH - Repmgr - Slave Stepping Down (This is good)', body=body_text)
        else:
            print("Something went wrong getting the masters")
            body_text="""This is the {0}.<br>I failed getting the masters of the cluster.
            If you are not testing something, this isn't good.
            Please check the cluster.""".format(socket.gethostname())

        time.sleep(10)

if __name__ == '__main__':
    main()