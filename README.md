* This is an analytics application for generating a weekly performance report for a typical large Investment Bank
* The application is generated with the following products in scope

  * Cash Equity
  * Fixed Income – Bonds, NCD, Secured Notes
  * Repos
  * Forex – Spot

* Derivatives – Equity, Forex, Interest rate and Credit
* Developed in python and streamlit, the application uses synthetically generated data of around 51000+ deals
* Application includes several dashboards to track weekly performance of deal volume/value, stp metrics, disputed margin calls etc
* App is developed in gitactions using python and streamlit with Google Gemma 2b as the LLM and Langchain for the development of AI agent
* app\_core directory has analytics.py loads the data from csv files (synthetic data related to investment banking operations), normalizes the data and generates key analytics related to performance of the investment banking business
* charts under app\_core directory has 7 python scripts needed to develop 7 charts using matplotlib as the presentation layer for the analytics 
* To automate the generation of the report 3 agents are present - data loading agent, analytics agent and chart agent (saved under \\agents directory), the first 2 agents being traditional agents and last agent being AI agent using Langchain and Google Gemma 2b. Chart agent, apart from automating the generation of 7 charts, also provides a weekly highlights generated using Gemma
* Synthetic data is saved in the form of csv files under \\data direcotory and the python scripts used in the generation of synthetic data is saved in \\datagen directory
* Application is deployed and triggered in gitactions and the streamlit is integrated with github. App can be triggered manually in gitactions and the dashboard is automatically updated in streamlit (through app.py). App is scheduled to run on every monday at 2 am 
* Due to constrained compute and storage resources, Gemma 2b is used with a limited functionality of generating weekly highlights. This architecture can be extended to generate more comprehensive weekly highlights functionality using larger Gemma models, using bank specific SFT training of the model and better prompt engineering. Data loading agent can be enhanced to AI agent to better understand data issues and possibly resolve them automatically 
