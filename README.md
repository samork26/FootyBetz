# **Instructions for Setting Up**

## **1. Install Required Tools**
Ensure you have the following installed:
- **Python (3.9 or later):** [Download Python](https://www.python.org/downloads/)
- **Git:** [Install Git](https://git-scm.com/)
- **VS Code** or any text editor: [Download VS Code](https://code.visualstudio.com/)

---

## **2. Clone the Project Repository**
```bash
# Navigate to your desired folder
cd path/to/your/folder

# Clone the repository
git clone <repository-url>

# Navigate into the project folder
cd <project-folder-name>
```

---

## **3. Set Up the Virtual Environment**
```bash
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

```

---

## **4. Install Django** 

1. Install Django using pip:
   ```bash
   pip install django
   ```

2. Verify the installation:
   ```bash
   python -m django --version
   ```
   This will display the installed Django version.
---

## **4. Run the Django Development Server**
```bash
# Run the Django development server
python manage.py runserver
```

Open your browser and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

