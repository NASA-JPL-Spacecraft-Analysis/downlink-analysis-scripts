FROM python:3.11

# pip commands below should reflect requirements.txt
# use the direct RUN pip install library_name,etcetc instead of requirements.txt because docker is rebuilding the image
# each time instead of using cached layers for some reason...bleh
RUN pip install xmltodict==0.13.0
RUN pip install click==8.1.7
RUN pip install bs4==0.0.2

RUN pip install m20-operational-cloud-store==7.7.1 -i https://cae-artifactory.jpl.nasa.gov/artifactory/api/pypi/pypi-develop-virtual/simple
RUN pip install m20-eas-dplib -i https://cae-artifactory.jpl.nasa.gov/artifactory/api/pypi/pypi-develop-virtual/simple
RUN pip install jpl_time -i https://cae-artifactory.jpl.nasa.gov/artifactory/api/pypi/pypi-develop-virtual/simple

RUN pip install lxml==5.1.0

#RUN pip install -r /transpire_dps/requirements.txt

# do not need to copy, these will get mounted in with 'make run'
#COPY . /transpire_dps/

WORKDIR /transpire_dps

# container does not stay up for whatever reason even with docker run -d so we'll just tail dev null
ENTRYPOINT ["tail"]
CMD ["-f","/dev/null"]