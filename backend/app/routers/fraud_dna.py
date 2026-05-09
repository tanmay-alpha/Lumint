from fastapi import APIRouter
from app.services.fraud_dna.store import load_all
from app.services.fraud_dna.clusterer import run_clustering, build_graph
from app.schemas.fraud_dna import CampaignsResponse, GraphResponse

router = APIRouter(prefix="/api/fraud-dna", tags=["fraud-dna"])


@router.get("/fingerprints")
def get_fingerprints():
    events = load_all()
    return {
        "total": len(events),
        "fingerprints": events,
    }


@router.get("/campaigns", response_model=CampaignsResponse)
def get_campaigns():
    return run_clustering()


@router.get("/graph", response_model=GraphResponse)
def get_graph():
    return build_graph()


@router.post("/recluster", response_model=CampaignsResponse)
def recluster():
    return run_clustering()