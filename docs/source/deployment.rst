Deploying the Bioregistry
=========================
The Bioregistry web application is a part of the ``bioregistry`` Python package which is updated,
packaged, and pushed weekly to the `Python Package Index (PyPI) <https://pypi.org/project/bioregistry/>`_.
A new deploy can also be triggered by admins using the
`update workflow <https://github.com/biopragmatics/bioregistry/actions/workflows/update.yml>`_ on GitHub.
It can be installed and run interactively in the command line with the following commands:

.. code-block:: shell

    python -m pip install --upgrade gunicorn bioregistry[web]
    python -m bioregistry web \
        --with-gunicorn --workers 4 \
        --port 8766 \
        --host "0.0.0.0" \
        --base-url https://example.com

.. note::

    The Bioregistry uses port 8766 by default. Using ``0.0.0.0`` makes sure that this
    works on a variety of systems, including docker, Mac, and Linux. The ``--base-url``
    should correspond to the location through which the service is accessed. In this
    example, https://example.com is used as the base.

The Bioregistry is also containerized and pushed during the weekly build to
`Docker Hub <https://hub.docker.com/r/biopragmatics/bioregistry>`_.
You can pull then run the latest in the command line with the following commands:

.. code-block:: shell

    docker pull biopragmatics/bioregistry:latest
    docker run --detach -i --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest

Note that ``-p`` says what ports to remap. Note that the base Bioregistry image uses ``8766``
as its port, so this is simply exposed via the same port.

The following shell script can be used to automatically update the containerized deployment:

.. code-block:: shell

    # restart.sh
    #!/bin/bash

    # Store the container's hash
    BIOREGISTRY_CONTAINER_ID=$(docker ps --filter "name=bioregistry" -aq)

    # Stop and remove the old container, taking advantage of the fact that it's named specifically
    if [ -n "BIOREGISTRY_CONTAINER_ID" ]; then
      docker stop $BIOREGISTRY_CONTAINER_ID
      docker rm $BIOREGISTRY_CONTAINER_ID
    fi

    # Pull the latest
    docker pull biopragmatics/bioregistry:latest

    # Run the start script
    docker run --detach -i --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest

Deploying a custom Bioregistry
==============================
This is a tutorial on how to run a custom instance of the Bioregistry that contains custom content.
If you don't need custom content, see the instructions above for deploying a vanilla copy of the Bioregistry.

Creating custom content
-----------------------
In the following example, a slimmed down registry is generated from the base
Bioregistry. It's also possible to add additional :class:`bioregistry.Resource`
instances from arbitrary sources.

.. code-block:: python

    import bioregistry
    from pathlib import Path

    slim_prefixes = {"chebi", "go", "ncbitaxonomy"}
    slim_registry: dict[str, bioregistry.Resource] = {
        resource.prefix: resource
        for resource in bioregistry.resources()
        if resource.prefix in slim_prefixes
    }
    bioregistry.write_registry(
        slim_registry,
        path=Path.home().joinpath("Desktop", "registry.json"),
    )

This script creates a new file that will be used when running the Bioregistry
with the ``--registry`` flag from the command line.

.. note:: The same is possible for collections, contexts, and even the metaregistry.

Custom configuration and branding
---------------------------------
The Bioregistry can be configured in several ways, including replacing various text in
the case of custom deployments. Please use good judgement with the following features to
best represent the Bioregistry project. The following table includes the keys that you
can put in a configuration JSON file, an explanation of the keys, and suggestions on
how to replace them.

+--------------------------------------+----------------------------------------------------------+
| Key                                  | Description                                              |
+======================================+==========================================================+
| ``METAREGISTRY_TITLE``               | The title on the home page, defaults to "Bioregistry".   |
+--------------------------------------+----------------------------------------------------------+
| ``METAREGISTRY_HEADER``              | The header text on the home page. Can include arbitrary  |
|                                      | HTML. Suggestions: use a ``<p class="lead">``.           |
+--------------------------------------+----------------------------------------------------------+
| ``METAREGISTRY_FOOTER``              | The footer text that appears on all pages. Can include   |
|                                      | arbitrary HTML.                                          |
+--------------------------------------+----------------------------------------------------------+
| ``METAREGISTRY_RESOURCES_SUBHEADER`` | The second paragraph on https://bioregistry.io/registry. |
+--------------------------------------+----------------------------------------------------------+
| ``METAREGISTRY_VERSION``             | The version to display in the top-right of each page.    |
|                                      | Can be set to an empty string if no meaningful version   |
|                                      | information exists.                                      |
+--------------------------------------+----------------------------------------------------------+
| ``METAREGISTRY_EXAMPLE_PREFIX``      | An example prefix. Defaults to ``chebi``.                |
+--------------------------------------+----------------------------------------------------------+
| ``METAREGISTRY_EXAMPLE_IDENTIFIER``  | An example local unique identifier to go with the        |
|                                      | example prefix                                           |
+--------------------------------------+----------------------------------------------------------+
| ``ANALYTICS_API_KEY``                | A key for https://github.com/tom-draper/api-analytics    |
+--------------------------------------+----------------------------------------------------------+

Finally, after filling up a configuration JSON file and naming it something like ``config.json``,
you can use the ``--config config.json`` flag in the Python commands to run the web service below.

Running in the command line with Python
---------------------------------------
The Bioregistry can be run from the Python shell directly following installation
from the Python Package Index. This example assumes ``registry.json``
is in the same directory, but any valid paths can be given.

.. code-block:: shell

    python -m pip install gunicorn bioregistry[web]
    python -m bioregistry web \
        --with-gunicorn --workers 4 \
        --port 8766 \
        --host "0.0.0.0" \
        --base-url https://example.com \
        --registry registry.json

.. note:: This is the same as deploying the vanilla Bioregistry except the usage of ``--registry registry.json``

Running with Docker
-------------------
Create the following ``Dockerfile`` in the same directory as your ``registry.json``, ``config.json``,
and any other custom files.

.. code-block:: docker

    # Dockerfile
    FROM python:3.11-alpine

    COPY registry.json
    COPY config.json

    RUN python -m pip install gunicorn bioregistry[web]
    ENTRYPOINT python -m bioregistry web \
        ---with-gunicorn --workers 4 \
        --port 8766 \
        --host "0.0.0.0" \
        --base-url https://example.com \
        --registry registry.json \
        --config config.json

There are two options for running the ``Dockerfile``. The first option
is by running the following two commands in the command line:

.. code-block:: shell

    # Build the docker image from the same directory as the Dockerfile
    docker build --tag bioregistry_custom:latest .

    # Run the docker image, -d means "detach"
    docker run -d -p 8766:8766 bioregistry_custom:latest

The second option is to use an additional `Docker compose <https://docs.docker.com/compose/>`_
file to orchestrate building, tagging, and running. It works by creating (yet another)
configuration file ``docker-compose.yml`` in the same directory as ``Dockerfile`` with
the following:

.. code-block:: yaml

    # docker-compose.yml
    version: '3'
    services:
      app:
        build: .
        restart: always
        ports:
          - "8766:8766"

.. note:: This is a relatively simple configuration, Docker Compose is capable of much more than this in general

The following command can be used to bring up the docker-compose configuration:

.. code-block:: shell

    docker-compose up
