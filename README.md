# START

## Installation

### GCS

To install on the GCS, execute `./install-gcs` and ignore all other
instructions.

### UP board

To install on the UP board, execute `./install-upboard` and ignore all other
instructions.

### Debgrind

To install Debgrind on Ubuntu:

```
$ sudo apt update
$ sudo apt install make automake autoconf g++ libc6-dbg
$ cd debgrind
$ sudo mkdir /opt/debgrind
$ sudo chown $USER /opt/debgrind
$ ./autogen.sh
$ ./configure --prefix=/opt/debgrind
$ make install
```

### Python 2.7

To install the rest of the START stack for Python 2.7, you will first need to
create a virtual environment via `pipenv`. To avoid introducing conflicts with
Python 3, you should create a separate environment directory for Python 2.7 and
Python 3, as shown below:

```
$ mkdir envs
$ mkdir envs/py3
$ mkdir envs/py2
```

Once the separate environment directories have been created, enter the
directory for Python 2 and create a new pipenv:

```
$ cd envs/py2
$ pipenv --python 2.7
```

To enter the newly created environment, simply execute the following:

```
$ cd envs/py2
$ pipenv shell
(py2) $ echo "now you are inside the pipenv"
```

Once inside the environment, the START stack can be quickly installed
using the install script at the root of this directory:

```
(py2) $ ./install
```

To exit the virtual environment:

```
(py2) $ exit
$ echo "now you are no longer inside the pipenv"
```

## Usage

To learn more about the command-line interface for START, `start-cli`, see:
https://github.com/ChrisTimperley/start-cli
