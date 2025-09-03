from flask import Blueprint, request, jsonify
from app.db.postgres import get_pg_connection

bookings_bp = Blueprint("bookings", __name__)

@bookings_bp.route("/bookings", methods=["POST"])
def create_booking():
    data = request.json
    conn = get_pg_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1
        FROM dips.bookings
        WHERE staff_id = %s 
          AND date = %s::DATE
          AND ((start_time, end_time) OVERLAPS (%s::TIME, %s::TIME))
          AND status IN ('pending', 'confirmed');
    """, (data["staff_id"], data["date"], data["start_time"], data["end_time"]))
    
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Staff already booked at this time"}), 400

    cur.execute("""
        INSERT INTO dips.bookings (user_id, staff_id, service_id, date, start_time, end_time, status)
        VALUES (%s, %s, %s, %s::DATE, %s::TIME, %s::TIME, %s)
        RETURNING id;
    """, (
        data["user_id"], data["staff_id"], data["service_id"],
        data["date"], data["start_time"], data["end_time"], "pending"
    ))
    
    booking_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": booking_id}), 201


@bookings_bp.route("/bookings", methods=["GET"])
def list_bookings():
    query = """
        SELECT b.id, u.name AS customer, s.name AS staff, sv.name AS service,
               b.date, b.start_time, b.end_time, b.status
        FROM dips.bookings b
        JOIN dips.users u ON b.user_id = u.id
        JOIN dips.staff s ON b.staff_id = s.id
        JOIN dips.services sv ON b.service_id = sv.id
        ORDER BY b.date, b.start_time;
    """

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    bookings = [
        {
            "id": row[0],
            "customer": row[1],
            "staff": row[2],
            "service": row[3],
            "date": str(row[4]),
            "start_time": str(row[5]),
            "end_time": str(row[6]),
            "status": row[7]
        }
        for row in rows
    ]

    return jsonify(bookings)
