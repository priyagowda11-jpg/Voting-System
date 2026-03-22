from flask import Flask, render_template, request, jsonify, session
import psycopg2  # type: ignore
import psycopg2.extras  # type: ignore
import os
from datetime import datetime
import socket
from dotenv import load_dotenv  # type: ignore
from auth_routes import auth_bp, login_required  # type: ignore

load_dotenv()  # loads DATABASE_URL from .env locally; Render uses env vars directly

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 3600
app.config["SESSION_COOKIE_HTTPONLY"] = False

# ── In-memory state (unchanged) ───────────────────────────────────────────────
pending_registrations = {}
pending_verifications = {}
verification_results = {}
verified_users = {}
lcd_message = {"line1": "Aadhaar Voting", "line2": "System Ready"}


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def get_conn():
    """Return a new psycopg2 connection to Supabase."""
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def init_db():
    """
    Create all tables if they don't exist.
    PostgreSQL differences from SQLite:
      - ? placeholders  → %s
      - INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
      - TEXT PRIMARY KEY → TEXT PRIMARY KEY (same)
      - BOOLEAN / INTEGER DEFAULT 0 → INTEGER DEFAULT 0 (kept same for compat)
    """
    conn = get_conn()
    c = conn.cursor()

    # Voters
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS voters (
            aadhaar_no      TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            age             INTEGER NOT NULL,
            city            TEXT NOT NULL,
            registered_city TEXT NOT NULL,
            fingerprint_id  INTEGER UNIQUE,
            voted           INTEGER DEFAULT 0,
            registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Votes
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id          SERIAL PRIMARY KEY,
            aadhaar_no  TEXT NOT NULL,
            candidate   TEXT NOT NULL,
            city        TEXT NOT NULL,
            vote_method TEXT NOT NULL,
            vote_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (aadhaar_no) REFERENCES voters(aadhaar_no)
        )
    """
    )

    # Migrated votes
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS migrated_votes (
            id              SERIAL PRIMARY KEY,
            aadhaar_no      TEXT NOT NULL,
            candidate       TEXT NOT NULL,
            registered_city TEXT NOT NULL,
            voting_city     TEXT NOT NULL,
            vote_method     TEXT NOT NULL,
            vote_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Fraud logs
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS fraud_logs (
            id           SERIAL PRIMARY KEY,
            aadhaar_no   TEXT,
            issue        TEXT NOT NULL,
            attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Admins (for auth_routes)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            phone      TEXT,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


# ── Fraud logger ──────────────────────────────────────────────────────────────
def log_fraud(aadhaar, issue):
    conn = get_conn()
    c = conn.cursor()
    # %s instead of ?
    c.execute(
        "INSERT INTO fraud_logs (aadhaar_no, issue) VALUES (%s, %s)", (aadhaar, issue)
    )
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# LCD MESSAGE
# ══════════════════════════════════════════════════════════════════════════════
def set_lcd_message(line1, line2):
    global lcd_message
    lcd_message = {"line1": line1[:16], "line2": line2[:16]}
    print(f"\n📟 LCD: '{line1}' | '{line2}'\n")


@app.route("/nodemcu/get_lcd", methods=["GET"])
def get_lcd_message():
    return jsonify(lcd_message)


# ══════════════════════════════════════════════════════════════════════════════
# WEB ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    data = request.form
    aadhaar = data.get("aadhaar")
    name = data.get("name")
    age = int(data.get("age"))
    city = data.get("city")

    if age < 18:
        return jsonify({"status": "error", "message": "Must be 18+ to register"})

    conn = get_conn()
    c = conn.cursor()
    # %s placeholder
    c.execute("SELECT 1 FROM voters WHERE aadhaar_no = %s", (aadhaar,))
    if c.fetchone():
        conn.close()
        set_lcd_message("Already", "Registered!")
        return jsonify({"status": "error", "message": "Already registered"})
    conn.close()

    pending_registrations[aadhaar] = {
        "name": name,
        "age": age,
        "city": city,
        "registered_city": city,
    }
    set_lcd_message("Registration", "Place Finger...")
    return jsonify({"status": "pending", "message": "Place finger on sensor"})


@app.route("/verify", methods=["POST"])
def verify():
    data = request.form
    aadhaar = data.get("aadhaar")
    city = data.get("city")

    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT fingerprint_id, name FROM voters WHERE aadhaar_no = %s", (aadhaar,)
    )
    voter = c.fetchone()
    conn.close()

    if not voter:
        set_lcd_message("Not Registered!", "Please Register")
        return jsonify({"status": "error", "message": "Voter not registered"})

    if aadhaar not in pending_verifications:
        pending_verifications[aadhaar] = {
            "fingerprint_id": voter["fingerprint_id"],
            "name": voter["name"],
            "city": city,
            "attempts": 0,
        }

    set_lcd_message("Verification", "Place Finger...")
    return jsonify({"status": "success", "message": "Place finger on sensor"})


@app.route("/vote", methods=["POST"])
def vote():
    aadhaar = request.form.get("aadhaar")
    candidate = request.form.get("candidate")

    if aadhaar not in verified_users or not verified_users[aadhaar].get("verified"):
        return jsonify({"status": "error", "message": "Please verify first"})

    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT voted, registered_city, name FROM voters WHERE aadhaar_no = %s",
        (aadhaar,),
    )
    result = c.fetchone()

    if result["voted"] == 1:
        conn.close()
        log_fraud(aadhaar, "Duplicate vote attempt via web")
        set_lcd_message("Already Voted!", "Cannot Vote Again")
        return jsonify({"status": "error", "message": "Already Voted!"})

    registered_city = result["registered_city"]
    voting_city = verified_users[aadhaar]["voting_city"]

    if registered_city == voting_city:
        c.execute(
            """
            INSERT INTO votes (aadhaar_no, candidate, city, vote_method)
            VALUES (%s, %s, %s, %s)
        """,
            (aadhaar, candidate, voting_city, "online"),
        )
    else:
        c.execute(
            """
            INSERT INTO migrated_votes
                (aadhaar_no, candidate, registered_city, voting_city, vote_method)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (aadhaar, candidate, registered_city, voting_city, "online"),
        )

    c.execute("UPDATE voters SET voted = 1 WHERE aadhaar_no = %s", (aadhaar,))
    conn.commit()
    conn.close()

    del verified_users[aadhaar]
    set_lcd_message("Vote Recorded!", "Thank You!")
    return jsonify({"status": "success", "message": "Vote recorded successfully!"})


