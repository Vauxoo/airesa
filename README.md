[![Build Status](https://git.vauxoo.com/vauxoo/airesa/badges/19.0/pipeline.svg)](https://git.vauxoo.com/vauxoo/airesa/pipelines)
[![Coverage Report](https://git.vauxoo.com/vauxoo/airesa/badges/19.0/coverage.svg)](https://coverage.vauxoo.com/19-0-airesa)
[![pre-commit-vauxoo](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/vauxoo/pre-commit-vauxoo)
[![black + pre-commit-vauxoo](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/vauxoo/pre-commit-vauxoo)


Modules for airesa
==================

Production Instances
--------------------

To have access to all the instances related to this project that are actually
deployed please go to the dashboard with such information which will have
all the connection information related to this repository.

Repositories which we depend on.
--------------------------------

Read the oca_dependencies.txt file.

Deploy locally
--------------

To deploy local instances we use a tool called travis2docker.
`travis2docker` is a Python tool created by Vauxoo, to create a docker container
from an Odoo repository. That allows us to perform functional tests or even to
implement new features.

1. Install travis2docker in order to create local environment (docker
   container) copy of last changes on the airesa repository:

    ```bash
    $ pip install travis2docker
    ```

2. You can check travis2docker  was correctly installed by running the following command:

    ```bash
    $ travisfile2dockerfile --version
    ```

    You should be able to see the installed version.

    travis2docker creates a folder on which created scripts will be placed.
    As a standard, this folder is usually named `.t2d` and is inside
    your HOME folder.

    Also, in order to use travis2docker easily, we highly recommend that you
    create an alias to make the command shorter and to define by default some
    arguments that are required so you will not have to add this parameters by
    hand every time that you run travis2docker.

    You can achieve this by adding the following to your `~/.bash_aliases` file:

    ```bash
    alias t2d="travisfile2dockerfile --run-extra-args='-it -e LANG=en_US.UTF-8' --add-remote=vauxoo,vauxoo-dev"
    ```

3. Now we can use the t2d command. This will be accomplished by using the following
   command line:

    ```bash
    $ t2d git@git.vauxoo.com:vauxoo/airesa.git 19.0
    ```

    The result after running this t2d script will be a log that have a local path
    with the directory created.

    ```bash
    ${HOME}/.t2d/script/git_git.vauxoo.com_vauxoo_airesa.git/19.0/<python_version>/env_1_job_1
    ```

    In this directory, there will be the necessary files that will let us create the environment
    to create databases and have access to review or edit the related branches.

    There will be two scripts:

    - 10-build.sh: will create the image (docker build with pre configured arguments)
    - 20-run.sh: will create the container (docker run with pre configured arguments)

4. The following step is to run the last mentioned scripts, we highly recommend to
   add the following extra arguments.

    ```bash
    $ cd ${HOME}/.t2d/script/git_git.vauxoo.com_vauxoo_airesa.git/19.0/<python_version>/env_1_job_1
    $ ./10-build.sh --no-cache
    $ ./20-run.sh --entrypoint=bash
    ```

    Additionally, you can name your container by adding the ```--name=``` parameter to the 20-run.sh script.
    For instance: 
    
    ```bash
    ./20-run.sh --entrypoint=bash --name=airesa
    ```

5. After the last script has finished, you will notice that your prompt has changed,
   this happens because you are inside your new container. It will look something
   like this:

    ```bash
    [odoo@a458896bf8f5]~/instance/extra_addons/airesa$
    (19.0)$
    ```

    where a458896bf8f5 is your container id. Now you have access to the
    development environment that has a clone of the repositories used for
    airesa:

    - Main repository will be ALWAYS inside /home/odoo/instance/extra_addons/airesa
    - The oca dependencies repositories will be inside /home/odoo/instance/extra_addons folder.

    The remotes will be already configured, so you can start working by creating
    new branches in vauxoo-dev,

6. In order to test the demo database or to create new features, you
   will need to have, at least, one demo database running to locally test
   your new changes. In order to accomplish this, you will need to run the following
   command inside your container:

    ```bash
    $ /entrypoint.sh
    ```

    This will run odoo server and will create a database: odoo
    This database has installed all the modules required to make
    the project run.

7. After this script has finished, you can run the odoo server again on demand
   using the following command:

    ```bash
    $ ~/instance/odoo/odoo-bin -d odoo
    ```

8. Last but not least, you will need to have more than one console view to your
   container, one for run the odoo server, another for use vim to add the changes
   to the code and to use the git commands. You can have several connections to
   your container with multiple docker exec, or, you can learn to use tmux in
   order to have only one connection to the container and have any amount of
   sub consoles you need.
   
   > **NOTE:** It is recommended to use tmux with the following tabs:
   >
   ```bash
   0: server
   1: git
   2: vim
   3: search
   ```
