FROM karmab/client-python-openshift
MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>

RUN useradd jhendrix
USER jhendrix
ADD basetemplate.j2 $HOME
ADD initializer.py $HOME

ENTRYPOINT  ["python", "-u", "initializer.py"]
