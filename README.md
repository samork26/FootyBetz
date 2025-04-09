# **Instructions for Deploying**

## **1. Install Required Tools**
Ensure you have the following installed:
- **Python (3.9 or later):** [Download Python](https://www.python.org/downloads/)
- **Git:** [Install Git](https://git-scm.com/)
---

## **2. Clone the Project Repository**
```bash
# Navigate to your desired folder
cd path/to/your/folder

# Clone the repository
git clone https://github.com/samork26/FootyBetz.git

# Navigate into the project folder
cd FootyBetz
```
---

## 3. Make an .env file, and populate the API keys. 
```bash 
touch .env
```
Please be sure to not commit this file! ^
---

## 4a. Run the start script - for Linux/MacOS
```bash 
./startup.sh 
```
---

## 4b. Run the start script - for Windows
```bash 
.\startup.bat
```
---

## 5a. Activate the virtual env (in case it isn't already) - for Linux/MacOS
```bash 
source venv/bin/activate
```
---

## 5b. Activate the virtual env (in case it isn't already) - for Windows
```bash
source venv\bin\activate
```
---

## 6. To run the server locally
```bash
python manage.py runserver
```
---

# **Usage of AI**
Used AI to:
1. Generate generic templates
2. Generic Tailwind classes for styling
3. Ideas for db model setup
4. Generate the Batch script
5. Organize our directory effectively