#!/usr/bin/python

#############################################################################
# Classes related to the CyTrONE password management
#############################################################################

import getpass
import sys

# Used by the passlib-based implementation (default, RECOMMENDED)
from passlib.hash import pbkdf2_sha256

# Used by the built-in implementation (NOT recommended)
import hashlib
import random

class Password:

    # Use this field to control whether passlib is used or not
    USE_PASSLIB = True

    # Encode a given raw password
    # Return the encrypted password
    @classmethod
    def encode(cls, raw_password):
        if cls.USE_PASSLIB:
            # Use recommended Python native algorithm PBKDF2-HMAC-SHA256
            # Reference: https://passlib.readthedocs.io/en/stable/narr/quickstart.html
            enc_password = pbkdf2_sha256.hash(raw_password)
        else:
            # Use SHA-1 algorithm with salt
            algorithm = "sha1"
            raw_salt = str(random.random())
            salt = hashlib.sha1(raw_salt).hexdigest()
            hash_value = hashlib.sha1(salt + raw_password).hexdigest()
            enc_password = "{}${}${}".format(algorithm, salt, hash_value)

        return enc_password

    # Verify a given raw password against an encrypted one
    # Return true if passwords match
    @classmethod
    def verify(cls, raw_password, enc_password):
        if cls.USE_PASSLIB:
            return pbkdf2_sha256.verify(raw_password, enc_password)
        else:
            algorithm, salt, hash_value = enc_password.split('$', 2)
            #algorithm, hash_value = enc_password.split('$', 1)
            if algorithm == "sha1":
                hex_digest = hashlib.sha1(salt + raw_password).hexdigest()
                return hash_value == hex_digest
            else:
                print("* ERROR: password.py: Unsupported hashing algorithm: {}".format(algorithm))
                return False

def main():
    
    # Set to True for a basic test, or to False in order to enable the password encoding functionality
    TEST_MODE = False

    if TEST_MODE:
        raw_password = "sample_passwd"
        Password.ENABLE_PASSLIB = False
        print("* TEST: Settings: Use passlib library => {}".format(Password.USE_PASSLIB))
        enc_password = Password.encode(raw_password)
        print("* TEST: Encode password '{}' =>  '{}'".format(raw_password, enc_password))

        result = Password.verify(raw_password, enc_password)
        print("* TEST: Verify password '{}' vs. '{}' => {}".format(raw_password, enc_password, result))
    else:
        print("* INFO: Password manager for CyTrONE: Please follow the instructions below.")
        raw_password = getpass.getpass("* INFO: Enter the password to be encoded: ")
        if not raw_password:
            print("* ERROR: Empty passwords are not considered valid, please retry.")
            sys.exit(1)
        raw_password2 = getpass.getpass("* INFO: Retype the password to be encoded: ")
        if raw_password==raw_password2:
            enc_password = Password.encode(raw_password)
            print("* INFO: Copy the string displayed below into the password database:")
            print(enc_password)
        else:
            print("* ERROR: Passwords do not match, please retry.")


#############################################################################
# Run
if __name__ == "__main__":
    main()
