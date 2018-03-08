# Strand Slack

[![CodeFactor](https://www.codefactor.io/repository/github/solutionloft/code-clippy-slack/badge)](https://www.codefactor.io/repository/github/solutionloft/code-clippy-slack)

## Getting Started
To start, clone the repository locally and create a virtual environment. Install the dependencies from the requirements file into your virtual environment.

## Running Tests
If you're using PyCharm, simply use the "Run Tests" run configuration to run all the tests.

Without PyCharm, `cd` into the root directory and run `pytest --flake8 --pep8 --no-cov`

You can also run `ptw` to run pytest-watch

## Running the application
Note that you'll need strand-api running on `CORE_API_HOST`

Make sure you've created a superuser with username `ccs`, email `ccs@solutionloft.com` and password `randomPassword`.

`$ python manage.py createsuperuser --username ccs`.

If you're using PyCharm, simply use the "Run (Local)" run configuration to start the Flask server.

If not, `cd` into the root directory and run `python3 run.py`


## Using ngrok for development
ngrok sets up a tunnel online so that we have an external URL to tell Slack about.

This is useful because much of strand-slack relies on triggers from Slack callbacks over the wire.

Steps to use ngrok:
1) Download ngrok, unzip, and put the script somewhere in your $PATH (likely `/usr/bin/local`)
2) Run `ngrok http 5000` (assuming 5000 is the `PORT` you set in `development.config.json`)
3) You can watch the requests getting routed through the tunnel at <http://localhost:4040/inspect/http>
4) Take the forwarding address (e.g. <http://5c80fc28.ngrok.io>) and configure it on <https://api.slack.com/apps/A8YTKNNMQ/interactive-messages>

Now Slack will be able to call your local server as you interact with the app!

Note that on the free ngrok plan, you'll need to do this every time you restart ngrok.


## Architecture Overview

### Data Flow

Typical flow is this:
1) Requests come into a `blueprint`
2) `blueprint` validates the payload, responds to the requestor, and passes the payload onto a `translator`
3) `translator` converts it to the SLA domain model and passes it to a `service`
4) `service`, with a scoped DB session, ingests state from the `DB` if needed, and delegates work to `commands`
5) `command`, with a scoped DB session, is a unit of work that makes API calls using `wrappers` and/or pushes state to the `DB`

Notable invariants:
1) `service` should not mutate the DB (only SELECT)
2) `command` should not read the DB (only UPDATE/INSERT)
3) `blueprints` (input point) and `wrappers` (output point) are not privy to the SLA domain model

### Domain Model

All modeled elements of the Strand API's domain are prefixed with `Api`, e.g. `ApiUser`.

All modeled elements of the Slack domain are prefixed with `Slack`, e.g. `SlackUser`.

All other modeled elements are part of the local, SLA domain.
