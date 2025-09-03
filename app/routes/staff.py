from flask import Blueprint, request, jsonify
from app.db.postgres import get_pg_connection

staff_bp = Blueprint("staff", __name__)

@staff_bp.route("/staff", methods=["POST"])
def add_staff():
    data = request.json
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO dips.staff (name) VALUES (%s) RETURNING id;", (data["name"],))
    staff_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": staff_id}), 201

@staff_bp.route("/staff/<int:staff_id>/services", methods=["POST"])
def assign_service(staff_id):
    data = request.json
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dips.staff_services (staff_id, service_id)
        VALUES (%s, %s);
    """, (staff_id, data["service_id"]))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Service assigned"}), 201

@staff_bp.route("/staff", methods=["GET"])
def list_staff():
    query = """
        SELECT s.id, s.name, array_agg(sv.name) AS services
        FROM dips.staff s
        LEFT JOIN dips.staff_services ss ON s.id = ss.staff_id
        LEFT JOIN dips.services sv ON ss.service_id = sv.id
        GROUP BY s.id, s.name;
    """

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    staff_list = [
        {
            "id": staff_id,
            "name": name,
            "services": services if services != [None] else []
        }
        for staff_id, name, services in rows
    ]

    return jsonify(staff_list)
