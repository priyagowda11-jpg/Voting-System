# 🗳️ Aadhaar-Based Voting System

A secure, modern web-based voting system using Aadhaar verification with support for voter migration and real-time analytics dashboard.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)

## ✨ Features

### 🔐 Core Voting Features
- **Aadhaar-based Registration**: Secure voter registration with Aadhaar validation
- **Biometric Verification**: Fingerprint-based voter authentication
- **Age Validation**: Automatic age calculation (18+ years required)
- **Duplicate Prevention**: Prevents multiple votes from same voter
- **Voter Migration**: Support for voters who migrate between cities
- **Session Management**: Secure session handling for verified voters

### 📊 Dashboard Analytics
- **Real-time Statistics**: Live vote counting and analytics
- **Election Results**: Combined and separate vote tallies
- **City-wise Analysis**: Voting patterns by city
- **Migration Tracking**: Monitor voter migration patterns
- **Recent Activity**: View last 10 votes (with privacy protection)
- **Turnout Percentage**: Calculate voter participation rate

### 🎨 User Interface
- **Modern Design**: Clean, responsive Bootstrap 5 interface
- **Sidebar Navigation**: Easy navigation between pages
- **Success Messages**: Clear feedback for all actions
- **Auto-redirect**: Smooth page transitions after voting
- **Candidate Photos**: Visual candidate selection
- **Gradient Dashboard**: Beautiful analytics visualization

## 📁 Project Structure

