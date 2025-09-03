from app.db.postgres import get_pg_connection

def init_db():
    conn = get_pg_connection()
    cur = conn.cursor()

    cur.execute("CREATE SCHEMA IF NOT EXISTS dips;")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dips.users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        phone VARCHAR(20),
        role VARCHAR(20) DEFAULT 'customer',
        password_hash TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dips.user_otps (
        id SERIAL PRIMARY KEY,
        mobile VARCHAR(20) NOT NULL,
        otp VARCHAR(6) NOT NULL,
        mb_id VARCHAR(50),
        is_verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dips.services (
        id SERIAL PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        category VARCHAR(50),
        duration INT,
        price NUMERIC(10,2)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dips.staff (
        id SERIAL PRIMARY KEY,
        name VARCHAR(120) NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dips.staff_services (
        staff_id INT REFERENCES dips.staff(id) ON DELETE CASCADE,
        service_id INT REFERENCES dips.services(id) ON DELETE CASCADE,
        PRIMARY KEY (staff_id, service_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dips.bookings (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES dips.users(id) ON DELETE CASCADE,
        staff_id INT REFERENCES dips.staff(id) ON DELETE CASCADE,
        service_id INT REFERENCES dips.services(id) ON DELETE CASCADE,
        date DATE NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        status VARCHAR(20) DEFAULT 'pending'
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
