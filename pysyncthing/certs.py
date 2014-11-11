
import os
from OpenSSL import crypto


def ensure_certs():
    if not os.path.exists("client.key"):
        print "Generating private key"
        private_key = crypto.PKey()
        private_key.generate_key(crypto.TYPE_RSA, 3096)

        print "Generating cert"
        cert = crypto.X509()
        subj = cert.get_subject()
        subj.C = "US"
        subj.ST = "Minnesota"
        subj.L = "Minnetonka"
        subj.O = "my company"
        subj.OU = "my organization"
        subj.CN = "syncthing"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_issuer(subj)
        cert.set_pubkey(private_key)
        cert.sign(private_key, 'sha1')

        with open("client.crt", "w") as fp:
            fp.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

        with open("client.key", "w") as fp:
            fp.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, private_key))
