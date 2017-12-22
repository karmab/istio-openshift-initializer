FROM karmab/client-python-openshift
MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>

ADD initializer.py /tmp

ENTRYPOINT  ["python", "-u", "/tmp/initializer.py"]
