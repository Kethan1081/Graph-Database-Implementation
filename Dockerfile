# Base image: ubuntu:22.04
FROM ubuntu:22.04

# ARGs
# https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG TARGETPLATFORM=linux/amd64,linux/arm64
ARG DEBIAN_FRONTEND=noninteractive

# neo4j 5.5.0 installation and some cleanup
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common && \
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - && \
    echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list && \
    add-apt-repository universe && \
    apt-get update && \
    apt-get install -y nano unzip neo4j=1:5.5.0 python3-pip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# TODO: Complete the Dockerfile
#neo4j password change to project2phase1
RUN bin/neo4j-admin dbms set-initial-password project2phase1

#Neo4j Conf and security changes
ENV NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
RUN sed -i 's/#* *server.default_listen_address=.*/server.default_listen_address=0.0.0.0/g' /etc/neo4j/neo4j.conf
RUN echo "dbms.security.procedures.unrestricted=gds.*" >> /etc/neo4j/neo4j.conf
RUN echo "dbms.security.procedures.allowlist=gds.*" >> /etc/neo4j/neo4j.conf

RUN apt-get update && apt-get install -y git
RUN apt-get install -y vim

#clone repo and file
ENV GITHUB_TOKEN=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
RUN git clone https://kethan1081asu:${GITHUB_TOKEN}@github.com/CSE511-SPRING-2023/kgaddam4-project-2.git
RUN wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet

#move files
RUN mkdir cse511
RUN cp -R /kgaddam4-project-2/* ./cse511
RUN cp -R /yellow_tripdata_2022-03.parquet ./cse511

#Inatalling Packages
RUN pip3 install pyarrow
RUN pip3 install pandas
RUN pip3 install requests
RUN pip3 install neo4j

#setting up GDS stuff
RUN apt-get update && apt-get install -y unzip
RUN wget -P /var/lib/neo4j/plugins https://graphdatascience.ninja/neo4j-graph-data-science-2.3.1.zip 
RUN unzip /var/lib/neo4j/plugins/neo4j-graph-data-science-2.3.1.zip -d /var/lib/neo4j/plugins

WORKDIR /cse511

# Run the data loader script
RUN chmod +x /cse511/data_loader.py && \
    neo4j start && \
    python3 data_loader.py && \
    neo4j stop

# Expose neo4j ports
EXPOSE 7474 7687

# Start neo4j service and show the logs on container run
CMD ["/bin/bash", "-c", "neo4j start && tail -f /dev/null"]