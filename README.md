# 📢 Campaigner – Lead Generation via Referral Campaigns

**Campaigner** is a Django-based web application that enables business owners to generate leads through referral campaigns. It works like an affiliate program—businesses can create campaigns, onboard initial customers, and empower them to refer others in exchange for rewards.

🚀 **Live Demo**: [https://campaigner-oioe.onrender.com/](https://campaigner-oioe.onrender.com/)

🎥 **Watch Demo Video**  
[![Campaigner Demo](https://www.loom.com/share/0da0c82f2ca342c2b20193bf3bf3aa8c?sid=4e5cbffd-9302-489b-b5a1-a78274d51280)](https://www.loom.com/share/0da0c82f2ca342c2b20193bf3bf3aa8c?sid=4e5cbffd-9302-489b-b5a1-a78274d51280)


🚀 **Demo Video**: https://www.loom.com/share/0da0c82f2ca342c2b20193bf3bf3aa8c?sid=4e5cbffd-9302-489b-b5a1-a78274d51280

---

## 🌟 Features

- Business owners can create and manage referral campaigns
- Customers can refer new individuals using unique referral links
- Dashboard to track campaign performance and rewards
- Secure user authentication for businesses and customers
- Admin panel to manage all users and campaigns

---

## 🛠️ Getting Started

To run this project locally, follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/campaigner.git
cd campaigner
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
# Create virtual environment
python3 -m venv env

# Activate virtual environment
# On macOS/Linux
source env/bin/activate
# On Windows
env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up the Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (for admin access)

```bash
python manage.py createsuperuser
```

### 6. Run the Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧾 Tech Stack

- **Backend**: Django (Python)
- **Database**: SQLite (for local dev), can be switched to PostgreSQL for production
- **Frontend**: Django templates, Bootstrap (optional)
- **Deployment**: Deployed on [your hosting provider, e.g., Render, Vercel, Heroku]

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License.
