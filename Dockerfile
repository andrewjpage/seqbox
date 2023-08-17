FROM ubuntu:20.04

# Install base packages
RUN apt-get update
ENV TZ=America/New_York
RUN DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends  -y tzdata
RUN apt-get install -y libxslt-dev libxml2-dev libpam-dev libedit-dev postgresql wget bzip2 ca-certificates curl git libarchive13 gcc python3-psycopg2 sudo nano

# Download and install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b && \ 
    rm Miniconda3-latest-Linux-x86_64.sh 
ENV PATH="/root/miniconda3/bin:$PATH"
# Install mamba
RUN conda install -c conda-forge mamba --yes

RUN mkdir /app && cd /app
WORKDIR /app

# Copy the currently checked out code into the container
RUN mkdir /app/seqbox
COPY . /app/seqbox

# Install the conda environment and activate it
RUN cd /app/seqbox &&  mamba env create --name seqbox --file seqbox_conda_env.yaml
RUN conda init
RUN echo "conda activate seqbox" >> /root/.bashrc
SHELL ["/bin/bash", "--login", "-c", "bash"]

# Setup the database
ENV PYTHONPATH=/app/seqbox/src:$PYTHONPATH
ENV DATABASE_URL="postgresql:///test_seqbox?host=/var/run/postgresql/"
RUN service postgresql start && sudo -u postgres createuser root && sudo -u postgres createdb test_seqbox && sudo -u postgres psql -c "grant all privileges on database test_seqbox to root;"
