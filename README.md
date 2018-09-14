# Fabulinkus ![CI status](https://img.shields.io/badge/build-passing-brightgreen.svg)

Fabulinkus project, aims to help people with specific disabilities, allowing them to speak using their face movements only. It augments the experience with auto word complete and text to speech features. Currently, only Turkish language is supported.

## Installation

### Requirements
* Linux
* Python 2.7
* dlib

To install all required python libraries, run this command on your terminal (preferably within your virtual environment):
`$ pip install -r requirements.txt`

## Usage

Make sure other files are on the same level with fabulinkus, don't forget to include the trained facial shape predictor from [here](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2).

`$ (venv) python2.7 fabulinkus.py`

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Authors
* [mehmetalpsumer](https://github.com/mehmetalpsumer) - Initial work
* [gokturktopar](https://github.com/gokturktopar) - Initial work

You can also see the list of [contributors](https://github.com/mehmetalpsumer/fabulinkus/graphs/contributors) who participated in this project.
## License
[GPL3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)
