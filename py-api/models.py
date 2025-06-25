from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
import re

# Fonction de validation d'email simple
def validate_email(email: str) -> str:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Email invalide")
    return email

# Modèles pour les clients
class ClientBase(BaseModel):
    nom: str
    email: str
    
    @validator('email')
    def email_must_be_valid(cls, v):
        return validate_email(v)

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    
    class Config:
        from_attributes = True

# Modèles pour les offres
class OffreBase(BaseModel):
    nom: str
    debit_mbps: Optional[int] = None
    prix: Optional[int] = None

class OffreCreate(OffreBase):
    pass

class OffreUpdate(OffreBase):
    pass

class Offre(OffreBase):
    id: int
    
    class Config:
        from_attributes = True

# Modèles pour les abonnements
class AbonnementBase(BaseModel):
    client_id: int
    offre_id: int
    date_debut: date
    date_fin: Optional[date] = None

class AbonnementCreate(AbonnementBase):
    pass

class AbonnementUpdate(BaseModel):
    offre_id: Optional[int] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None

class Abonnement(AbonnementBase):
    id: int
    
    class Config:
        from_attributes = True

class AbonnementDetail(BaseModel):
    id: int
    client_id: int
    client_nom: str
    offre_id: int
    offre_nom: str
    date_debut: date
    date_fin: Optional[date] = None
    
    class Config:
        from_attributes = True

# Modèles pour les paiements
class PaiementBase(BaseModel):
    abonnement_id: int
    montant: Decimal = Field(..., ge=0)
    date_paiement: date

class PaiementCreate(PaiementBase):
    pass

class PaiementUpdate(BaseModel):
    montant: Optional[Decimal] = Field(None, ge=0)
    date_paiement: Optional[date] = None

class Paiement(PaiementBase):
    id: int
    
    class Config:
        from_attributes = True

class PaiementDetail(BaseModel):
    id: int
    abonnement_id: int
    client_nom: str
    offre_nom: str
    montant: Decimal
    date_paiement: date
    
    class Config:
        from_attributes = True

# Modèles pour les logs
class Log(BaseModel):
    id: int
    table_modifiee: str
    action: str
    date_action: datetime
    donnees: Optional[dict] = None
    
    class Config:
        from_attributes = True

# Modèles pour les réponses paginées
class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int

class ClientsResponse(BaseModel):
    clients: List[Client]
    pagination: PaginationMeta

class OffresResponse(BaseModel):
    offres: List[Offre]
    pagination: PaginationMeta

class AbonnementsResponse(BaseModel):
    abonnements: List[AbonnementDetail]
    pagination: PaginationMeta

class PaiementsResponse(BaseModel):
    paiements: List[PaiementDetail]
    pagination: PaginationMeta

class LogsResponse(BaseModel):
    logs: List[Log]
    pagination: PaginationMeta