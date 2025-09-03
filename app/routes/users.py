import requests
import random
from datetime import datetime, timedelta
import re
from flask import Blueprint, request, jsonify
from app.db.postgres import get_pg_connection
from werkzeug.security import generate_password_hash

users_bp = Blueprint("users", __name__)

CHECK_API_URL = "https://waapi.shifteasy.ai/api/check"
SEND_API_URL = "https://waapi.shifteasy.ai/api/send"

def generate_otp():
    return str(random.randint(100000, 999999))

@users_bp.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    number = data.get("mobile")
    mb_id = data.get("mb_id")

    if not number:
        return jsonify({"error": "Mobile number is required"}), 400
    
    if not re.match(r"^\+\d{6,15}$", number):
        return jsonify({"error": "Mobile number must include country code"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, email, phone, role FROM dips.users
            WHERE phone = %s;
        """, (number,))
        user_exists = cur.fetchone()

        if user_exists:
            return jsonify({
                "message": "Mobile Number already registered",
                "user_id": user_exists[0],
                "name": user_exists[1],
                "email": user_exists[2],
                "phone": user_exists[3],
                "role": user_exists[4],
            }), 200

        check_response = requests.post(CHECK_API_URL, json={"number": number})
        if check_response.status_code != 200:
            return jsonify({"error": "Failed to check number"}), 500
        
        check_data = check_response.json()
        if not check_data.get("success") or not check_data.get("exists"):
            return jsonify({"message": "Number is not a valid WhatsApp number"}), 400
        
        jid = check_data.get("jid")

        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        cur.execute("""
            INSERT INTO dips.user_otps (mobile, otp, mb_id, expires_at)
            VALUES (%s, %s, %s, %s);
        """, (number, otp, mb_id, expires_at))
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        if conn:
            cur.close()
            conn.close()

    requests.post(SEND_API_URL, json={
        "recipient": jid,
        "message": f"Your OTP is: {otp}",
        "mediaPath": ""
    })

    return jsonify({"message": f"OTP sent to {number}"}), 200


@users_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    number = data.get("mobile")
    otp = data.get("otp")

    if not number or not otp:
        return jsonify({"error": "Mobile and OTP are required"}), 400

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, expires_at, is_verified FROM dips.user_otps
        WHERE mobile = %s AND otp = %s
        ORDER BY created_at DESC LIMIT 1;
    """, (number, otp))
    record = cur.fetchone()

    if not record:
        cur.close()
        conn.close()
        return jsonify({"error": "Invalid OTP"}), 400

    otp_id, expires_at, is_verified = record
    if is_verified:
        cur.close()
        conn.close()
        return jsonify({"error": "OTP already used"}), 400
    if datetime.utcnow() > expires_at:
        cur.close()
        conn.close()
        return jsonify({"error": "OTP expired"}), 400

    cur.execute("UPDATE dips.user_otps SET is_verified = TRUE WHERE id = %s", (otp_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "OTP verified successfully"}), 200


@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    mobile = data.get("phone")
    password = data.get("password")

    if not all([name, email, mobile, password]):
        return jsonify({"error": "Name, email, phone, and password are required"}), 400

    if not re.match(r"^\+\d{6,15}$", mobile):
        return jsonify({"error": "Mobile number must include country code"}), 400

    conn = None
    try:
        conn = get_pg_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id FROM dips.user_otps
            WHERE mobile = %s AND is_verified = TRUE
            ORDER BY created_at DESC LIMIT 1;
        """, (mobile,))
        verified_otp = cur.fetchone()

        if not verified_otp:
            return jsonify({"error": "Mobile number not verified"}), 400

        cur.execute("""
            SELECT id FROM dips.users
            WHERE email = %s OR phone = %s;
        """, (email, mobile))
        if cur.fetchone():
            return jsonify({"error": "Email or phone number already registered"}), 409

        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        cur.execute("""
            INSERT INTO dips.users (name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (name, email, mobile, password_hash))
        user_id = cur.fetchone()[0]
        conn.commit()

        return jsonify({
            "message": "User registered successfully",
            "user": {"id": user_id, "name": name, "email": email, "phone": mobile}
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        if conn:
            cur.close()
            conn.close()


@users_bp.route("/users", methods=["GET"])
def list_users():
    query = """
        SELECT id, name, email, phone, role
        FROM dips.users;
    """

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    users = [
        {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "role": role
        }
        for user_id, name, email, phone, role in rows
    ]

    return jsonify(users)
