from flask import Blueprint, request, jsonify
from app.db.postgres import get_pg_connection

services_bp = Blueprint("services", __name__)

@services_bp.route("/services", methods=["POST"])
def add_service():
    data = request.json
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dips.services (name, category, duration, price)
        VALUES (%s, %s, %s, %s) RETURNING id;
    """, (data["name"], data["category"], data["duration"], data["price"]))
    service_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": service_id}), 201

@services_bp.route("/services", methods=["GET"])
def list_services():
    query = """
        SELECT id, name, category, duration, price
        FROM dips.services;
    """

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    services = [
        {
            "id": service_id,
            "name": name,
            "category": category,
            "duration": duration,
            "price": float(price) if price is not None else None
        }
        for service_id, name, category, duration, price in rows
    ]

    return jsonify(services)
