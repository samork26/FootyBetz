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
Used ChatGPT 4o and o3-mini-high to:
1. Generate generic templates (app/templates/...)     
    Prompt used:   
    &nbsp;&nbsp;&nbsp;&nbsp;"Can you generate a basic base template using django-tailwind?"  
    &nbsp;&nbsp;&nbsp;&nbsp;"Can you generate a basic league / match table using django-tailwind" 
2. Generic Tailwind classes for styling
3. Ideas for db model setup (app/models.py)   
    Prompt used:    
    &nbsp;&nbsp;&nbsp;&nbsp;"I have an app that displays EPL matches and what the best betting lines are looking like for each outcome, how could the models look?"
4. Generate the Batch script (app/startup.bat)    
    Prompt used:    
    &nbsp;&nbsp;&nbsp;&nbsp;"I have this script (startup.sh), can you help me make a batch script for windows users?"
5. Organize our directory effectively    
    Prompt used:    
    &nbsp;&nbsp;&nbsp;&nbsp;"How is a django app setup, in terms of directories?"