# ══════════════════════════════════════════════════════════════════════════════
# NODEMCU ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/nodemcu/poll", methods=["GET"])
def nodemcu_poll():
    if pending_registrations:
        aadhaar = list(pending_registrations.keys())[0]
        return jsonify({"action": "register", "aadhaar": aadhaar})

    if pending_verifications:
        aadhaar = list(pending_verifications.keys())[0]
        data = pending_verifications[aadhaar]
        return jsonify(
            {
                "action": "verify",
                "aadhaar": aadhaar,
                "fingerprint_id": data["fingerprint_id"],
                "attempts": data.get("attempts", 0),
            }
        )

    return jsonify({"action": "none"})


@app.route("/nodemcu/register_complete", methods=["POST"])
def register_complete():
    data = request.json
    aadhaar = data.get("aadhaar")
    fingerprint_id = data.get("fingerprint_id")

    if aadhaar not in pending_registrations:
        return jsonify({"status": "error", "message": "No pending registration"})

    voter_data = pending_registrations[aadhaar]
    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute(
            """
            INSERT INTO voters
                (aadhaar_no, name, age, city, registered_city, fingerprint_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                aadhaar,
                voter_data["name"],
                voter_data["age"],
                voter_data["city"],
                voter_data["registered_city"],
                fingerprint_id,
            ),
        )
        conn.commit()
        conn.close()
        del pending_registrations[aadhaar]
        set_lcd_message("Registration", "Successful!")
        print(f"✅ Registered: {voter_data['name']} | FP-ID: {fingerprint_id}")
        return jsonify({"status": "success", "message": "Registration complete"})

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        conn.close()
        del pending_registrations[aadhaar]
        set_lcd_message("Fingerprint", "Already Exists!")
        return jsonify({"status": "error", "message": "Fingerprint already exists"})


@app.route("/nodemcu/verify_complete", methods=["POST"])
def verify_complete():
    data = request.json
    aadhaar = data.get("aadhaar")
    matched = data.get("matched")

    if aadhaar not in pending_verifications:
        return jsonify({"status": "error", "message": "No pending verification"})

    if matched:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT name, registered_city FROM voters WHERE aadhaar_no = %s", (aadhaar,)
        )
        voter = c.fetchone()
        conn.close()

        voter_name = voter["name"] if voter else "Unknown"
        registered_city = voter["registered_city"] if voter else "Unknown"
        voting_city = pending_verifications[aadhaar]["city"]
        is_migrated = registered_city != voting_city

        verified_users[aadhaar] = {
            "verified": True,
            "voting_city": voting_city,
            "registered_city": registered_city,
        }

        session.permanent = True
        session["aadhaar"] = aadhaar
        session["voting_city"] = voting_city
        session["verified"] = True
        session.modified = True

        verification_results[aadhaar] = {
            "status": "verified",
            "message": "Verified! You can vote now.",
            "migrated": is_migrated,
            "registered_city": registered_city,
            "voting_city": voting_city,
        }

        del pending_verifications[aadhaar]
        set_lcd_message("Welcome!", voter_name[:16])

        return jsonify(
            {
                "status": "success",
                "message": "Verified! You can vote now.",
                "migrated": is_migrated,
            }
        )

    else:
        pending_verifications[aadhaar]["attempts"] += 1
        attempts = pending_verifications[aadhaar]["attempts"]

        if attempts >= 3:
            log_fraud(aadhaar, f"Multiple fingerprint mismatch attempts ({attempts})")
            verification_results[aadhaar] = {
                "status": "fraud",
                "message": "Multiple failed attempts. Access blocked.",
                "attempts": attempts,
            }
            del pending_verifications[aadhaar]
            set_lcd_message("FRAUD ALERT!", "Access Blocked")
            return jsonify(
                {
                    "status": "fraud",
                    "message": "Multiple failed attempts. Access blocked.",
                }
            )
        else:
            log_fraud(aadhaar, "Fingerprint mismatch during verification")
            verification_results[aadhaar] = {
                "status": "error",
                "message": "Fingerprint mismatch. Please try again.",
                "attempts": attempts,
                "show_retry": True,
            }
            set_lcd_message("Mismatch!", f"Try Again ({attempts}/3)")
            return jsonify(
                {
                    "status": "error",
                    "message": "Fingerprint mismatch. Please try again.",
                    "attempts": attempts,
                }
            )


# ══════════════════════════════════════════════════════════════════════════════
# OFFLINE VOTING (hardware button)
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/nodemcu/cast_vote", methods=["POST"])
def cast_vote_offline():
    data = request.json
    aadhaar = data.get("aadhaar")
    candidate = data.get("candidate")
    fingerprint_id = data.get("fingerprint_id")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM voters WHERE aadhaar_no = %s", (aadhaar,))
    voter = c.fetchone()

    if not voter:
        conn.close()
        log_fraud(aadhaar, "Unregistered user attempted offline voting")
        set_lcd_message("FRAUD!", "Unregistered User")
        return jsonify(
            {
                "status": "fraud",
                "message": "Unregistered User",
                "lcd_msg": "FRAUD! Unregistered",
            }
        )

    if voter["voted"] == 1:
        conn.close()
        log_fraud(aadhaar, "Duplicate offline vote attempt")
        set_lcd_message("Already Voted!", "Cannot Vote Again")
        return jsonify(
            {
                "status": "already_voted",
                "message": "Already Voted",
                "lcd_msg": "Already Voted!",
            }
        )

    if voter["fingerprint_id"] != fingerprint_id:
        conn.close()
        log_fraud(aadhaar, "Wrong fingerprint during offline voting")
        set_lcd_message("FRAUD!", "Wrong Finger")
        return jsonify(
            {
                "status": "fraud",
                "message": "Wrong Fingerprint",
                "lcd_msg": "FRAUD! Wrong Finger",
            }
        )

    registered_city = voter["registered_city"]
    voting_city = voter["city"]
    voter_name = voter["name"]

    if registered_city == voting_city:
        c.execute(
            """
            INSERT INTO votes (aadhaar_no, candidate, city, vote_method)
            VALUES (%s, %s, %s, %s)
        """,
            (aadhaar, candidate, voting_city, "offline"),
        )
    else:
        c.execute(
            """
            INSERT INTO migrated_votes
                (aadhaar_no, candidate, registered_city, voting_city, vote_method)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (aadhaar, candidate, registered_city, voting_city, "offline"),
        )

    c.execute("UPDATE voters SET voted = 1 WHERE aadhaar_no = %s", (aadhaar,))
    conn.commit()
    conn.close()

    set_lcd_message("Vote Recorded!", "Thank You!")
    print(f"✅ OFFLINE VOTE: {voter_name} → {candidate}")
    return jsonify(
        {"status": "success", "message": "Vote Recorded", "lcd_msg": "Vote Recorded ✅"}
    )


