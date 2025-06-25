import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
import math

# Configuration de la base de données
DB_CONFIG = {
    "host": "localhost",
    "dbname": "wigest",
    "user": "postgres",
    "password": "pass"
}

@contextmanager
def get_db_connection():
    """Crée une connexion à la base de données et la ferme automatiquement après utilisation."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_db_cursor(commit=False):
    """Crée un curseur de base de données et le ferme automatiquement après utilisation."""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

def paginate_query(query: str, count_query: str, params: List, page: int, limit: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Exécute une requête avec pagination et renvoie les résultats et les métadonnées de pagination.
    
    Args:
        query: La requête SQL à exécuter
        count_query: La requête SQL pour compter le nombre total d'éléments
        params: Les paramètres de la requête
        page: Le numéro de page (commence à 1)
        limit: Le nombre d'éléments par page
    
    Returns:
        Un tuple contenant la liste des résultats et les métadonnées de pagination
    """
    offset = (page - 1) * limit
    
    with get_db_cursor() as cursor:
        # Exécuter la requête de comptage
        cursor.execute(count_query, params)
        total = cursor.fetchone()["count"]
        
        # Ajouter la pagination à la requête principale
        paginated_query = f"{query} LIMIT %s OFFSET %s"
        paginated_params = params + [limit, offset]
        
        # Exécuter la requête paginée
        cursor.execute(paginated_query, paginated_params)
        results = cursor.fetchall()
        
        # Calculer les métadonnées de pagination
        pagination = {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total > 0 else 1
        }
        
        return list(results), pagination

# Fonctions CRUD pour les clients
def get_clients(search: Optional[str] = None, page: int = 1, limit: int = 10) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Récupère tous les clients avec pagination et recherche optionnelle."""
    query = "SELECT * FROM clients"
    count_query = "SELECT COUNT(*) as count FROM clients"
    params = []
    
    if search:
        query += " WHERE nom ILIKE %s OR email ILIKE %s"
        count_query += " WHERE nom ILIKE %s OR email ILIKE %s"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY id DESC"
    
    return paginate_query(query, count_query, params, page, limit)

def get_client(client_id: int) -> Optional[Dict[str, Any]]:
    """Récupère un client par son ID."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM clients WHERE id = %s", [client_id])
        return cursor.fetchone()

def create_client(nom: str, email: str) -> Dict[str, Any]:
    """Crée un nouveau client."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO clients (nom, email) VALUES (%s, %s) RETURNING *",
            [nom, email]
        )
        return cursor.fetchone()

def update_client(client_id: int, nom: str, email: str) -> Optional[Dict[str, Any]]:
    """Met à jour un client existant."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE clients SET nom = %s, email = %s WHERE id = %s RETURNING *",
            [nom, email, client_id]
        )
        return cursor.fetchone()

def delete_client(client_id: int) -> bool:
    """Supprime un client."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM clients WHERE id = %s RETURNING id", [client_id])
        return cursor.fetchone() is not None

# Fonctions CRUD pour les offres
def get_offres(search: Optional[str] = None, page: int = 1, limit: int = 10) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Récupère toutes les offres avec pagination et recherche optionnelle."""
    query = "SELECT * FROM offres"
    count_query = "SELECT COUNT(*) as count FROM offres"
    params = []
    
    if search:
        query += " WHERE nom ILIKE %s"
        count_query += " WHERE nom ILIKE %s"
        params.append(f"%{search}%")
    
    query += " ORDER BY id DESC"
    
    return paginate_query(query, count_query, params, page, limit)

def get_offre(offre_id: int) -> Optional[Dict[str, Any]]:
    """Récupère une offre par son ID."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM offres WHERE id = %s", [offre_id])
        return cursor.fetchone()

def create_offre(nom: str, debit_mbps: Optional[int] = None, prix: Optional[int] = None) -> Dict[str, Any]:
    """Crée une nouvelle offre."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO offres (nom, debit_mbps, prix) VALUES (%s, %s, %s) RETURNING *",
            [nom, debit_mbps, prix]
        )
        return cursor.fetchone()

def update_offre(offre_id: int, nom: str, debit_mbps: Optional[int] = None, prix: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Met à jour une offre existante."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE offres SET nom = %s, debit_mbps = %s, prix = %s WHERE id = %s RETURNING *",
            [nom, debit_mbps, prix, offre_id]
        )
        return cursor.fetchone()

def delete_offre(offre_id: int) -> bool:
    """Supprime une offre."""
    with get_db_cursor(commit=True) as cursor:
        # Vérifier si l'offre est utilisée dans des abonnements
        cursor.execute("SELECT COUNT(*) as count FROM abonnements WHERE offre_id = %s", [offre_id])
        if cursor.fetchone()["count"] > 0:
            return False
        
        cursor.execute("DELETE FROM offres WHERE id = %s RETURNING id", [offre_id])
        return cursor.fetchone() is not None

