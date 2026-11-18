"""Readable company names for job-board slugs (e.g. "launchdarkly" -> "LaunchDarkly")."""

OVERRIDES = {
    "launchdarkly": "LaunchDarkly", "mongodb": "MongoDB", "clickup": "ClickUp", "grafanalabs": "Grafana Labs",
    "pagerduty": "PagerDuty", "hackerrank": "HackerRank", "hubspot": "HubSpot", "gitlab": "GitLab",
    "github": "GitHub", "zoominfo": "ZoomInfo", "servicetitan": "ServiceTitan", "datadog": "Datadog",
    "doordash": "DoorDash", "linkedin": "LinkedIn", "salesloft": "Salesloft", "smartsheet": "Smartsheet",
    "openai": "OpenAI", "dbtlabs": "dbt Labs", "airtable": "Airtable", "chargebee": "Chargebee",
    "ringcentral": "RingCentral", "brex": "Brex", "rippling": "Rippling", "cockroachlabs": "Cockroach Labs",
    "newrelic": "New Relic", "planetscale": "PlanetScale", "sumologic": "Sumo Logic", "onetrust": "OneTrust",
    "seatgeek": "SeatGeek", "bamboohr": "BambooHR", "workos": "WorkOS", "postman": "Postman",
}


def display_name(slug):
    return OVERRIDES.get(slug.lower(), slug[:1].upper() + slug[1:])
