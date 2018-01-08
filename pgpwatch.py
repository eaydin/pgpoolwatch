#!/usr/bin/python
import subprocess
import argparse
import time
import ConfigParser
import io
import SocketServer
import socket
from operator import xor

def check_port(address='localhost', port=5559):
    s = socket.socket()
    try:
        s.connect((address, port))
        print("Socket is open")
        del s
        return True
    except socket.error as err:
        print("Socket is closed?: %s" % str(err))
        del s
        return False


class PGPWRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        pass

class PGPWServer(SocketServer.TCPServer):
    def __init__(self, host='0.0.0.0', port=5559, handler_class=PGPWRequestHandler):
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


def send_mail(path='/root/pgpoolwatch/sendmail.py', arguments='/root/pgpoolwatch/args.txt', subject="PGPWATCH", failed_node='none', new_master='none', body=None):
    p = subprocess.Popen(["/usr/bin/python", path, "@{0}".format(arguments), "--subject={0}".format(subject), "--failed-node={0}".format(failed_node),
                          "--new-master={0}".format(new_master), "--body={0}".format(body)])
    p.communicate()[0]


def runpoolstatus(success=False, poolstatus_path='/root/pgpoolwatch/poolstatus.py', poolstatus_user='postgres',
                  sendmail_status=False, sendmail_path='/root/pgpoolwatch/sendmail.py',
                  sendmail_settings_path='/root/pgpoolwatch/args.txt'):

    try:
        output = subprocess.check_output(["/usr/sbin/runuser", "-l", poolstatus_user, "-c", "'{0}'".format(poolstatus_path)])

        if success:
            if sendmail_status:
                p = subprocess.Popen(["/usr/bin/python", sendmail_path, "@{0}".format(sendmail_settings_path),
                        "--subject=PGPWATCH - Status OK", "--failed-node=none", "--new-master=none",
                        "--body=This is the {0}. The pgpwatch script returned fine.<br><br>{1}".format(socket.gethostname(),output.replace("\n", "<br>"))], stdout=subprocess.PIPE)
                p.communicate()[0]
        return True

    except subprocess.CalledProcessError as outputexc:
        print("Error Code: {0}".format(outputexc.returncode))
        output_text = outputexc.output
        print("Output: {0}".format(output_text))

        if sendmail_status:
            p = subprocess.Popen(["/usr/bin/python", sendmail_path, "@{0}".format(sendmail_settings_path),
                                  "--subject=PGPWATCH - Error", "--failed-node=none", "--new-master=none",
                                  "--body=This is the {0}.<br>The pgpwatch script <b>failed!</b><br><br>{1}".format(socket.gethostname(), output_text.replace("\n", "<br>"))], stdout=subprocess.PIPE)
            p.communicate()[0]

        return False

