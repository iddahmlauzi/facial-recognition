THIS PROGRAM WAS DEVELOPED FOR MY HIT400 PROJECT, IT USES: 
PYTHON
OPENCV
face_recognition module 
AES-128 IMPLEMENTATION FOR MORE SECURITY  


Security overview:

- The random salt ensures the same image data will map to different ciphertexts.

- The HMAC ensures the integrity of both the entire ciphertext and the PKBDF2
  salt; encrypt-then-mac prevents attacks like Padding Oracle.

- Bytes from keys, iv and salt are not reused in different algorithms.

- PBKDF2 key stretching allows for relatively weak passwords to be used as AES
  keys and be moderately resistant to brute-force, but sacrificing performance.
