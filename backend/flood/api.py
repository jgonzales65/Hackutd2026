"""Standalone frontend interface: python -m uvicorn backend.flood.api:app."""
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.flood.service import assess_parcel, connect

app = FastAPI(title='FEMA Parcel Flood Overlap')
app.add_middleware(CORSMiddleware,
                   allow_origins=os.getenv('FLOOD_CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(','),
                   allow_methods=['GET'], allow_headers=['*'])


@app.get('/api/parcels/{parcel_id}/flood-risk')
def flood_risk(parcel_id: str):
    try:
        with connect() as conn:
            result = assess_parcel(conn, parcel_id)
    except Exception as exc:
        logging.getLogger(__name__).warning('Flood assessment unavailable (%s)', type(exc).__name__)
        raise HTTPException(status_code=503, detail='Flood assessment temporarily unavailable') from None
    if result is None:
        raise HTTPException(status_code=404, detail='Parcel not found')
    return result
