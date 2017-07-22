#!/bin/bash
DIR=/home/roger/opt/tesseract_gif/
PATH=/home/roger/miniconda3/bin:/usr/local/bin:$PATH
echo $PATH

cd ${DIR}
. /home/roger/miniconda3/bin/activate scrapy
python make_apt.py
. /home/roger/miniconda3/bin/deactivate scrapy