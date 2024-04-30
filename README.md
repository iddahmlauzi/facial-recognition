THIS PROGRAM WAS DEVELOPED FOR MY HIT400 PROJECT, IT USES: 
PYTHON
OPENCV
face_recognition module 
AES-128 IMPLEMENTATION FOR MORE SECURITY  

# Facial Recognition System

Welcome to the Facial Recognition Based Access Control System project! This repository contains a robust and efficient solution for facial recognition tasks, leveraging state-of-the-art machine learning algorithms and techniques.

## Features

- **Real-time facial recognition**: Identify and verify individuals in real-time with high accuracy.
- **Facial analysis**: Detect various attributes from a user to determine weather to grant or deny access to a user.
- **aes encrytion**: great secuirty features to ensure safety of program 
- **Easy integration**: Simple API for seamless integration with existing systems.

## Getting Started

To get started with this project, clone the repository and install the required dependencies:

bash
git clone https://github.com/lionel700/facial-recognition.git
cd facial-recognition
pip install -r requirements.txt


## Usage

Here's a quick example of how to use the facial recognition system:

python
from facial_recognition import Recognizer
recognizer = Recognizer()
recognizer.load_model('path/to/model')
recognizer.recognize('path/to/image.jpg')


## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - [@your_twitter](^3^) - email@example.com

Project Link: [https://github.com/lionel700/facial-recognition](^3^)

## Acknowledgements

- [OpenFace](^1^)
- [FaceNet](^2^)
- [DeepFace](^1^)
- [TensorFlow](https://www.tensorflow.org/)
- [PyTorch](https://pytorch.org/)

Security overview:

- The random salt ensures the same image data will map to different ciphertexts.

- The HMAC ensures the integrity of both the entire ciphertext and the PKBDF2
  salt; encrypt-then-mac prevents attacks like Padding Oracle.

- Bytes from keys, iv and salt are not reused in different algorithms.

- PBKDF2 key stretching allows for relatively weak passwords to be used as AES
  keys and be moderately resistant to brute-force, but sacrificing performance.
