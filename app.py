# app.py
import os, uuid, time
from typing import Dict, Any, Literal
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field

from sweep import sweep_area
from webhook import post_webhook


app = FastAPI(title="Transformer Sweep Service")

class ScanRequest(BaseModel):
    provider: Literal["afinia", "aire"]
    lat: float
    lon: float
    radius: int = 1000
    step: int = 150
    workers: int = 12
    webhook: str

def _finish_and_callback(job_id: str, req: ScanRequest):
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results = sweep_area(
        provider=req.provider,
        center_lat=req.lat,
        center_lon=req.lon,
        radius_m=req.radius,
        step_m=req.step,
        max_workers=req.workers,
    )
    finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    payload: Dict[str, Any] = {
        "status": "completed",
        "meta": {
            "job_id": job_id, "provider": req.provider,
            "center_lat": req.lat, "center_lon": req.lon,
            "radius_m": req.radius, "step_m": req.step,
            "workers": req.workers,
            "probes_total": None,  # (optional: expose from sweep if you want)
            "started_at": started_at, "finished_at": finished_at,
        },
        "found_count": len(results),
        "results": results,
    }
    ok = post_webhook(req.webhook, payload)
    if not ok:
        # Fall back: log; or persist locally (left simple here)
        print(f"[WARN] webhook delivery failed for job_id={job_id}")

@app.post("/scan")
async def scan(req: ScanRequest, background: BackgroundTasks):
    job_id = str(uuid.uuid4())
    background.add_task(_finish_and_callback, job_id, req)
    return {"job_id": job_id, "status": "started"}

@app.post("/webhooks/transformer-scan")
async def webhook_receiver(payload: dict):
    # Just log / handle the payload
    print(f"[Webhook] received job {payload['meta']['job_id']} with {payload['found_count']} transformers")
    return {"ok": True}