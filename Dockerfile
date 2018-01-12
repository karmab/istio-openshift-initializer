FROM karmab/client-python-openshift
MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>

ADD initializer.py /tmp
ADD basetemplate.j2 /tmp

ENTRYPOINT  ["python", "-u", "/tmp/initializer.py"]
