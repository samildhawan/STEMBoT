# MathScraper
This README document provides a comprehensive guide to assist you in successfully setting up and running the MathScraper project. Please follow these steps carefully to ensure optimal functionality.

### Step 1: Environment Setup
Commence the setup process by installing the necessary environment, which can be achieved by utilising the provided `requirements.txt` file. This file contains a list of necessary Python packages for this project.

### Step 2: Modify Py_asciimath Package
In the `py_asciimath` site package, locate the file named `latex.py`. Replace the existing version of this file with the one provided as part of the MathScraper project. This modification ensures compatibility with the specific functionalities of the project.

### Step 3: User Data Directory Update
For the proper functioning of the project, it is essential to update the user data directory of Google Chrome in the `scraper.py` file. To do this, navigate to line 382 and replace the `usr_data_dir` placeholder with your personal Google Chrome user data directory path.

### Step 4: Execution of MathScraper
With the environment set up and the necessary modifications implemented, you are ready to run the MathScraper project. Execute the `scraper.py` script to generate the required Python script.