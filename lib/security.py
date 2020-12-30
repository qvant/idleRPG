from cryptography.fernet import Fernet
import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .consts import CONFIG_PARAM_SECRET_CONST


def is_password_encrypted(password):
    return password[-2:] == '=='


def set_up_encryption(server_name, port):
    salt = bytes(port)
    # TODO: rewrite to AES
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                     length=32,
                     salt=salt,
                     iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive((server_name + CONFIG_PARAM_SECRET_CONST).encode('UTF-8')))
    f = Fernet(key)
    return f


def decrypt_password(password, server_name, port):
    f = set_up_encryption(server_name, port)
    password = f.decrypt(password.encode('UTF-8'))
    return password.decode('UTF-8')


def encrypt_password(password, server_name, port):
    f = set_up_encryption(server_name, port)
    password = f.encrypt(password.encode('UTF-8'))
    return password.decode('UTF-8')
