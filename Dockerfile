FROM ubuntu:20.04

# Update the package list and install any necessary packages
RUN apt-get update
ENV TZ=America/New_York
RUN DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends  -y tzdata
RUN apt-get install -y libxslt-dev libxml2-dev libpam-dev libedit-dev postgresql wget bzip2 ca-certificates curl git libarchive13 gcc python3-psycopg2 sudo

# Download and install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b && \ 
    rm Miniconda3-latest-Linux-x86_64.sh 


# Set conda path
ENV PATH="/root/miniconda3/bin:$PATH"

RUN mkdir /app && cd /app
# Set working directory
WORKDIR /app

# Install Python packages
RUN conda install -c conda-forge mamba --yes

RUN git clone  https://github.com/andrewjpage/seqbox.git
RUN cd seqbox
RUN cd /app/seqbox && git checkout ajp_unit_tests

RUN cd /app/seqbox &&  mamba env create --name seqbox --file seqbox_conda_env.yaml
RUN echo "conda activate seqbox" >> /root/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

ENV PYTHONPATH=/app/seqbox/src:$PYTHONPATH
ENV DATABASE_URL="postgresql:///test_seqbox?host=/var/run/postgresql/"
RUN service postgresql start

RUN sudo -u postgres createuser root
RUN sudo -u postgres createdb test_seqbox
RUN sudo -u postgres psql -c "grant all privileges on database test_seqbox to root;"

