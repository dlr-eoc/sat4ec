FROM registry.eodc.eu/jrc-gfm/dlr/gzs-python-base:latest

ENV PYTHONUNBUFFERED=1
WORKDIR /source

# mountpoint /scratch
RUN mkdir /scratch && \
    chmod og+rwx /scratch

# dependencies and installation
RUN apt-get -y update && \
    apt-get -y upgrade

# Python dependencies that require compilation
RUN pip install --no-cache-dir jsonformatter requests adtk numpy pandas matplotlib sentinelhub

# Copy code files
COPY source /source

ENTRYPOINT ["/usr/local/bin/python3", "-u", "-m", "main"]
