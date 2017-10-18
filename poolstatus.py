#!/usr/bin/python
import subprocess
import argparse
import time
import ConfigParser
import io
import SocketServer
import threading
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



def runpgpwatch(success=False):

    try:
        output = subprocess.check_output(["/usr/sbin/runuser", "-l", "postgres", "-c", "'/var/lib/pgsql/pgpoolwatch/pgpwatch.py'"])
        # git durum iyi diye bir yere yaz
        if success:
            p = subprocess.Popen(["/usr/bin/python", "/root/vt/sendmail.py", "@/root/vt/args.txt",
                              "--subject=PGPWATCH - Status OK", "--failed-node=none", "--new-master=none", "--body=The pgpwatch script returned fine.<br><br>{0}".format(output.replace("\n", "<br>"))], stdout=subprocess.PIPE)
            p.communicate()[0]

    except subprocess.CalledProcessError as outputexc:
        print("Error Code: {0}".format(outputexc.returncode))
        output_text = outputexc.output
        print("Output: {0}".format(output_text))

        p = subprocess.Popen(["/usr/bin/python", "/root/vt/sendmail.py", "@/root/vt/args.txt",
                              "--subject=PGPWATCH - Error", "--failed-node=none", "--new-master=none", "--body=The pgpwatch script <b>failed!</b><br><br>{0}".format(output_text.replace("\n", "<br>"))], stdout=subprocess.PIPE)
        p.communicate()[0]

        # git durum kotu diye bir yere yaz


if __name__ == '__main__':

    description="""Checks PGPOOL Status via pgpwatch script, by Veriteknik - tech@veritech.net"""

    parser = argparse.ArgumentParser(prog='poolstatus.py', formatter_class=argparse.RawDescriptionHelpFormatter,
                                    fromfile_prefix_chars="@", description=description)

    parser.add_argument("--mail-on-success", help="Mails even on success.", action='store_true', default=False)
    parser.add_argument("--run-once", help="Run the script once and exit", action="store_true", default=False)
    parser.add_argument("--check-period", help="Check status every x seconds")
    parser.add_argument("--success-period", help="Send successfull checks every x checks (not seconds!)")
    parser.add_argument("--config", help="Path to the config file")

    args = parser.parse_args()

    if args.config:
        config_file_path = args.config
    else:
        config_file_path = "/root/vt/config.ini"

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

    if not args.run_once:

        # run the port things
        server = PGPWServer('0.0.0.0', 5559)

        m = 0
        n = 0
        while True:
            if n == success_period or m == 0:
                if mail_on_success:
                    runpgpwatch(True)
                n = 0
                m = 1
            else:
                runpgpwatch(False)
            n += 1
            time.sleep(check_period)
            if check_port():
                print "Let's close the port"
                server.close()
            else:
                print "Let's open the port"
                server.start()
    else:
        if mail_on_success:
            runpgpwatch(True)
        else:
            runpgpwatch(False)
