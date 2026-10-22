ARG DOCKER_IMAGE_NAME
FROM $DOCKER_IMAGE_NAME

# CentOS 8 is archived; its retired mirrorlist no longer resolves.
RUN if [ -f /etc/centos-release ] && grep -q 'release 8' /etc/centos-release; then \
      sed -i -e 's|^mirrorlist=|#mirrorlist=|' \
        -e 's|^#baseurl=http://mirror.centos.org/$contentdir/$releasever|baseurl=https://vault.centos.org/8.3.2011|' \
        /etc/yum.repos.d/CentOS-Linux-*.repo; \
    fi

# Archived CentOS CA packages still contain incident roots.
COPY tests/distrust_emsign.py /tmp/distrust_emsign.py
RUN if [ -x /usr/libexec/platform-python ] && [ -f /etc/centos-release ]; then \
      /usr/libexec/platform-python /tmp/distrust_emsign.py; \
    fi && rm /tmp/distrust_emsign.py

# Add your specific Ansible SSH public key. This only works when run via
# kitchen, when run with the following options in your .kitchen.yml file:
#
#    driver_config:
#      build_options:
#        build-arg: SSH_KEY=<%= File.read('.kitchen/docker_id_rsa.pub') %>
#
ARG SSH_KEY
RUN echo "$SSH_KEY" >> /home/kitchen/.ssh/authorized_keys