```
aadhaar-voting-system/
├── app.py                      # Main voting application
├── dashboard.py                # Analytics dashboard
├── fix_database.py             # Database update utility
├── voting.db                   # SQLite database (auto-created)
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
├── templates/
│   ├── index.html             # Voting interface
│   └── dashboard.html         # Dashboard interface
└── static/
    ├── aap.jpg                # AAP party logo
    ├── bjp.jpg                # BJP party logo
    ├── congress.jpg           # Congress party logo
    ├── jds.jpg                # JDS party logo
    ├── rjd.jpg                # RJD party logo
    └── placeholder.jpg        # Fallback image
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/aadhaar-voting-system.git
cd aadhaar-voting-system
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create Required Directories
```bash
mkdir templates
mkdir static
```

### Step 5: Add Candidate Photos
Place the following images in the `static/` folder:
- `aap.jpg`
- `bjp.jpg`
- `congress.jpg`
- `jds.jpg`
- `rjd.jpg`
- `placeholder.jpg`

## 📦 Dependencies

Create a `requirements.txt` file with:

```txt
Flask==2.3.0
python-dateutil==2.8.2
```

## 🎮 Usage

### Running the Main Voting Application

```bash
python app.py
```

Access at: **http://127.0.0.1:5000**

### Running the Dashboard

Open a **new terminal** (keep app.py running):

```bash
python dashboard.py
```

Access at: **http://127.0.0.1:5001/dashboard**

## 📖 User Guide

### 1. Voter Registration
1. Navigate to **Register** page
2. Enter the following details:
   - Aadhaar Number (12 digits)
   - Full Name
   - Date of Birth
   - City
   - Fingerprint ID
3. Click **Register**
4. Success message will appear

### 2. Voter Verification
1. Navigate to **Verify** page
2. Enter:
   - Aadhaar Number
   - Fingerprint ID
   - Voting City
3. Click **Verify**
4. If successful, click **Proceed to Vote**

### 3. Casting Vote
1. After verification, you'll see candidate list
2. Select one candidate (radio button)
3. Click **Submit Vote**
4. Success message appears for 3 seconds
5. Auto-redirects to Verify page

### 4. Viewing Results
1. Open dashboard at http://127.0.0.1:5001/dashboard
2. View:
   - Total statistics
   - Election results
   - City-wise breakdown
   - Migration patterns
   - Recent votes

## 🗄️ Database Schema

### Tables

#### 1. `voters`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| aadhaar_no | TEXT | Unique Aadhaar number |
| name | TEXT | Voter name |
| dob | TEXT | Date of birth |
| city | TEXT | Registered city |
| fingerprint | TEXT | Fingerprint ID |
| voted | INTEGER | Vote status (0/1) |
| register_time | TIMESTAMP | Registration time |

#### 2. `votes`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| aadhaar_no | TEXT | Voter's Aadhaar |
| candidate | TEXT | Chosen candidate |
| city | TEXT | Voting city |
| vote_time | TIMESTAMP | Vote timestamp |

#### 3. `migrated_votes`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| aadhaar_no | TEXT | Voter's Aadhaar |
| candidate | TEXT | Chosen candidate |
| registered_city | TEXT | Original city |
| voting_city | TEXT | Current voting city |
| vote_time | TIMESTAMP | Vote timestamp |

#### 4. `candidates`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Candidate/Party name |
| photo | TEXT | Photo filename |

#### 5. `fraud_logs`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| aadhaar_no | TEXT | Suspicious Aadhaar |
| issue | TEXT | Fraud description |

## 🛠️ Troubleshooting

### Issue: Images Not Showing

**Solution 1: Update Database**
```bash
python fix_database.py
```

**Solution 2: Manual Update**
```python
import sqlite3
conn = sqlite3.connect("voting.db")
cursor = conn.cursor()
cursor.execute("UPDATE candidates SET photo='congress.jpg' WHERE name='Congress'")
cursor.execute("UPDATE candidates SET photo='bjp.jpg' WHERE name='BJP'")
cursor.execute("UPDATE candidates SET photo='rjd.jpg' WHERE name='RJD'")
cursor.execute("UPDATE candidates SET photo='aap.jpg' WHERE name='AAP'")
cursor.execute("UPDATE candidates SET photo='jds.jpg' WHERE name='JDS'")
conn.commit()
conn.close()
```

### Issue: Port Already in Use

**Change Port in app.py:**
```python
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5002)  # Change port
```

### Issue: Module Not Found

**Reinstall dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue: Database Locked

**Stop all running instances:**
```bash
# Kill all Python processes
# Windows: Task Manager → End Python tasks
# Linux/Mac: killall python
```

## 🔒 Security Features

- ✅ Aadhaar validation (12-digit check)
- ✅ Age verification (18+ years)
- ✅ Fingerprint authentication
- ✅ Duplicate vote prevention
- ✅ Session management
- ✅ Vote anonymity (masked Aadhaar in dashboard)
- ✅ SQL injection prevention (parameterized queries)

## 🚨 Important Notes

### Privacy & Security
- Aadhaar numbers are **masked** in dashboard (last 4 digits only)
- Fingerprint data is stored as simple IDs (not actual biometric data)
- Sessions cleared after voting
- No direct vote-to-voter linking in public view

### Production Considerations
⚠️ **This is a demonstration project. For production use:**
- Implement real biometric authentication
- Add HTTPS/SSL encryption
- Use stronger secret keys
- Implement proper access control
- Add audit logging
- Use production database (PostgreSQL/MySQL)
- Add rate limiting
- Implement CAPTCHA
- Add email/SMS verification

## 🎯 Future Enhancements

- [ ] Real biometric scanner integration
- [ ] Multi-language support
- [ ] Mobile app version
- [ ] QR code-based voting
- [ ] Live results broadcasting
- [ ] Admin panel for election management
- [ ] Voter ID card generation
- [ ] Email/SMS notifications
- [ ] Export results to PDF/Excel
- [ ] Blockchain integration for transparency

## 📊 Sample Data

### Test Voters
You can use these for testing:

| Aadhaar | Name | DOB | City | Fingerprint |
|---------|------|-----|------|-------------|
| 123456789012 | Raj Kumar | 1990-01-15 | Delhi | FP001 |
| 234567890123 | Priya Sharma | 1995-05-20 | Mumbai | FP002 |
| 345678901234 | Amit Patel | 1988-08-10 | Bangalore | FP003 |

## 📞 Support

For issues, questions, or contributions:
- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/aadhaar-voting-system/issues)
- 📖 Wiki: [Project Wiki](https://github.com/yourusername/aadhaar-voting-system/wiki)

## 📄 License

This project is licensed under the MIT License - see below:

```
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👥 Contributors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Bootstrap team for the UI framework
- Flask community for the web framework
- Election Commission of India for inspiration
- All contributors and testers

## 📸 Screenshots

### Voting Interface
![Voting Interface](screenshots/voting.png)

### Dashboard
![Dashboard](screenshots/dashboard.png)

---

**Made with ❤️ for secure and transparent elections**

**⭐ Star this repo if you find it helpful!**