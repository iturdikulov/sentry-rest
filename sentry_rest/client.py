import asyncio
import logging
from types import SimpleNamespace
from typing import Dict, Any
from urllib.parse import quote_plus

from aiohttp import (
    ClientConnectorError,
    ClientError,
    ClientHttpProxyError,
    ClientSession,
    TraceConfig,
    TraceRequestEndParams,
    TraceRequestStartParams,
)
import backoff

logging.getLogger("backoff").addHandler(logging.StreamHandler())
logger = logging.getLogger(__name__)


class SentryClient:
    """
    This class filter sentry issues withint period and get their events.
    """

    RETRY_MAX_INTERVAL = 60.0

    def __init__(
        self,
        auth_token: str,
        auth_organization: str,
        auth_project: str,
        sentry_url: str = "https://app.getsentry.com/api/0",
        search_query: str | None = None,
        period: str = "14d",
        request_limit: int = 25,
        tracing_enabled: bool = False,
    ):
        self.sentry_url = sentry_url
        self.auth_header = {"Authorization": f"Bearer {auth_token}"}

        # Optional search query, used to filter issues
        # more information: https://docs.sentry.io/concepts/search/#query-syntax
        self.search_query = search_query

        # Issuses endpoint
        self.issues_base_url = (
            f"{self.sentry_url}/projects/{auth_organization}/"
            f"{auth_project}/issues/?statsPeriod={period}"
        )
        if self.search_query:
            self.issues_base_url += f"&query={quote_plus(self.search_query)}"

        # Specific issue endpoint
        self.issue_events_base_url = (
            f"{self.sentry_url}/organizations/{auth_organization}/"
            "issues/{issue_id}/events/"
        )

        # Optional requests tracing (only on_request_start)
        self.tracing_enabled = tracing_enabled

    @backoff.on_exception(
        backoff.expo,
        (ClientConnectorError, ClientHttpProxyError),
        max_time=RETRY_MAX_INTERVAL,
    )
    async def extract_endpoint_data(
        self, session: ClientSession, endpoint_url: str
    ) -> list[Dict[str, Any]]:
        """Extract all paginated data from a specific endpoint"""
        items: list[Dict[str, Any]] = []
        while True:
            async with session.get(endpoint_url) as resp:
                resp.raise_for_status()

                res = await resp.json()
                if isinstance(res, dict) and "detail" in res:
                    logger.warning(f"Error: {res['detail']}")
                    raise ClientError

                items += res

                if resp.links and resp.links["next"]["results"] == "true":
                    endpoint_url = str(resp.links["next"]["url"])
                else:
                    break

        return items

    async def get_sentry_events(self) -> list[Any]:
        """Retrive sentry issues and their events."""
        trace_configs = []
        if self.tracing_enabled:
            trace_config = TraceConfig()
            trace_config.on_request_start.append(self.on_request_start)
            trace_config.on_request_end.append(self.on_request_end)
            trace_configs = [trace_config]

        async with ClientSession(
            headers=self.auth_header, trace_configs=trace_configs
        ) as session:
            issues = await self.extract_endpoint_data(session, self.issues_base_url)
            issue_events_tasks = [
                self.extract_endpoint_data(
                    session, self.issue_events_base_url.format(issue_id=issue["id"])
                )
                for issue in issues
            ]
            return [
                issue
                for issue_events in await asyncio.gather(*issue_events_tasks)
                for issue in issue_events
            ]

    async def extract(self) -> list[Any]:
        issues = asyncio.create_task(self.get_sentry_events())
        return await issues

    @staticmethod
    async def on_request_start(
        session: ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: TraceRequestStartParams,
    ):
        trace_config_ctx.on_request_start = session.loop.time()
        logger.info(f"Starting request {params.url}")

    @staticmethod
    async def on_request_end(
        session: ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: TraceRequestEndParams,
    ):
        total = session.loop.time() - trace_config_ctx.on_request_start
        logger.info(f"Finished request {params.url} in {total:.2f}s")