if __name__ == '__main__':

    description="""Checks PGPOOL Status via pgpwatch script, by Veriteknik - tech@veritech.net"""

    parser = argparse.ArgumentParser(prog='pgpwatch.py', formatter_class=argparse.RawDescriptionHelpFormatter,
                                    fromfile_prefix_chars="@", description=description)

    parser.add_argument("--mail-on-success", help="Mails even on success.", action='store_true', default=False)
    parser.add_argument("--run-once", help="Run the script once and exit", action="store_true", default=False)
    parser.add_argument("--check-period", help="Check status every x seconds")
    parser.add_argument("--success-period", help="Send successful checks every x checks (not seconds!)")
    parser.add_argument("--config", help="Path to the config file")

    args = parser.parse_args()

    if args.config:
        config_file_path = args.config
    else:
        config_file_path = "/root/pgpoolwatch/config.ini"

    # Load the configuration file
    with open(config_file_path) as f:
        sample_config = f.read()
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(io.BytesIO(sample_config))

    # Get check period
    # First if argument specified, else read from config
    if args.check_period:
        check_period = args.check_period
    else:
        check_period = config.getfloat('pgp', 'check_period')
    print("Check Period:", check_period)

    # Get Success Period
    if args.success_period:
        success_period = args.success_period
    else:
        success_period = config.getfloat('pgp', 'success_period')
    print("Success Period:", success_period)

    mail_on_success = config.getboolean('pgp', 'mail_on_success')
    if args.mail_on_success:
        mail_on_success = args.mail_on_success
    print("Mail on Success:", mail_on_success)

    # Initiate default values for general settings
    sendmail_status = False
    sendmail_path = '/root/pgpoolwatch/sendmail.py'
    sendmail_settings_path = '/root/pgpoolwatch/args.txt'
    poolstatus_path = '/var/lib/pgsql/poolstatus.py'
    poolstatus_user = 'postgres'

    # Read General Settings
    sendmail_status = config.getboolean('general', 'sendmail')
    sendmail_path = config.get('general', 'sendmail_path')
    sendmail_settings_path = config.get('general', 'sendmail_settings_path')
    poolstatus_path = config.get('general', 'poolstatus_path')
    poolstatus_user = config.get('general', 'poolstatus_user')

    open_port = 5559
    # Read Port Settings
    open_port = config.getint('pgp', 'open_port')

    if not args.run_once:

        # run the port things
        pgp_status = runpoolstatus(False, poolstatus_path=poolstatus_path, poolstatus_user=poolstatus_user,
                                   sendmail_status=sendmail_status, sendmail_path=sendmail_path,
                                   sendmail_settings_path=sendmail_settings_path)
        if pgp_status:
            server = PGPWServer('0.0.0.0', open_port)
        server_status = check_port(port=open_port)

        m = 0 # the first instance
        n = 0 # the usual counter
        while True:
            if n == success_period or m == 0:
                if mail_on_success:
                    pgp_status = runpoolstatus(True, poolstatus_path=poolstatus_path, poolstatus_user=poolstatus_user,
                                   sendmail_status=sendmail_status, sendmail_path=sendmail_path,
                                   sendmail_settings_path=sendmail_settings_path)
                n = 0
                m = 1
            else:
                pgp_status = runpoolstatus(False, poolstatus_path=poolstatus_path, poolstatus_user=poolstatus_user,
                                   sendmail_status=sendmail_status, sendmail_path=sendmail_path,
                                   sendmail_settings_path=sendmail_settings_path)

            server_status = check_port(port=open_port)

            if not xor(pgp_status, server_status):
                # this means the state hasn't changed
                # if it was up, it is still up
                # if it was down, it is still down
                # so we don't inform any cylons
                print("No State Change")
                print("pgp_status", pgp_status)
                print("server_status", server_status)
                print("xor", xor(pgp_status, server_status))
                pass
            else:
                # something smells fishy
                # there has been a state change
                # let's detect it
                print("State change detected...")
                if pgp_status:
                    # pgp is running, probably it just revived
                    if not server_status:
                        # let's check if the port is really closed
                        if not check_port(port=open_port):
                            # let's open it up
                            try:
                                server.start()
                            except Exception as err:
                                print("Error while server.start: {0}".format(str(err)))
                                print("Recreating the server instance")
                                server = PGPWServer('0.0.0.0', open_port)
                            if check_port(port=open_port):
                                print("Port {0} Startup success".format(open_port))
                                send_mail(path=sendmail_path, arguments=sendmail_settings_path,
                                          subject="PGPWATCH - Status Change - PGP Up",
                                          body="This is the {0}.<br>The PGPServer was down, now switching to <b>up</b> state. <br>Opening port for GSLB.".format(socket.gethostname()))
                                server_status = True
                            else:
                                print("Port {0} Startup failed?".format(open_port))
                        else:
                            # the port is already open
                            # yet the server_status thinks it is closed
                            print("Port {0} is open but server_status is False, this is weird".format(open_port))
                            server_status = True

                    else:
                        # this means that pgp_status is true, server_status is true, yet xor returned false, wtf?
                        print("A WTF situation, this should never happen")
                        print("pgp_status", pgp_status)
                        print("server_status", server_status)
                        print("xor", xor(pgp_status, server_status))
                else:
                    # pgp is not running, probably just died
                    if server_status:
                        # let's check if the port is really open
                        if check_port(port=open_port):
                            # let's close it up
                            try:
                                server.close()
                            except Exception as err:
                                print("Error while server.stop: {0}".format(str(err)))
                                pass
                            if not check_port(port=open_port):
                                print("Port {0} Closeup success".format(open_port))
                                send_mail(path=sendmail_path, arguments=sendmail_settings_path,
                                          subject="PGPWATCH - Status Change - PGP Down",
                                          body="This is the {0}.<br>The PGPServer was up, now it <b>failed</b>. <br>Closing port {1} for GSLB.".format(socket.gethostname(), open_port))
                                server_status = False
                            else:
                                print("Port {0} Closeup failed?".format(open_port))
                        else:
                            # the port is already closed
                            # yet the server_status thinks it is open
                            print("Port is closed but server_status if True, this is weird")
                            server_status = False
                    else:
                        # This means that pgp_status is false, and server_status is false, yet xor returned false, wtf?
                        print("Another WTF situation, this should never happen")
                        print("pgp_status", pgp_status)
                        print("server_status", server_status)
                        print("xor", xor(pgp_status, server_status))
            n += 1
            time.sleep(check_period)
    else:
        runpoolstatus(mail_on_success, poolstatus_path=poolstatus_path, poolstatus_user=poolstatus_user,
                      sendmail_status=sendmail_status, sendmail_path=sendmail_path,
                      sendmail_settings_path=sendmail_settings_path)