# ══════════════════════════════════════════════════════════════════════════════
# CHECK STATUS ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/check_registration/<aadhaar>", methods=["GET"])
def check_registration(aadhaar):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT name, fingerprint_id FROM voters WHERE aadhaar_no = %s", (aadhaar,)
    )
    voter = c.fetchone()
    conn.close()

    if voter:
        return jsonify(
            {
                "status": "complete",
                "name": voter["name"],
                "fingerprint_id": voter["fingerprint_id"],
            }
        )
    elif aadhaar in pending_registrations:
        return jsonify({"status": "pending"})
    else:
        return jsonify({"status": "not_found"})


@app.route("/check_verification/<aadhaar>", methods=["GET"])
def check_verification(aadhaar):
    if aadhaar in verification_results:
        result = verification_results.pop(aadhaar)
        return jsonify(result)

    if session.get("aadhaar") == aadhaar and session.get("verified"):
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT registered_city FROM voters WHERE aadhaar_no = %s", (aadhaar,)
        )
        voter = c.fetchone()
        conn.close()
        return jsonify(
            {
                "status": "verified",
                "aadhaar": aadhaar,
                "migrated": (
                    voter["registered_city"] != session.get("voting_city")
                    if voter
                    else False
                ),
                "registered_city": voter["registered_city"] if voter else "Unknown",
                "voting_city": session.get("voting_city", "Unknown"),
            }
        )

    if aadhaar in pending_verifications:
        return jsonify(
            {
                "status": "pending",
                "attempts": pending_verifications[aadhaar].get("attempts", 0),
            }
        )

    return jsonify({"status": "not_verified"})


@app.route("/check_session", methods=["GET"])
def check_session():
    aadhaar = request.args.get("aadhaar")
    if (
        aadhaar
        and aadhaar in verified_users
        and verified_users[aadhaar].get("verified")
    ):
        return jsonify(
            {
                "logged_in": True,
                "aadhaar": aadhaar,
                "voting_city": verified_users[aadhaar].get("voting_city", "Unknown"),
            }
        )
    return jsonify({"logged_in": False})


# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


if __name__ == "__main__":
    init_db()
    local_ip = get_local_ip()
    port = 5000

    print("\n" + "=" * 70)
    print("🗳️  AADHAAR VOTING SYSTEM — SUPABASE (PostgreSQL)")
    print("=" * 70)
    print(f"\n📡 Server: http://{local_ip}:{port}")
    print(f'🔧 ESP32:  String serverURL = "http://{local_ip}:{port}";')
    print("\n⚠️  After deploy, update ESP32 to your Render URL!")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=port, debug=True)
