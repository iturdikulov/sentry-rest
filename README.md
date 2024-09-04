Initial version of the sentry rest API client, with reporting generation.
This software is not production ready, and may greatly change in the future.

## Usage examples

First you need to get auth token, organization and project name.

To get auth token check this documentation:
[Auth Tokens](https://docs.sentry.io/account/auth-tokens/#user-auth-tokens).
Don't forget to allow at least read access for `Issues & Events`.

organization and project name you can find in sentry UI.

`https://<your_organization>.sentry.io/projects/` - here you can find required
project.

```
export SENTRY_AUTH_TOKEN=...
export SENTRY_ORGANIZATION=my_org
export SENTRY_PROJECT=my_project
```

Then you can use this package to interact with sentry API.

```python
from os import environ
import asyncio
from sentry_rest import SentryClient

sentry_client = SentryClient(
    auth_token=environ["SENTRY_AUTH_TOKEN"],
    auth_organization=environ["SENTRY_ORGANIZATION"],
    auth_project=environ["SENTRY_PROJECT"],
    search_query="Proxy error detected",
    tracing_enabled=False,  # toggle aiohttp requests information
)

# Filter issues with `search_query` and print their event ids
print([event["id"] for event in asyncio.run(sentry_client.extract())])
# TODO: explain which fields are available in event
```

More [complex example](./examples/proxy_errors.py), with grouping by proxy IP
and time range aviable in `examples` directory. But it can not work for you,
because it's relays on specific messages format.

TODO: add more examples, which may work everywhere.

My main usage (current one) of this package is to generate reports for groups of
specific errors, here is an example how to use it to group proxy-related issues
and events by specific time range (14 days by default).

```bash
# Run example from your directory (copy it to your project root)
python proxy_errors.py

# If you want to run example from package root directory, use this command:
PYTHONPATH=. python examples/proxy_errors.py
```

For me this example will generate report like this:

```text
Proxy checking report (2 weeks), timezone is UTC
========================================
[Proxy: 111.111.111.111 Total erors: 5]  <!-- group by proxy -->
        2024-09-04: 3 errors             <!-- group by day -->
                02:18:20 >> ProxyCheckError
                --------🕐--------       <!-- group by hour -->
                06:18:20 >> ProxyCheckError
                --------🕐--------
                10:18:20 >> ProxyCheckError
        2024-09-03: 2 errors
                18:18:20 >> ProxyCheckError
                --------🕐--------
                22:18:20 >> ProxyCheckError
========================================
[Proxy: 111.111.111.111 Total erors: 39]
        2024-09-04: 3 errors
                02:18:20 >> ProxyCheckError
                --------🕐--------
                06:18:20 >> ProxyCheckError
                --------🕐--------
                10:18:20 >> ProxyCheckError
        2024-09-03: 36 errors
                14:36:32 >> APIError_fetch_data
                14:36:33 >> APIError_fetch_data
                14:36:34 >> APIError_fetch_data
                14:36:36 >> APIError_fetch_data
                14:36:37 >> APIError_fetch_data
                14:36:38 >> APIError_fetch_data
                14:36:52 >> initialize_api
                --------🕐--------
                18:13:12 >> APIError_fetch_data
                18:13:13 >> APIError_fetch_data
                18:13:14 >> APIError_fetch_data
                18:13:15 >> APIError_fetch_data
                18:13:18 >> APIError_fetch_data
                18:13:32 >> APIError_fetch_data
                18:13:32 >> initialize_api
                18:18:20 >> ProxyCheckError
                18:58:11 >> APIError_fetch_data
                18:58:12 >> APIError_fetch_data
                18:58:13 >> APIError_fetch_data
                18:58:15 >> APIError_fetch_data
                18:58:20 >> APIError_fetch_data
                18:58:31 >> initialize_api
                --------🕐--------
                19:56:58 >> APIError_fetch_data
                19:56:58 >> APIError_fetch_data
                19:56:59 >> APIError_fetch_data
                19:57:02 >> APIError_fetch_data
                19:57:11 >> APIError_fetch_data
                19:57:17 >> APIError_fetch_data
                19:57:18 >> initialize_api
                20:01:57 >> APIError_fetch_data
                20:01:58 >> APIError_fetch_data
                20:01:59 >> APIError_fetch_data
                20:02:00 >> APIError_fetch_data
                20:02:04 >> APIError_fetch_data
                20:02:06 >> APIError_fetch_data
                20:02:17 >> initialize_api
                --------🕐--------
                22:18:20 >> ProxyCheckError
========================================
[Proxy: 111.111.111.111 Total erors: 5]
        2024-09-04: 3 errors
                01:31:38 >> APIError_fetch_data
                --------🕐--------
                09:01:08 >> APIError_fetch_data
                09:38:20 >> APIError_fetch_data
        2024-09-03: 2 errors
                22:03:20 >> APIError_fetch_data
                22:03:39 >> APIError_fetch_data
========================================
```

## Features

- Built with `asyncio` and `aiohttp`, we get sentry events concurrently.
- Used `backoff` package to retry failed requests.

## Limitations

Right now we don't support many sentry API endpoints. And this package right
now focused on `Issues & Events` API.

## Dependencies

- aiohttp
- backoff

## To-do

- [ ] verify and fix types
- [ ] add tests
