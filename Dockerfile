FROM ubuntu:22.04

# Install base packages
RUN apt-get update
ENV TZ=Europe/London
RUN DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends  -y tzdata
RUN apt-get install -y gnupg libxslt-dev libxml2-dev libpam-dev libedit-dev  wget bzip2 ca-certificates curl git libarchive13 gcc python3-psycopg2 sudo nano

# Install a newer version of postgresql (16) as the default with jammy is 14
RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ jammy-pgdg main' > /etc/apt/sources.list.d/pgdg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get update && apt-get install -y postgresql-16

# Make the app directory
RUN mkdir /app && cd /app
WORKDIR /app

# Copy the currently checked out code into the container
RUN mkdir /app/seqbox
COPY . /app/seqbox

# create seqbox user
ENV SEQBOX_USER=phil
RUN useradd -ms /bin/bash $SEQBOX_USER
RUN usermod -aG sudo $SEQBOX_USER
RUN echo "$SEQBOX_USER:you-will-never-guess" | chpasswd
RUN echo "${SEQBOX_USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
RUN chown -R $SEQBOX_USER:$SEQBOX_USER /app
USER $SEQBOX_USER

# Download and install miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b && \ 
    rm Miniconda3-latest-Linux-x86_64.sh 
ENV PATH="/home/phil/miniconda3/bin:$PATH"
# Install mamba
RUN conda install -c conda-forge mamba --yes

# Install the conda environment and activate it
RUN cd /app/seqbox &&  mamba env create --name seqbox --file seqbox_conda_env.yaml
RUN conda init
RUN echo "conda activate seqbox" >> /home/phil/.bashrc
SHELL ["/bin/bash", "--login", "-c", "bash"]

# Setup the database
USER root
ENV PYTHONPATH=/app/seqbox/src:$PYTHONPATH
ENV DATABASE_URL="postgresql:///test_seqbox?host=/var/run/postgresql"
RUN sudo service postgresql start && \
    sudo -u postgres createuser root && \
    sudo -u postgres createuser $SEQBOX_USER && \
    sudo -u postgres createuser cat && \
    sudo -u postgres createdb test_seqbox && \
    sudo -u postgres psql -c "ALTER SCHEMA public OWNER TO postgres;" && \
    sudo -u postgres psql -c "grant all privileges on database test_seqbox to $SEQBOX_USER;" && \
    sudo -u postgres psql -c "ALTER USER $SEQBOX_USER WITH PASSWORD 'you-will-never-guess';" && \
    sudo service postgresql restart

RUN sudo -u postgres psql -c "grant all privileges on database test_seqbox to $SEQBOX_USER;" && \
    sudo -u postgres psql -c "GRANT USAGE ON SCHEMA public TO $SEQBOX_USER;" && \
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $SEQBOX_USER;" && \
    sudo -u postgres psql -c "GRANT CREATE ON SCHEMA public TO $SEQBOX_USER;" && \
    sudo service postgresql restart
CMD ["service" "postgresql" "start"]

USER $SEQBOX_USER
ENV DATABASE_URL="postgresql:///test_seqbox?host=/var/run/postgresql"
ENV SECRET_KEY="you-will-never-guess"
ENV FLASK_APP=/app/seqbox/src/main.py

# Load a database dump for testing
#RUN sudo -u postgres pg_restore -d test_seqbox /data/seqbox.tar && \
#    sudo -u postgres psql -d test_seqbox -c "DELETE FROM alembic_version;" && \
#    sudo -u postgres psql -d test_seqbox -c "INSERT INTO alembic_version (version_num) VALUES ('c48cdec0b1db');" 
    