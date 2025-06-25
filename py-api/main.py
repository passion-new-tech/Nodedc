from fastapi import FastAPI, APIRouter, Query, Path, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import psycopg2
from psycopg2.errors import UniqueViolation
from decimal import Decimal
from datetime import date

# Import des modèles et fonctions de base de données
from models import (
    Client, ClientCreate, ClientUpdate, ClientsResponse,
    Offre, OffreCreate, OffreUpdate, OffresResponse,
    Abonnement, AbonnementCreate, AbonnementUpdate, AbonnementDetail, AbonnementsResponse,
    Paiement, PaiementCreate, PaiementUpdate, PaiementDetail, PaiementsResponse,
    Log, LogsResponse
)
import database as db

app = FastAPI(
    title="Wigest API",
    description="API pour la gestion des clients, abonnements, offres et paiements",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Création des routers pour chaque entité
router = APIRouter()
clients_router = APIRouter(prefix="/clients", tags=["Clients"])
offres_router = APIRouter(prefix="/offres", tags=["Offres"])
abonnements_router = APIRouter(prefix="/abonnements", tags=["Abonnements"])
paiements_router = APIRouter(prefix="/paiements", tags=["Paiements"])
logs_router = APIRouter(prefix="/logs", tags=["Logs"])
stats_router = APIRouter(prefix="/stats", tags=["Statistiques"])

# Endpoints pour les clients
@clients_router.get("", response_model=ClientsResponse)
async def read_clients(
    search: Optional[str] = None,
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste des clients avec pagination et recherche optionnelle.
    """
    try:
        clients, pagination = db.get_clients(search, page, limit)
        return {"clients": clients, "pagination": pagination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@clients_router.get("/{client_id}", response_model=Client)
async def read_client(
    client_id: int = Path(..., ge=1, description="ID du client")
):
    """
    Récupère un client par son ID.
    """
    client = db.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client

@clients_router.post("", response_model=Client, status_code=201)
async def create_client(
    client: ClientCreate = Body(...)
):
    """
    Crée un nouveau client.
    """
    try:
        return db.create_client(client.nom, client.email)
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Un client avec cet email existe déjà")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@clients_router.put("/{client_id}", response_model=Client)
async def update_client(
    client_id: int = Path(..., ge=1, description="ID du client"),
    client: ClientUpdate = Body(...)
):
    """
    Met à jour un client existant.
    """
    try:
        updated_client = db.update_client(client_id, client.nom, client.email)
        if not updated_client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        return updated_client
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Un client avec cet email existe déjà")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@clients_router.delete("/{client_id}")
async def delete_client(
    client_id: int = Path(..., ge=1, description="ID du client")
):
    """
    Supprime un client.
    """
    try:
        if not db.delete_client(client_id):
            raise HTTPException(status_code=404, detail="Client non trouvé")
        return {"message": "Client supprimé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints pour les offres
@offres_router.get("", response_model=OffresResponse)
async def read_offres(
    search: Optional[str] = None,
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste des offres avec pagination et recherche optionnelle.
    """
    try:
        offres, pagination = db.get_offres(search, page, limit)
        return {"offres": offres, "pagination": pagination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@offres_router.get("/{offre_id}", response_model=Offre)
async def read_offre(
    offre_id: int = Path(..., ge=1, description="ID de l'offre")
):
    """
    Récupère une offre par son ID.
    """
    offre = db.get_offre(offre_id)
    if not offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    return offre

@offres_router.post("", response_model=Offre, status_code=201)
async def create_offre(
    offre: OffreCreate = Body(...)
):
    """
    Crée une nouvelle offre.
    """
    try:
        return db.create_offre(offre.nom, offre.debit_mbps, offre.prix)
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Une offre avec ce nom existe déjà")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@offres_router.put("/{offre_id}", response_model=Offre)
async def update_offre(
    offre_id: int = Path(..., ge=1, description="ID de l'offre"),
    offre: OffreUpdate = Body(...)
):
    """
    Met à jour une offre existante.
    """
    try:
        updated_offre = db.update_offre(offre_id, offre.nom, offre.debit_mbps, offre.prix)
        if not updated_offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        return updated_offre
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Une offre avec ce nom existe déjà")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@offres_router.delete("/{offre_id}")
async def delete_offre(
    offre_id: int = Path(..., ge=1, description="ID de l'offre")
):
    """
    Supprime une offre.
    """
    try:
        if not db.delete_offre(offre_id):
            raise HTTPException(status_code=409, detail="Impossible de supprimer cette offre car elle est utilisée par des abonnements")
        return {"message": "Offre supprimée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints pour les abonnements
@abonnements_router.get("", response_model=AbonnementsResponse)
async def read_abonnements(
    client_id: Optional[int] = None,
    offre_id: Optional[int] = None,
    mois: Optional[str] = None,
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste des abonnements avec pagination et filtres optionnels.
    """
    try:
        abonnements, pagination = db.get_abonnements(client_id, offre_id, mois, page, limit)
        return {"abonnements": abonnements, "pagination": pagination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@abonnements_router.get("/{abonnement_id}", response_model=AbonnementDetail)
async def read_abonnement(
    abonnement_id: int = Path(..., ge=1, description="ID de l'abonnement")
):
    """
    Récupère un abonnement par son ID.
    """
    abonnement = db.get_abonnement(abonnement_id)
    if not abonnement:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")
    return abonnement

@abonnements_router.post("", response_model=AbonnementDetail, status_code=201)
async def create_abonnement(
    abonnement: AbonnementCreate = Body(...)
):
    """
    Crée un nouvel abonnement.
    """
    try:
        # Vérifier si le client existe
        client = db.get_client(abonnement.client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        # Vérifier si l'offre existe
        offre = db.get_offre(abonnement.offre_id)
        if not offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        return db.create_abonnement(
            abonnement.client_id,
            abonnement.offre_id,
            abonnement.date_debut.isoformat(),
            abonnement.date_fin.isoformat() if abonnement.date_fin else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@abonnements_router.put("/{abonnement_id}", response_model=AbonnementDetail)
async def update_abonnement(
    abonnement_id: int = Path(..., ge=1, description="ID de l'abonnement"),
    abonnement: AbonnementUpdate = Body(...)
):
    """
    Met à jour un abonnement existant.
    """
    try:
        # Vérifier si l'offre existe si elle est fournie
        if abonnement.offre_id is not None:
            offre = db.get_offre(abonnement.offre_id)
            if not offre:
                raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        updated_abonnement = db.update_abonnement(
            abonnement_id,
            abonnement.offre_id,
            abonnement.date_debut.isoformat() if abonnement.date_debut else None,
            abonnement.date_fin.isoformat() if abonnement.date_fin else None
        )
        
        if not updated_abonnement:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        return updated_abonnement
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@abonnements_router.delete("/{abonnement_id}")
async def delete_abonnement(
    abonnement_id: int = Path(..., ge=1, description="ID de l'abonnement")
):
    """
    Supprime un abonnement.
    """
    try:
        if not db.delete_abonnement(abonnement_id):
            raise HTTPException(
                status_code=409,
                detail="Impossible de supprimer cet abonnement car il a des paiements associés"
            )
        return {"message": "Abonnement supprimé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints pour les paiements
@paiements_router.get("", response_model=PaiementsResponse)
async def read_paiements(
    abonnement_id: Optional[int] = None,
    client_id: Optional[int] = None,
    offre_id: Optional[int] = None,
    mois: Optional[str] = None,
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste des paiements avec pagination et filtres optionnels.
    """
    try:
        paiements, pagination = db.get_paiements(abonnement_id, client_id, offre_id, mois, page, limit)
        return {"paiements": paiements, "pagination": pagination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@paiements_router.get("/{paiement_id}", response_model=PaiementDetail)
async def read_paiement(
    paiement_id: int = Path(..., ge=1, description="ID du paiement")
):
    """
    Récupère un paiement par son ID.
    """
    paiement = db.get_paiement(paiement_id)
    if not paiement:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    return paiement

@paiements_router.post("", response_model=PaiementDetail, status_code=201)
async def create_paiement(
    paiement: PaiementCreate = Body(...)
):
    """
    Crée un nouveau paiement.
    """
    try:
        # Vérifier si l'abonnement existe
        abonnement = db.get_abonnement(paiement.abonnement_id)
        if not abonnement:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        return db.create_paiement(
            paiement.abonnement_id,
            float(paiement.montant),
            paiement.date_paiement.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@paiements_router.put("/{paiement_id}", response_model=PaiementDetail)
async def update_paiement(
    paiement_id: int = Path(..., ge=1, description="ID du paiement"),
    paiement: PaiementUpdate = Body(...)
):
    """
    Met à jour un paiement existant.
    """
    try:
        updated_paiement = db.update_paiement(
            paiement_id,
            float(paiement.montant) if paiement.montant is not None else None,
            paiement.date_paiement.isoformat() if paiement.date_paiement else None
        )
        
        if not updated_paiement:
            raise HTTPException(status_code=404, detail="Paiement non trouvé")
        
        return updated_paiement
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@paiements_router.delete("/{paiement_id}")
async def delete_paiement(
    paiement_id: int = Path(..., ge=1, description="ID du paiement")
):
    """
    Supprime un paiement.
    """
    try:
        if not db.delete_paiement(paiement_id):
            raise HTTPException(status_code=404, detail="Paiement non trouvé")
        return {"message": "Paiement supprimé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints pour les logs
@logs_router.get("", response_model=LogsResponse)
async def read_logs(
    table: Optional[str] = None,
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page")
):
    """
    Récupère la liste des logs avec pagination et filtre optionnel par table.
    """
    try:
        logs, pagination = db.get_logs(table, page, limit)
        return {"logs": logs, "pagination": pagination}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints pour les statistiques (conservés de l'ancienne version)
@stats_router.get("/paiements")
async def stats_paiements(
    mois: Optional[str] = Query(None, description="Format YYYY-MM"),  
    offre: Optional[int] = Query(None, description="ID de l'offre")
):
    """
    Récupère les statistiques des paiements avec filtres optionnels.
    """
    try:
        paiements, _ = db.get_paiements(offre_id=offre, mois=mois, limit=1000)
        return {"paiements": paiements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stats_router.get("/abonnements")
async def stats_abonnements(
    mois: Optional[str] = Query(None, description="Format YYYY-MM"),      
    offre: Optional[int] = Query(None, description="ID de l'offre")
):
    """
    Récupère les statistiques des abonnements avec filtres optionnels.
    """
    try:
        abonnements, _ = db.get_abonnements(offre_id=offre, mois=mois, limit=1000)
        return {"abonnements": abonnements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enregistrement des routers
app.include_router(clients_router)
app.include_router(offres_router)
app.include_router(abonnements_router)
app.include_router(paiements_router)
app.include_router(logs_router)
app.include_router(stats_router)
app.include_router(router)