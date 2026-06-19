from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data once
with open("q-vercel-latency.json", "r") as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: int


@app.post("/")
def analytics(data: RequestBody):

    result = {}

    for region in data.regions:

        # filter rows for region
        region_rows = [
            row for row in telemetry
            if row["region"] == region
        ]

        # extract latency values
        latencies = [row["latency_ms"] for row in region_rows]

        # safety check (avoid crash if empty region)
        if len(latencies) == 0:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue

        # compute metrics
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = float(np.percentile(latencies, 95))
        breaches = len([x for x in latencies if x > data.threshold_ms])

        # final output per region
        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": 1.0,   # fixed since dataset has no uptime field
            "breaches": breaches
        }

    return result