# Fonctions CRUD pour les abonnements
def get_abonnements(
    client_id: Optional[int] = None,
    offre_id: Optional[int] = None,
    mois: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Récupère tous les abonnements avec pagination et filtres optionnels."""
    query = """
        SELECT a.*, c.nom as client_nom, o.nom as offre_nom
        FROM abonnements a
        JOIN clients c ON a.client_id = c.id
        JOIN offres o ON a.offre_id = o.id
        WHERE 1=1
    """
    count_query = """
        SELECT COUNT(*) as count
        FROM abonnements a
        JOIN clients c ON a.client_id = c.id
        JOIN offres o ON a.offre_id = o.id
        WHERE 1=1
    """
    params = []
    
    if client_id:
        query += " AND a.client_id = %s"
        count_query += " AND a.client_id = %s"
        params.append(client_id)
    
    if offre_id:
        query += " AND a.offre_id = %s"
        count_query += " AND a.offre_id = %s"
        params.append(offre_id)
    
    if mois:
        query += " AND TO_CHAR(a.date_debut, 'YYYY-MM') = %s"
        count_query += " AND TO_CHAR(a.date_debut, 'YYYY-MM') = %s"
        params.append(mois)
    
    query += " ORDER BY a.date_debut DESC"
    
    return paginate_query(query, count_query, params, page, limit)

def get_abonnement(abonnement_id: int) -> Optional[Dict[str, Any]]:
    """Récupère un abonnement par son ID avec les détails du client et de l'offre."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT a.*, c.nom as client_nom, o.nom as offre_nom
            FROM abonnements a
            JOIN clients c ON a.client_id = c.id
            JOIN offres o ON a.offre_id = o.id
            WHERE a.id = %s
        """, [abonnement_id])
        return cursor.fetchone()

def create_abonnement(client_id: int, offre_id: int, date_debut: str, date_fin: Optional[str] = None) -> Dict[str, Any]:
    """Crée un nouvel abonnement."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO abonnements (client_id, offre_id, date_debut, date_fin) VALUES (%s, %s, %s, %s) RETURNING *",
            [client_id, offre_id, date_debut, date_fin]
        )
        abonnement = cursor.fetchone()
        
        # Récupérer les détails du client et de l'offre
        cursor.execute("""
            SELECT c.nom as client_nom, o.nom as offre_nom
            FROM clients c, offres o
            WHERE c.id = %s AND o.id = %s
        """, [client_id, offre_id])
        details = cursor.fetchone()
        
        abonnement["client_nom"] = details["client_nom"]
        abonnement["offre_nom"] = details["offre_nom"]
        
        return abonnement

def update_abonnement(
    abonnement_id: int,
    offre_id: Optional[int] = None,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Met à jour un abonnement existant."""
    # D'abord, récupérer l'abonnement actuel
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM abonnements WHERE id = %s", [abonnement_id])
        current = cursor.fetchone()
        
        if not current:
            return None
    
    # Préparer les valeurs à mettre à jour
    new_offre_id = offre_id if offre_id is not None else current["offre_id"]
    new_date_debut = date_debut if date_debut is not None else current["date_debut"]
    new_date_fin = date_fin if date_fin is not None else current["date_fin"]
    
    # Mettre à jour l'abonnement
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE abonnements SET offre_id = %s, date_debut = %s, date_fin = %s WHERE id = %s RETURNING *",
            [new_offre_id, new_date_debut, new_date_fin, abonnement_id]
        )
        abonnement = cursor.fetchone()
        
        if abonnement:
            # Récupérer les détails du client et de l'offre
            cursor.execute("""
                SELECT c.nom as client_nom, o.nom as offre_nom
                FROM clients c, offres o
                WHERE c.id = %s AND o.id = %s
            """, [abonnement["client_id"], new_offre_id])
            details = cursor.fetchone()
            
            abonnement["client_nom"] = details["client_nom"]
            abonnement["offre_nom"] = details["offre_nom"]
        
        return abonnement

def delete_abonnement(abonnement_id: int) -> bool:
    """Supprime un abonnement."""
    with get_db_cursor(commit=True) as cursor:
        # Vérifier si l'abonnement a des paiements
        cursor.execute("SELECT COUNT(*) as count FROM paiements WHERE abonnement_id = %s", [abonnement_id])
        if cursor.fetchone()["count"] > 0:
            # Si l'abonnement a des paiements, on ne le supprime pas directement
            # On pourrait implémenter une suppression en cascade si nécessaire
            return False
        
        cursor.execute("DELETE FROM abonnements WHERE id = %s RETURNING id", [abonnement_id])
        return cursor.fetchone() is not None

# Fonctions CRUD pour les paiements
def get_paiements(
    abonnement_id: Optional[int] = None,
    client_id: Optional[int] = None,
    offre_id: Optional[int] = None,
    mois: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Récupère tous les paiements avec pagination et filtres optionnels."""
    query = """
        SELECT p.*, c.nom as client_nom, o.nom as offre_nom
        FROM paiements p
        JOIN abonnements a ON p.abonnement_id = a.id
        JOIN clients c ON a.client_id = c.id
        JOIN offres o ON a.offre_id = o.id
        WHERE 1=1
    """
    count_query = """
        SELECT COUNT(*) as count
        FROM paiements p
        JOIN abonnements a ON p.abonnement_id = a.id
        JOIN clients c ON a.client_id = c.id
        JOIN offres o ON a.offre_id = o.id
        WHERE 1=1
    """
    params = []
    
    if abonnement_id:
        query += " AND p.abonnement_id = %s"
        count_query += " AND p.abonnement_id = %s"
        params.append(abonnement_id)
    
    if client_id:
        query += " AND a.client_id = %s"
        count_query += " AND a.client_id = %s"
        params.append(client_id)
    
    if offre_id:
        query += " AND a.offre_id = %s"
        count_query += " AND a.offre_id = %s"
        params.append(offre_id)
    
    if mois:
        query += " AND TO_CHAR(p.date_paiement, 'YYYY-MM') = %s"
        count_query += " AND TO_CHAR(p.date_paiement, 'YYYY-MM') = %s"
        params.append(mois)
    
    query += " ORDER BY p.date_paiement DESC"
    
    return paginate_query(query, count_query, params, page, limit)

def get_paiement(paiement_id: int) -> Optional[Dict[str, Any]]:
    """Récupère un paiement par son ID avec les détails du client et de l'offre."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT p.*, c.nom as client_nom, o.nom as offre_nom
            FROM paiements p
            JOIN abonnements a ON p.abonnement_id = a.id
            JOIN clients c ON a.client_id = c.id
            JOIN offres o ON a.offre_id = o.id
            WHERE p.id = %s
        """, [paiement_id])
        return cursor.fetchone()

