
import os
import hashlib
import base64
from binascii import a2b_base64
from OpenSSL import crypto

LUHN_ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")


def generate_check_character(input):
    input = [LUHN_ALPHABET.index(x) for x in reversed(input)]
    total = (sum(input[::2]) + sum(sum(divmod(i * 2, 32)) for i in input[1::2]))
    idx = (32 - (total % 32)) % 32
    return LUHN_ALPHABET[idx]


def get_fingerprint(pem):
    key = a2b_base64(''.join(pem.splitlines()[1:-1]))
    return hashlib.sha256(key).digest()


def _split(data, step):
    return [data[x:x+step] for x in range(0, len(data), step)]


def get_device_id(pem):
    fingerprint = get_fingerprint(pem)
    b32 = base64.b32encode(fingerprint).rstrip("=")

    chunks = [x + generate_check_character(x) for x in _split(b32, 13)]
    return "-".join(_split("".join(chunks), 7))


def get_fingerprint_from_device_id(device_id):
    device_id = device_id.replace("-", "")
    b32 = "".join(x[:13] for x in  _split(device_id, 14)) + "===="
    return base64.b32decode(b32)


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
