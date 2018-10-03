# BoonAI
A simple ML suite for use by non-experts.

## How to run

Everything will be run from a single Flask app, but this can be decoupled if needed. 
The default database is SQLite, so no need to install or set anything upfront.



### Create the Python environment
1. Create virtual environment with your preferred tool (virtualenv, conda,...).
Check [virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/) 
or [conda]() pages for more details.

2. Activate the environment

3. Install requirements with pip:
    ```bash
    $ pip install -r requirements.txt
    ```
    Consider using conda to install numpy beforehand, so you will be able to benefit from the mkl speedups.

### Setup App and run
1. Set PYTHONPATH if needed:
    ```bash
    $ export PYTHONPATH="$HOME/path/to/boonai"
    ```

2. Check the config file and correct values if needed. Don't forget to set the correct connection string for database.

3. Navigate to the root of the project and run:
    ```bash
    cd ~/path/to/boonai
    python boonai/run.py
    ```
### (Optional) Install PostgreSQL
If you don't want to use SQLite as your database, you might want ot install a proper database.
Follow the guide on the PostgreSQL homepage ([link](www.postgresql.org/download)) to install it on your platform.

Create the user, unless you want to use the default one. The app will create necessary tables the first time it is run.
