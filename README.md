# sparv-catapult
The purpose of the catapult is to run the Sparv pipeline. It pre-loads some of
the models and thus speeds up the analysis process. The idea is that it can be
run with the Sparv pipeline as a stand-alone application, but at the moment it
is adapted for usage with the Sparv backend (flask application).

## Requirements

* [Python 3.4](http://python.org/) or newer
* [GCC](http://gcc.gnu.org/install)

## Installation

1. Build the catalaunch binary:

    `make -C catapult`

2. Create python virtual environment for catapult (not required but recommended):

    ```
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    ```

3. Set paths in `config.sh`.

4. Run the catapult:

    `start-server.sh`
