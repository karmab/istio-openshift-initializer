FROM karmab/client-python-openshift
MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>

ADD controller.py /tmp

ENTRYPOINT  ["python", "-u", "/tmp/controller.py"]