def create_paiement(abonnement_id: int, montant: float, date_paiement: str) -> Dict[str, Any]:
    """Crée un nouveau paiement."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO paiements (abonnement_id, montant, date_paiement) VALUES (%s, %s, %s) RETURNING *",
            [abonnement_id, montant, date_paiement]
        )
        paiement = cursor.fetchone()
        
        # Récupérer les détails du client et de l'offre
        cursor.execute("""
            SELECT c.nom as client_nom, o.nom as offre_nom
            FROM abonnements a
            JOIN clients c ON a.client_id = c.id
            JOIN offres o ON a.offre_id = o.id
            WHERE a.id = %s
        """, [abonnement_id])
        details = cursor.fetchone()
        
        paiement["client_nom"] = details["client_nom"]
        paiement["offre_nom"] = details["offre_nom"]
        
        return paiement

def update_paiement(paiement_id: int, montant: Optional[float] = None, date_paiement: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Met à jour un paiement existant."""
    # D'abord, récupérer le paiement actuel
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM paiements WHERE id = %s", [paiement_id])
        current = cursor.fetchone()
        
        if not current:
            return None
    
    # Préparer les valeurs à mettre à jour
    new_montant = montant if montant is not None else current["montant"]
    new_date_paiement = date_paiement if date_paiement is not None else current["date_paiement"]
    
    # Mettre à jour le paiement
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE paiements SET montant = %s, date_paiement = %s WHERE id = %s RETURNING *",
            [new_montant, new_date_paiement, paiement_id]
        )
        paiement = cursor.fetchone()
        
        if paiement:
            # Récupérer les détails du client et de l'offre
            cursor.execute("""
                SELECT c.nom as client_nom, o.nom as offre_nom
                FROM abonnements a
                JOIN clients c ON a.client_id = c.id
                JOIN offres o ON a.offre_id = o.id
                WHERE a.id = %s
            """, [paiement["abonnement_id"]])
            details = cursor.fetchone()
            
            paiement["client_nom"] = details["client_nom"]
            paiement["offre_nom"] = details["offre_nom"]
        
        return paiement

def delete_paiement(paiement_id: int) -> bool:
    """Supprime un paiement."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM paiements WHERE id = %s RETURNING id", [paiement_id])
        return cursor.fetchone() is not None

# Fonctions pour les logs
def get_logs(table: Optional[str] = None, page: int = 1, limit: int = 10) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Récupère tous les logs avec pagination et filtre optionnel par table."""
    query = "SELECT * FROM logs"
    count_query = "SELECT COUNT(*) as count FROM logs"
    params = []
    
    if table:
        query += " WHERE table_modifiee = %s"
        count_query += " WHERE table_modifiee = %s"
        params.append(table)
    
    query += " ORDER BY date_action DESC"
    
    return paginate_query(query, count_query, params, page, limit)