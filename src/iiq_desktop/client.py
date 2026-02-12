from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import requests


@dataclass
class IncidentIQClient:
    base_url: str
    api_key: str
    timeout_seconds: int = 30

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        response = requests.get(
            f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
            headers=self._headers(),
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()

    def _post(self, path: str, body: dict) -> dict | list:
        response = requests.post(
            f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
            headers=self._headers(),
            json=body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()

    def search_people(self, query: str, limit: int = 25) -> list[dict]:
        payload = self._get("people", params={"$top": limit, "$filter": f"contains(fullName,'{query}')"})
        return payload.get("value", payload if isinstance(payload, list) else [])

    def get_assets_for_person(self, person_id: str, limit: int = 100) -> list[dict]:
        payload = self._get(
            "assets",
            params={
                "$top": limit,
                "$filter": f"assignedTo/id eq {person_id}",
                "$orderby": "serialNumber asc",
            },
        )
        return payload.get("value", payload if isinstance(payload, list) else [])

    def get_unassigned_chromebooks(self, limit: int = 300) -> list[dict]:
        payload = self._get(
            "assets",
            params={
                "$top": limit,
                "$filter": "contains(model,'Chromebook') and assignedTo eq null",
                "$orderby": "serialNumber asc",
            },
        )
        return payload.get("value", payload if isinstance(payload, list) else [])

    def get_recent_timeline(self, person_id: str, days: int = 60) -> list[dict]:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        payload = self._get(
            "ticketactivity",
            params={
                "$top": 200,
                "$filter": f"person/id eq {person_id} and createdOn ge {since}",
                "$orderby": "createdOn desc",
            },
        )
        return payload.get("value", payload if isinstance(payload, list) else [])

    def mass_assign(self, person_id: str, asset_ids: list[str], notes: str = "Bulk assigned via desktop app") -> dict:
        body = {
            "personId": person_id,
            "assetIds": asset_ids,
            "notes": notes,
        }
        return self._post("assets/bulkassign", body)
