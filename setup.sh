#! /usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
virtualenv $DIR
pushd $DIR
source ./bin/activate
mkdir third_party
cd third_party
git clone https://github.com/burnash/gspread.git gspread
cd gspread
python setup.py install
cd ..
git clone git://github.com/hyperic/sigar.git sigar
cd sigar/bindings/python
python setup.py install
cd ..
popd
pip install oauth2client
deactivate
